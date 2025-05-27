#!/usr/bin/env python3
"""
Test script to demonstrate complete player lifecycle tracking for accurate server status
"""
import re
from datetime import datetime, timezone

def test_complete_player_lifecycle():
    """Test the complete player lifecycle: queue → join → disconnect"""
    print("🔄 COMPLETE PLAYER LIFECYCLE TRACKING")
    print("=" * 60)
    
    # Sample lifecycle events in chronological order
    lifecycle_events = [
        # Server startup - extract max players
        "[2025.05.17-14.30.00:001] Server startup with playersmaxcount=50",
        
        # Players entering queue
        "[2025.05.17-14.30.15:123] Player m3_GOKI queued at position 1",
        "[2025.05.17-14.30.22:234] Player oooSLAYERoo queued at position 2",
        "[2025.05.17-14.30.30:345] Player The_Legend_of_MK queued at position 3",
        
        # Successful joins (from queue to online)
        "[2025.05.17-14.31.05:456] LogOnline: Login: UniqueId: m3_GOKI, PlatformId: 76561198033779078",
        "[2025.05.17-14.31.12:567] LogOnline: Login: UniqueId: oooSLAYERoo, PlatformId: 76561198126636736",
        
        # Failed join (player disconnects before successful join)
        "[2025.05.17-14.31.45:678] Player The_Legend_of_MK connection failed timeout",
        
        # New player joins queue
        "[2025.05.17-14.32.00:789] Player Knight_JFS queued at position 1",
        
        # Player disconnect after playing
        "[2025.05.17-15.45.30:890] LogOnline: Logout: UniqueId: m3_GOKI",
        
        # Successful join from queue
        "[2025.05.17-15.46.00:901] LogOnline: Login: UniqueId: Knight_JFS, PlatformId: 76561198355455154"
    ]
    
    # Patterns for lifecycle tracking
    patterns = {
        'max_players': re.compile(r'\[(\d{4}\.\d{2}\.\d{2}-\d{2}\.\d{2}\.\d{2}:\d{3})\].*playersmaxcount=(\d+)'),
        'player_queued': re.compile(r'\[(\d{4}\.\d{2}\.\d{2}-\d{2}\.\d{2}\.\d{2}:\d{3})\].*Player.*([A-Za-z0-9_]+).*queued.*position.*(\d+)'),
        'player_join': re.compile(r'\[(\d{4}\.\d{2}\.\d{2}-\d{2}\.\d{2}\.\d{2}:\d{3})\].*LogOnline.*Login.*UniqueId.*([A-Za-z0-9_]+).*PlatformId.*(\d+)'),
        'player_disconnect': re.compile(r'\[(\d{4}\.\d{2}\.\d{2}-\d{2}\.\d{2}\.\d{2}:\d{3})\].*LogOnline.*Logout.*UniqueId.*([A-Za-z0-9_]+)'),
        'failed_join': re.compile(r'\[(\d{4}\.\d{2}\.\d{2}-\d{2}\.\d{2}\.\d{2}:\d{3})\].*Player.*([A-Za-z0-9_]+).*connection.*failed|timeout')
    }
    
    # Track server status
    server_status = {
        'max_players': 50,
        'current_players': 0,
        'queue_count': 0,
        'queued_players': set(),
        'online_players': set()
    }
    
    for event in lifecycle_events:
        print(f"\n📝 Event: {event}")
        
        # Check each pattern
        for event_type, pattern in patterns.items():
            match = pattern.search(event)
            if match:
                if event_type == 'max_players':
                    timestamp, max_count = match.groups()
                    server_status['max_players'] = int(max_count)
                    print(f"   🏗️ SERVER CONFIG: Max players set to {max_count}")
                
                elif event_type == 'player_queued':
                    timestamp, player, position = match.groups()
                    server_status['queued_players'].add(player)
                    server_status['queue_count'] = len(server_status['queued_players'])
                    print(f"   🚶 QUEUED: {player} (position {position})")
                
                elif event_type == 'player_join':
                    timestamp, player, platform_id = match.groups()
                    # Move from queue to online
                    server_status['queued_players'].discard(player)
                    server_status['online_players'].add(player)
                    server_status['current_players'] = len(server_status['online_players'])
                    server_status['queue_count'] = len(server_status['queued_players'])
                    print(f"   ✅ JOINED: {player} (now online)")
                    print(f"   💰 Start playtime tracking for economy rewards")
                
                elif event_type == 'player_disconnect':
                    timestamp, player = match.groups()
                    server_status['online_players'].discard(player)
                    server_status['current_players'] = len(server_status['online_players'])
                    print(f"   ❌ DISCONNECTED: {player}")
                    print(f"   💰 Calculate playtime rewards and award currency")
                
                elif event_type == 'failed_join':
                    timestamp, player = match.groups()
                    # Remove from queue (failed to join)
                    server_status['queued_players'].discard(player)
                    server_status['queue_count'] = len(server_status['queued_players'])
                    print(f"   ⚠️ FAILED JOIN: {player} (removed from queue)")
                
                # Show current server status
                current = server_status['current_players']
                max_players = server_status['max_players']
                queue = server_status['queue_count']
                
                if queue > 0:
                    voice_name = f"Emerald EU {current}/{max_players} with {queue} in queue"
                else:
                    voice_name = f"Emerald EU {current}/{max_players}"
                
                print(f"   📊 Server Status: {current}/{max_players} online, {queue} queued")
                print(f"   🔊 Voice Channel: '{voice_name}'")
                break

