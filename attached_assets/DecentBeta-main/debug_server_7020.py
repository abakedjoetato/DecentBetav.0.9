#!/usr/bin/env python3
"""
Debug script to examine server 7020 data structure and fix removal issues
"""

import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient

async def debug_server_7020():
    """Debug the problematic server 7020"""
    
    # Connect to MongoDB
    mongo_uri = os.getenv('MONGODB_URI')
    if not mongo_uri:
        print("❌ MONGODB_URI not found in environment variables")
        return
    
    client = AsyncIOMotorClient(mongo_uri)
    db = client.emerald_killfeed
    guilds_collection = db.guilds
    
    guild_id = 1219706687980568769  # From the logs
    
    try:
        # Get guild configuration
        guild_doc = await guilds_collection.find_one({"guild_id": guild_id})
        
        if not guild_doc:
            print(f"❌ Guild {guild_id} not found in database")
            return
        
        print(f"✅ Found guild: {guild_doc.get('guild_name', 'Unknown')}")
        
        servers = guild_doc.get('servers', [])
        print(f"📊 Total servers in guild: {len(servers)}")
        
        # Find server 7020
        server_7020 = None
        for i, server in enumerate(servers):
            print(f"\n🔍 Server {i+1}:")
            print(f"   Data: {server}")
            
            if str(server.get('_id')) == '7020' or str(server.get('server_id')) == '7020':
                server_7020 = server
                print(f"   ⭐ This is server 7020!")
        
        if not server_7020:
            print(f"\n❌ Server 7020 not found in database")
            return
        
        print(f"\n🎯 Server 7020 details:")
        print(f"   _id: {server_7020.get('_id')}")
        print(f"   server_id: {server_7020.get('server_id')}")
        print(f"   name: {server_7020.get('name')}")
        print(f"   host: {server_7020.get('host')}")
        print(f"   All fields: {list(server_7020.keys())}")
        
        # Check if removal would work
        print(f"\n🧪 Testing removal query:")
        print(f"   Looking for servers with _id = '7020'")
        
        # Test the removal query without actually removing
        match_query = {"guild_id": guild_id, "servers._id": "7020"}
        matching_doc = await guilds_collection.find_one(match_query)
        
        if matching_doc:
            print(f"   ✅ Query would match - removal should work")
        else:
            print(f"   ❌ Query would NOT match - this is the problem!")
            
            # Try alternative queries
            alt_queries = [
                {"guild_id": guild_id, "servers.server_id": "7020"},
                {"guild_id": guild_id, "servers._id": 7020},  # Integer
                {"guild_id": guild_id, "servers.server_id": 7020},  # Integer
            ]
            
            for i, alt_query in enumerate(alt_queries):
                alt_match = await guilds_collection.find_one(alt_query)
                if alt_match:
                    print(f"   ✅ Alternative query {i+1} MATCHES: {alt_query}")
                else:
                    print(f"   ❌ Alternative query {i+1} fails: {alt_query}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    
    finally:
        client.close()

if __name__ == "__main__":
    asyncio.run(debug_server_7020())