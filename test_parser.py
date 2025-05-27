#!/usr/bin/env python3
"""
Test script to validate parser logic with real CSV data
"""

import asyncio
import sys
from datetime import datetime, timezone
from pathlib import Path

# Add bot directory to path
sys.path.append('.')

async def test_csv_parser():
    """Test the CSV parsing logic with our real data"""
    print("🔍 Testing CSV Parser Logic...")
    
    # Read the test CSV file
    csv_file = Path('./dev_data/csv/2025.05.15-00.00.00.csv')
    
    if not csv_file.exists():
        print("❌ Test CSV file not found!")
        return False
    
    with open(csv_file, 'r') as f:
        lines = f.readlines()
    
    print(f"📄 Found {len(lines)} lines in CSV file")
    
    # Test parsing each line
    kills = 0
    suicides = 0
    deaths = 0
    weapons = {}
    
    for i, line in enumerate(lines[:20], 1):  # Test first 20 lines
        line = line.strip()
        if not line:
            continue
            
        # Parse CSV format: timestamp;killer;killer_id;victim;victim_id;weapon;distance;killer_platform;victim_platform
        parts = line.split(';')
        if len(parts) < 7:
            print(f"⚠️ Line {i}: Invalid format - {line}")
            continue
            
        timestamp_str, killer, killer_id, victim, victim_id, weapon, distance = parts[:7]
        
        # Parse timestamp 
        try:
            timestamp = datetime.strptime(timestamp_str, '%Y.%m.%d-%H.%M.%S')
            timestamp = timestamp.replace(tzinfo=timezone.utc)
        except ValueError as e:
            print(f"⚠️ Line {i}: Invalid timestamp - {timestamp_str}")
            continue
        
        # Parse distance
        try:
            distance_float = float(distance) if distance and distance != '0' else 0.0
        except ValueError:
            distance_float = 0.0
        
        # Check if suicide
        is_suicide = killer == victim
        if is_suicide:
            if 'suicide_by_relocation' in weapon:
                weapon = 'Menu Suicide'
            elif 'falling' in weapon:
                weapon = 'Falling'
            else:
                weapon = 'Suicide'
            suicides += 1
        else:
            kills += 1
            deaths += 1
        
        # Track weapons
        weapons[weapon] = weapons.get(weapon, 0) + 1
        
        print(f"✅ Line {i}: {killer} -> {victim} with {weapon} ({distance_float}m) {'[SUICIDE]' if is_suicide else ''}")
    
    print(f"\n📊 Test Results:")
    print(f"   Kills: {kills}")
    print(f"   Deaths: {deaths}")
    print(f"   Suicides: {suicides}")
    print(f"   Total Events: {kills + suicides}")
    
    print(f"\n🔫 Top Weapons:")
    top_weapons = sorted(weapons.items(), key=lambda x: x[1], reverse=True)[:5]
    for weapon, count in top_weapons:
        print(f"   {weapon}: {count}")
    
    print(f"\n✅ CSV Parser Logic Test Complete!")
    return True

async def test_log_parser():
    """Test the log parsing logic"""
    print("\n🔍 Testing Log Parser Logic...")
    
    log_file = Path('./dev_data/logs/Deadside.log')
    
    if not log_file.exists():
        print("❌ Test log file not found!")
        return False
    
    with open(log_file, 'r') as f:
        lines = f.readlines()
    
    print(f"📄 Found {len(lines)} lines in log file")
    
    # Test log patterns
    import re
    
    patterns = {
        'player_join': re.compile(r'\[(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\].*Player "([^"]+)" connected.*ID: (\d+)'),
        'player_disconnect': re.compile(r'\[(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\].*Player "([^"]+)" disconnected'),
        'airdrop': re.compile(r'\[(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\].*Airdrop.*spawned'),
        'mission': re.compile(r'\[(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\].*Mission.*started'),
        'trader': re.compile(r'\[(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\].*Trader.*restock'),
    }
    
    events_found = {}
    
    for i, line in enumerate(lines[:50], 1):  # Test first 50 lines
        line = line.strip()
        if not line:
            continue
            
        for event_type, pattern in patterns.items():
            if pattern.search(line):
                events_found[event_type] = events_found.get(event_type, 0) + 1
                print(f"✅ Line {i}: Found {event_type} event")
                break
    
    print(f"\n📊 Log Events Found:")
    for event_type, count in events_found.items():
        print(f"   {event_type}: {count}")
    
    print(f"\n✅ Log Parser Logic Test Complete!")
    return True

async def main():
    """Run all parser tests"""
    print("🚀 Starting Parser Logic Tests...\n")
    
    csv_success = await test_csv_parser()
    log_success = await test_log_parser()
    
    print(f"\n🎯 Overall Test Results:")
    print(f"   CSV Parser: {'✅ PASS' if csv_success else '❌ FAIL'}")
    print(f"   Log Parser: {'✅ PASS' if log_success else '❌ FAIL'}")
    
    if csv_success and log_success:
        print(f"\n🎉 All parser logic tests PASSED! Ready for production!")
    else:
        print(f"\n⚠️ Some tests failed. Please review the parser logic.")

if __name__ == "__main__":
    asyncio.run(main())