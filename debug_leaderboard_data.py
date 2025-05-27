"""
Debug script to examine leaderboard data structure and fix the "unknown" player names issue
"""
import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient

async def debug_database_structure():
    """Check what data is actually stored in the database"""
    
    # Connect to MongoDB
    mongo_uri = os.getenv('MONGODB_URI')
    if not mongo_uri:
        print("❌ MONGODB_URI not found in environment")
        return
    
    client = AsyncIOMotorClient(mongo_uri)
    db = client.emerald_killfeed
    
    print("🔍 Examining database structure...")
    
    # Check collections
    collections = await db.list_collection_names()
    print(f"📊 Available collections: {collections}")
    
    # Check pvp_data structure
    if 'pvp_data' in collections:
        print("\n📈 Examining pvp_data collection...")
        sample_doc = await db.pvp_data.find_one()
        if sample_doc:
            print(f"📄 Sample document structure:")
            for key, value in sample_doc.items():
                print(f"  {key}: {type(value).__name__} = {value}")
        
        # Count total documents
        total_docs = await db.pvp_data.count_documents({})
        print(f"📊 Total pvp_data documents: {total_docs}")
        
        # Check for player_name field specifically
        docs_with_names = await db.pvp_data.count_documents({"player_name": {"$exists": True, "$ne": None}})
        print(f"👤 Documents with player_name: {docs_with_names}")
    
    # Check players collection
    if 'players' in collections:
        print("\n👥 Examining players collection...")
        sample_player = await db.players.find_one()
        if sample_player:
            print(f"📄 Sample player document:")
            for key, value in sample_player.items():
                print(f"  {key}: {type(value).__name__} = {value}")
        
        total_players = await db.players.count_documents({})
        print(f"📊 Total linked players: {total_players}")
    
    # Test aggregation query
    print("\n🔄 Testing leaderboard aggregation...")
    pipeline = [
        {"$limit": 5},  # Just get first 5 for testing
        {"$project": {
            "player_name": 1,
            "kills": 1,
            "deaths": 1,
            "guild_id": 1,
            "_id": 1
        }}
    ]
    
    async for doc in db.pvp_data.aggregate(pipeline):
        print(f"📊 Document: {doc}")
    
    await client.close()

if __name__ == "__main__":
    asyncio.run(debug_database_structure())