#!/usr/bin/env node
import csv
import math
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

def detect_peak_index(times, counts, K=3.0):
    """Robust peak detection"""
    if not times:
        return 0
    
    x_s = median_filter(counts, k=5)
    baseline, mad = rolling_median_mad(x_s, win=31)
    thr = [b + K*m for b, m in zip(baseline, mad)]

    # Find candidates: local maxima above threshold
    candidates = []
    for i in range(1, len(x_s)-1):
        if x_s[i] >= thr[i] and x_s[i] > x_s[i-1] and x_s[i] >= x_s[i+1]:
            prom = x_s[i] - baseline[i]
            candidates.append((i, prom))
    
    if candidates:
        best_idx = max(candidates, key=lambda t: t[1])[0]
    else:
        best_idx = int(max(range(len(x_s)), key=lambda i: x_s[i])) if x_s else 0
    
    return best_idx

def parse_engagement_csv(csv_path):
    """Parse the new CSV format"""
    rows = []
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter=';')
        for row in reader:
            try:
                sec = int(float(row.get("video_second", 0)))
                cps = float(row.get("comments_per_second", 0))
                rows.append((sec, cps))
            except:
                continue
    
    if not rows:
        return [], []
    
    max_s = max(s for s, _ in rows)
    series = [0.0] * (max_s + 1)
    for s, cps in rows:
        if 0 <= s < len(series):
            series[s] = float(cps)
    times = [float(i) for i in range(len(series))]
    return times, series

def compute_dynamic_pre_post(times, counts, peak_idx, target_len=60.0, min_len=20.0, max_len=60.0):
    """Compute dynamic window around peak"""
    peak_time = times[peak_idx]
    
    # Start with target length
    total_len = min(target_len, max_len)
    
    # Adjust based on activity around peak
    window_start = max(0, peak_idx - int(total_len/2))
    window_end = min(len(counts), peak_idx + int(total_len/2))
    
    # Check activity levels
    pre_activity = sum(counts[window_start:peak_idx]) / max(1, peak_idx - window_start)
    post_activity = sum(counts[peak_idx:window_end]) / max(1, window_end - peak_idx)
    
    # Adjust window based on activity
    if pre_activity > post_activity:
        pre = min(total_len * 0.7, total_len - 10)
        post = total_len - pre
    else:
        post = min(total_len * 0.7, total_len - 10)
        pre = total_len - post
    
    return max(min_len/2, pre), max(min_len/2, post)

def analyze_csv_file(csv_file):
    """Analyze CSV file using the new system"""
    print(f"\n🔍 Analyzing {csv_file} with NEW SYSTEM...")
    
    # Parse the CSV
    times, counts = parse_engagement_csv(csv_file)
    
    if not times:
        print("❌ No data found in CSV")
        return None
    
    print(f"📊 Data points: {len(times)}")
    print(f"⏱️  Duration: {times[0]/3600:.1f}h to {times[-1]/3600:.1f}h")
    print(f"📈 Max comments/sec: {max(counts)}")
    print(f"📉 Min comments/sec: {min(counts)}")
    
    # Detect peak
    peak_idx = detect_peak_index(times, counts, K=3.0)
    peak_time = times[peak_idx]
    
    # Convert peak time to HH:MM:SS
    peak_hours = int(peak_time // 3600)
    peak_minutes = int((peak_time % 3600) // 60)
    peak_seconds = int(peak_time % 60)
    peak_time_str = f"{peak_hours:02d}:{peak_minutes:02d}:{peak_seconds:02d}"
    
    print(f"🎯 PEAK DETECTED at: {peak_time_str} ({peak_time:.0f} seconds)")
    print(f"📊 Peak activity: {counts[peak_idx]:.0f} comments/second")
    
    # Compute dynamic window
    pre, post = compute_dynamic_pre_post(times, counts, peak_idx, target_len=60.0)
    
    clip_start = max(0, peak_time - pre)
    clip_end = peak_time + post
    
    clip_start_h = int(clip_start // 3600)
    clip_start_m = int((clip_start % 3600) // 60)
    clip_start_s = int(clip_start % 60)
    
    clip_end_h = int(clip_end // 3600)
    clip_end_m = int((clip_end % 3600) // 60)
    clip_end_s = int(clip_end % 60)
    
    print(f"🎬 DYNAMIC CLIP WINDOW:")
    print(f"   ⏱️  Start: {clip_start_h:02d}:{clip_start_m:02d}:{clip_start_s:02d}")
    print(f"   ⏱️  End: {clip_end_h:02d}:{clip_end_m:02d}:{clip_end_s:02d}")
    print(f"   📏 Duration: {pre + post:.1f} seconds (Pre: {pre:.1f}s, Post: {post:.1f}s)")
    
    return {
        "peak_time": peak_time,
        "peak_time_str": peak_time_str,
        "clip_start": clip_start,
        "clip_end": clip_end,
        "pre": pre,
        "post": post,
        "max_activity": counts[peak_idx]
    }

if __name__ == "__main__":
    print("🚀 NEW ClipPulse System Analysis")
    print("=" * 60)
    
    # Analyze converted CSV files
    converted_files = [
        "media/engagement/converted_Dataset of evolution in comments.csv",
        "media/engagement/converted_New fake dataset with 3 spike (500 datapoints).csv"
    ]
    
    results = []
    for csv_file in converted_files:
        if Path(csv_file).exists():
            result = analyze_csv_file(csv_file)
            if result:
                filename = Path(csv_file).name
                dataset_name = "Real Data" if "Dataset of evolution" in filename else "Synthetic Data"
                results.append((dataset_name, result))
        else:
            print(f"❌ File not found: {csv_file}")
    
    print("\n" + "=" * 60)
    print("📋 SUMMARY OF DETECTED PEAKS (NEW SYSTEM):")
    print("=" * 60)
    
    for dataset_name, result in results:
        print(f"\n📊 {dataset_name}:")
        print(f"   🎯 Peak at: {result['peak_time_str']}")
        print(f"   📈 Activity: {result['max_activity']:.0f} comments/sec")
        print(f"   🎬 Dynamic Window: {result['pre']:.1f}s + {result['post']:.1f}s = {result['pre'] + result['post']:.1f}s total")
        print(f"   ⏱️  Clip: {result['clip_start']:.0f}s to {result['clip_end']:.0f}s")
    
    print(f"\n✅ NEW SYSTEM ANALYSIS COMPLETE!")
    print(f"💡 The new system uses dynamic window sizing based on activity patterns.")
    print(f"🎬 These clips would be extracted with the updated ClipPulse Backend.")
