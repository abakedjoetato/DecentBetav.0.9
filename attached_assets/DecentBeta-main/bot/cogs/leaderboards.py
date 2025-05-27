"""
Emerald's Killfeed - Leaderboard System (PHASE 10)
/setleaderboardchannel
Hourly auto-update
Tracks: kills, KDR, streaks, factions, bounty claims
"""

import asyncio
import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any

import discord
from discord.ext import commands
from ..utils.embed_factory import EmbedFactory

logger = logging.getLogger(__name__)

class Leaderboards(commands.Cog):
    """
    LEADERBOARDS (PREMIUM)
    - /setleaderboardchannel
    - Hourly auto-update
    - Tracks: kills, KDR, streaks, factions, bounty claims
    """

    def __init__(self, bot):
        self.bot = bot
        self.leaderboard_messages: Dict[int, Dict[str, int]] = {}  # Track persistent leaderboard message IDs per guild

    def cog_load(self):
        """Called when the cog is loaded"""
        self.bot.loop.create_task(self.schedule_leaderboard_updates())

    async def check_premium_server(self, guild_id: int) -> bool:
        """Check if guild has premium access for leaderboard features"""
        guild_doc = await self.bot.db_manager.get_guild(guild_id)
        if not guild_doc:
            return False

        servers = guild_doc.get('servers', [])
        for server_config in servers:
            server_id = server_config.get('server_id', 'default')
            if await self.bot.db_manager.is_premium_server(guild_id, server_id):
                return True

        return False

    @discord.slash_command(name="setleaderboardchannel", description="Set the leaderboard channel")
    @commands.has_permissions(administrator=True)
    async def set_leaderboard_channel(self, ctx):
        """Set the current channel as the leaderboard channel"""
        try:
            guild_id = ctx.guild.id
            channel_id = ctx.channel.id

            # Check premium access
            if not await self.check_premium_server(guild_id):
                embed = discord.Embed(
                    title="🔒 Premium Feature",
                    description="Leaderboard system requires premium subscription!",
                    color=0xFF6B6B
                )
                await ctx.respond(embed=embed, ephemeral=True)
                return

            # Update guild configuration
            await self.bot.db_manager.guilds.update_one(
                {"guild_id": guild_id},
                {
                    "$set": {
                        "channels.leaderboard": channel_id,
                        "leaderboard_enabled": True,
                        "leaderboard_updated": datetime.now(timezone.utc)
                    }
                },
                upsert=True
            )

            # Create confirmation embed
            embed = discord.Embed(
                title="📊 Leaderboard Channel Set",
                description=f"Leaderboards will be posted in {ctx.channel.mention}!",
                color=0x00FF00,
                timestamp=datetime.now(timezone.utc)
            )

            embed.add_field(
                name="🔄 Updates",
                value="Leaderboards will update automatically every hour",
                inline=True
            )

            embed.add_field(
                name="📈 Categories",
                value="• Top Killers\n• Best K/D Ratios\n• Longest Streaks\n• Top Factions\n• Bounty Hunters",
                inline=True
            )

            embed.add_field(
                name="⏰ Next Update",
                value="Starting in the next hour...",
                inline=False
            )

            embed.set_thumbnail(url="attachment://Leaderboard.png")
            embed.set_footer(text="Powered by Discord.gg/EmeraldServers")

            await ctx.respond(embed=embed)

            # Generate initial leaderboard
            await self.generate_leaderboards(guild_id)

        except Exception as e:
            logger.error(f"Failed to set leaderboard channel: {e}")
            await ctx.respond("❌ Failed to set leaderboard channel.", ephemeral=True)

    @discord.slash_command(name="leaderboard", description="Show specific leaderboard")
    @discord.option(
        name="stat",
        description="Which stat to show",
        choices=[
            discord.OptionChoice("Kills", "kills"),
            discord.OptionChoice("K/D Ratio", "kdr"),
            discord.OptionChoice("Longest Streak", "longest_streak"),
            discord.OptionChoice("Deaths", "deaths"),
            discord.OptionChoice("Total Distance", "total_distance")
        ]
    )
    async def show_leaderboard(self, ctx: discord.ApplicationContext, stat: str):
        """Show a specific leaderboard"""
        try:
            guild_id = ctx.guild.id

            # Create the appropriate leaderboard
            if stat == "kills":
                embed = await self.create_leaderboard_embed(guild_id, "kills", "⚔️ Top Killers", "Most eliminations across all servers")
            elif stat == "kdr":
                embed = await self.create_leaderboard_embed(guild_id, "kdr", "🎯 Best K/D Ratios", "Highest kill-to-death ratios (min 5 kills)")
            elif stat == "longest_streak":
                embed = await self.create_leaderboard_embed(guild_id, "longest_streak", "🔥 Longest Streaks", "Most consecutive kills without dying")
            elif stat == "deaths":
                embed = await self.create_leaderboard_embed(guild_id, "deaths", "💀 Most Deaths", "Players with the most deaths")
            elif stat == "total_distance":
                embed = await self.create_leaderboard_embed(guild_id, "total_distance", "📏 Longest Distance Kills", "Highest total kill distances")
            else:
                await ctx.respond("❌ Invalid stat type!", ephemeral=True)
                return

            if embed:
                await ctx.respond(embed=embed)
            else:
                await ctx.respond("❌ No data available for this leaderboard yet!", ephemeral=True)

        except Exception as e:
            logger.error(f"Failed to show leaderboard: {e}")
            await ctx.respond("❌ Failed to show leaderboard.", ephemeral=True)

    async def generate_leaderboards(self, guild_id: int):
        """Generate and post all leaderboards for a guild"""
        try:
            # Get guild configuration
            guild_config = await self.bot.db_manager.get_guild(guild_id)
            if not guild_config:
                return

            leaderboard_channel_id = guild_config.get('channels', {}).get('leaderboard')
            if not leaderboard_channel_id:
                return

            channel = self.bot.get_channel(leaderboard_channel_id)
            if not channel:
                return

            # Check if leaderboards are enabled
            if not guild_config.get('leaderboard_enabled', False):
                return

            # Clear old leaderboard messages
            if guild_id in self.leaderboard_messages:
                for message_id in self.leaderboard_messages[guild_id]:
                    try:
                        old_message = await channel.fetch_message(message_id)
                        await old_message.delete()
                    except:
                        pass
                self.leaderboard_messages[guild_id] = []
            else:
                self.leaderboard_messages[guild_id] = []

            # Generate each leaderboard
            leaderboards = [
                ("kills", "⚔️ Top Killers", "Most eliminations across all servers"),
                ("kdr", "🎯 Best K/D Ratios", "Highest kill-to-death ratios"),
                ("longest_streak", "🔥 Longest Streaks", "Most consecutive kills without dying"),
                ("bounty_claims", "💰 Bounty Hunters", "Most bounties claimed"),
                ("factions", "🏛️ Top Factions", "Highest performing factions")
            ]

            for stat_type, title, description in leaderboards:
                embed = await self.create_leaderboard_embed(guild_id, stat_type, title, description)
                if embed:
                    message = await channel.send(embed=embed)
                    self.leaderboard_messages[guild_id].append(message.id)
                    await asyncio.sleep(1)  # Prevent rate limiting

            # Update last update time
            await self.bot.db_manager.guilds.update_one(
                {"guild_id": guild_id},
                {"$set": {"leaderboard_updated": datetime.now(timezone.utc)}}
            )

            logger.info(f"Generated leaderboards for guild {guild_id}")

        except Exception as e:
            logger.error(f"Failed to generate leaderboards for guild {guild_id}: {e}")

    async def create_leaderboard_embed(self, guild_id: int, stat_type: str, 
                                     title: str, description: str) -> Optional[discord.Embed]:
        """Create a leaderboard embed for a specific stat type"""
        try:
            if stat_type == "factions":
                return await self.create_faction_leaderboard(guild_id, title, description)
            elif stat_type == "bounty_claims":
                return await self.create_bounty_leaderboard(guild_id, title, description)
            elif stat_type == "weapons":
                return await self.create_weapon_leaderboard(guild_id, title, description)
            else:
                return await self.create_player_leaderboard(guild_id, stat_type, title, description)

        except Exception as e:
            logger.error(f"Failed to create {stat_type} leaderboard: {e}")
            return None

    async def create_player_leaderboard(self, guild_id: int, stat_type: str, 
                                      title: str, description: str) -> Optional[discord.Embed]:
        """Create player-based leaderboard"""
        try:
            # Get top players for this stat
            sort_field = stat_type
            if stat_type == "kdr":
                # Only include players with at least 5 kills for KDR
                pipeline = [
                    {"$match": {"guild_id": guild_id}},
                    {"$group": {
                        "_id": "$player_name",
                        "kills": {"$sum": "$kills"},
                        "deaths": {"$sum": "$deaths"}
                    }},
                    {"$match": {"kills": {"$gte": 5}}},
                    {"$addFields": {
                        "kdr": {"$divide": ["$kills", {"$max": ["$deaths", 1]}]}
                    }},
                    {"$sort": {"kdr": -1}},
                    {"$limit": 10}
                ]
                top_players = await self.bot.db_manager.pvp_data.aggregate(pipeline).to_list(length=None)
            else:
                # Regular aggregation for other stats
                pipeline = [
                    {"$match": {"guild_id": guild_id}},
                    {"$group": {
                        "_id": "$player_name",
                        "player_name": {"$first": "$player_name"},
                        "kills": {"$sum": "$kills"},
                        "deaths": {"$sum": "$deaths"},
                        "kdr": {"$avg": "$kdr"},
                        "longest_streak": {"$max": "$longest_streak"}
                    }},
                    {"$sort": {sort_field: -1}},
                    {"$limit": 10}
                ]
                top_players = await self.bot.db_manager.pvp_data.aggregate(pipeline).to_list(length=None)

            if not top_players:
                return None

            # Create embed data
            embed_data = {
                'title': title,
                'description': description,
                'rankings': [],
                'total_kills': 0,
                'total_deaths': 0,
                'thumbnail_url': 'attachment://Leaderboard.png'
            }

            # Add players to leaderboard
            leaderboard_text = []
            for i, player in enumerate(top_players, 1):
                # Get player name - try multiple fields for compatibility
                player_name = player.get('player_name') or player.get('_id') or 'Unknown'

                if stat_type == "total_distance":
                    distance = player.get('total_distance', 0)
                    value = f"{distance:.1f}m" if isinstance(distance, (int, float)) else "0.0m"
                elif stat_type == "kdr":
                    kills = player.get('kills', 0)
                    deaths = player.get('deaths', 0)
                    kdr = kills / max(deaths, 1)
                    value = f"{kdr:.2f}"
                else:
                    stat_val = player.get(stat_type, 0)
                    value = f"{stat_val:,}" if stat_val is not None else "0"

                # Clean format without emojis - themed approach
                rank = f"**{i}.**" if i > 3 else ["**1.**", "**2.**", "**3.**"][i-1]
                leaderboard_text.append(f"{rank} {player_name} - {value}")

            # Prepare embed data for factory
            embed_data = {
                'title': title,
                'description': description,
                'rankings': "\n".join(leaderboard_text),
                'total_kills': sum(p.get('kills', 0) for p in top_players),
                'total_deaths': sum(p.get('deaths', 0) for p in top_players),
                'thumbnail_url': 'attachment://Leaderboard.png',
                'color': 0xFFD700
            }

            # Create themed embed using factory
            try:
                return await EmbedFactory.build('leaderboard', embed_data)
            except Exception as e:
                logger.error(f"Failed to build leaderboard embed: {e}")
                raise

        except Exception as e:
            logger.error(f"Failed to create player leaderboard: {e}")
            return None

    async def create_faction_leaderboard(self, guild_id: int, title: str, description: str) -> Optional[discord.Embed]:
        """Create faction leaderboard"""
        try:
            # Get all factions
            factions_cursor = self.bot.db_manager.factions.find({"guild_id": guild_id})
            factions = await factions_cursor.to_list(length=None)

            if not factions:
                return None

            # Calculate stats for each faction
            faction_stats = []
            for faction in factions:
                # Get combined stats for all faction members
                total_kills = 0
                total_deaths = 0
                member_count = len(faction['members'])

                for member_id in faction['members']:
                    # Get member's linked characters
                    player_data = await self.bot.db_manager.get_linked_player(guild_id, member_id)
                    if not player_data:
                        continue

                    # Get stats for each character
                    for character in player_data['linked_characters']:
                        cursor = self.bot.db_manager.pvp_data.find({
                            'guild_id': guild_id,
                            'player_name': character
                        })

                        async for server_stats in cursor:
                            total_kills += server_stats.get('kills', 0)
                            total_deaths += server_stats.get('deaths', 0)

                # Calculate faction KDR
                faction_kdr = total_kills / max(total_deaths, 1)

                faction_stats.append({
                    'name': faction['faction_name'],
                    'tag': faction.get('faction_tag'),
                    'kills': total_kills,
                    'deaths': total_deaths,
                    'kdr': faction_kdr,
                    'members': member_count
                })

            # Sort by KDR
            faction_stats.sort(key=lambda f: f['kdr'], reverse=True)

            # Create themed faction leaderboard using EmbedFactory
            leaderboard_text = []
            for i, faction in enumerate(faction_stats[:10], 1):
                name = faction['name']
                tag = f"[{faction['tag']}] " if faction['tag'] else ""
                kdr = faction['kdr']
                kills = faction['kills']
                members = faction['members']

                # Clean format without emojis - themed approach
                rank = f"**{i}.**" if i > 3 else ["**1.**", "**2.**", "**3.**"][i-1]
                leaderboard_text.append(f"{rank} {tag}{name}")
                leaderboard_text.append(f"    {kdr:.2f} K/D • {kills:,} kills • {members} members")

            # Use EmbedFactory for consistent theming
            embed_data = {
                'title': title,
                'description': description,
                'rankings': "\n".join(leaderboard_text),
                'total_kills': sum(f['kills'] for f in faction_stats),
                'total_deaths': sum(f['deaths'] for f in faction_stats),
                'thumbnail_url': 'attachment://Faction.png'
            }
            
            return await EmbedFactory.build('leaderboard', embed_data)

        except Exception as e:
            logger.error(f"Failed to create faction leaderboard: {e}")
            return None

    async def create_bounty_leaderboard(self, guild_id: int, title: str, description: str) -> Optional[discord.Embed]:
        """Create bounty hunters leaderboard"""
        try:
            # Get top bounty hunters
            pipeline = [
                {"$match": {"guild_id": guild_id, "claimed": True}},
                {"$group": {
                    "_id": "$claimer_character",
                    "bounties_claimed": {"$sum": 1},
                    "total_earned": {"$sum": "$amount"}
                }},
                {"$sort": {"bounties_claimed": -1}},
                {"$limit": 10}
            ]

            top_hunters = await self.bot.db_manager.bounties.aggregate(pipeline).to_list(length=None)

            if not top_hunters:
                return None

            # Create themed bounty leaderboard using EmbedFactory
            leaderboard_text = []
            for i, hunter in enumerate(top_hunters, 1):
                hunter_name = hunter['_id'] or 'Unknown'
                bounties = hunter['bounties_claimed']
                earned = hunter['total_earned']

                # Clean format without emojis
                rank = f"**{i}.**" if i > 3 else ["**1.**", "**2.**", "**3.**"][i-1]
                leaderboard_text.append(f"{rank} {hunter_name}")
                leaderboard_text.append(f"    {bounties:,} bounties • ${earned:,} earned")

            # Use EmbedFactory for consistent theming
            embed_data = {
                'title': title,
                'description': description,
                'rankings': "\n".join(leaderboard_text),
                'total_kills': sum(h['bounties_claimed'] for h in top_hunters),
                'total_deaths': sum(h['total_earned'] for h in top_hunters),
                'thumbnail_url': 'attachment://Bounty.png'
            }
            
            return await EmbedFactory.build('leaderboard', embed_data)

        except Exception as e:
            logger.error(f"Failed to create bounty leaderboard: {e}")
            return None

    def schedule_leaderboard_updates(self):
        """Schedule automated leaderboard updates every hour"""
        try:
            self.bot.scheduler.add_job(
                self.run_hourly_leaderboard_updates,
                'interval',
                hours=1,
                id='leaderboard_updates',
                replace_existing=True
            )
            logger.info("Leaderboard updates scheduled (every hour)")

        except Exception as e:
            logger.error(f"Failed to schedule leaderboard updates: {e}")

    async def run_hourly_leaderboard_updates(self):
        """Run automated leaderboard updates for all guilds"""
        try:
            logger.info("Running hourly leaderboard updates...")

            # Get all guilds with leaderboard enabled
            guilds_cursor = self.bot.db_manager.guilds.find({"leaderboard_enabled": True})

            async for guild_doc in guilds_cursor:
                guild_id = guild_doc['guild_id']

                # Check if guild has premium access
                if await self.check_premium_server(guild_id):
                    await self.update_persistent_leaderboards(guild_id)
                else:
                    # Disable leaderboards if premium expired
                    await self.bot.db_manager.guilds.update_one(
                        {"guild_id": guild_id},
                        {"$set": {"leaderboard_enabled": False}}
                    )
                    logger.info(f"Disabled leaderboards for guild {guild_id} - premium expired")

            logger.info("Hourly leaderboard updates completed")

        except Exception as e:
            logger.error(f"Failed to run hourly leaderboard updates: {e}")

    async def update_persistent_leaderboards(self, guild_id: int):
        """Update persistent leaderboard embeds (intelligent embed reuse)"""
        try:
            # Get guild configuration
            guild_config = await self.bot.db_manager.get_guild(guild_id)
            if not guild_config:
                return

            leaderboard_channel_id = guild_config.get('channels', {}).get('leaderboard')
            if not leaderboard_channel_id:
                return

            channel = self.bot.get_channel(leaderboard_channel_id)
            if not channel:
                return

            # Initialize tracking for this guild
            if guild_id not in self.leaderboard_messages:
                self.leaderboard_messages[guild_id] = {}

            # Generate each leaderboard type
            leaderboard_types = [
                ("kills", "⚔️ Top Killers", "Most eliminations across all servers"),
                ("kdr", "🎯 Best K/D Ratios", "Highest kill-to-death ratios"),
                ("longest_streak", "🔥 Longest Streaks", "Most consecutive kills without dying"),
                ("weapons", "🔫 Top Weapons", "Most used weapons and their masters"),
                ("factions", "🏛️ Top Factions", "Highest performing factions")
            ]

            for stat_type, title, description in leaderboard_types:
                await self.update_single_leaderboard(guild_id, channel, stat_type, title, description)
                await asyncio.sleep(2)  # Prevent rate limiting

            # Update last update time
            await self.bot.db_manager.guilds.update_one(
                {"guild_id": guild_id},
                {"$set": {"leaderboard_updated": datetime.now(timezone.utc)}}
            )

            logger.info(f"Updated persistent leaderboards for guild {guild_id}")

        except Exception as e:
            logger.error(f"Failed to update persistent leaderboards for guild {guild_id}: {e}")

    async def update_single_leaderboard(self, guild_id: int, channel, stat_type: str, title: str, description: str):
        """Update or create a single persistent leaderboard"""
        try:
            # Generate new embed
            new_embed = await self.create_leaderboard_embed(guild_id, stat_type, title, description)
            if not new_embed:
                return

            # Check if we have an existing message for this leaderboard type
            existing_message_id = self.leaderboard_messages[guild_id].get(stat_type)

            if existing_message_id:
                try:
                    # Try to edit existing message
                    existing_message = await channel.fetch_message(existing_message_id)
                    await existing_message.edit(embed=new_embed)
                    logger.debug(f"Updated existing {stat_type} leaderboard message")
                    return

                except discord.NotFound:
                    # Message was deleted, remove from tracking
                    del self.leaderboard_messages[guild_id][stat_type]
                except Exception as e:
                    logger.warning(f"Failed to edit existing {stat_type} leaderboard: {e}")
                    # Continue to post new message

            # Post new message
            await channel.send(embed=new_embed)
            new_message = await channel.send(embed=new_embed)
            self.leaderboard_messages[guild_id][stat_type] = new_message.id
            logger.debug(f"Posted new {stat_type} leaderboard message")

        except Exception as e:
            logger.error(f"Failed to update {stat_type} leaderboard: {e}")

    async def create_weapon_leaderboard(self, guild_id: int, title: str, description: str) -> Optional[discord.Embed]:
        """Create weapon usage leaderboard"""
        try:
            # Aggregate weapon usage data
            pipeline = [
                {"$match": {"guild_id": guild_id}},
                {"$group": {
                    "_id": "$weapon",
                    "total_kills": {"$sum": 1},
                    "top_user": {"$first": "$killer"},
                    "users": {"$addToSet": "$killer"}
                }},
                {"$addFields": {"unique_users": {"$size": "$users"}}},
                {"$sort": {"total_kills": -1}},
                {"$limit": 5}
            ]

            top_weapons = await self.bot.db_manager.kill_events.aggregate(pipeline).to_list(length=None)

            if not top_weapons:
                return None

            # Create embed
            embed = discord.Embed(
                title=title,
                description=description,
                color=0xFF4500,
                timestamp=datetime.now(timezone.utc)
            )

            # Add weapons to leaderboard
            weapon_text = []
            for i, weapon_data in enumerate(top_weapons, 1):
                weapon = weapon_data['_id']
                kills = weapon_data['total_kills']
                users = weapon_data['unique_users']

                # Find top player for this weapon
                top_player_pipeline = [
                    {"$match": {"guild_id": guild_id, "weapon": weapon}},
                    {"$group": {
                        "_id": "$killer",
                        "weapon_kills": {"$sum": 1}
                    }},
                    {"$sort": {"weapon_kills": -1}},
                    {"$limit": 1}
                ]

                top_player_result = await self.bot.db_manager.kill_events.aggregate(top_player_pipeline).to_list(length=1)
                top_player = top_player_result[0]['_id'] if top_player_result else "Unknown"
                player_kills = top_player_result[0]['weapon_kills'] if top_player_result else 0

                medal = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣"][i-1]
                weapon_text.append(f"{medal} **{weapon}**")
                weapon_text.append(f"    {kills:,} kills • {users} users • Top: {top_player} ({player_kills})")

            embed.add_field(
                name="🔫 Most Used Weapons",
                value="\n".join(weapon_text),
                inline=False
            )

            embed.set_thumbnail(url="attachment://WeaponStats.png")
            embed.set_footer(text="Powered by Discord.gg/EmeraldServers • Updates hourly")

            return embed

        except Exception as e:
            logger.error(f"Failed to create weapon leaderboard: {e}")
            return None

    async def update_all_leaderboards(self):
        """Update leaderboards for all guilds with leaderboards enabled"""
        try:
            logger.info("Starting hourly leaderboard update...")

            # Get all guilds with leaderboards enabled
            guilds_cursor = self.bot.db_manager.guilds.find({
                "leaderboard_enabled": True,
                "channels.leaderboard": {"$exists": True}
            })

            async for guild_doc in guilds_cursor:
                guild_id = guild_doc['guild_id']

                # Check if guild still has premium
                if await self.check_premium_server(guild_id):
                    await self.generate_leaderboards(guild_id)
                    await asyncio.sleep(2)  # Prevent rate limiting
                else:
                    # Disable leaderboards for non-premium guilds
                    await self.bot.db_manager.guilds.update_one(
                        {"guild_id": guild_id},
                        {"$unset": {"leaderboard_enabled": ""}}
                    )

            logger.info("Completed hourly leaderboard update")

        except Exception as e:
            logger.error(f"Failed to update leaderboards: {e}")

    async def schedule_leaderboard_updates(self):
        """Schedule hourly leaderboard updates"""
        try:
            self.bot.scheduler.add_job(
                self.update_all_leaderboards,
                'interval',
                hours=1,
                id='leaderboard_updates',
                replace_existing=True
            )
            logger.info("Leaderboard updates scheduled (every hour)")

            # Schedule only once
            await self.update_all_leaderboards()

        except Exception as e:
            logger.error(f"Failed to schedule leaderboard updates: {e}")

def setup(bot):
    bot.add_cog(Leaderboards(bot))