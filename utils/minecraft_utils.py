from mcstatus import JavaServer
from typing import Optional, Dict, List
import asyncio

class MinecraftServerUtils:
    def __init__(self, server_address: str):
        """Initialize with Minecraft server address"""
        self.server = JavaServer.lookup(server_address)
        
    async def get_server_status(self) -> Dict:
        """Get server status including player count and latency"""
        try:
            status = await self.server.async_status()
            return {
                'online': True,
                'players_online': status.players.online,
                'players_max': status.players.max,
                'latency': status.latency,
                'version': status.version.name
            }
        except Exception as e:
            return {
                'online': False,
                'error': str(e)
            }

    async def get_players(self) -> List[str]:
        """Get list of online players"""
        try:
            status = await self.server.async_status()
            if status.players.sample is None:
                return []
            return [player.name for player in status.players.sample]
        except Exception:
            return []

    async def is_player_online(self, username: str) -> bool:
        """Check if specific player is online"""
        try:
            players = await self.get_players()
            return username in players
        except Exception:
            return False

    async def get_player_count(self) -> Optional[int]:
        """Get number of online players"""
        try:
            status = await self.server.async_status()
            return status.players.online
        except Exception:
            return None
