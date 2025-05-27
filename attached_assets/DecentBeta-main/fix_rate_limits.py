"""
Fixed Discord API Rate Limit Issues for Emerald's Killfeed Bot

This utility permanently fixes the global command sync rate limit issues
by implementing per-guild command registration that completely avoids
the strict global command rate limits.

Key features:
1. Completely avoids global command sync
2. Uses per-guild registration only
3. Tracks guilds with hash-based detection
4. Automatically handles new guilds

Original issue: Discord's global command sync API has strict rate limits that
cause problems on bot restart, especially for bots with many slash commands.
"""

import logging
import asyncio
import json
import hashlib
import os
from pathlib import Path

logger = logging.getLogger("discord.rate_limit_fix")

def compute_command_hash(bot):
    """
    Computes a hash of all slash commands to detect changes.
    
    Args:
        bot: The Discord bot instance
        
    Returns:
        str: SHA-256 hash of command structure
    """
    commands = []
    
    # Use pending_application_commands if available
    if hasattr(bot, 'pending_application_commands') and bot.pending_application_commands:
        commands = [cmd.to_dict() for cmd in bot.pending_application_commands]
    # Otherwise use application_commands
    elif hasattr(bot, 'application_commands') and bot.application_commands:
        commands = [cmd.to_dict() for cmd in bot.application_commands]
    
    # Generate hash
    raw = json.dumps(commands, sort_keys=True).encode('utf-8')
    hash_value = hashlib.sha256(raw).hexdigest()
    return hash_value

async def register_guild_commands(bot, guild, hash_file="command_hash.txt", processed_guilds_file="processed_guilds.txt"):
    """
    Register commands to a specific guild without using global sync
    
    Args:
        bot: The Discord bot instance
        guild: The guild to register commands to
        hash_file: Path to command hash file
        processed_guilds_file: Path to processed guilds file
    """
    logger.info(f"Syncing commands to guild: {guild.name} (ID: {guild.id})")
    
    try:
        # Guild-specific sync avoids global rate limits
        await bot.sync_commands(guild_ids=[guild.id])
        logger.info(f"Successfully synced commands to {guild.name}")
        
        # Track that we've processed this guild
        with open(processed_guilds_file, 'a') as f:
            f.write(f"{guild.id}\n")
        
        return True
        
    except Exception as e:
        logger.error(f"Failed to sync commands to {guild.name}: {e}")
        return False

async def register_commands_on_all_guilds(bot, hash_file="command_hash.txt", processed_guilds_file="processed_guilds.txt"):
    """
    Register commands on all guilds the bot is in without using global sync
    
    Args:
        bot: The Discord bot instance
        hash_file: Path to command hash file
        processed_guilds_file: Path to processed guilds file
    """
    if not bot.guilds:
        logger.warning("No guilds available for command registration")
        return
    
    # Calculate command hash to track changes
    current_hash = compute_command_hash(bot)
    previous_hash = ''
    
    # Check for existing hash
    if os.path.exists(hash_file):
        try:
            with open(hash_file, 'r') as f:
                previous_hash = f.read().strip()
        except Exception as e:
            logger.warning(f"Could not read previous hash: {e}")
    
    # Has command structure changed?
    hash_changed = current_hash != previous_hash
    
    # Load list of already processed guilds
    processed_guild_ids = set()
    if os.path.exists(processed_guilds_file):
        try:
            with open(processed_guilds_file, 'r') as f:
                for line in f:
                    guild_id = line.strip()
                    if guild_id:
                        try:
                            processed_guild_ids.add(int(guild_id))
                        except ValueError:
                            pass
        except Exception as e:
            logger.warning(f"Could not read processed guilds: {e}")
    
    # Determine which guilds need processing
    guilds_to_process = []
    for guild in bot.guilds:
        if hash_changed or guild.id not in processed_guild_ids:
            guilds_to_process.append(guild)
    
    if not guilds_to_process:
        logger.info("All guilds already processed, commands are synced")
        return
    
    # Process each guild
    successful_count = 0
    for guild in guilds_to_process:
        if await register_guild_commands(bot, guild, hash_file, processed_guilds_file):
            successful_count += 1
        
        # Avoid secondary rate limits
        await asyncio.sleep(1)
    
    # Save the new hash
    if successful_count > 0:
        with open(hash_file, 'w') as f:
            f.write(current_hash)
        logger.info(f"Command hash saved: {current_hash[:10]}...")
    
    logger.info(f"Successfully synced commands to {successful_count} guilds")