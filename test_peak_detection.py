#!/usr/bin/env node
import json
import csv
import math
import random
from pathlib import Path

# Import the peak detection functions from main.py
def median_filter(x, k=5):
    if k <= 1 or len(x) == 0:
        return x
    pad = k // 2
    xp = [x[0]]*pad + list(x) + [x[-1]]*pad
    out = []
    for i in range(len(x)):
        window = xp[i:i+k]
        sorted_w = sorted(window)
        out.append(sorted_w[len(sorted_w)//2])
    return out

def rolling_median_mad(x, win=31):
    if len(x) == 0:
        return [], []
    pad = win // 2
    xp = [x[0]]*pad + list(x) + [x[-1]]*pad
    med = []
    mad = []
    for i in range(len(x)):
        w = xp[i:i+win]
        m = sorted(w)[len(w)//2]
        med.append(m)
        mad.append(sorted([abs(v - m) for v in w])[len(w)//2] + 1e-6)
    return med, mad

def aggregate_counts(events):
    if not events:
        return [], []
    t_max = max(float(e.get("t", 0.0)) for e in events)
    n_bins = int(math.floor(t_max)) + 1
    counts = [0.0] * n_bins
    for e in events:
        t = float(e.get("t", 0.0))
        w = float(e.get("weight", 1.0))
        idx = int(math.floor(max(0.0, t)))
        if 0 <= idx < n_bins:
            counts[idx] += w
    times = [float(i) for i in range(n_bins)]
    return times, counts

def detect_peak(times, counts, K=3.0):
    if not times:
        return 0.0
    x = counts[:]
    x_s = median_filter(x, k=5)
    baseline, mad = rolling_median_mad(x_s, win=31)
    thr = [b + K*m for b, m in zip(baseline, mad)]

    # candidates: local maxima above threshold
    candidates = []
    for i in range(1, len(x_s)-1):
        if x_s[i] >= thr[i] and x_s[i] > x_s[i-1] and x_s[i] >= x_s[i+1]:
            prom = x_s[i] - baseline[i]
            candidates.append((i, prom))
    if candidates:
        best_idx = max(candidates, key=lambda t: t[1])[0]
    else:
        best_idx = int(max(range(len(x_s)), key=lambda i: x_s[i])) if x_s else 0
    return float(times[best_idx])

def analyze_csv_file(csv_file):
    """Analyze CSV file and find peaks"""
    print(f"\n🔍 Analyzing {csv_file}...")
    
    # Read CSV data
    times = []
    counts = []
    
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f, delimiter=';')
        for row in reader:
            # Parse time (format: HH:MM:SS)
            time_str = row['time']
            hours, minutes, seconds = map(int, time_str.split(':'))
            total_seconds = hours * 3600 + minutes * 60 + seconds
            
            times.append(total_seconds)
            counts.append(float(row['comments_per_second']))
    
    print(f"📊 Data points: {len(times)}")
    print(f"⏱️  Duration: {times[0]/3600:.1f}h to {times[-1]/3600:.1f}h")
    print(f"📈 Max comments/sec: {max(counts)}")
    print(f"📉 Min comments/sec: {min(counts)}")
    
    # Convert to events format
    events = []
    for t, count in zip(times, counts):
        for i in range(int(count)):
            events.append({"t": t, "weight": 1.0})
    
    # Detect peak
    peak_time = detect_peak(times, counts)
    
    # Convert peak time back to HH:MM:SS
    peak_hours = int(peak_time // 3600)
    peak_minutes = int((peak_time % 3600) // 60)
    peak_seconds = int(peak_time % 60)
    peak_time_str = f"{peak_hours:02d}:{peak_minutes:02d}:{peak_seconds:02d}"
    
    print(f"🎯 PEAK DETECTED at: {peak_time_str} ({peak_time:.0f} seconds)")
    
    # Find the actual count at peak time
    peak_index = min(int(peak_time - times[0]), len(counts) - 1)
    peak_activity = counts[peak_index] if peak_index < len(counts) else counts[-1]
    print(f"📊 Peak activity: {peak_activity:.0f} comments/second")
    
    # Find clip time range (±30 seconds)
    clip_start = max(0, peak_time - 30)
    clip_end = peak_time + 30
    
    clip_start_h = int(clip_start // 3600)
    clip_start_m = int((clip_start % 3600) // 60)
    clip_start_s = int(clip_start % 60)
    
    clip_end_h = int(clip_end // 3600)
    clip_end_m = int((clip_end % 3600) // 60)
    clip_end_s = int(clip_end % 60)
    
    print(f"🎬 CLIP RANGE: {clip_start_h:02d}:{clip_start_m:02d}:{clip_start_s:02d} to {clip_end_h:02d}:{clip_end_m:02d}:{clip_end_s:02d}")
    print(f"⏱️  Duration: 60 seconds")
    
    return {
        "peak_time": peak_time,
        "peak_time_str": peak_time_str,
        "clip_start": clip_start,
        "clip_end": clip_end,
        "max_activity": peak_activity
    }

if __name__ == "__main__":
    print("🚀 ClipPulse Peak Detection Analysis")
    print("=" * 50)
    
    # Analyze both CSV files
    results = []
    
    if Path("Dataset of evolution in comments.csv").exists():
        result1 = analyze_csv_file("Dataset of evolution in comments.csv")
        results.append(("Real Data", result1))
    
    if Path("New fake dataset with 3 spike (500 datapoints).csv").exists():
        result2 = analyze_csv_file("New fake dataset with 3 spike (500 datapoints).csv")
        results.append(("Synthetic Data", result2))
    
    print("\n" + "=" * 50)
    print("📋 SUMMARY OF DETECTED PEAKS:")
    print("=" * 50)
    
    for dataset_name, result in results:
        print(f"\n📊 {dataset_name}:")
        print(f"   🎯 Peak at: {result['peak_time_str']}")
        print(f"   📈 Activity: {result['max_activity']:.0f} comments/sec")
        print(f"   🎬 Clip: {result['clip_start']:.0f}s to {result['clip_end']:.0f}s")
    
    print(f"\n✅ Analysis complete! These are the moments that would be extracted as clips.")
    print(f"💡 To extract actual video clips, you'll need FFmpeg installed and working.")
