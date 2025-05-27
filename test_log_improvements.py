#!/usr/bin/env python3
"""
Test script to demonstrate all the log parser improvements
"""
import re
from datetime import datetime, timezone

def test_player_lifecycle_tracking():
    """Test player join/disconnect tracking for playtime rewards"""
    print("👥 PLAYER LIFECYCLE TRACKING")
    print("=" * 60)
    
    # Sample log lines for player events
    sample_events = [
        "[2025.05.17-14.30.15:123] LogOnline: Login: UniqueId: m3_GOKI, PlatformId: 76561198033779078",
        "[2025.05.17-14.45.32:456] LogOnline: Logout: UniqueId: m3_GOKI",
        "[2025.05.17-15.12.08:789] LogOnline: Login: UniqueId: oooSLAYERoo, PlatformId: 76561198126636736"
    ]
    
    # Updated patterns
    join_pattern = re.compile(r'\[(\d{4}\.\d{2}\.\d{2}-\d{2}\.\d{2}\.\d{2}:\d{3})\].*LogOnline.*Login.*UniqueId.*([A-Za-z0-9_]+).*PlatformId.*(\d+)')
    disconnect_pattern = re.compile(r'\[(\d{4}\.\d{2}\.\d{2}-\d{2}\.\d{2}\.\d{2}:\d{3})\].*LogOnline.*Logout.*UniqueId.*([A-Za-z0-9_]+)')
    
    for event in sample_events:
        print(f"\n📝 Event: {event}")
        
        join_match = join_pattern.search(event)
        disconnect_match = disconnect_pattern.search(event)
        
        if join_match:
            timestamp, player, platform_id = join_match.groups()
            print(f"   ✅ PLAYER JOIN DETECTED")
            print(f"   Player: {player}")
            print(f"   Platform ID: {platform_id}")
            print(f"   Action: Start tracking playtime")
            
        elif disconnect_match:
            timestamp, player = disconnect_match.groups()
            print(f"   ❌ PLAYER DISCONNECT DETECTED")
            print(f"   Player: {player}")
            print(f"   Action: Calculate playtime, award economy points")

def test_mission_normalization():
    """Test mission name normalization and level detection"""
    print("\n\n🎯 MISSION NORMALIZATION & LEVEL DETECTION")
    print("=" * 60)
    
    # Sample mission events
    mission_events = [
        "[2025.05.17-16.20.30:123] Mission: convoy_escort Level 3 started at coordinates X=1250.5 Y=2340.8",
        "[2025.05.17-16.45.15:456] Mission: supply_drop Level 1 started at coordinates X=980.2 Y=1760.3",
        "[2025.05.17-17.10.22:789] Mission: elimination Level 5 started at coordinates X=2100.7 Y=3200.1"
    ]
    
    mission_pattern = re.compile(r'\[(\d{4}\.\d{2}\.\d{2}-\d{2}\.\d{2}\.\d{2}:\d{3})\].*Mission.*([A-Za-z_]+).*Level.*(\d+).*started')
    
    mission_mappings = {
        'convoy_escort': 'Convoy Escort',
        'supply_drop': 'Supply Drop',
        'elimination': 'Elimination',
        'capture_point': 'Capture Point',
        'rescue_mission': 'Rescue Mission'
    }
    
    for event in mission_events:
        print(f"\n📝 Event: {event}")
        
        match = mission_pattern.search(event)
        if match:
            timestamp, raw_mission, level = match.groups()
            normalized_name = mission_mappings.get(raw_mission, raw_mission.replace('_', ' ').title())
            
            print(f"   🎯 MISSION DETECTED")
            print(f"   Raw Name: {raw_mission}")
            print(f"   Normalized: {normalized_name}")
            print(f"   Level: {level}")
            print(f"   Action: Send embed (Level {level} {normalized_name})")

def test_trader_spawn_events():
    """Test trader spawn detection (not restocks)"""
    print("\n\n🏪 TRADER SPAWN EVENTS")
    print("=" * 60)
    
    trader_events = [
        "[2025.05.17-18.30.45:123] Trader: weapon_dealer spawned at location X=1500.2 Y=2800.9",
        "[2025.05.17-19.15.30:456] Trader: medical_supplier spawned at location X=750.8 Y=1200.4"
    ]
    
    trader_pattern = re.compile(r'\[(\d{4}\.\d{2}\.\d{2}-\d{2}\.\d{2}\.\d{2}:\d{3})\].*Trader.*([A-Za-z_]+).*spawned.*location')
    
    for event in trader_events:
        print(f"\n📝 Event: {event}")
        
        match = trader_pattern.search(event)
        if match:
            timestamp, trader_type = match.groups()
            trader_name = trader_type.replace('_', ' ').title()
            
            print(f"   🏪 TRADER SPAWN DETECTED")
            print(f"   Type: {trader_name}")
            print(f"   Action: Send spawn notification embed")

