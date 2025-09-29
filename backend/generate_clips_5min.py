#!/usr/bin/env node
import csv
import subprocess
from pathlib import Path

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

def detect_peaks_comprehensive(times, counts, engagement_rates):
    """Comprehensive peak detection"""
    # Find top 10 highest engagement moments
    top_indices = sorted(range(len(counts)), key=lambda i: counts[i], reverse=True)[:10]
    
    peaks = []
    for idx in top_indices:
        time_seconds = times[idx]
        time_str = f"{time_seconds//60:02d}:{time_seconds%60:02d}"
        
        # Check if it's a local maximum (peak)
        is_local_max = (idx == 0 or counts[idx] > counts[idx-1]) and \
                      (idx == len(counts)-1 or counts[idx] > counts[idx+1])
        
        peaks.append({
            'index': idx,
            'time': time_seconds,
            'time_str': time_str,
            'activity': counts[idx],
            'engagement': engagement_rates[idx],
            'is_local_max': is_local_max
        })
    
    return peaks

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
    print("🎬 Generating Clips from 5-Minute Demo Video")
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
    
    # Detect peaks
    peaks = detect_peaks_comprehensive(times, counts, engagement_rates)
    
    print(f"\n🎯 DETECTED SPIKES: {len(peaks)}")
    print("=" * 60)
    
    for i, peak in enumerate(peaks):
        print(f"📊 Spike #{i+1}:")
        print(f"   ⏰ Time: {peak['time_str']} ({peak['time']}s)")
        print(f"   📈 Activity: {peak['activity']:.0f} comments/sec")
        print(f"   📊 Engagement Rate: {peak['engagement']:.2f}")
        print(f"   🎯 Local Max: {'Yes' if peak['is_local_max'] else 'No'}")
    
    # Generate clips for top spikes
    output_dir = Path("media/output")
    output_dir.mkdir(exist_ok=True)
    
    # Select top 5 peaks for clip generation
    top_peaks = peaks[:5]
    
    print(f"\n🎬 GENERATING CLIPS FROM TOP {len(top_peaks)} SPIKES:")
    print("=" * 60)
    
    clips_generated = 0
    
    for i, peak in enumerate(top_peaks):
        # Generate 30s, 60s, and 90s clips for each peak
        durations = [30, 60, 90]
        
        for duration in durations:
            start_time = max(0, peak['time'] - duration // 2)
            
            # Create filename
            time_str_clean = peak['time_str'].replace(':', '')
            output_path = output_dir / f"demo_5min_spike_{i+1}_{time_str_clean}_{duration}s.mp4"
            
            print(f"\n🎬 Creating clip for Spike #{i+1} ({duration}s):")
            print(f"   ⏰ Peak Time: {peak['time_str']}")
            print(f"   📈 Activity: {peak['activity']:.0f} comments/sec")
            print(f"   ⏱️  Clip: {start_time}s to {start_time+duration}s")
            print(f"   📁 Output: {output_path.name}")
            
            success = extract_clip_with_ffmpeg(video_path, start_time, duration, str(output_path))
            
            if success:
                file_size = Path(output_path).stat().st_size / (1024*1024)
                print(f"   ✅ Success! Size: {file_size:.1f} MB")
                clips_generated += 1
            else:
                print(f"   ❌ Failed to create clip")
    
    print(f"\n🎉 SUMMARY:")
    print(f"   📊 Total spikes analyzed: {len(peaks)}")
    print(f"   🎬 Clips generated: {clips_generated}")
    print(f"   📁 Location: media/output/")
    
    # Show the strongest spike
    if peaks:
        strongest = peaks[0]
        print(f"\n🔥 STRONGEST SPIKE:")
        print(f"   ⏰ Time: {strongest['time_str']}")
        print(f"   📈 Activity: {strongest['activity']:.0f} comments/sec")
        print(f"   📊 Engagement Rate: {strongest['engagement']:.2f}")

if __name__ == "__main__":
    main()
