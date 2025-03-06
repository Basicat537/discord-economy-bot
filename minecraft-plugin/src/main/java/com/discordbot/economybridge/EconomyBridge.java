package com.discordbot.economybridge;

import org.bukkit.plugin.java.JavaPlugin;
import me.clip.placeholderapi.expansion.PlaceholderExpansion;
import org.bukkit.OfflinePlayer;
import org.bukkit.entity.Player;
import org.bukkit.configuration.file.FileConfiguration;
import javax.crypto.Mac;
import javax.crypto.spec.SecretKeySpec;
import java.nio.charset.StandardCharsets;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.net.URI;
import org.json.simple.JSONObject;
import org.json.simple.parser.JSONParser;
import org.geysermc.floodgate.api.FloodgateApi;
import github.scarsz.discordsrv.DiscordSRV;
import github.scarsz.discordsrv.api.Subscribe;
import github.scarsz.discordsrv.api.events.DiscordGuildMessageReceivedEvent;
import net.luckperms.api.LuckPerms;
import net.luckperms.api.LuckPermsProvider;
import net.coreprotect.CoreProtect;
import net.coreprotect.CoreProtectAPI;
import com.sk89q.worldguard.WorldGuard;
import com.sk89q.worldguard.protection.regions.RegionContainer;
import com.sk89q.worldguard.protection.flags.registry.FlagRegistry;
import com.sk89q.worldguard.protection.flags.Flag;
import com.sk89q.worldguard.protection.flags.StateFlag;

public class EconomyBridge extends JavaPlugin {
    private static String API_URL;
    private static String API_KEY;
    private final HttpClient httpClient = HttpClient.newHttpClient();
    private FloodgateApi floodgateApi;
    private LuckPerms luckPerms;
    private DiscordSRV discordSRV;
    private CoreProtectAPI coreProtect;
    private StateFlag ALLOW_ECONOMY;

    @Override
    public void onEnable() {
        saveDefaultConfig();
        API_URL = getConfig().getString("api.url");
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

        // Инициализация LuckPerms
        if (getServer().getPluginManager().getPlugin("LuckPerms") != null) {
            luckPerms = LuckPermsProvider.get();
            getLogger().info("LuckPerms API успешно инициализирован");
        }

        // Инициализация DiscordSRV
        if (getServer().getPluginManager().getPlugin("DiscordSRV") != null) {
            discordSRV = DiscordSRV.getPlugin();
            discordSRV.getMainGuild();
            getLogger().info("DiscordSRV API успешно инициализирован");
        }

        // Инициализация CoreProtect
        if (getServer().getPluginManager().getPlugin("CoreProtect") != null) {
            CoreProtect coreProtect = (CoreProtect) getServer().getPluginManager().getPlugin("CoreProtect");
            if (coreProtect != null) {
                this.coreProtect = coreProtect.getAPI();
                if (this.coreProtect.isEnabled()) {
                    getLogger().info("CoreProtect API успешно инициализирован");
                }
            }
        }

        // Инициализация WorldGuard
        if (getServer().getPluginManager().getPlugin("WorldGuard") != null) {
            FlagRegistry registry = WorldGuard.getInstance().getFlagRegistry();
            try {
                StateFlag flag = new StateFlag("allow-economy", true);
                registry.register(flag);
                ALLOW_ECONOMY = flag;
                getLogger().info("WorldGuard флаг 'allow-economy' успешно зарегистрирован");
            } catch (Exception e) {
                Flag<?> existing = registry.get("allow-economy");
                if (existing instanceof StateFlag) {
                    ALLOW_ECONOMY = (StateFlag) existing;
                }
            }
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

            // Проверка WorldGuard региона
            if (!canUseEconomyInRegion(player)) {
                player.sendMessage("§cВы не можете использовать экономику в этом регионе!");
                return true;
            }

            try {
                int balance = getBalance(player.getUniqueId().toString());
                String message = getConfig().getString("messages.balance", "&aВаш баланс: &f%balance% монет")
                    .replace("%balance%", String.valueOf(balance))
                    .replace('&', '§');
                player.sendMessage(message);

                // Логирование в CoreProtect
                if (coreProtect != null) {
                    coreProtect.logCommand(player.getName(), "/balance");
                }
            } catch (Exception e) {
                player.sendMessage("§cОшибка при получении баланса: " + e.getMessage());
            }
            return true;
        });

        // Добавляем команду для проверки API
        getCommand("checkapi").setExecutor((sender, cmd, label, args) -> {
            if (!sender.hasPermission("economybridge.admin")) {
                sender.sendMessage("§cУ вас нет прав для выполнения этой команды!");
                return true;
            }
            try {
                HttpRequest request = HttpRequest.newBuilder()
                    .uri(URI.create(API_URL + "/balance/test"))
                    .header("X-Signature", generateSignature("test"))
                    .GET()
                    .build();

                HttpResponse<String> response = httpClient.send(request, HttpResponse.BodyHandlers.ofString());
                if (response.statusCode() == 200) {
                    sender.sendMessage("§aAPI работает корректно! Код ответа: 200");
                } else {
                    sender.sendMessage("§cAPI вернул ошибку! Код: " + response.statusCode());
                }
            } catch (Exception e) {
                sender.sendMessage("§cОшибка при проверке API: " + e.getMessage());
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

                // Проверка WorldGuard региона
                if (player.isOnline() && !canUseEconomyInRegion(player.getPlayer())) {
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

        getLogger().info("EconomyBridge успешно загружен!");
    }

    private boolean isBedrockPlayer(Player player) {
        if (floodgateApi != null) {
            return floodgateApi.isFloodgatePlayer(player.getUniqueId());
        }
        return false;
    }

    private boolean canUseEconomyInRegion(Player player) {
        if (ALLOW_ECONOMY == null) return true;
        RegionContainer container = WorldGuard.getInstance().getPlatform().getRegionContainer();
        return container.createQuery().testState(
            com.sk89q.worldedit.bukkit.BukkitAdapter.adapt(player.getLocation()),
            WorldGuard.getInstance().getPlatform().getSessionManager().get(
                com.sk89q.worldedit.bukkit.BukkitAdapter.adapt(player)
            ),
            ALLOW_ECONOMY
        );
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

        return Integer.parseInt(response.body());
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

    @Subscribe
    public void onDiscordMessage(DiscordGuildMessageReceivedEvent event) {
        // Обработка сообщений из Discord для синхронизации экономики
        if (event.getMessage().getContentRaw().startsWith("!balance")) {
            // Здесь можно добавить логику обработки команд из Discord
            getLogger().info("Получена команда баланса из Discord");
        }
    }
}