#!/usr/bin/env python3
"""
Convert CSV from time;comments_per_second format to video_second;time_label;comments_per_second format
"""

import csv
import sys
from pathlib import Path

def convert_csv_format(input_csv, output_csv):
    """Convert CSV format for ClipPulse backend"""
    
    with open(input_csv, 'r', encoding='utf-8') as infile:
        reader = csv.DictReader(infile, delimiter=';')
        
        rows = []
        for row in reader:
            time_str = row['time']  # e.g., "43:00:00"
            comments_per_second = float(row['comments_per_second'])
            
            # Convert time string to seconds
            # Format: HH:MM:SS or MM:SS
            time_parts = time_str.split(':')
            if len(time_parts) == 3:  # HH:MM:SS
                hours, minutes, seconds = map(int, time_parts)
                total_seconds = hours * 3600 + minutes * 60 + seconds
            elif len(time_parts) == 2:  # MM:SS
                minutes, seconds = map(int, time_parts)
                total_seconds = minutes * 60 + seconds
            else:
                print(f"Warning: Unknown time format: {time_str}")
                continue
            
            # Convert to minutes:seconds format for time_label
            mins = total_seconds // 60
            secs = total_seconds % 60
            time_label = f"{mins}:{secs:02d}"
            
            rows.append({
                'video_second': total_seconds,
                'time_label': time_label,
                'comments_per_second': comments_per_second
            })
    
    # Write converted CSV
    with open(output_csv, 'w', encoding='utf-8', newline='') as outfile:
        fieldnames = ['video_second', 'time_label', 'comments_per_second']
        writer = csv.DictWriter(outfile, fieldnames=fieldnames, delimiter=';')
        writer.writeheader()
        writer.writerows(rows)
    
    print(f"✅ Converted {input_csv} -> {output_csv}")
    print(f"📊 Converted {len(rows)} data points")

if __name__ == "__main__":
    input_file = "New fake dataset with 3 spike (500 datapoints).csv"
    output_file = "converted_3_spike_dataset.csv"
    
    if Path(input_file).exists():
        convert_csv_format(input_file, output_file)
        print(f"\n🎯 Ready to use: {output_file}")
    else:
        print(f"❌ File not found: {input_file}")
