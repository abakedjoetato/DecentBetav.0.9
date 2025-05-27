"""
Emerald's Killfeed - Log Parser (PHASE 2)
Parses Deadside.log files for server events (PREMIUM ONLY)
"""

import asyncio
import logging
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Any

import aiofiles
import discord
import asyncssh

logger = logging.getLogger(__name__)

class LogParser:
    """
    LOG PARSER (PREMIUM ONLY)
    - Runs every 300 seconds
    - SFTP path: ./{host}_{serverID}/Logs/Deadside.log
    - Detects: Player joins/disconnects, Queue sizes, Airdrops, missions, traders, crashes
    - Detects log rotation
    - Sends styled embeds to respective channels
    """

    def __init__(self, bot):
        self.bot = bot
        self.last_log_position: Dict[str, int] = {}  # Track file position per server
        self.log_patterns = self._compile_log_patterns()
        self.player_sessions: Dict[str, Dict[str, datetime]] = {}  # Track player join times for playtime rewards
        self.server_status: Dict[str, Dict[str, Any]] = {}  # Track real-time server status per guild_server
        self.sftp_pool: Dict[str, asyncssh.SSHClientConnection] = {}  # SFTP connection pool
        self.log_file_hashes: Dict[str, str] = {}  # Track log file rotation

    def _compile_log_patterns(self) -> Dict[str, re.Pattern]:
        """Compile regex patterns for log parsing"""
        return {
            # Complete player lifecycle tracking
            'player_queued': re.compile(r'\[(\d{4}\.\d{2}\.\d{2}-\d{2}\.\d{2}\.\d{2}:\d{3})\].*Player.*([A-Za-z0-9_]+).*queued.*position.*(\d+)'),
            'player_join': re.compile(r'\[(\d{4}\.\d{2}\.\d{2}-\d{2}\.\d{2}\.\d{2}:\d{3})\].*LogOnline.*Login.*UniqueId.*([A-Za-z0-9_]+).*PlatformId.*(\d+)'),
            'player_disconnect': re.compile(r'\[(\d{4}\.\d{2}\.\d{2}-\d{2}\.\d{2}\.\d{2}:\d{3})\].*LogOnline.*Logout.*UniqueId.*([A-Za-z0-9_]+)'),
            'player_failed_join': re.compile(r'\[(\d{4}\.\d{2}\.\d{2}-\d{2}\.\d{2}\.\d{2}:\d{3})\].*Player.*([A-Za-z0-9_]+).*connection.*failed|timeout'),
            'queue_size': re.compile(r'\[(\d{4}\.\d{2}\.\d{2}-\d{2}\.\d{2}\.\d{2}:\d{3})\].*Queue.*size.*(\d+)'),
            'server_max_players': re.compile(r'\[(\d{4}\.\d{2}\.\d{2}-\d{2}\.\d{2}\.\d{2}:\d{3})\].*playersmaxcount=(\d+)'),

            # Airdrop - trigger on "Flying" line
            'airdrop_flying': re.compile(r'\[(\d{4}\.\d{2}\.\d{2}-\d{2}\.\d{2}\.\d{2}:\d{3})\].*Airdrop.*Flying.*location.*X=([0-9.-]+).*Y=([0-9.-]+)'),

            # Mission with level detection
            'mission_start': re.compile(r'\[(\d{4}\.\d{2}\.\d{2}-\d{2}\.\d{2}\.\d{2}:\d{3})\].*Mission.*([A-Za-z_]+).*Level.*(\d+).*started'),

            # Trader spawn events (not restocks)
            'trader_spawn': re.compile(r'\[(\d{4}\.\d{2}\.\d{2}-\d{2}\.\d{2}\.\d{2}:\d{3})\].*Trader.*([A-Za-z_]+).*spawned.*location'),

            # Helicopter crash
            'helicrash': re.compile(r'\[(\d{4}\.\d{2}\.\d{2}-\d{2}\.\d{2}\.\d{2}:\d{3})\].*Helicopter.*crash.*X=([0-9.-]+).*Y=([0-9.-]+)'),

            # Server events
            'server_crash': re.compile(r'\[(\d{4}\.\d{2}\.\d{2}-\d{2}\.\d{2}\.\d{2}:\d{3})\].*Fatal error|Assertion failed|Access violation'),
            'server_restart': re.compile(r'\[(\d{4}\.\d{2}\.\d{2}-\d{2}\.\d{2}\.\d{2}:\d{3})\].*Server.*restart|shutdown')
        }

    def normalize_mission_name(self, raw_mission_name: str) -> str:
        """Normalize mission names for consistency"""
        mission_mappings = {
            'convoy_escort': 'Convoy Escort',
            'supply_drop': 'Supply Drop',
            'elimination': 'Elimination',
            'capture_point': 'Capture Point',
            'rescue_mission': 'Rescue Mission',
            'defend_base': 'Defend Base',
            'intel_gathering': 'Intel Gathering',
            'sabotage': 'Sabotage',
            'vip_extraction': 'VIP Extraction',
            'patrol_route': 'Patrol Route'
        }

        # Convert to lowercase and replace underscores
        normalized = raw_mission_name.lower().replace('_', '_')
        return mission_mappings.get(normalized, raw_mission_name.replace('_', ' ').title())

    async def track_player_join(self, guild_id: int, server_id: str, player_name: str, timestamp: datetime):
        """Track player join for playtime rewards"""
        session_key = f"{guild_id}_{server_id}_{player_name}"
        self.player_sessions[session_key] = {
            'join_time': timestamp,
            'guild_id': guild_id,
            'server_id': server_id,
            'player_name': player_name
        }

    async def track_player_disconnect(self, guild_id: int, server_id: str, player_name: str, timestamp: datetime):
        """Track player disconnect and award playtime economy points"""
        session_key = f"{guild_id}_{server_id}_{player_name}"

        if session_key in self.player_sessions:
            join_time = self.player_sessions[session_key]['join_time']
            playtime_minutes = (timestamp - join_time).total_seconds() / 60

            # Award economy points (1 point per minute, minimum 5 minutes)
            if playtime_minutes >= 5:
                points_earned = int(playtime_minutes)

                # Find Discord user by character name
                discord_id = await self._find_discord_user_by_character(guild_id, player_name)
                if discord_id:
                    # Get currency name for this guild
                    currency_name = await self._get_guild_currency_name(guild_id)

                    # Award playtime points
                    await self.bot.get_cog('Economy').add_wallet_event(
                        guild_id, discord_id, points_earned, 
                        'playtime', f'Online time: {int(playtime_minutes)} minutes'
                    )

            # Remove from tracking
            del self.player_sessions[session_key]

    async def _find_discord_user_by_character(self, guild_id: int, character_name: str) -> Optional[int]:
        """Find Discord user ID by character name"""
        try:
            linking_data = await self.bot.db_manager.player_linking.find_one({
                'guild_id': guild_id,
                'characters': character_name
            })
            return linking_data.get('discord_id') if linking_data else None
        except Exception:
            return None

    async def _get_guild_currency_name(self, guild_id: int) -> str:
        """Get custom currency name for guild or default"""
        try:
            guild_config = await self.bot.db_manager.get_guild(guild_id)
            return guild_config.get('currency_name', 'Emeralds')
        except Exception:
            return 'Emeralds'

    def get_server_status_key(self, guild_id: int, server_id: str) -> str:
        """Generate server status tracking key"""
        return f"{guild_id}_{server_id}"

    async def init_server_status(self, guild_id: int, server_id: str, server_name: str = None):
        """Initialize server status tracking"""
        status_key = self.get_server_status_key(guild_id, server_id)
        self.server_status[status_key] = {
            'guild_id': guild_id,
            'server_id': server_id,
            'server_name': server_name or server_id,
            'current_players': 0,
            'max_players': 50,  # Default, will be updated from log
            'queue_count': 0,
            'queued_players': set(),
            'online_players': set(),
            'last_updated': datetime.now(timezone.utc)
        }

    async def update_server_max_players(self, guild_id: int, server_id: str, max_players: int):
        """Update server max player count from log"""
        status_key = self.get_server_status_key(guild_id, server_id)

        if status_key not in self.server_status:
            await self.init_server_status(guild_id, server_id)

        self.server_status[status_key]['max_players'] = max_players
        await self.update_voice_channel_name(guild_id, server_id)

    async def track_player_queued(self, guild_id: int, server_id: str, player_name: str, queue_position: int):
        """Track player entering queue"""
        status_key = self.get_server_status_key(guild_id, server_id)

        if status_key not in self.server_status:
            await self.init_server_status(guild_id, server_id)

        # Add to queued players
        self.server_status[status_key]['queued_players'].add(player_name)
        self.server_status[status_key]['queue_count'] = len(self.server_status[status_key]['queued_players'])
        self.server_status[status_key]['last_updated'] = datetime.now(timezone.utc)

        await self.update_voice_channel_name(guild_id, server_id)

    async def track_player_successful_join(self, guild_id: int, server_id: str, player_name: str, timestamp: datetime):
        """Track successful player join (from queue to online)"""
        status_key = self.get_server_status_key(guild_id, server_id)

        if status_key not in self.server_status:
            await self.init_server_status(guild_id, server_id)

        # Remove from queue, add to online
        self.server_status[status_key]['queued_players'].discard(player_name)
        self.server_status[status_key]['online_players'].add(player_name)

        # Update counts
        self.server_status[status_key]['current_players'] = len(self.server_status[status_key]['online_players'])
        self.server_status[status_key]['queue_count'] = len(self.server_status[status_key]['queued_players'])
        self.server_status[status_key]['last_updated'] = datetime.now(timezone.utc)

        # Start playtime tracking
        await self.track_player_join(guild_id, server_id, player_name, timestamp)

        await self.update_voice_channel_name(guild_id, server_id)

    async def track_player_disconnect_or_failed_join(self, guild_id: int, server_id: str, player_name: str, timestamp: datetime):
        """Track player disconnect or failed join"""
        status_key = self.get_server_status_key(guild_id, server_id)

        if status_key not in self.server_status:
            await self.init_server_status(guild_id, server_id)

        # Remove from both queue and online (handles both disconnect and failed join)
        was_online = player_name in self.server_status[status_key]['online_players']

        self.server_status[status_key]['queued_players'].discard(player_name)
        self.server_status[status_key]['online_players'].discard(player_name)

        # Update counts
        self.server_status[status_key]['current_players'] = len(self.server_status[status_key]['online_players'])
        self.server_status[status_key]['queue_count'] = len(self.server_status[status_key]['queued_players'])
        self.server_status[status_key]['last_updated'] = datetime.now(timezone.utc)

        # Award playtime if they were online
        if was_online:
            await self.track_player_disconnect(guild_id, server_id, player_name, timestamp)

        await self.update_voice_channel_name(guild_id, server_id)

    async def update_voice_channel_name(self, guild_id: int, server_id: str):
        """Update voice channel name with current server status"""
        try:
            status_key = self.get_server_status_key(guild_id, server_id)

            if status_key not in self.server_status:
                return

            status = self.server_status[status_key]

            # Get guild config to find voice channel
            guild_config = await self.bot.db_manager.get_guild(guild_id)
            if not guild_config:
                return

            # Look for voice channel ID in server config
            servers = guild_config.get('servers', {})
            server_config = servers.get(server_id, {})
            voice_channel_id = server_config.get('voice_channel_id')

            if not voice_channel_id:
                return

            # Get the voice channel
            guild = self.bot.get_guild(guild_id)
            if not guild:
                return

            voice_channel = guild.get_channel(voice_channel_id)
            if not voice_channel:
                return

            # Build channel name: "{Server name} {current}/{max} with {queue} in queue"
            server_name = status['server_name']
            current = status['current_players']
            max_players = status['max_players']
            queue = status['queue_count']

            if queue > 0:
                new_name = f"{server_name} {current}/{max_players} with {queue} in queue"
            else:
                new_name = f"{server_name} {current}/{max_players}"

            # Update channel name if different
            if voice_channel.name != new_name:
                await voice_channel.edit(name=new_name)
                logger.info(f"Updated voice channel name to: {new_name}")

        except Exception as e:
            logger.error(f"Failed to update voice channel name: {e}")

    async def get_sftp_log_content(self, server_config: Dict[str, Any]) -> Optional[str]:
        """Get log content from SFTP server using AsyncSSH with rotation detection"""
        try:
            conn = await self.get_sftp_connection(server_config)
            if not conn:
                return None

            server_id = str(server_config.get('_id', 'unknown'))
            sftp_host = server_config.get('host')
            # Ensure log file detection starts at ./ and uses correct _id path resolution
            remote_path = f"./{sftp_host}_{server_id}/Logs/Deadside.log"
            logger.info(f"Using SFTP log path: {remote_path} for server {server_id} on host {sftp_host}")

            async with conn.start_sftp_client() as sftp:
                try:
                    # Check file stats for rotation detection
                    file_stat = await sftp.stat(remote_path)
                    file_size = file_stat.size

                    server_key = f"{sftp_host}_{server_id}"

                    # Detect log rotation by checking if file size decreased
                    if server_key in self.last_log_position:
                        if file_size < self.last_log_position[server_key]:
                            logger.info(f"Log rotation detected for {server_key}")
                            self.last_log_position[server_key] = 0  # Reset position

                    # Read from last position
                    start_position = self.last_log_position.get(server_key, 0)

                    async with sftp.open(remote_path, 'r') as f:
                        await f.seek(start_position)
                        new_content = await f.read()

                        # Update position
                        self.last_log_position[server_key] = file_size

                        return new_content

                except FileNotFoundError:
                    logger.warning(f"Log file not found: {remote_path}")
                    return None

        except Exception as e:
            logger.error(f"Failed to fetch SFTP log file: {e}")
            return None

    async def get_sftp_connection(self, server_config: Dict[str, Any]) -> Optional[asyncssh.SSHClientConnection]:
        """Get or create SFTP connection with pooling and timeout handling"""
        try:
            sftp_host = server_config.get('host')
            sftp_port = server_config.get('port', 22)
            sftp_username = server_config.get('username')
            sftp_password = server_config.get('password')

            if not all([sftp_host, sftp_username, sftp_password]):
                return None

            pool_key = f"{sftp_host}:{sftp_port}:{sftp_username}"

            # Check existing connection with improved validation
            if pool_key in self.sftp_pool:
                conn = self.sftp_pool[pool_key]
                try:
                    if not conn.is_closed():
                        return conn
                    else:
                        del self.sftp_pool[pool_key]
                except Exception:
                    del self.sftp_pool[pool_key]

            # Create new connection with retry/backoff
            for attempt in range(3):
                try:
                    # Use exact format specified in diagnostic for asyncssh connection
                    conn = await asyncio.wait_for(
                        asyncssh.connect(
                            sftp_host, 
                            username=sftp_username, 
                            password=sftp_password, 
                            port=sftp_port, 
                            known_hosts=None
                        ),
                        timeout=30
                    )
                    self.sftp_pool[pool_key] = conn
                    return conn

                except (asyncio.TimeoutError, asyncssh.Error) as e:
                    logger.warning(f"SFTP connection attempt {attempt + 1} failed: {e}")
                    if attempt < 2:
                        await asyncio.sleep(2 ** attempt)

            return None

        except Exception as e:
            logger.error(f"Failed to get SFTP connection: {e}")
            return None

    async def get_dev_log_content(self) -> Optional[str]:
        """Get log content from attached_assets and dev_data directories"""
        try:
            # Check attached_assets first
            attached_log = Path('./attached_assets/Deadside.log')
            if attached_log.exists():
                async with aiofiles.open(attached_log, 'r') as f:
                    content = await f.read()
                    return content

            # Fallback to dev_data
            log_path = Path('./dev_data/logs/Deadside.log')
            if log_path.exists():
                async with aiofiles.open(log_path, 'r') as f:
                    content = await f.read()
                    return content

            logger.warning("No log file found in attached_assets or dev_data/logs/")
            return None

        except Exception as e:
            logger.error(f"Failed to read dev log file: {e}")
            return None

    def parse_log_line(self, line: str) -> Optional[Dict[str, Any]]:
        """Parse a single log line and extract event data"""
        line = line.strip()
        if not line:
            return None

        # Try each pattern
        for event_type, pattern in self.log_patterns.items():
            match = pattern.search(line)
            if match:
                try:
                    timestamp_str = match.group(1)
                    timestamp = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
                    timestamp = timestamp.replace(tzinfo=timezone.utc)

                    event_data = {
                        'type': event_type,
                        'timestamp': timestamp,
                        'raw_line': line
                    }

                    # Extract specific data based on event type
                    if event_type == 'player_join':
                        event_data.update({
                            'player_name': match.group(2),
                            'player_id': match.group(3)
                        })
                    elif event_type == 'player_disconnect':
                        event_data['player_name'] = match.group(2)
                    elif event_type == 'queue_size':
                        event_data['queue_size'] = int(match.group(2))
                    elif event_type in ['airdrop', 'helicrash']:
                        event_data.update({
                            'x_coordinate': float(match.group(2)),
                            'y_coordinate': float(match.group(3))
                        })
                    elif event_type == 'mission':
                        event_data['mission_type'] = match.group(2)
                    elif event_type == 'trader':
                        event_data['trader_name'] = match.group(2)

                    return event_data

                except Exception as e:
                    logger.error(f"Failed to parse log line '{line}': {e}")
                    continue

        return None

    async def send_log_event_embed(self, guild_id: int, server_id: str, event_data: Dict[str, Any]):
        """Send log event embed to appropriate channel"""
        try:
            # Get guild configuration
            guild_config = await self.bot.db_manager.get_guild(guild_id)
            if not guild_config:
                return

            logs_channel_id = guild_config.get('channels', {}).get('logs')
            if not logs_channel_id:
                return

            channel = self.bot.get_channel(logs_channel_id)
            if not channel:
                return

            # Create event-specific embed
            embed = await self._create_event_embed(event_data)
            if embed:
                await channel.send(embed=embed)

        except Exception as e:
            logger.error(f"Failed to send log event embed: {e}")

    async def _create_event_embed(self, event_data: Dict[str, Any]) -> Optional[discord.Embed]:
        """Create styled embed for log event"""
        try:
            event_type = event_data['type']
            timestamp = event_data['timestamp']

            # Event-specific embed styling
            if event_type == 'player_join':
                embed = discord.Embed(
                    title="🟢 Player Connected",
                    description=f"**{event_data['player_name']}** joined the server",
                    color=0x00FF00,
                    timestamp=timestamp
                )
                embed.add_field(name="Player ID", value=event_data['player_id'], inline=True)
                thumbnail = "Connections.png"

            elif event_type == 'player_disconnect':
                embed = discord.Embed(
                    title="🔴 Player Disconnected",
                    description=f"**{event_data['player_name']}** left the server",
                    color=0xFF0000,
                    timestamp=timestamp
                )
                thumbnail = "Connections.png"

            elif event_type == 'queue_size':
                embed = discord.Embed(
                    title="⏳ Server Queue",
                    description=f"Players in queue: **{event_data['queue_size']}**",
                    color=0xFFD700,
                    timestamp=timestamp
                )
                thumbnail = "main.png"

            elif event_type == 'airdrop':
                embed = discord.Embed(
                    title="📦 Airdrop Spawned",
                    description="A supply drop has been deployed!",
                    color=0x00BFFF,
                    timestamp=timestamp
                )
                embed.add_field(
                    name="📍 Location",
                    value=f"X: {event_data['x_coordinate']:.1f}\nY: {event_data['y_coordinate']:.1f}",
                    inline=True
                )
                thumbnail = "Airdrop.png"

            elif event_type == 'helicrash':
                embed = discord.Embed(
                    title="🚁 Helicopter Crash",
                    description="A helicopter has crashed on the map!",
                    color=0xFF4500,
                    timestamp=timestamp
                )
                embed.add_field(
                    name="📍 Crash Site",
                    value=f"X: {event_data['x_coordinate']:.1f}\nY: {event_data['y_coordinate']:.1f}",
                    inline=True
                )
                thumbnail = "Helicrash.png"

            elif event_type == 'mission':
                embed = discord.Embed(
                    title="🎯 Mission Started",
                    description=f"New **{event_data['mission_type']}** mission available",
                    color=0x9932CC,
                    timestamp=timestamp
                )
                thumbnail = "Mission.png"

            elif event_type == 'trader':
                embed = discord.Embed(
                    title="🏪 Trader Restock",
                    description=f"**{event_data['trader_name']}** has restocked inventory",
                    color=0x32CD32,
                    timestamp=timestamp
                )
                thumbnail = "Trader.png"

            elif event_type == 'server_crash':
                embed = discord.Embed(
                    title="💥 Server Error",
                    description="Server encountered a fatal error",
                    color=0x8B0000,
                    timestamp=timestamp
                )
                thumbnail = "main.png"

            elif event_type == 'server_restart':
                embed = discord.Embed(
                    title="🔄 Server Restart",
                    description="Server is restarting",
                    color=0xFFA500,
                    timestamp=timestamp
                )
                thumbnail = "main.png"

            else:
                return None

            # Add thumbnail if exists
            thumbnail_path = Path(f'./assets/{thumbnail}')
            if thumbnail_path.exists():
                embed.set_thumbnail(url=f"attachment://{thumbnail}")

            embed.set_footer(text="Powered by Discord.gg/EmeraldServers")
            return embed

        except Exception as e:
            logger.error(f"Failed to create event embed: {e}")
            return None

    async def parse_logs_for_server(self, guild_id: int, server_config: Dict[str, Any]):
        """Parse logs for a specific server"""
        try:
            if not await self.bot.db_manager.is_premium_server(guild_id, server_config['server_id']):
                return

            # Parse logs using SSH/SFTP
            if self.bot.dev_mode:
                await self.parse_dev_logs(guild_id, server_config)
            else:
                await self.parse_sftp_logs(guild_id, server_config)

        except Exception as e:
            logger.error(f"Failed to parse logs for server {server_config}: {e}")

    async def parse_sftp_logs(self, guild_id: int, server_config: Dict[str, Any]):
        """Parse logs from SFTP server"""
        try:
            host = server_config.get('host', server_config.get('hostname'))
            port = server_config.get('port', 22)
            username = server_config.get('username')
            password = server_config.get('password')
            server_id = server_config.get('server_id', server_config.get('_id'))

            if not all([host, username, password]):
                logger.warning(f"Missing SFTP credentials for server {server_id}")
                return

            # Create SSH connection
            async with asyncssh.connect(
                host, port=port, username=username, password=password,
                known_hosts=None, server_host_key_algs=['ssh-rsa', 'rsa-sha2-256', 'rsa-sha2-512']
            ) as conn:

                async with conn.start_sftp_client() as sftp:
                    # Get log files
                    log_path = f"./{host}_{server_id}/actual1/logs/"

                    try:
                        files = await sftp.glob(f"{log_path}**/*.log")

                        # Get current time with timezone awareness
                        current_time = datetime.now(timezone.utc)

                        for file_path in files:
                            try:
                                # Check file modification time
                                stat = await sftp.stat(file_path)
                                # Make file_mtime timezone-aware
                                file_mtime = datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc)

                                # Only process recent files (last 24 hours)
                                if (current_time - file_mtime).total_seconds() > 86400:
                                    continue

                                # Read and parse file
                                async with sftp.open(file_path, 'r') as f:
                                    content = await f.read()
                                    await self.parse_log_content(guild_id, server_id, content)

                            except Exception as e:
                                logger.error(f"Failed to process log file {file_path}: {e}")
                                continue

                    except Exception as e:
                        logger.warning(f"No log files found at {log_path}: {e}")

        except Exception as e:
            logger.error(f"Failed SFTP log parsing: {e}")

    async def parse_server_logs(self, guild_id: int, server_config: Dict[str, Any]):
        """Parse logs for a single server (PREMIUM ONLY)"""
        try:
            server_id = server_config.get('server_id', 'unknown')

            # Check if server has premium
            is_premium = await self.bot.db_manager.is_premium_server(guild_id, server_id)
            if not is_premium:
                logger.debug(f"Server {server_id} does not have premium access for log parsing")
                return

            logger.info(f"Parsing logs for premium server {server_id} in guild {guild_id}")

            # Get log content
            if self.bot.dev_mode:
                log_content = await self.get_dev_log_content()
            else:
                log_content = await self.get_sftp_log_content(server_config)

            if not log_content:
                logger.warning(f"No log content found for server {server_id}")
                return

            lines = log_content.splitlines()

            # Track position for incremental parsing
            server_key = f"{guild_id}_{server_id}"
            last_position = self.last_log_position.get(server_key, 0)

            # Process new lines only
            new_lines = lines[last_position:]
            new_events = 0

            for line in new_lines:
                event_data = self.parse_log_line(line)
                if event_data:
                    await self.send_log_event_embed(guild_id, server_id, event_data)
                    new_events += 1

            # Update position
            self.last_log_position[server_key] = len(lines)

            if new_events > 0:
                logger.info(f"Processed {new_events} new log events for server {server_id}")

        except Exception as e:
            logger.error(f"Failed to parse logs for server {server_config}: {e}")

    async def run_log_parser(self):
        """Run log parser for all premium servers"""
        try:
            logger.info("Running log parser for premium servers...")

            # Get all guilds with configured servers
            guilds_cursor = self.bot.db_manager.guilds.find({})

            async for guild_doc in guilds_cursor:
                guild_id = guild_doc['guild_id']
                servers = guild_doc.get('servers', [])

                for server_config in servers:
                    await self.parse_server_logs(guild_id, server_config)

            logger.info("Log parser completed")

        except Exception as e:
            logger.error(f"Failed to run log parser: {e}")

    def schedule_log_parser(self):
        """Schedule log parser to run every 300 seconds"""
        try:
            self.bot.scheduler.add_job(
                self.run_log_parser,
                'interval',
                seconds=300,  # 5 minutes
                id='log_parser',
                replace_existing=True
            )
            logger.info("Log parser scheduled (every 300 seconds)")

        except Exception as e:
            logger.error(f"Failed to schedule log parser: {e}")