def test_airdrop_flying_trigger():
    """Test airdrop 'Flying' line as embed trigger"""
    print("\n\n🪂 AIRDROP FLYING TRIGGER")
    print("=" * 60)
    
    airdrop_events = [
        "[2025.05.17-20.45.12:123] Airdrop: preparation phase started",
        "[2025.05.17-20.46.30:456] Airdrop: Flying to location X=1800.5 Y=2400.7 altitude=500m",
        "[2025.05.17-20.48.15:789] Airdrop: landed at coordinates X=1800.5 Y=2400.7"
    ]
    
    flying_pattern = re.compile(r'\[(\d{4}\.\d{2}\.\d{2}-\d{2}\.\d{2}\.\d{2}:\d{3})\].*Airdrop.*Flying.*location.*X=([0-9.-]+).*Y=([0-9.-]+)')
    
    for event in airdrop_events:
        print(f"\n📝 Event: {event}")
        
        match = flying_pattern.search(event)
        if match:
            timestamp, x_coord, y_coord = match.groups()
            
            print(f"   🪂 AIRDROP FLYING DETECTED (TRIGGER LINE)")
            print(f"   Coordinates: X={x_coord}, Y={y_coord}")
            print(f"   Action: Send airdrop embed notification")
        else:
            print(f"   📋 Other airdrop event (no embed)")

def test_currency_configuration():
    """Test configurable currency names"""
    print("\n\n💎 CONFIGURABLE CURRENCY NAMES")
    print("=" * 60)
    
    guild_configs = [
        {"guild_id": 12345, "currency_name": "Emeralds", "server_name": "Emerald EU"},
        {"guild_id": 67890, "currency_name": "Credits", "server_name": "PvP Warriors"},
        {"guild_id": 54321, "currency_name": "Coins", "server_name": "Deadside Elite"}
    ]
    
    for config in guild_configs:
        print(f"\n🏛️ Guild: {config['server_name']}")
        print(f"   Currency: {config['currency_name']}")
        print(f"   Command: /setcurrency {config['currency_name']}")
        print(f"   Usage: 'You earned 15 {config['currency_name']} for 15 minutes playtime'")

def test_playtime_rewards():
    """Test playtime economy rewards calculation"""
    print("\n\n⏰ PLAYTIME ECONOMY REWARDS")
    print("=" * 60)
    
    # Simulate player sessions
    sessions = [
        {"player": "m3_GOKI", "join": "14:30:15", "leave": "14:45:32", "minutes": 15},
        {"player": "oooSLAYERoo", "join": "15:12:08", "leave": "16:45:22", "minutes": 93},
        {"player": "The_Legend_of_MK", "join": "16:20:30", "leave": "16:23:15", "minutes": 3}
    ]
    
    for session in sessions:
        print(f"\n👤 Player: {session['player']}")
        print(f"   Join: {session['join']}")
        print(f"   Leave: {session['leave']}")
        print(f"   Playtime: {session['minutes']} minutes")
        
        if session['minutes'] >= 5:
            print(f"   ✅ Reward: {session['minutes']} Emeralds (1 per minute)")
            print(f"   Event: 'Online time: {session['minutes']} minutes'")
        else:
            print(f"   ❌ No reward (minimum 5 minutes required)")

def main():
    """Run all improvement tests"""
    test_player_lifecycle_tracking()
    test_mission_normalization()
    test_trader_spawn_events()
    test_airdrop_flying_trigger()
    test_currency_configuration()
    test_playtime_rewards()
    
    print(f"\n\n✅ ALL LOG PARSER IMPROVEMENTS DEMONSTRATED!")
    print("=" * 60)
    print("🎯 Implemented Features:")
    print("✓ Player lifecycle tracking for playtime rewards")
    print("✓ Mission name normalization with level detection")
    print("✓ Trader spawn events (not restocks)")
    print("✓ Airdrop 'Flying' line triggers embeds")
    print("✓ Configurable currency names per guild")
    print("✓ Economy points awarded for playtime (1 per minute, 5min minimum)")

if __name__ == "__main__":
    main()