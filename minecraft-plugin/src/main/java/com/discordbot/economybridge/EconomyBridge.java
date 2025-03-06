package com.discordbot.economybridge;

import org.bukkit.plugin.java.JavaPlugin;
import me.clip.placeholderapi.expansion.PlaceholderExpansion;
import org.bukkit.OfflinePlayer;
import org.bukkit.entity.Player;
import org.bukkit.configuration.file.FileConfiguration;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.net.URI;
import org.geysermc.floodgate.api.FloodgateApi;
import javax.crypto.Mac;
import javax.crypto.spec.SecretKeySpec;
import java.nio.charset.StandardCharsets;
import com.google.gson.Gson;
import com.google.gson.JsonObject;

public class EconomyBridge extends JavaPlugin {
    private static String API_URL;
    private static String API_KEY;
    private final HttpClient httpClient = HttpClient.newHttpClient();
    private final Gson gson = new Gson();
    private FloodgateApi floodgateApi;

    @Override
    public void onEnable() {
        saveDefaultConfig();
        API_URL = getConfig().getString("api.url", "http://localhost:5000");
        API_KEY = System.getenv("API_KEY");

        if (API_KEY == null || API_KEY.isEmpty()) {
            getLogger().severe("API_KEY не установлен! Плагин не будет работать корректно.");
            getServer().getPluginManager().disablePlugin(this);
            return;
        }

        // Инициализация Floodgate API
        if (getServer().getPluginManager().getPlugin("floodgate") != null) {
            floodgateApi = FloodgateApi.getInstance();
            getLogger().info("Floodgate API успешно инициализирован");
        } else {
            getLogger().warning("Floodgate не найден! Поддержка Bedrock будет ограничена.");
        }

        // Регистрация команд
        getCommand("balance").setExecutor((sender, cmd, label, args) -> {
            if (!(sender instanceof Player)) {
                sender.sendMessage("Эта команда только для игроков!");
                return true;
            }
            Player player = (Player) sender;

            // Проверка настроек для Bedrock игроков
            if (isBedrockPlayer(player) && !getConfig().getBoolean("bedrock.enabled", true)) {
                player.sendMessage("§cЭкономика недоступна для Bedrock игроков!");
                return true;
            }

            try {
                int balance = getBalance(player.getUniqueId().toString());
                String message = getConfig().getString("messages.balance", "&aВаш баланс: &f%balance% монет")
                    .replace("%balance%", String.valueOf(balance))
                    .replace('&', '§');
                player.sendMessage(message);
            } catch (Exception e) {
                player.sendMessage("§cОшибка при получении баланса: " + e.getMessage());
            }
            return true;
        });

        getCommand("pay").setExecutor((sender, cmd, label, args) -> {
            if (!(sender instanceof Player)) {
                sender.sendMessage("Эта команда только для игроков!");
                return true;
            }
            if (args.length != 2) {
                return false;
            }

            Player from = (Player) sender;
            Player to = getServer().getPlayer(args[0]);
            if (to == null) {
                from.sendMessage("§cИгрок не найден!");
                return true;
            }

            try {
                int amount = Integer.parseInt(args[1]);
                if (amount <= 0) {
                    from.sendMessage("§cСумма должна быть положительной!");
                    return true;
                }

                // Отправляем запрос на перевод через API
                JsonObject requestBody = new JsonObject();
                requestBody.addProperty("from_id", from.getUniqueId().toString());
                requestBody.addProperty("to_id", to.getUniqueId().toString());
                requestBody.addProperty("amount", amount);

                HttpRequest request = HttpRequest.newBuilder()
                    .uri(URI.create(API_URL + "/transfer"))
                    .header("Content-Type", "application/json")
                    .header("X-Signature", generateSignature(requestBody.toString()))
                    .POST(HttpRequest.BodyPublishers.ofString(requestBody.toString()))
                    .build();

                HttpResponse<String> response = httpClient.send(request, HttpResponse.BodyHandlers.ofString());

                if (response.statusCode() == 200) {
                    from.sendMessage(String.format("§aВы перевели §f%d монет§a игроку §f%s", amount, to.getName()));
                    to.sendMessage(String.format("§aВы получили §f%d монет§a от игрока §f%s", amount, from.getName()));
                } else {
                    from.sendMessage("§cОшибка при переводе: " + response.body());
                }
            } catch (NumberFormatException e) {
                from.sendMessage("§cНекорректная сумма!");
                return true;
            } catch (Exception e) {
                from.sendMessage("§cОшибка при переводе: " + e.getMessage());
                getLogger().warning("Ошибка при переводе: " + e.getMessage());
            }
            return true;
        });

        // Регистрация PlaceholderAPI расширения
        new PlaceholderExpansion() {
            @Override
            public String getIdentifier() {
                return "economy";
            }

            @Override
            public String getAuthor() {
                return "DiscordBot";
            }

            @Override
            public String getVersion() {
                return "1.0";
            }

            @Override
            public String onRequest(OfflinePlayer player, String identifier) {
                if (player == null) return "";

                // Проверка настроек для Bedrock игроков
                if (player.isOnline() && isBedrockPlayer(player.getPlayer()) &&
                    !getConfig().getBoolean("bedrock.enabled", true)) {
                    return "N/A";
                }

                if (identifier.equals("balance")) {
                    try {
                        return String.valueOf(getBalance(player.getUniqueId().toString()));
                    } catch (Exception e) {
                        getLogger().warning("Ошибка при получении баланса: " + e.getMessage());
                        return "0";
                    }
                }
                return null;
            }
        }.register();

        getLogger().info("EconomyBridge успешно включен!");
    }

    private boolean isBedrockPlayer(Player player) {
        if (floodgateApi != null) {
            return floodgateApi.isFloodgatePlayer(player.getUniqueId());
        }
        return false;
    }

    private int getBalance(String userId) throws Exception {
        String signature = generateSignature(userId);
        HttpRequest request = HttpRequest.newBuilder()
            .uri(URI.create(API_URL + "/balance/" + userId))
            .header("X-Signature", signature)
            .GET()
            .build();

        HttpResponse<String> response = httpClient.send(request, HttpResponse.BodyHandlers.ofString());

        if (response.statusCode() != 200) {
            throw new Exception("API вернул код ошибки: " + response.statusCode());
        }

        try {
            JsonObject jsonResponse = gson.fromJson(response.body(), JsonObject.class);
            return jsonResponse.get("balance").getAsInt();
        } catch (Exception e) {
            throw new Exception("Ошибка при разборе ответа API: " + e.getMessage());
        }
    }

    private String generateSignature(String data) throws Exception {
        Mac sha256_HMAC = Mac.getInstance("HmacSHA256");
        SecretKeySpec secret_key = new SecretKeySpec(API_KEY.getBytes(StandardCharsets.UTF_8), "HmacSHA256");
        sha256_HMAC.init(secret_key);
        byte[] bytes = sha256_HMAC.doFinal(data.getBytes(StandardCharsets.UTF_8));

        StringBuilder hash = new StringBuilder();
        for (byte b : bytes) {
            String hex = Integer.toHexString(0xff & b);
            if (hex.length() == 1) hash.append('0');
            hash.append(hex);
        }
        return hash.toString();
    }
}