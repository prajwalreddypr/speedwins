#!/usr/bin/env node
import csv
import numpy as np
from pathlib import Path

def median(vals):
    if not vals: return 0.0
    s = sorted(vals)
    n = len(s)
    mid = n // 2
    return float((s[mid] if n % 2 else (s[mid - 1] + s[mid]) / 2))

def detect_peaks_simple(data, threshold_factor=1.5):
    """Simple peak detection based on threshold above mean"""
    if not data:
        return []
    
    mean_val = sum(data) / len(data)
    std_val = (sum((x - mean_val)**2 for x in data) / len(data))**0.5
    threshold = mean_val + threshold_factor * std_val
    
    peaks = []
    for i in range(1, len(data)-1):
        if (data[i] > threshold and 
            data[i] > data[i-1] and 
            data[i] > data[i+1]):
            peaks.append({
                'index': i,
                'value': data[i],
                'prominence': data[i] - mean_val
            })
    
    return sorted(peaks, key=lambda x: x['value'], reverse=True)

def detect_peaks_top_percentile(data, top_percent=10):
    """Detect top percentile peaks"""
    if not data:
        return []
    
    sorted_data = sorted(enumerate(data), key=lambda x: x[1], reverse=True)
    num_peaks = max(1, len(data) * top_percent // 100)
    
    peaks = []
    for i, (idx, value) in enumerate(sorted_data[:num_peaks]):
        # Check if it's a local maximum
        if (idx > 0 and idx < len(data)-1 and 
            data[idx] > data[idx-1] and data[idx] > data[idx+1]):
            peaks.append({
                'index': idx,
                'value': value,
                'prominence': value - min(data)
            })
    
    return sorted(peaks, key=lambda x: x['index'])

def parse_csv(csv_path):
    """Parse the CSV data"""
    times = []
    counts = []
    engagement_rates = []
    
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f, delimiter=';')
        for row in reader:
            try:
                sec = int(float(row.get("video_second", 0)))
                cps = float(row.get("comments_per_second", 0))
                engagement = float(row.get("engagement_rate_scaled", 0))
                
                times.append(sec)
                counts.append(cps)
                engagement_rates.append(engagement)
            except:
                continue
    
    return times, counts, engagement_rates

def main():
    print("🎬 Detailed Analysis of 5-Minute Demo Video")
    print("=" * 60)
    
    csv_path = "video_with_comments_with_scaled_engagement.csv"
    
    if not Path(csv_path).exists():
        print(f"❌ CSV file not found: {csv_path}")
        return
    
    print(f"📊 Analyzing CSV: {csv_path}")
    times, counts, engagement_rates = parse_csv(csv_path)
    
    if not times:
        print("❌ No data found in CSV")
        return
    
    print(f"📈 Found {len(times)} data points (5 minutes)")
    print(f"📊 Max comments/sec: {max(counts)}")
    print(f"📊 Min comments/sec: {min(counts)}")
    print(f"📊 Average comments/sec: {sum(counts)/len(counts):.1f}")
    print(f"📊 Max engagement rate: {max(engagement_rates):.2f}")
    print(f"📊 Average engagement rate: {sum(engagement_rates)/len(engagement_rates):.2f}")
    
    # Method 1: Simple threshold-based detection
    print(f"\n🔍 METHOD 1: Threshold-based detection")
    peaks_threshold = detect_peaks_simple(counts, threshold_factor=1.5)
    
    print(f"📊 Peaks found with 1.5x std threshold: {len(peaks_threshold)}")
    for i, peak in enumerate(peaks_threshold[:5]):  # Show top 5
        time_seconds = times[peak['index']]
        time_str = f"{time_seconds//60:02d}:{time_seconds%60:02d}"
        print(f"   {i+1}. {time_str} - {peak['value']:.0f} comments/sec")
    
    # Method 2: Top percentile detection
    print(f"\n🔍 METHOD 2: Top 15% percentile detection")
    peaks_percentile = detect_peaks_top_percentile(counts, top_percent=15)
    
    print(f"📊 Peaks found in top 15%: {len(peaks_percentile)}")
    for i, peak in enumerate(peaks_percentile):
        time_seconds = times[peak['index']]
        time_str = f"{time_seconds//60:02d}:{time_seconds%60:02d}"
        print(f"   {i+1}. {time_str} - {peak['value']:.0f} comments/sec")
    
    # Method 3: Engagement rate based
    print(f"\n🔍 METHOD 3: Engagement rate based detection")
    peaks_engagement = detect_peaks_simple(engagement_rates, threshold_factor=1.2)
    
    print(f"📊 Peaks found in engagement rate: {len(peaks_engagement)}")
    for i, peak in enumerate(peaks_engagement[:5]):  # Show top 5
        time_seconds = times[peak['index']]
        time_str = f"{time_seconds//60:02d}:{time_seconds%60:02d}"
        engagement_val = engagement_rates[peak['index']]
        print(f"   {i+1}. {time_str} - {engagement_val:.2f} engagement rate")
    
    # Show data distribution
    print(f"\n📊 DATA DISTRIBUTION:")
    sorted_counts = sorted(counts, reverse=True)
    print(f"   Top 10% values: {sorted_counts[:len(sorted_counts)//10]}")
    print(f"   Top 5% values: {sorted_counts[:len(sorted_counts)//20]}")
    print(f"   Top 3% values: {sorted_counts[:len(sorted_counts)//33]}")
    
    # Find the highest values
    print(f"\n🔥 HIGHEST ENGAGEMENT MOMENTS:")
    top_indices = sorted(range(len(counts)), key=lambda i: counts[i], reverse=True)[:10]
    for i, idx in enumerate(top_indices):
        time_seconds = times[idx]
        time_str = f"{time_seconds//60:02d}:{time_seconds%60:02d}"
        print(f"   {i+1}. {time_str} - {counts[idx]:.0f} comments/sec (engagement: {engagement_rates[idx]:.2f})")
    
    # Recommend the best method
    best_peaks = peaks_percentile if len(peaks_percentile) > 0 else peaks_threshold
    if len(best_peaks) == 0:
        best_peaks = [{'index': idx, 'value': counts[idx]} for idx in top_indices[:5]]
    
    print(f"\n🎯 RECOMMENDED SPIKES FOR CLIP GENERATION: {len(best_peaks)}")
    print("=" * 60)
    
    for i, peak in enumerate(best_peaks):
        time_seconds = times[peak['index']]
        time_str = f"{time_seconds//60:02d}:{time_seconds%60:02d}"
        engagement_val = engagement_rates[peak['index']]
        
        print(f"📊 Spike #{i+1}:")
        print(f"   ⏰ Time: {time_str} ({time_seconds}s)")
        print(f"   📈 Activity: {peak['value']:.0f} comments/sec")
        print(f"   📊 Engagement Rate: {engagement_val:.2f}")
        print(f"   📏 Clip Window: {max(0, time_seconds-30)}s to {time_seconds+30}s")
    
    return best_peaks

if __name__ == "__main__":
    peaks = main()
