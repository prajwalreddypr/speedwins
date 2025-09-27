#!/usr/bin/env python3
import csv
import re

def analyze_csv_spikes():
    """Analyze the CSV to find the 3 spikes"""
    
    csv_file = "New fake dataset with 3 spike (500 datapoints).csv"
    
    # Read and parse the CSV
    data = []
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f, delimiter=';')
        for row in reader:
            time_str = row['time']  # e.g., "43:00:00"
            comments = float(row['comments_per_second'])
            
            # Convert time to seconds (assuming format HH:MM:SS)
            time_parts = time_str.split(':')
            if len(time_parts) == 3:
                hours, minutes, seconds = map(int, time_parts)
                total_seconds = hours * 3600 + minutes * 60 + seconds
            else:
                print(f"Warning: Unknown time format: {time_str}")
                continue
            
            data.append({
                'time_str': time_str,
                'seconds': total_seconds,
                'comments': comments
            })
    
    print(f"📊 Total data points: {len(data)}")
    print(f"📈 Max engagement: {max(d['comments'] for d in data):.0f} comments/sec")
    
    # Find top 10 highest engagement moments
    sorted_data = sorted(data, key=lambda x: x['comments'], reverse=True)
    
    print(f"\n🎯 TOP 10 ENGAGEMENT MOMENTS:")
    for i, item in enumerate(sorted_data[:10]):
        print(f"#{i+1}. {item['time_str']} ({item['seconds']}s) - {item['comments']:.0f} comments/sec")
    
    # Convert to backend format
    converted_csv = "converted_spike_dataset.csv"
    with open(converted_csv, 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f, delimiter=';')
        writer.writerow(['video_second', 'time_label', 'comments_per_second'])
        
        for item in data:
            mins = item['seconds'] // 60
            secs = item['seconds'] % 60
            time_label = f"{mins}:{secs:02d}"
            
            writer.writerow([
                item['seconds'],
                time_label,
                item['comments']
            ])
    
    print(f"\n✅ Converted CSV saved as: {converted_csv}")
    print(f"🎬 Ready to process with kaicenat.mov")

if __name__ == "__main__":
    analyze_csv_spikes()