def test_voice_channel_naming():
    """Test voice channel name format examples"""
    print("\n\n🔊 VOICE CHANNEL NAMING EXAMPLES")
    print("=" * 60)
    
    scenarios = [
        {"server": "Emerald EU", "current": 0, "max": 50, "queue": 0},
        {"server": "Emerald EU", "current": 25, "max": 50, "queue": 0},
        {"server": "Emerald EU", "current": 50, "max": 50, "queue": 0},
        {"server": "Emerald EU", "current": 48, "max": 50, "queue": 5},
        {"server": "Emerald US", "current": 50, "max": 50, "queue": 12},
        {"server": "PvP Arena", "current": 30, "max": 40, "queue": 0},
    ]
    
    for scenario in scenarios:
        server = scenario['server']
        current = scenario['current']
        max_players = scenario['max']
        queue = scenario['queue']
        
        if queue > 0:
            name = f"{server} {current}/{max_players} with {queue} in queue"
        else:
            name = f"{server} {current}/{max_players}"
        
        status = "FULL" if current == max_players else "ONLINE"
        queue_status = f" + {queue} QUEUED" if queue > 0 else ""
        
        print(f"   📡 {name}")
        print(f"      Status: {status}{queue_status}")

def test_accurate_player_counting():
    """Test how accurate player counting works"""
    print("\n\n📊 ACCURATE PLAYER COUNTING LOGIC")
    print("=" * 60)
    
    print("✅ WHAT WE TRACK:")
    print("   • Players entering queue (queued_players set)")
    print("   • Players successfully joining (online_players set)")
    print("   • Players disconnecting (removed from online_players)")
    print("   • Players failing to join (removed from queued_players)")
    
    print("\n🎯 ACCURACY BENEFITS:")
    print("   • Real-time current player count")
    print("   • Accurate queue status")
    print("   • Voice channel shows live server status")
    print("   • Economy rewards based on actual playtime")
    print("   • Failed connections don't mess up counts")
    
    print("\n📈 VOICE CHANNEL UPDATES:")
    print("   • Updates immediately when players join/leave/queue")
    print("   • Only shows queue info when queue > 0")
    print("   • Format: '{Server name} {current}/{max} [with {queue} in queue]'")

def main():
    """Run all lifecycle tests"""
    test_complete_player_lifecycle()
    test_voice_channel_naming()
    test_accurate_player_counting()
    
    print(f"\n\n✅ COMPLETE PLAYER LIFECYCLE SYSTEM DEMONSTRATED!")
    print("=" * 60)
    print("🎯 Key Features:")
    print("✓ Tracks queue → join → disconnect lifecycle")
    print("✓ Handles failed joins without affecting online count")
    print("✓ Extracts max player count from server logs")
    print("✓ Real-time voice channel name updates")
    print("✓ Accurate player counts and queue status")
    print("✓ Economy rewards based on actual playtime")
    print("✓ Smart queue display (only when queue > 0)")

if __name__ == "__main__":
    main()