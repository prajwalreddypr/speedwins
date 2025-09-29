#!/usr/bin/env node
import csv
from pathlib import Path

def convert_to_proper_format(input_csv, output_csv):
    """Convert CSV to the format expected by the updated system"""
    
    # Read the original CSV
    rows = []
    with open(input_csv, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f, delimiter=';')
        for row in reader:
            time_str = row.get('time', '')
            comments_per_second = row.get('comments_per_second', '0')
            
            # Convert time to seconds
            if ':' in time_str:
                parts = time_str.split(':')
                if len(parts) == 3:
                    hours, minutes, seconds = map(int, parts)
                    video_second = hours * 3600 + minutes * 60 + seconds
                else:
                    video_second = 0
            else:
                video_second = int(float(time_str)) if time_str.isdigit() else 0
            
            rows.append({
                'video_second': video_second,
                'time_label': time_str,
                'comments_per_second': comments_per_second
            })
    
    # Write the new format CSV
    with open(output_csv, 'w', newline='', encoding='utf-8') as f:
        if rows:
            fieldnames = ['video_second', 'time_label', 'comments_per_second']
            writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter=';')
            writer.writeheader()
            writer.writerows(rows)
    
    print(f"✅ Converted {len(rows)} rows to proper format: {output_csv}")
    return len(rows)

if __name__ == "__main__":
    # Convert the engagement CSV to proper format
    input_file = "media/engagement/engagement.csv"
    output_file = "media/engagement/proper_format_engagement.csv"
    
    if Path(input_file).exists():
        convert_to_proper_format(input_file, output_file)
        print(f"🎯 Ready to process with: {output_file}")
    else:
        print(f"❌ File not found: {input_file}")
