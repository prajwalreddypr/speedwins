#!/usr/bin/env node
import csv
import subprocess
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

def parse_csv(csv_path):
    """Parse the CSV data"""
    times = []
    counts = []
    
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f, delimiter=';')
        for row in reader:
            try:
                sec = int(float(row.get("video_second", 0)))
                cps = float(row.get("comments_per_second", 0))
                times.append(sec)
                counts.append(cps)
            except:
                continue
    
    return times, counts

def extract_clip_with_ffmpeg(video_path, start_time, duration, output_path):
    """Extract clip using FFmpeg"""
    # Use local FFmpeg
    ffmpeg_path = "ffmpeg"
    local_ffmpeg = Path(__file__).parent / "ffmpeg_bin" / "ffmpeg-master-latest-win64-gpl" / "bin" / "ffmpeg.exe"
    if local_ffmpeg.exists():
        ffmpeg_path = str(local_ffmpeg)
    
    cmd = [
        ffmpeg_path,
        "-ss", str(start_time),
        "-t", str(duration),
        "-i", video_path,
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
        "-c:a", "aac", "-b:a", "128k",
        "-movflags", "+faststart",
        "-y", output_path
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        if result.returncode == 0:
            return True
        else:
            print(f"FFmpeg error: {result.stderr}")
            return False
    except Exception as e:
        print(f"Error: {e}")
        return False

def main():
    print("🎬 Generating Clips from Synthetic Data")
    print("=" * 50)
    
    # Parse synthetic CSV data
    csv_path = "media/engagement/converted_New fake dataset with 3 spike (500 datapoints).csv"
    video_path = "media/input/kaicenat.mov"
    
    if not Path(csv_path).exists():
        print(f"❌ CSV file not found: {csv_path}")
        return
    
    if not Path(video_path).exists():
        print(f"❌ Video file not found: {video_path}")
        return
    
    print(f"📊 Parsing CSV: {csv_path}")
    times, counts = parse_csv(csv_path)
    
    if not times:
        print("❌ No data found in CSV")
        return
    
    print(f"📈 Found {len(times)} data points")
    print(f"📊 Max engagement: {max(counts)} comments/second")
    
    # Detect peak
    peak_idx = detect_peak_index(times, counts, K=3.0)
    peak_time = times[peak_idx]
    
    print(f"🎯 Peak detected at: {peak_time} seconds ({peak_time//3600:02d}:{(peak_time%3600)//60:02d}:{peak_time%60:02d})")
    print(f"📈 Peak activity: {counts[peak_idx]:.0f} comments/second")
    
    # Create clips with different durations
    clips_to_create = [
        {"name": "synthetic_short", "duration": 30},
        {"name": "synthetic_medium", "duration": 60},
        {"name": "synthetic_long", "duration": 90}
    ]
    
    output_dir = Path("media/output")
    output_dir.mkdir(exist_ok=True)
    
    clips_generated = 0
    
    for clip in clips_to_create:
        start_time = max(0, peak_time - clip["duration"] // 2)
        output_path = output_dir / f"kaicenat_synthetic_{clip['name']}_{start_time}_{clip['duration']}.mp4"
        
        print(f"\n🎬 Creating {clip['name']} clip...")
        print(f"   ⏱️  Start: {start_time}s, Duration: {clip['duration']}s")
        print(f"   📁 Output: {output_path}")
        
        success = extract_clip_with_ffmpeg(video_path, start_time, clip["duration"], str(output_path))
        
        if success:
            file_size = Path(output_path).stat().st_size / (1024*1024)
            print(f"   ✅ Success! Size: {file_size:.1f} MB")
            clips_generated += 1
        else:
            print(f"   ❌ Failed to create clip")
    
    print(f"\n🎉 SYNTHETIC DATA SUMMARY:")
    print(f"   📊 Peak detected at: {peak_time//3600:02d}:{(peak_time%3600)//60:02d}:{peak_time%60:02d}")
    print(f"   📈 Peak activity: {counts[peak_idx]:.0f} comments/second")
    print(f"   🎬 Clips generated: {clips_generated}/{len(clips_to_create)}")
    print(f"   📁 Check 'media/output/' for your clips!")

if __name__ == "__main__":
    main()
