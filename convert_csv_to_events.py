#!/usr/bin/env node
import csv
import json
import sys
from pathlib import Path

def convert_csv_to_events(csv_file, output_file=None):
    """Convert CSV comment data to ClipPulse API events format"""
    events = []
    
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f, delimiter=';')
        
        for row in reader:
            # Parse time (format: HH:MM:SS)
            time_str = row['time']
            hours, minutes, seconds = map(int, time_str.split(':'))
            
            # Convert to seconds since start
            total_seconds = hours * 3600 + minutes * 60 + seconds
            
            # Get comment count as weight
            weight = float(row['comments_per_second'])
            
            # Create events (one per second for that time period)
            for i in range(int(weight)):
                events.append({
                    "t": total_seconds,
                    "weight": 1.0
                })
    
    if output_file:
        with open(output_file, 'w') as f:
            json.dump({"events": events}, f, indent=2)
        print(f"Converted {len(events)} events to {output_file}")
    else:
        return events

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python convert_csv_to_events.py <csv_file> [output_json]")
        sys.exit(1)
    
    csv_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None
    
    events = convert_csv_to_events(csv_file, output_file)
    if not output_file:
        print(f"Generated {len(events)} events")
        print("First 5 events:")
        for event in events[:5]:
            print(f"  Time: {event['t']}s, Weight: {event['weight']}")
