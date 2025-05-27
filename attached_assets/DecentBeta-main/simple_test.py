#!/usr/bin/env python3
"""
Simple test script to verify Discord connectivity and MongoDB connection
"""

import os
import sys
import discord
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient
import asyncio

# Load environment variables
load_dotenv()

# Set up logging
import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

async def test_connections():
    """Test Discord and MongoDB connections"""
    # Check for tokens
    bot_token = os.getenv('DISCORD_TOKEN') or os.getenv('BOT_TOKEN')
    mongo_uri = os.getenv('MONGODB_URI') or os.getenv('MONGO_URI')
    
    print(f"Discord Token Available: {bool(bot_token)}")
    print(f"MongoDB URI Available: {bool(mongo_uri)}")
    
    # Test MongoDB connection
    if mongo_uri:
        try:
            print("Testing MongoDB connection...")
            client = AsyncIOMotorClient(mongo_uri)
            db = client.emerald_killfeed
            
            # Test a simple operation
            guilds = await db.guilds.find_one()
            print(f"MongoDB connection successful. Found guild: {bool(guilds)}")
            
            # Check for servers in guild
            if guilds and 'servers' in guilds:
                servers = guilds['servers']
                print(f"Found {len(servers)} servers in the guild")
                
                # Print server details for debugging
                for server in servers:
                    server_id = str(server.get('_id', 'unknown'))
                    server_name = server.get('name', f'Server {server_id}')
                    print(f"  - Server: {server_name} (ID: {server_id})")
            else:
                print("No servers found in the guild or guild structure is different")
                
        except Exception as e:
            print(f"MongoDB connection error: {e}")
    else:
        print("No MongoDB URI provided, skipping test")
    
    # Create a simple Discord client
    if bot_token:
        try:
            print("Testing Discord connection...")
            intents = discord.Intents.default()
            intents.message_content = True
            client = discord.Client(intents=intents)
            
            @client.event
            async def on_ready():
                print(f"Discord connection successful! Logged in as {client.user}")
                print(f"Bot is in {len(client.guilds)} guilds")
                await client.close()
            
            # Start the client (with a timeout)
            try:
                print("Starting Discord client...")
                await asyncio.wait_for(client.start(bot_token), timeout=30)
            except asyncio.TimeoutError:
                print("Discord connection timed out after 30 seconds")
                if client and not client.is_closed():
                    await client.close()
        except Exception as e:
            print(f"Discord connection error: {e}")
    else:
        print("No Discord token provided, skipping test")
    
    print("Tests completed")

if __name__ == "__main__":
    asyncio.run(test_connections())