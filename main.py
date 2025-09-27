\
from fastapi import FastAPI, Request
from typing import List, Dict, Any
import os, subprocess, math, random
from pathlib import Path

# ---- SH-BE-0: Bootstrap ----
CLIP_PRE = 30.0
CLIP_POST = 30.0
MEDIA_IN = Path(__file__).parent / "media" / "input"
MEDIA_OUT = Path(__file__).parent / "media" / "output"
MEDIA_IN.mkdir(parents=True, exist_ok=True)
MEDIA_OUT.mkdir(parents=True, exist_ok=True)

app = FastAPI(title="ClipPulse Backend (Minimal Hackathon)")

@app.get("/health")
def health():
    return {"ok": True}

# ---- Utility: median filter (k=5) ----
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

# ---- Utility: rolling median + MAD ----
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

# ---- SH-BE-2: Aggregation counts/sec ----
def aggregate_counts(events: List[Dict[str, Any]]):
    # events: [{t: float, weight?: float}]
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

# ---- SH-BE-3: Peak detection ----
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

# ---- SH-BE-4: Clip cutter ----
def cut_clip(input_path: str, center_time: float, pre: float = CLIP_PRE, post: float = CLIP_POST) -> str:
    start = max(0.0, center_time - pre)
    duration = pre + post
    base = os.path.splitext(os.path.basename(input_path))[0]
    out_path = str(MEDIA_OUT / f"{base}_clip_{int(start)}_{int(duration)}.mp4")

    # ffmpeg happy path re-encode for safety
    cmd = [
        "ffmpeg",
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

# ---- SH-BE-6: Chat mock ----
@app.post("/chat/mock")
async def chat_mock(body: Dict[str, Any]):
    duration_sec = float(body.get("duration_sec", 120))
    fps = float(body.get("fps", 1.0))
    peak_at = body.get("peak_at", duration_sec * 0.5)
    if peak_at is None:
        peak_at = duration_sec * 0.5
    peak_at = float(peak_at)

    events = []
    n = int(duration_sec * fps)
    for i in range(n):
        t = i / fps
        base = 0.5 * (1 + math.sin(2*math.pi*(t/duration_sec*3)))
        noise = random.gauss(0, 0.1)
        bump = math.exp(-0.5*((t-peak_at)/3.0)**2) * 4.0
        rate = max(0.0, base + noise + bump) * 10.0
        k = int(max(0, round(rate)))
        for _ in range(k):
            events.append({"t": t, "weight": 1.0})
    return {"events": events}

# ---- SH-BE-1 & SH-BE-5: Orchestrator ----
@app.post("/process")
async def process(request: Request):
    data = await request.json()
    video_path = data.get("video_path")
    events = data.get("events", [])

    times, counts = aggregate_counts(events)
    peak_time = detect_peak(times, counts, K=3.0)
    clip_path = cut_clip(video_path, center_time=peak_time, pre=CLIP_PRE, post=CLIP_POST)

    return {"peak_time": peak_time, "clip_path": clip_path}
