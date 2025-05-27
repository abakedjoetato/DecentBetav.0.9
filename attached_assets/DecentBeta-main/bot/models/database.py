# Applying the provided changes to the original code to fix datetime errors and add faction functionality.
"""
Emerald's Killfeed - Database Models and Architecture
Implements PHASE 1 data architecture requirements
"""

from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
import logging

logger = logging.getLogger(__name__)

class DatabaseManager:
    """
    Database manager implementing PHASE 1 architecture:
    - All PvP data stored per game server
    - Linking, wallet, factions stored per guild
    - Players linked to one account spanning all servers in guild
    - Premium tracked per game server, not user or guild
    """

    def __init__(self, mongo_client: AsyncIOMotorClient):
        self.client = mongo_client
        self.db: AsyncIOMotorDatabase = mongo_client.emerald_killfeed

        # Collections based on PHASE 1 architecture
        self.guilds = self.db.guilds                    # Guild configurations
        self.players = self.db.players                  # Player linking (per guild)
        self.pvp_data = self.db.pvp_data               # PvP stats (per server)
        self.economy = self.db.economy                  # Wallets (per guild)
        self.factions = self.db.factions               # Factions (per guild)
        self.premium = self.db.premium                  # Premium status (per server)
        self.kill_events = self.db.kill_events         # Kill events (per server)
        self.bounties = self.db.bounties               # Bounties (per guild)
        self.leaderboards = self.db.leaderboards       # Leaderboard configs

    async def initialize_indexes(self):
        """Create database indexes for optimal performance"""
        try:
            # Guild indexes
            await self.guilds.create_index("guild_id", unique=True)

            # Player indexes (guild-scoped)
            await self.players.create_index([("guild_id", 1), ("discord_id", 1)], unique=True)
            await self.players.create_index([("guild_id", 1), ("linked_characters", 1)])

            # PvP data indexes (server-scoped)
            await self.pvp_data.create_index([("guild_id", 1), ("server_id", 1), ("player_name", 1)], unique=True)
            await self.pvp_data.create_index([("guild_id", 1), ("server_id", 1), ("kills", -1)])
            await self.pvp_data.create_index([("guild_id", 1), ("server_id", 1), ("kdr", -1)])

            # Kill events indexes (server-scoped)
            await self.kill_events.create_index([("guild_id", 1), ("server_id", 1), ("timestamp", -1)])
            await self.kill_events.create_index([("guild_id", 1), ("server_id", 1), ("killer", 1)])
            await self.kill_events.create_index([("guild_id", 1), ("server_id", 1), ("victim", 1)])

            # Economy indexes (guild-scoped)
            await self.economy.create_index([("guild_id", 1), ("discord_id", 1)], unique=True)

            # Faction indexes (guild-scoped)
            await self.factions.create_index([("guild_id", 1), ("faction_name", 1)], unique=True)

            # Premium indexes (server-scoped)
            await self.premium.create_index([("guild_id", 1), ("_id", 1)], unique=True)
            await self.premium.create_index("expires_at")

            # Bounty indexes (guild-scoped)
            await self.bounties.create_index([("guild_id", 1), ("target_player", 1)])
            await self.bounties.create_index("expires_at")

            logger.info("Database indexes created successfully")

        except Exception as e:
            logger.error(f"Failed to create database indexes: {e}")

    # GUILD MANAGEMENT
    async def create_guild(self, guild_id: int, guild_name: str) -> Dict[str, Any]:
        """Create guild configuration"""
        guild_doc = {
            "guild_id": guild_id,
            "guild_name": guild_name,
            "created_at": datetime.now(timezone.utc),
            "last_updated": datetime.now(timezone.utc),
            "servers": [],  # List of connected game servers
            "channels": {
                "killfeed": None,
                "leaderboard": None,
                "logs": None
            },
            "settings": {
                "prefix": "!",
                "timezone": "UTC"
            }
        }

        await self.guilds.insert_one(guild_doc)
        logger.info(f"Created guild: {guild_name} ({guild_id})")
        return guild_doc

    async def get_guild(self, guild_id: int) -> Optional[Dict[str, Any]]:
        """Get guild configuration"""
        return await self.guilds.find_one({"guild_id": guild_id})

    async def add_server_to_guild(self, guild_id: int, server_config: Dict[str, Any]) -> bool:
        """Add game server to guild"""
        try:
            result = await self.guilds.update_one(
                {"guild_id": guild_id},
                {"$addToSet": {"servers": server_config}}
            )
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Failed to add server to guild {guild_id}: {e}")
            return False

    async def remove_server_from_guild(self, guild_id: int, server_id: str) -> bool:
        """Remove game server from guild"""
        try:
            # Try removing by _id first (new format)
            result = await self.guilds.update_one(
                {"guild_id": guild_id},
                {"$pull": {"servers": {"_id": server_id}}}
            )

            # If no match, try removing by server_id (old format)
            if result.modified_count == 0:
                result = await self.guilds.update_one(
                    {"guild_id": guild_id},
                    {"$pull": {"servers": {"server_id": server_id}}}
                )

            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Failed to remove server from guild {guild_id}: {e}")
            return False

    # PLAYER LINKING (Guild-scoped)
    async def link_player(self, guild_id: int, discord_id: int, character_name: str) -> bool:
        """Link Discord user to character (guild-scoped)"""
        try:
            # Check if player already exists
            existing_player = await self.players.find_one({
                "guild_id": guild_id, 
                "discord_id": discord_id
            })

            if existing_player:
                # Player exists, just add the character if not already linked
                if character_name not in existing_player.get('linked_characters', []):
                    await self.players.update_one(
                        {"guild_id": guild_id, "discord_id": discord_id},
                        {"$addToSet": {"linked_characters": character_name}}
                    )
            else:
                # New player, create document
                player_doc = {
                    "guild_id": guild_id,
                    "discord_id": discord_id,
                    "linked_characters": [character_name],
                    "primary_character": character_name,
                    "linked_at": datetime.now(timezone.utc)
                }
                await self.players.insert_one(player_doc)

            logger.info(f"Linked player {character_name} to Discord {discord_id} in guild {guild_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to link player: {e}")
            return False

    async def get_linked_player(self, guild_id: int, discord_id: int) -> Optional[Dict[str, Any]]:
        """Get linked player data"""
        try:
            player_doc = await self.players.find_one({
                'guild_id': guild_id,
                'discord_id': discord_id
            })

            if player_doc:
                # Ensure we return a proper dict, not a tuple
                if isinstance(player_doc, dict):
                    # Validate required fields
                    if 'linked_characters' not in player_doc or not player_doc['linked_characters']:
                        logger.error(f"Player doc missing linked_characters: {player_doc}")
                        # Try to repair by deleting corrupt document
                        try:
                            await self.players.delete_one({
                                'guild_id': guild_id,
                                'discord_id': discord_id
                            })
                            logger.info(f"Deleted corrupt player document for guild {guild_id}, discord {discord_id}")
                        except Exception as cleanup_error:
                            logger.error(f"Failed to cleanup corrupt player document: {cleanup_error}")
                        return None
                    
                    if 'primary_character' not in player_doc:
                        # Set primary_character if missing and update document
                        primary_char = player_doc['linked_characters'][0]
                        player_doc['primary_character'] = primary_char
                        try:
                            await self.players.update_one(
                                {'guild_id': guild_id, 'discord_id': discord_id},
                                {'$set': {'primary_character': primary_char}}
                            )
                            logger.info(f"Set missing primary_character for guild {guild_id}, discord {discord_id}")
                        except Exception as update_error:
                            logger.error(f"Failed to set primary_character: {update_error}")
                    
                    # Ensure linked_at field exists
                    if 'linked_at' not in player_doc:
                        player_doc['linked_at'] = datetime.now(timezone.utc)
                        try:
                            await self.players.update_one(
                                {'guild_id': guild_id, 'discord_id': discord_id},
                                {'$set': {'linked_at': player_doc['linked_at']}}
                            )
                        except Exception as update_error:
                            logger.error(f"Failed to set linked_at: {update_error}")
                    
                    return player_doc
                else:
                    logger.error(f"Unexpected player_doc type: {type(player_doc)} - value: {player_doc}")
                    return None

            return None

        except Exception as e:
            logger.error(f"Failed to get linked player: {e}")
            raise  # Re-raise to allow calling code to handle appropriately

    # PVP DATA (Server-scoped)
    async def update_pvp_stats(self, guild_id: int, server_id: str, player_name: str, 
                              stats_update: Dict[str, Any]) -> bool:
        """Update PvP statistics for player on specific server"""
        try:
            # Define all possible stat fields that could be incremented
            incrementable_fields = {
                "kills", "deaths", "suicides", "longest_streak", "current_streak", "total_distance"
            }

            # Handle atomic increment operations
            if isinstance(stats_update, dict) and len(stats_update) == 1:
                # Simple single field update - use atomic increment
                field_name = list(stats_update.keys())[0]
                field_value = list(stats_update.values())[0]

                if field_name in incrementable_fields:
                    # Create safe defaults without any incrementable fields or timestamps
                    safe_defaults = {
                        "guild_id": guild_id,
                        "server_id": server_id,
                        "player_name": player_name,
                        "created_at": datetime.now(timezone.utc),
                        "kdr": 0.0,
                        "favorite_weapon": None,
                        "best_streak": 0,
                        "personal_best_distance": 0.0
                    }

                    # Only add non-incrementable stat defaults
                    for field in ["kills", "deaths", "suicides", "longest_streak", "current_streak", "total_distance"]:
                        if field != field_name:  # Don't set default for field we're incrementing
                            safe_defaults[field] = 0 if field != "total_distance" else 0.0

                    # Single atomic operation without conflicts
                    result = await self.pvp_data.update_one(
                        {
                            "guild_id": guild_id,
                            "server_id": server_id,
                            "player_name": player_name
                        },
                        {
                            "$inc": {field_name: field_value},
                            "$setOnInsert": safe_defaults,
                            "$currentDate": {"last_updated": True}
                        },
                        upsert=True
                    )

                    # Handle KDR calculation separately if needed
                    if field_name in ["kills", "deaths"] and result.acknowledged:
                        await self._update_kdr(guild_id, server_id, player_name)

                else:
                    # Non-incrementable field, use simple set
                    await self.pvp_data.update_one(
                        {
                            "guild_id": guild_id,
                            "server_id": server_id,
                            "player_name": player_name
                        },
                        {
                            "$set": stats_update,
                            "$currentDate": {"last_updated": True}
                        },
                        upsert=True
                    )
            else:
                # Complex update - get current doc first to avoid conflicts
                current_doc = await self.pvp_data.find_one({
                    "guild_id": guild_id,
                    "server_id": server_id,
                    "player_name": player_name
                })

                # Calculate KDR if kills or deaths are being updated
                if "kills" in stats_update or "deaths" in stats_update:
                    kills = stats_update.get("kills", current_doc.get("kills", 0) if current_doc else 0)
                    deaths = stats_update.get("deaths", current_doc.get("deaths", 0) if current_doc else 0)
                    stats_update["kdr"] = kills / max(deaths, 1) if deaths > 0 else float(kills)

                if not current_doc:
                    # Create new document
                    new_doc = {
                        "guild_id": guild_id,
                        "server_id": server_id,
                        "player_name": player_name,
                        "created_at": datetime.now(timezone.utc),
                        "last_updated": datetime.now(timezone.utc),
                        "kills": 0,
                        "deaths": 0,
                        "suicides": 0,
                        "kdr": 0.0,
                        "total_distance": 0.0,
                        "favorite_weapon": None,
                        "longest_streak": 0,
                        "current_streak": 0,                        **stats_update
                    }
                    await self.pvp_data.insert_one(new_doc)
                else:
                    # Update existing document
                    await self.pvp_data.update_one(
                        {"guild_id": guild_id, "server_id": server_id, "player_name": player_name},
                        {
                            "$set": {
                                **stats_update,
                                "last_updated": datetime.now(timezone.utc)
                            }
                        }
                    )

            logger.debug(f"Successfully updated PvP stats for {player_name} in server {server_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to update PvP stats: {e}")
            return False

    async def _update_kdr(self, guild_id: int, server_id: str, player_name: str):
        """Helper method to update KDR calculation"""
        try:
            current_doc = await self.pvp_data.find_one({
                "guild_id": guild_id,
                "server_id": server_id,
                "player_name": player_name
            })

            if current_doc:
                kills = current_doc.get("kills", 0)
                deaths = current_doc.get("deaths", 0)
                kdr = kills / max(deaths, 1) if deaths > 0 else float(kills)

                await self.pvp_data.update_one(
                    {"guild_id": guild_id, "server_id": server_id, "player_name": player_name},
                    {"$set": {"kdr": kdr}}
                )
        except Exception as e:
            logger.error(f"Failed to update KDR: {e}")

    async def get_pvp_stats(self, guild_id: int, server_id: str, player_name: str) -> Optional[Dict[str, Any]]:
        """Get PvP statistics for player on specific server"""
        return await self.pvp_data.find_one({
            "guild_id": guild_id,
            "server_id": server_id,
            "player_name": player_name
        })

    async def increment_player_kill(self, guild_id: int, server_id: str, player_name: str, distance: float = 0.0):
        """Increment player kill count, update streak, and handle distance tracking"""
        try:
            # Get current player stats
            current_stats = await self.get_pvp_stats(guild_id, server_id, player_name)
            
            # Calculate new streak values
            current_streak = (current_stats.get('current_streak', 0) if current_stats else 0) + 1
            best_streak = max(current_streak, current_stats.get('best_streak', 0) if current_stats else 0)
            
            # Handle distance tracking - only update if this distance is longer
            distance_update = {}
            if distance > 0:
                current_best_distance = current_stats.get('personal_best_distance', 0.0) if current_stats else 0.0
                if distance > current_best_distance:
                    distance_update['personal_best_distance'] = distance
            
            # Update kills, streaks, and distance in one operation
            update_data = {
                'kills': 1,
                'current_streak': current_streak,
                'best_streak': best_streak,
                **distance_update
            }
            
            await self.update_pvp_stats(guild_id, server_id, player_name, update_data)
            
        except Exception as e:
            logger.error(f"Failed to increment player kill: {e}")

    async def increment_player_death(self, guild_id: int, server_id: str, player_name: str):
        """Increment player death count and reset current streak"""
        try:
            # Reset current streak to 0 when player dies
            await self.update_pvp_stats(guild_id, server_id, player_name, {
                'deaths': 1,
                'current_streak': 0
            })
            
        except Exception as e:
            logger.error(f"Failed to increment player death: {e}")

    async def reset_player_streak(self, guild_id: int, server_id: str, player_name: str):
        """Reset player's current streak (for suicides, disconnects, etc.)"""
        try:
            await self.update_pvp_stats(guild_id, server_id, player_name, {
                'current_streak': 0
            })
            
        except Exception as e:
            logger.error(f"Failed to reset player streak: {e}")

    # KILL EVENTS (Server-scoped)
    async def add_kill_event(self, guild_id: int, server_id: str, kill_data: Dict[str, Any]) -> bool:
        """Add kill event to database"""
        try:
            kill_event = {
                "guild_id": guild_id,
                "server_id": server_id,
                "timestamp": datetime.now(timezone.utc),
                **kill_data
            }

            await self.kill_events.insert_one(kill_event)
            return True

        except Exception as e:
            logger.error(f"Failed to add kill event: {e}")
            return False

    async def get_recent_kills(self, guild_id: int, server_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent kill events for server"""
        cursor = self.kill_events.find(
            {"guild_id": guild_id, "server_id": server_id}
        ).sort("timestamp", -1).limit(limit)

        return await cursor.to_list(length=limit)

    # ECONOMY (Guild-scoped)
    async def get_wallet(self, guild_id: int, discord_id: int) -> Dict[str, Any]:
        """Get user wallet (guild-scoped)"""
        wallet = await self.economy.find_one({"guild_id": guild_id, "discord_id": discord_id})

        if not wallet:
            wallet = {
                "guild_id": guild_id,
                "discord_id": discord_id,
                "balance": 0,
                "total_earned": 0,
                "total_spent": 0,
                "created_at": datetime.now(timezone.utc)
            }
            await self.economy.insert_one(wallet)

        return wallet

    async def update_wallet(self, guild_id: int, discord_id: int, amount: int, 
                           transaction_type: str) -> bool:
        """Update user wallet balance"""
        try:
            inc_updates = {"balance": amount}
            if amount > 0:
                inc_updates["total_earned"] = amount
            else:
                inc_updates["total_spent"] = abs(amount)

            update_query = {
                "$inc": inc_updates,
                "$set": {"last_updated": datetime.now(timezone.utc)}
            }

            result = await self.economy.update_one(
                {"guild_id": guild_id, "discord_id": discord_id},
                update_query,
                upsert=True
            )

            return result.acknowledged

        except Exception as e:
            logger.error(f"Failed to update wallet: {e}")
            return False

    # PREMIUM (Server-scoped)
    async def set_premium_status(self, guild_id: int, server_id: str, 
                                expires_at: Optional[datetime] = None) -> bool:
        """Set premium status for specific server"""
        try:
            # Ensure expires_at is timezone-aware if provided
            if expires_at and expires_at.tzinfo is None:
                expires_at = expires_at.replace(tzinfo=timezone.utc)

            premium_doc = {
                "guild_id": guild_id,
                "server_id": server_id,
                "active": expires_at is not None,
                "expires_at": expires_at,
                "updated_at": datetime.now(timezone.utc)
            }

            await self.premium.update_one(
                {"guild_id": guild_id, "server_id": server_id},
                {"$set": premium_doc},
                upsert=True
            )

            return True

        except Exception as e:
            logger.error(f"Failed to set premium status: {e}")
            return False

    async def is_premium_server(self, guild_id: int, server_id: str) -> bool:
        """Check if server has active premium"""
        premium_doc = await self.premium.find_one({"guild_id": guild_id, "server_id": server_id})

        if not premium_doc or not premium_doc.get("active"):
            return False

        expires_at = premium_doc.get("expires_at")
        if expires_at:
            # Ensure both datetimes are timezone-aware for comparison
            if expires_at.tzinfo is None:
                expires_at = expires_at.replace(tzinfo=timezone.utc)

            current_time = datetime.now(timezone.utc)

            if expires_at < current_time:
                # Premium expired, update status
                await self.set_premium_status(guild_id, server_id, None)
                return False

        return True

    # LEADERBOARDS
    async def get_leaderboard(self, guild_id: int, server_id: str, stat: str = "kills", 
                             limit: int = 10) -> List[Dict[str, Any]]:
        """Get leaderboard for specific stat"""
        sort_order = -1 if stat in ["kills", "kdr", "longest_streak"] else 1

        cursor = self.pvp_data.find(
            {"guild_id": guild_id, "server_id": server_id}
        ).sort(stat, sort_order).limit(limit)

        return await cursor.to_list(length=limit)