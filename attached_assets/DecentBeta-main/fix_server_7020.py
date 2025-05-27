#!/usr/bin/env python3
"""
Script to directly fix server 7020 removal issue
"""

import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient

async def fix_server_7020():
    """Fix server 7020 by updating its data structure"""
    
    # Connect to MongoDB
    mongo_uri = os.getenv('MONGODB_URI')
    if not mongo_uri:
        print("❌ MONGODB_URI not found")
        return
    
    client = AsyncIOMotorClient(mongo_uri)
    db = client.emerald_killfeed
    guilds_collection = db.guilds
    
    guild_id = 1219706687980568769
    
    try:
        # Get guild configuration
        guild_doc = await guilds_collection.find_one({"guild_id": guild_id})
        
        if not guild_doc:
            print(f"❌ Guild {guild_id} not found")
            return
        
        servers = guild_doc.get('servers', [])
        print(f"📊 Found {len(servers)} servers")
        
        # Find and fix server 7020
        updated_servers = []
        fixed = False
        
        for server in servers:
            if str(server.get('server_id')) == '7020':
                print(f"🔧 Fixing server 7020...")
                # Add missing fields to make it compatible with new format
                fixed_server = server.copy()
                fixed_server['_id'] = server.get('server_id')  # Add _id field
                fixed_server['name'] = server.get('server_name')  # Add name field
                fixed_server['host'] = server.get('sftp_host')  # Add host field
                fixed_server['port'] = server.get('sftp_port')  # Add port field
                fixed_server['username'] = server.get('sftp_username')  # Add username field
                fixed_server['password'] = server.get('sftp_password')  # Add password field
                
                updated_servers.append(fixed_server)
                fixed = True
                print(f"✅ Fixed server 7020 data structure")
            else:
                updated_servers.append(server)
        
        if fixed:
            # Update the guild document
            result = await guilds_collection.update_one(
                {"guild_id": guild_id},
                {"$set": {"servers": updated_servers}}
            )
            
            if result.modified_count > 0:
                print(f"✅ Successfully updated guild configuration")
                
                # Verify the fix
                updated_guild_doc = await guilds_collection.find_one({"guild_id": guild_id})
                updated_servers = updated_guild_doc.get('servers', [])
                
                for server in updated_servers:
                    if str(server.get('_id')) == '7020':
                        print(f"🎯 Verified: Server 7020 now has _id field: {server.get('_id')}")
                        print(f"🎯 Server 7020 fields: {list(server.keys())}")
                        break
            else:
                print(f"❌ Failed to update guild configuration")
        else:
            print(f"❌ Server 7020 not found for fixing")
    
    except Exception as e:
        print(f"❌ Error: {e}")
    
    finally:
        client.close()

if __name__ == "__main__":
    asyncio.run(fix_server_7020())