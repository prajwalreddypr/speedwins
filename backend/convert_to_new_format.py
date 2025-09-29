#!/usr/bin/env node
import csv
import re
from pathlib import Path

def convert_time_to_seconds(time_str):
    """Convert HH:MM:SS to seconds since start"""
    # Remove any leading/trailing whitespace
    time_str = time_str.strip()
    
    # Parse the time format (HH:MM:SS)
    parts = time_str.split(':')
    if len(parts) == 3:
        hours, minutes, seconds = map(int, parts)
        return hours * 3600 + minutes * 60 + seconds
    return 0

def convert_csv_format(input_csv, output_csv):
    """Convert old format to new format expected by the updated system"""
    
    # Read the input CSV
    rows = []
    with open(input_csv, 'r', encoding='utf-8') as f:
        # Detect delimiter
        first_line = f.readline().strip()
        f.seek(0)
        delimiter = ';' if ';' in first_line else ','
        
        reader = csv.DictReader(f, delimiter=delimiter)
        for row in reader:
            time_str = row.get('time', '')
            comments_per_second = row.get('comments_per_second', '0')
            
            # Convert time to seconds
            video_second = convert_time_to_seconds(time_str)
            
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
    
    print(f"✅ Converted {len(rows)} rows from {input_csv} to {output_csv}")
    return len(rows)

if __name__ == "__main__":
    # Convert both CSV files
    files_to_convert = [
        "Dataset of evolution in comments.csv",
        "New fake dataset with 3 spike (500 datapoints).csv"
    ]
    
    for input_file in files_to_convert:
        if Path(input_file).exists():
            output_file = f"media/engagement/converted_{input_file}"
            convert_csv_format(input_file, output_file)
        else:
            print(f"❌ File not found: {input_file}")
    
    print("\n🎯 Conversion complete! The new format CSV files are in media/engagement/")
