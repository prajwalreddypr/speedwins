from fastapi import FastAPI, Request, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from typing import List, Dict, Any, Tuple
import os, subprocess, math, csv
from pathlib import Path

# ---- Bootstrap ----
MEDIA_IN = Path(__file__).parent / "media" / "input"       # videos
MEDIA_OUT = Path(__file__).parent / "media" / "output"     # clips
ENG_DIR = Path(__file__).parent / "media" / "engagement"   # CSVs
for p in (MEDIA_IN, MEDIA_OUT, ENG_DIR):
    p.mkdir(parents=True, exist_ok=True)

app = FastAPI(title="ClipPulse Backend (CSV + Dynamic Window)")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8081", "http://127.0.0.1:8081", "http://localhost:8080", "http://127.0.0.1:8080"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files for serving video clips
app.mount("/media", StaticFiles(directory="media"), name="media")

@app.get("/health")
def health():
    return {"ok": True}

# ===============================
# Utilities (filters & statistics)
# ===============================
def median(vals: List[float]) -> float:
    if not vals: return 0.0
    s = sorted(vals)
    n = len(s)
    mid = n // 2
    return float((s[mid] if n % 2 else (s[mid - 1] + s[mid]) / 2))

def median_filter(x: List[float], k: int = 5) -> List[float]:
    if k <= 1 or not x:
        return x
    pad = k // 2
    xp = [x[0]] * pad + list(x) + [x[-1]] * pad
    out: List[float] = []
    for i in range(len(x)):
        w = xp[i:i + k]
        out.append(median(w))
    return out

def rolling_median_mad(x: List[float], win: int = 31) -> Tuple[List[float], List[float]]:
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

# ===============================
# CSV engagement (semicolon) I/O
# ===============================
def _guess_delimiter(sample: str) -> str:
    # prefer semicolon if header contains it, else comma
    return ';' if ';' in sample.splitlines()[0] else ','

def parse_engagement_csv(csv_path: str) -> Tuple[List[float], List[float]]:
    """
    Expect headers: video_second;time_label;comments_per_second
    Returns (times_seconds, counts_per_second).
    Missing seconds are zero-filled.
    """
    rows = []
    with open(csv_path, "r", encoding="utf-8") as f:
        head = f.read(2048)
        f.seek(0)
        delim = _guess_delimiter(head)
        reader = csv.DictReader(f, delimiter=delim)
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

# ===============================
# Peak detection
# ===============================
def detect_peak_index(times: List[float], counts: List[float], K: float = 3.0) -> int:
    """
    Robust detector:
      - median smoothing
      - rolling median + MAD threshold
      - choose local max above threshold with highest (value - baseline)
      - fallback to global max if none
    Returns peak index (into times/counts).
    """
    if not counts: return 0
    x_s = median_filter(counts, k=5)
    baseline, mad = rolling_median_mad(x_s, win=31)
    thr = [b + K * m for b, m in zip(baseline, mad)]

    cand: List[Tuple[int, float]] = []
    for i in range(1, len(x_s) - 1):
        if x_s[i] >= thr[i] and x_s[i] > x_s[i - 1] and x_s[i] >= x_s[i + 1]:
            cand.append((i, x_s[i] - baseline[i]))
    if cand:
        return max(cand, key=lambda t: t[1])[0]
    return int(max(range(len(x_s)), key=lambda j: x_s[j]))  # global max

