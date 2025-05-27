#!/usr/bin/env python3
"""
Complete analysis of ALL CSV data to get accurate stats
"""

def analyze_full_csv():
    """Analyze all 283 lines in the CSV file"""
    
    with open('./dev_data/csv/2025.05.15-00.00.00.csv', 'r') as f:
        lines = f.readlines()
    
    print(f"📊 ANALYZING ALL {len(lines)} LINES OF CSV DATA")
    print("="*60)
    
    kills = 0
    suicides = 0
    total_events = 0
    weapons = {}
    players = set()
    
    for line_num, line in enumerate(lines, 1):
        line = line.strip()
        if not line:
            continue
            
        parts = line.split(';')
        if len(parts) < 7:
            continue
            
        timestamp_str, killer, killer_id, victim, victim_id, weapon, distance = parts[:7]
        
        # Track players
        players.add(killer)
        players.add(victim)
        
        # Check if suicide
        is_suicide = killer == victim
        
        if is_suicide:
            suicides += 1
            # Normalize suicide weapons
            if 'suicide_by_relocation' in weapon:
                weapon = 'Menu Suicide'
            elif 'falling' in weapon:
                weapon = 'Falling'
            else:
                weapon = 'Suicide'
        else:
            kills += 1
        
        # Track weapons
        weapons[weapon] = weapons.get(weapon, 0) + 1
        total_events += 1
    
    print(f"📈 COMPLETE RESULTS:")
    print(f"   Total Lines: {len(lines)}")
    print(f"   Total Events: {total_events}")
    print(f"   Actual Kills: {kills}")
    print(f"   Suicides: {suicides}")
    print(f"   Unique Players: {len(players)}")
    
    print(f"\n🔫 TOP 10 WEAPONS:")
    top_weapons = sorted(weapons.items(), key=lambda x: x[1], reverse=True)[:10]
    for weapon, count in top_weapons:
        print(f"   {weapon}: {count}")
    
    print(f"\n📊 BREAKDOWN:")
    suicide_percentage = (suicides / total_events * 100) if total_events > 0 else 0
    kill_percentage = (kills / total_events * 100) if total_events > 0 else 0
    print(f"   Kills: {kill_percentage:.1f}%")
    print(f"   Suicides: {suicide_percentage:.1f}%")
    
    # Show some sample players
    print(f"\n👥 SAMPLE PLAYERS:")
    player_list = list(players)[:10]
    for player in player_list:
        print(f"   {player}")
    
    return kills, suicides, total_events, len(players)

if __name__ == "__main__":
    analyze_full_csv()