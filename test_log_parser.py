#!/usr/bin/env python3
"""
Test the Deadside.log parser to see what events it can detect
"""
import re
from pathlib import Path

def analyze_deadside_log():
    """Analyze the Deadside.log file to see what events are present"""
    
    log_file = Path('./dev_data/logs/Deadside.log')
    if not log_file.exists():
        print("❌ Deadside.log file not found")
        return
    
    print("🔍 ANALYZING DEADSIDE.LOG FILE")
    print("=" * 60)
    
    # Patterns the log parser looks for
    patterns = {
        'player_join': re.compile(r'\[(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\].*Player "([^"]+)" connected.*ID: (\d+)'),
        'player_disconnect': re.compile(r'\[(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\].*Player "([^"]+)" disconnected'),
        'queue_size': re.compile(r'\[(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\].*Queue size: (\d+)'),
        'airdrop': re.compile(r'\[(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\].*Airdrop.*spawned.*location.*X=([0-9.-]+).*Y=([0-9.-]+)'),
        'mission': re.compile(r'\[(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\].*Mission.*started.*type.*([A-Za-z]+)'),
        'trader': re.compile(r'\[(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\].*Trader.*([A-Za-z ]+).*restock'),
        'helicrash': re.compile(r'\[(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\].*Helicopter.*crash.*X=([0-9.-]+).*Y=([0-9.-]+)'),
        'server_crash': re.compile(r'\[(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\].*Fatal error|Assertion failed|Access violation'),
        'server_restart': re.compile(r'\[(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\].*Server.*restart|shutdown')
    }
    
    # Count different event types
    event_counts = {key: 0 for key in patterns.keys()}
    found_events = {key: [] for key in patterns.keys()}
    
    with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
        lines = f.readlines()
    
    print(f"📄 Total lines in log: {len(lines)}")
    
    # Analyze each line
    for line_num, line in enumerate(lines, 1):
        line = line.strip()
        if not line:
            continue
            
        for event_type, pattern in patterns.items():
            if pattern.search(line):
                event_counts[event_type] += 1
                found_events[event_type].append((line_num, line[:100] + "..." if len(line) > 100 else line))
    
    print("\n📊 EVENT DETECTION RESULTS:")
    print("-" * 40)
    
    total_events = sum(event_counts.values())
    
    for event_type, count in event_counts.items():
        status = "✅" if count > 0 else "❌"
        print(f"{status} {event_type.replace('_', ' ').title()}: {count} events")
    
    print(f"\n🎯 TOTAL DETECTABLE EVENTS: {total_events}")
    
    # Show sample events found
    if total_events > 0:
        print(f"\n🔍 SAMPLE EVENTS FOUND:")
        print("-" * 40)
        
        for event_type, events in found_events.items():
            if events:
                print(f"\n📝 {event_type.replace('_', ' ').title()}:")
                for i, (line_num, sample) in enumerate(events[:3]):  # Show first 3 of each type
                    print(f"   Line {line_num}: {sample}")
                if len(events) > 3:
                    print(f"   ... and {len(events) - 3} more")
    else:
        print("\n⚠️  NO DETECTABLE EVENTS FOUND")
        print("The log file may contain:")
        print("- Server startup/initialization logs only")
        print("- Different log format than expected")
        print("- No player activity during this period")
        
        # Show sample lines to understand the format
        print(f"\n📄 SAMPLE LOG LINES:")
        print("-" * 40)
        for i in range(min(10, len(lines))):
            print(f"Line {i+1}: {lines[i].strip()[:100]}")
    
    # Check for any connection-related logs
    print(f"\n🔍 CHECKING FOR CONNECTION ACTIVITY:")
    print("-" * 40)
    
    connection_keywords = ['connect', 'disconnect', 'accept', 'player', 'steam', 'epic']
    connection_lines = []
    
    for line_num, line in enumerate(lines, 1):
        line_lower = line.lower()
        if any(keyword in line_lower for keyword in connection_keywords):
            connection_lines.append((line_num, line.strip()))
    
    if connection_lines:
        print(f"Found {len(connection_lines)} connection-related lines:")
        for i, (line_num, line) in enumerate(connection_lines[:10]):  # Show first 10
            print(f"   Line {line_num}: {line[:100]}")
        if len(connection_lines) > 10:
            print(f"   ... and {len(connection_lines) - 10} more")
    else:
        print("No obvious connection activity found")

def main():
    """Run the log analysis"""
    analyze_deadside_log()
    
    print(f"\n✅ LOG PARSER ANALYSIS COMPLETE!")
    print("=" * 60)
    print("The log parser is designed to detect:")
    print("• Player connections and disconnections")
    print("• Server queue sizes")
    print("• Airdrop spawns with coordinates")
    print("• Mission starts")
    print("• Trader restocks")
    print("• Helicopter crashes with coordinates") 
    print("• Server crashes and restarts")

if __name__ == "__main__":
    main()