# ===============================
# Dynamic window (short-form optimized)
# ===============================
def compute_dynamic_pre_post(
    times: List[float],
    counts: List[float],
    peak_idx: int,
    target_len: float = 60.0,   # Reels/Shorts sweet spot (use 60s default)
    min_len: float = 20.0,
    max_len: float = 60.0
) -> Tuple[float, float]:
    """
    Choose CLIP_PRE/CLIP_POST dynamically:
      1) Smooth counts.
      2) Compute baseline (series median).
      3) FWHM around peak: find left/right indices where signal falls below
         half-level = baseline + 0.5*(peak - baseline).
      4) Pre/Post are distances to those crossings.
      5) Scale to target length while preserving left/right ratio, bounded by [min_len, max_len]
         and by available starts/ends.
    """
    if not counts or peak_idx < 0 or peak_idx >= len(counts):
        return target_len / 2.0, target_len / 2.0

    x_s = median_filter(counts, k=5)
    base = median(x_s)
    peak_val = x_s[peak_idx]
    half = base + 0.5 * (peak_val - base)

    # Find left crossing
    L = peak_idx
    while L > 0 and x_s[L] >= half:
        L -= 1
    # Find right crossing
    R = peak_idx
    while R < len(x_s) - 1 and x_s[R] >= half:
        R += 1

    # Convert to seconds
    peak_t = times[peak_idx]
    left_t = times[max(L, 0)]
    right_t = times[min(R, len(times) - 1)]

    pre = max(0.0, peak_t - left_t)
    post = max(0.0, right_t - peak_t)

    # If extremely narrow spike, give a minimal context
    if pre + post < min_len / 2.0:
        pre = post = min_len / 2.0

    # Desired final length and ratio preservation
    raw_len = pre + post
    ratio = (pre / raw_len) if raw_len > 0 else 0.5

    # Available head/tail in seconds
    headroom_left = peak_t - 0.0
    headroom_right = times[-1] - peak_t

    # Start with target length within [min_len, max_len]
    desired = max(min_len, min(target_len, max_len))

    # If raw_len > desired, scale down pre/post preserving ratio
    if raw_len > desired:
        scale = desired / raw_len
        pre, post = pre * scale, post * scale
    else:
        # raw_len < desired: try to grow to desired with available headroom
        grow = desired - raw_len
        add_pre = min(grow * ratio, headroom_left)
        add_post = min(grow * (1 - ratio), headroom_right)
        pre += add_pre
        post += add_post
        # If still short (hit a boundary), dump remainder to the other side
        remaining = desired - (pre + post)
        if remaining > 0:
            if headroom_left - add_pre > headroom_right - add_post:
                pre += min(remaining, headroom_left - add_pre)
            else:
                post += min(remaining, headroom_right - add_post)

    # Final clamp: don't exceed available range
    pre = min(pre, headroom_left)
    post = min(post, headroom_right)

    # Ensure not below minimum total
    if pre + post < min_len:
        need = min_len - (pre + post)
        # try to spread equally within remaining headroom
        grow_left = max(0.0, headroom_left - pre)
        grow_right = max(0.0, headroom_right - post)
        g_pre = min(need / 2.0, grow_left)
        g_post = min(need / 2.0, grow_right)
        pre += g_pre
        post += g_post
        # push remainder to any side that still has room
        rem = min_len - (pre + post)
        if rem > 0 and grow_left - g_pre > 0:
            pre += min(rem, grow_left - g_pre)
            rem = min_len - (pre + post)
        if rem > 0 and grow_right - g_post > 0:
            post += min(rem, grow_right - g_post)

    return float(pre), float(post)

# ===============================
# Video cutting
# ===============================
def cut_clip(input_path: str, center_time: float, pre: float, post: float) -> str:
    start = max(0.0, center_time - pre)
    duration = pre + post
    base = os.path.splitext(os.path.basename(input_path))[0]
    out_path = str(MEDIA_OUT / f"{base}_clip_{int(start)}_{int(duration)}.mp4")
    
    # Check if input file exists
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input video file not found: {input_path}")
    
    # Use local FFmpeg if available
    ffmpeg_path = "ffmpeg"
    local_ffmpeg = Path(__file__).parent / "ffmpeg_bin" / "ffmpeg-master-latest-win64-gpl" / "bin" / "ffmpeg.exe"
    if local_ffmpeg.exists():
        ffmpeg_path = str(local_ffmpeg)
    
    # Check if ffmpeg is available
    try:
        subprocess.run([ffmpeg_path, "-version"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except (subprocess.CalledProcessError, FileNotFoundError):
        # If ffmpeg is not available, create a placeholder file
        placeholder_path = str(MEDIA_OUT / f"{base}_clip_{int(start)}_{int(duration)}_placeholder.txt")
        with open(placeholder_path, "w") as f:
            f.write(f"Clip placeholder\nPeak time: {center_time}s\nDuration: {duration}s\nStart: {start}s\n")
        return placeholder_path
    
    cmd = [
        ffmpeg_path,
        "-ss", str(start),
        "-t", str(duration),
        "-i", input_path,
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
        "-c:a", "aac", "-b:a", "128k",
        "-movflags", "+faststart",
        "-y", out_path
    ]
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return out_path

# ===============================
# Upload endpoints (video + CSV)
# ===============================
@app.post("/video/upload")
async def upload_video(file: UploadFile = File(...)):
    dest = MEDIA_IN / file.filename
    with open(dest, "wb") as f:
        f.write(await file.read())
    return {"video_path": str(dest)}

@app.post("/engagement/upload")
async def engagement_upload(file: UploadFile = File(...)):
    dest = ENG_DIR / file.filename
    with open(dest, "wb") as f:
        f.write(await file.read())
    return {"csv_path": str(dest)}

# ===============================
# Orchestrator (CSV-driven)
# ===============================
@app.post("/process_csv")
async def process_csv(request: Request):
    data = await request.json()
    video_path = data.get("video_path")
    csv_path = data.get("csv_path")
    target_len = float(data.get("target_len", 60.0))  # allow UI override if needed

    times, counts = parse_engagement_csv(csv_path)
    peak_idx = detect_peak_index(times, counts, K=3.0)
    peak_time = float(times[peak_idx])

    # dynamic pre/post for short-form
    pre, post = compute_dynamic_pre_post(
        times, counts, peak_idx,
        target_len=target_len,  # 60s default (Reels/Shorts)
        min_len=20.0,           # ensure enough context
        max_len=60.0            # keep under 60s for universal short-form
    )

    clip_path = cut_clip(video_path, center_time=peak_time, pre=pre, post=post)

    return {
        "peak_time": peak_time,
        "clip_path": clip_path,
        "window": {"pre_sec": pre, "post_sec": post, "total_sec": pre + post},
        "peak_index": peak_idx
    }
