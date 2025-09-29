#!/usr/bin/env node
import csv
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path

def median(vals):
    if not vals: return 0.0
    s = sorted(vals)
    n = len(s)
    mid = n // 2
    return float((s[mid] if n % 2 else (s[mid - 1] + s[mid]) / 2))

def median_filter(x, k=5):
    if k <= 1 or not x:
        return x
    pad = k // 2
    xp = [x[0]] * pad + list(x) + [x[-1]] * pad
    out = []
    for i in range(len(x)):
        w = xp[i:i + k]
        out.append(median(w))
    return out

def rolling_median_mad(x, win=31):
    if not x: return [], []
    pad = win // 2
    xp = [x[0]] * pad + list(x) + [x[-1]] * pad
    med, mad = [], []
    for i in range(len(x)):
        w = xp[i:i + win]
        m = median(w)
        med.append(m)
        mad.append(median([abs(v - m) for v in w]) + 1e-6)
    return med, mad

def detect_all_peaks(times, counts, K=2.5, min_prominence=10):
    """Detect all significant peaks in the data"""
    if not times:
        return []
    
    x_s = median_filter(counts, k=5)
    baseline, mad = rolling_median_mad(x_s, win=31)
    thr = [b + K*m for b, m in zip(baseline, mad)]

    # Find all local maxima above threshold
    peaks = []
    for i in range(1, len(x_s)-1):
        if (x_s[i] >= thr[i] and 
            x_s[i] > x_s[i-1] and 
            x_s[i] >= x_s[i+1] and
            x_s[i] - baseline[i] >= min_prominence):
            
            prominence = x_s[i] - baseline[i]
            peaks.append({
                'index': i,
                'time': times[i],
                'activity': x_s[i],
                'baseline': baseline[i],
                'prominence': prominence,
                'threshold': thr[i]
            })
    
    # Sort by prominence (strongest peaks first)
    peaks.sort(key=lambda x: x['prominence'], reverse=True)
    
    return peaks

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
    print("🎬 Analyzing 5-Minute Demo Video Spikes")
    print("=" * 60)
    
    csv_path = "video_with_comments_with_scaled_engagement.csv"
    video_path = "demo-video-5min.mp4"
    
    if not Path(csv_path).exists():
        print(f"❌ CSV file not found: {csv_path}")
        return
    
    if not Path(video_path).exists():
        print(f"❌ Video file not found: {video_path}")
        return
    
    print(f"📊 Analyzing CSV: {csv_path}")
    times, counts, engagement_rates = parse_csv(csv_path)
    
    if not times:
        print("❌ No data found in CSV")
        return
    
    print(f"📈 Found {len(times)} data points (5 minutes)")
    print(f"📊 Max comments/sec: {max(counts)}")
    print(f"📊 Max engagement rate: {max(engagement_rates):.2f}")
    print(f"📊 Average comments/sec: {sum(counts)/len(counts):.1f}")
    
    # Detect all peaks
    peaks = detect_all_peaks(times, counts, K=2.5, min_prominence=5)
    
    print(f"\n🎯 SPIKES DETECTED: {len(peaks)}")
    print("=" * 60)
    
    for i, peak in enumerate(peaks):
        time_seconds = peak['time']
        time_str = f"{time_seconds//60:02d}:{time_seconds%60:02d}"
        
        print(f"\n📊 Spike #{i+1}:")
        print(f"   ⏰ Time: {time_str} ({time_seconds}s)")
        print(f"   📈 Activity: {peak['activity']:.0f} comments/sec")
        print(f"   📊 Baseline: {peak['baseline']:.1f} comments/sec")
        print(f"   🎯 Prominence: {peak['prominence']:.1f}")
        print(f"   📏 Clip Window: {max(0, time_seconds-30)}s to {time_seconds+30}s")
    
    # Summary statistics
    if peaks:
        strongest_peak = peaks[0]
        weakest_peak = peaks[-1]
        
        print(f"\n📋 SUMMARY:")
        print(f"   🎯 Total Spikes: {len(peaks)}")
        print(f"   🔥 Strongest: {strongest_peak['time']//60:02d}:{strongest_peak['time']%60:02d} ({strongest_peak['activity']:.0f} comments/sec)")
        print(f"   📉 Weakest: {weakest_peak['time']//60:02d}:{weakest_peak['time']%60:02d} ({weakest_peak['activity']:.0f} comments/sec)")
        print(f"   ⏱️  Duration: 5 minutes ({len(times)} seconds)")
        print(f"   📊 Average spike interval: {len(times)//len(peaks):.0f} seconds")
    
    print(f"\n🎬 Ready to generate clips from the {len(peaks)} detected spikes!")
    return peaks

if __name__ == "__main__":
    peaks = main()
