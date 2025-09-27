#!/usr/bin/env node
import subprocess
import os
import json
from pathlib import Path

def find_ffmpeg():
    """Try to find FFmpeg executable"""
    possible_paths = [
        "ffmpeg",
        "C:\\Program Files\\FFmpeg\\bin\\ffmpeg.exe",
        "C:\\ffmpeg\\bin\\ffmpeg.exe",
        "C:\\ProgramData\\chocolatey\\bin\\ffmpeg.exe",
        ".\\ffmpeg\\bin\\ffmpeg.exe"
    ]
    
    for path in possible_paths:
        try:
            result = subprocess.run([path, "-version"], 
                                  capture_output=True, 
                                  text=True, 
                                  timeout=5)
            if result.returncode == 0:
                print(f"✅ Found FFmpeg at: {path}")
                return path
        except:
            continue
    
    print("❌ FFmpeg not found in common locations")
    return None

def extract_clip(video_path, start_time, duration, output_path, ffmpeg_path):
    """Extract a video clip using FFmpeg"""
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
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        if result.returncode == 0:
            print(f"✅ Successfully extracted clip: {output_path}")
            return True
        else:
            print(f"❌ FFmpeg error: {result.stderr}")
            return False
    except subprocess.TimeoutExpired:
        print(f"❌ FFmpeg timeout")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    print("🎬 ClipPulse Video Clip Extractor")
    print("=" * 50)
    
    # Find FFmpeg
    ffmpeg_path = find_ffmpeg()
    if not ffmpeg_path:
        print("\n💡 To extract video clips, you need FFmpeg installed.")
        print("   You can download it from: https://ffmpeg.org/download.html")
        print("   Or install via: winget install FFmpeg")
        print("\n📋 Here are the clips that would be extracted:")
        show_clip_info()
        return
    
    # Video file
    video_path = "media/input/kaicenat.mov"
    if not Path(video_path).exists():
        print(f"❌ Video file not found: {video_path}")
        return
    
    print(f"📹 Processing video: {video_path}")
    
    # Peak data from our analysis
    peaks = [
        {
            "name": "Real Data Peak",
            "start_time": 168450,  # 46:47:30 in seconds
            "duration": 60
        },
        {
            "name": "Synthetic Data Peak", 
            "start_time": 162090,  # 45:01:30 in seconds
            "duration": 60
        }
    ]
    
    # Create output directory
    output_dir = Path("media/output")
    output_dir.mkdir(exist_ok=True)
    
    print(f"\n🎯 Extracting {len(peaks)} peak clips...")
    
    for i, peak in enumerate(peaks):
        output_path = output_dir / f"peak_{i+1}_{peak['name'].replace(' ', '_').lower()}.mp4"
        
        print(f"\n🎬 Extracting {peak['name']}...")
        print(f"   ⏱️  Start: {peak['start_time']}s ({peak['start_time']//3600:02d}:{(peak['start_time']%3600)//60:02d}:{peak['start_time']%60:02d})")
        print(f"   📏 Duration: {peak['duration']}s")
        print(f"   📁 Output: {output_path}")
        
        success = extract_clip(
            video_path, 
            peak['start_time'], 
            peak['duration'], 
            str(output_path),
            ffmpeg_path
        )
        
        if success:
            file_size = Path(output_path).stat().st_size / (1024*1024)
            print(f"   📊 File size: {file_size:.1f} MB")
    
    print(f"\n✅ Clip extraction complete!")
    print(f"📁 Check the 'media/output' folder for your spike clips.")

def show_clip_info():
    """Show information about clips that would be extracted"""
    peaks = [
        {
            "name": "Real Data Peak",
            "start_time": 168450,  # 46:47:30 in seconds
            "duration": 60,
            "description": "Massive engagement spike from real comment data"
        },
        {
            "name": "Synthetic Data Peak", 
            "start_time": 162090,  # 45:01:30 in seconds
            "duration": 60,
            "description": "Peak detected from synthetic test data"
        }
    ]
    
    for i, peak in enumerate(peaks):
        start_h = peak['start_time'] // 3600
        start_m = (peak['start_time'] % 3600) // 60
        start_s = peak['start_time'] % 60
        
        end_time = peak['start_time'] + peak['duration']
        end_h = end_time // 3600
        end_m = (end_time % 3600) // 60
        end_s = end_time % 60
        
        print(f"\n🎬 Clip {i+1}: {peak['name']}")
        print(f"   📝 {peak['description']}")
        print(f"   ⏱️  Time: {start_h:02d}:{start_m:02d}:{start_s:02d} to {end_h:02d}:{end_m:02d}:{end_s:02d}")
        print(f"   📏 Duration: {peak['duration']} seconds")
        print(f"   📁 Would be saved as: peak_{i+1}_{peak['name'].replace(' ', '_').lower()}.mp4")

if __name__ == "__main__":
    main()
