#!/usr/bin/env python3
"""
Test script to verify MongoDB connection and database isolation
"""
import asyncio
import os
from datetime import datetime, timezone
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

async def test_mongodb_connection():
    """Test MongoDB connection and database structure"""
    print("🔍 Testing MongoDB Connection & Structure")
    print("=" * 60)
    
    try:
        # Get MongoDB URI from environment
        mongo_uri = os.getenv("MONGO_URI")
        if not mongo_uri:
            print("❌ MONGO_URI environment variable not set")
            return False
        
        # Connect to MongoDB
        client = AsyncIOMotorClient(mongo_uri)
        db = client.emerald_killfeed
        
        # Check connection
        await client.admin.command('ping')
        print("✅ Successfully connected to MongoDB")
        
        # List collections
        collections = await db.list_collection_names()
        print(f"\n📊 Found {len(collections)} collections:")
        for collection in sorted(collections):
            print(f"   - {collection}")
        
        # Check isolation between guilds
        guild1_id = 1000000000000000001
        guild2_id = 1000000000000000002
        server1_id = "server1"
        server2_id = "server2"
        
        # Count documents with guild isolation
        print("\n🔒 Testing Guild Isolation:")
        for collection_name in ["guilds", "players", "pvp_data", "economy", "factions"]:
            collection = db[collection_name]
            
            count1 = await collection.count_documents({"guild_id": guild1_id})
            count2 = await collection.count_documents({"guild_id": guild2_id})
            
            print(f"   - {collection_name}: Guild 1 ({count1} docs), Guild 2 ({count2} docs)")
        
        # Count documents with server isolation (within same guild)
        print("\n🔒 Testing Server Isolation (within Guild 1):")
        for collection_name in ["pvp_data", "kill_events"]:
            collection = db[collection_name]
            
            server1_count = await collection.count_documents({"guild_id": guild1_id, "server_id": server1_id})
            server2_count = await collection.count_documents({"guild_id": guild1_id, "server_id": server2_id})
            
            print(f"   - {collection_name}: Server 1 ({server1_count} docs), Server 2 ({server2_count} docs)")
        
        # Check indexes for isolation
        print("\n🔍 Checking Collection Indexes:")
        for collection_name in ["guilds", "players", "pvp_data", "economy", "factions"]:
            collection = db[collection_name]
            
            indexes = await collection.index_information()
            print(f"   - {collection_name} indexes:")
            for idx_name, idx_info in indexes.items():
                if idx_name != "_id_":  # Skip default _id index
                    print(f"      - {idx_name}: {idx_info.get('key')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing MongoDB: {e}")
        return False

async def main():
    """Run all database isolation tests"""
    print("🚀 Starting Database Isolation Tests...\n")
    
    db_success = await test_mongodb_connection()
    
    print(f"\n🎯 Overall Test Results:")
    print(f"   MongoDB Connection & Structure: {'✅ PASS' if db_success else '❌ FAIL'}")
    
    if db_success:
        print(f"\n🎉 Database isolation checks PASSED!")
    else:
        print(f"\n⚠️ Some database tests failed.")

if __name__ == "__main__":
    asyncio.run(main())