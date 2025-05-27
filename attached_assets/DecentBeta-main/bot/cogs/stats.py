"""
Emerald's Killfeed - PvP Stats System (PHASE 6)
/stats shows: Kills, deaths, KDR, Suicides, Longest streak, Most used weapon, Rival/Nemesis
/compare <user> compares two profiles
"""

import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, Tuple

import discord
from discord.ext import commands

logger = logging.getLogger(__name__)

class Stats(commands.Cog):
    """
    PVP STATS (FREE)
    - /stats shows: Kills, deaths, KDR, Suicides, Longest streak, Most used weapon, Rival/Nemesis
    - /compare <user> compares two profiles
    """
    
    def __init__(self, bot):
        self.bot = bot
    
    async def get_player_combined_stats(self, guild_id: int, player_characters: List[str]) -> Dict[str, Any]:
        """Get combined stats across all servers for a player's characters"""
        # Initialize with safe defaults
        combined_stats = {
            'kills': 0,
            'deaths': 0,
            'suicides': 0,
            'kdr': 0.0,
            'best_streak': 0,
            'current_streak': 0,
            'personal_best_distance': 0.0,
            'servers_played': 0,
            'favorite_weapon': None,
            'weapon_stats': {},
            'rival': None,
            'nemesis': None
        }
        
        try:
            if not player_characters:
                logger.warning("No player characters provided for stats calculation")
                return combined_stats
            
            # Get stats from all servers
            for character in player_characters:
                try:
                    cursor = self.bot.db_manager.pvp_data.find({
                        'guild_id': guild_id,
                        'player_name': character
                    })
                    
                    async for server_stats in cursor:
                        if not isinstance(server_stats, dict):
                            logger.warning(f"Invalid server_stats type: {type(server_stats)}")
                            continue
                            
                        combined_stats['kills'] += server_stats.get('kills', 0)
                        combined_stats['deaths'] += server_stats.get('deaths', 0)
                        combined_stats['suicides'] += server_stats.get('suicides', 0)
                        # Track personal best distance (take the maximum across all servers)
                        if server_stats.get('personal_best_distance', 0.0) > combined_stats['personal_best_distance']:
                            combined_stats['personal_best_distance'] = server_stats.get('personal_best_distance', 0.0)
                        combined_stats['servers_played'] += 1
                        
                        # Track best streak
                        if server_stats.get('best_streak', 0) > combined_stats['best_streak']:
                            combined_stats['best_streak'] = server_stats.get('best_streak', 0)
                
                except Exception as char_error:
                    logger.error(f"Error processing character {character}: {char_error}")
                    continue
            
            # Calculate KDR safely
            if combined_stats['deaths'] > 0:
                combined_stats['kdr'] = combined_stats['kills'] / combined_stats['deaths']
            else:
                combined_stats['kdr'] = float(combined_stats['kills'])
            
            # Get weapon statistics and rivals/nemesis
            try:
                await self._calculate_weapon_stats(guild_id, player_characters, combined_stats)
            except Exception as weapon_error:
                logger.error(f"Error calculating weapon stats: {weapon_error}")
            
            try:
                await self._calculate_rivals_nemesis(guild_id, player_characters, combined_stats)
            except Exception as rival_error:
                logger.error(f"Error calculating rivals/nemesis: {rival_error}")
            
            return combined_stats
            
        except Exception as e:
            logger.error(f"Failed to get combined stats: {e}")
            import traceback
            logger.error(f"Stack trace: {traceback.format_exc()}")
            return combined_stats
    
    async def _calculate_weapon_stats(self, guild_id: int, player_characters: List[str], 
                                    combined_stats: Dict[str, Any]):
        """Calculate weapon statistics from kill events (excludes suicides)"""
        try:
            weapon_counts = {}
            
            for character in player_characters:
                cursor = self.bot.db_manager.kill_events.find({
                    'guild_id': guild_id,
                    'killer': character,
                    'is_suicide': False  # Only count actual PvP kills for weapon stats
                })
                
                async for kill_event in cursor:
                    weapon = kill_event.get('weapon', 'Unknown')
                    # Skip suicide weapons even if they somehow got through
                    if weapon not in ['Menu Suicide', 'Suicide', 'Falling']:
                        weapon_counts[weapon] = weapon_counts.get(weapon, 0) + 1
            
            if weapon_counts:
                combined_stats['favorite_weapon'] = max(weapon_counts.keys(), key=lambda x: weapon_counts[x])
                combined_stats['weapon_stats'] = weapon_counts
            
        except Exception as e:
            logger.error(f"Failed to calculate weapon stats: {e}")
    
    async def _calculate_rivals_nemesis(self, guild_id: int, player_characters: List[str], 
                                      combined_stats: Dict[str, Any]):
        """Calculate rival (most killed) and nemesis (killed by most)"""
        try:
            kills_against = {}
            deaths_to = {}
            
            for character in player_characters:
                # Count kills against others
                cursor = self.bot.db_manager.kill_events.find({
                    'guild_id': guild_id,
                    'killer': character,
                    'is_suicide': False
                })
                
                async for kill_event in cursor:
                    victim = kill_event.get('victim')
                    if victim and victim not in player_characters:  # Don't count alt kills
                        kills_against[victim] = kills_against.get(victim, 0) + 1
                
                # Count deaths to others
                cursor = self.bot.db_manager.kill_events.find({
                    'guild_id': guild_id,
                    'victim': character,
                    'is_suicide': False
                })
                
                async for kill_event in cursor:
                    killer = kill_event.get('killer')
                    if killer and killer not in player_characters:  # Don't count alt deaths
                        deaths_to[killer] = deaths_to.get(killer, 0) + 1
            
            # Set rival and nemesis
            if kills_against:
                combined_stats['rival'] = max(kills_against.keys(), key=lambda x: kills_against[x])
                combined_stats['rival_kills'] = kills_against[combined_stats['rival']]
            
            if deaths_to:
                combined_stats['nemesis'] = max(deaths_to.keys(), key=lambda x: deaths_to[x])
                combined_stats['nemesis_deaths'] = deaths_to[combined_stats['nemesis']]
            
        except Exception as e:
            logger.error(f"Failed to calculate rivals/nemesis: {e}")
    
    @discord.slash_command(name="stats", description="View PvP statistics")
    async def stats(self, ctx, user: discord.Member = None):
        """View PvP statistics for yourself or another user"""
        try:
            guild_id = ctx.guild.id
            target_user = user or ctx.user
            
            # Get linked characters
            player_data = await self.bot.db_manager.get_linked_player(guild_id, target_user.id)
            
            # Enhanced validation
            if not player_data:
                if target_user == ctx.user:
                    await ctx.respond(
                        "❌ You don't have any linked characters! Use `/link <character>` to get started.",
                        ephemeral=True
                    )
                else:
                    await ctx.respond(
                        f"❌ {target_user.mention} doesn't have any linked characters!",
                        ephemeral=True
                    )
                return
            
            if not isinstance(player_data, dict):
                logger.error(f"Invalid player_data type: {type(player_data)} - {player_data}")
                await ctx.respond("❌ Player data is corrupted. Please contact an administrator.", ephemeral=True)
                return
            
            if 'linked_characters' not in player_data or not player_data['linked_characters']:
                logger.error(f"Player data missing linked_characters: {player_data}")
                await ctx.respond("❌ No linked characters found. Please use `/link <character>` to link a character.", ephemeral=True)
                return
            
            await ctx.defer()
            
            # Get combined stats
            stats = await self.get_player_combined_stats(guild_id, player_data['linked_characters'])
            
            # Create manual embed since EmbedFactory might not have 'profile' template
            embed = discord.Embed(
                title=f"⚔️ PvP Statistics",
                description=f"Statistics for **{player_data.get('primary_character', player_data['linked_characters'][0])}**",
                color=0x00ff00
            )
            
            # Add fields
            embed.add_field(
                name="🎯 Combat Stats",
                value=f"**Kills:** {stats['kills']}\n**Deaths:** {stats['deaths']}\n**KDR:** {stats['kdr']:.2f}",
                inline=True
            )
            
            embed.add_field(
                name="💀 Other Stats", 
                value=f"**Suicides:** {stats['suicides']}\n**Best Streak:** {stats['best_streak']}\n**Current Streak:** {stats['current_streak']}",
                inline=True
            )
            
            embed.add_field(
                name="🔫 Weapon Info",
                value=f"**Favorite Weapon:** {stats.get('favorite_weapon', 'None')}\n**Best Distance:** {stats['personal_best_distance']:.1f}m",
                inline=False
            )
            
            if stats.get('rival'):
                embed.add_field(
                    name="⚔️ Rivalries",
                    value=f"**Rival:** {stats['rival']} ({stats.get('rival_kills', 0)} kills)\n**Nemesis:** {stats.get('nemesis', 'None')} ({stats.get('nemesis_deaths', 0)} deaths)",
                    inline=False
                )
            
            embed.set_thumbnail(url=target_user.avatar.url if target_user.avatar else target_user.default_avatar.url)
            embed.set_footer(text=f"Requested by {ctx.user.display_name}")
            
            await ctx.followup.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Failed to show stats: {e}")
            import traceback
            logger.error(f"Stack trace: {traceback.format_exc()}")
            if ctx.response.is_done():
                await ctx.followup.send("❌ Failed to retrieve statistics.", ephemeral=True)
            else:
                await ctx.respond("❌ Failed to retrieve statistics.", ephemeral=True)
    
    @discord.slash_command(name="compare", description="Compare stats with another player")
    async def compare(self, ctx: discord.ApplicationContext, user: discord.Member):
        """Compare your stats with another player"""
        try:
            guild_id = ctx.guild.id
            user1 = ctx.user
            user2 = user
            
            if user1.id == user2.id:
                await ctx.respond("❌ You can't compare stats with yourself!", ephemeral=True)
                return
            
            # Get both players' data
            player1_data = await self.bot.db_manager.get_linked_player(guild_id, user1.id)
            player2_data = await self.bot.db_manager.get_linked_player(guild_id, user2.id)
            
            if not player1_data or not isinstance(player1_data, dict):
                await ctx.respond(
                    "❌ You don't have any linked characters! Use `/link <character>` to get started.",
                    ephemeral=True
                )
                return
            
            if not player2_data or not isinstance(player2_data, dict):
                await ctx.respond(
                    f"❌ {user2.mention} doesn't have any linked characters!",
                    ephemeral=True
                )
                return
            
            await ctx.defer()
            
            # Get stats for both players
            stats1 = await self.get_player_combined_stats(guild_id, player1_data['linked_characters'])
            stats2 = await self.get_player_combined_stats(guild_id, player2_data['linked_characters'])
            
            # Create comparison embed manually for reliability
            embed = discord.Embed(
                title="⚔️ Player Comparison",
                description=f"{user1.mention} **VS** {user2.mention}",
                color=0xff6600
            )
            
            # Player 1 stats
            embed.add_field(
                name=f"🎯 {user1.display_name}",
                value=f"**Kills:** {stats1['kills']}\n**Deaths:** {stats1['deaths']}\n**KDR:** {stats1['kdr']:.2f}\n**Best Streak:** {stats1['best_streak']}",
                inline=True
            )
            
            # VS separator
            embed.add_field(
                name="⚔️",
                value="**VS**",
                inline=True
            )
            
            # Player 2 stats
            embed.add_field(
                name=f"🎯 {user2.display_name}",
                value=f"**Kills:** {stats2['kills']}\n**Deaths:** {stats2['deaths']}\n**KDR:** {stats2['kdr']:.2f}\n**Best Streak:** {stats2['best_streak']}",
                inline=True
            )
            
            # Determine winners
            kill_winner = user1.display_name if stats1['kills'] > stats2['kills'] else user2.display_name if stats2['kills'] > stats1['kills'] else "Tie"
            kdr_winner = user1.display_name if stats1['kdr'] > stats2['kdr'] else user2.display_name if stats2['kdr'] > stats1['kdr'] else "Tie"
            
            embed.add_field(
                name="🏆 Comparison Results",
                value=f"**Most Kills:** {kill_winner}\n**Better KDR:** {kdr_winner}",
                inline=False
            )
            
            if stats1.get('favorite_weapon') or stats2.get('favorite_weapon'):
                embed.add_field(
                    name="🔫 Favorite Weapons",
                    value=f"**{user1.display_name}:** {stats1.get('favorite_weapon', 'None')}\n**{user2.display_name}:** {stats2.get('favorite_weapon', 'None')}",
                    inline=False
                )
            
            embed.set_footer(text=f"Comparison requested by {ctx.user.display_name}")
            
            await ctx.followup.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Failed to compare stats: {e}")
            await ctx.respond("❌ Failed to compare statistics.", ephemeral=True)

def setup(bot):
    bot.add_cog(Stats(bot))