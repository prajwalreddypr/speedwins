# ClipPulse Backend — CSV + Dynamic Window (Short‑Form Optimized)

FastAPI backend that:
- uploads a **video** and an **engagement CSV** (from your live platform),
- detects the **strongest engagement peak** (robust stats: median + MAD),
- computes a **dynamic clip window** (pre/post around the peak) tuned for **short‑form** content,
- cuts a playable **MP4** with ffmpeg.

> No mock data. Happy‑path only. Bring your own CSV + MP4.

---

## 1) Requirements

- **Python 3.10+**
- **ffmpeg** installed and on your PATH  
  - macOS: `brew install ffmpeg`  
  - Ubuntu/Debian: `sudo apt-get install ffmpeg`  
  - Windows: download from ffmpeg.org and add to PATH
- Python deps (see `requirements.txt`): `fastapi`, `uvicorn`, `python-multipart`

Folder layout created automatically on first run:
```
media/
  input/        # uploaded videos
  engagement/   # uploaded CSVs
  output/       # rendered clips
```

CSV format (semicolon `;` delimiter):
```
video_second;time_label;comments_per_second
0;0:00;21
1;0:01;30
...
```

## 2) Install & Run

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

uvicorn main:app --reload
```

## 3) Open the API docs

- **Swagger UI:** http://localhost:8000/docs  
- **ReDoc:**      http://localhost:8000/redoc

You can try every endpoint directly from the Swagger UI (“Try it out”).

## 4) Endpoints

### Health
`GET /health` → `{"ok": true}`

### Upload video
`POST /video/upload` (multipart/form-data)
- **form field**: `file=@your_video.mp4`  
- **Response:** `{"video_path": "media/input/your_video.mp4"}`

Example:
```bash
curl -s -X POST "http://localhost:8000/video/upload"   -F "file=@media/input/demo.mp4"
```

### Upload engagement CSV
`POST /engagement/upload` (multipart/form-data)
- **form field**: `file=@engagement.csv`  
- **Response:** `{"csv_path": "media/engagement/engagement.csv"}`

Example:
```bash
curl -s -X POST "http://localhost:8000/engagement/upload"   -F "file=@engagement.csv"
```

**CSV required headers (semicolon‑delimited):**
- `video_second` → integer second offset from stream start (0,1,2,…)
- `time_label`   → display string like `M:SS` (not used for math)
- `comments_per_second` → numeric engagement count for that second

### Process (CSV‑driven)
`POST /process_csv` (application/json)

Body:
```json
{
  "video_path": "media/input/demo.mp4",
  "csv_path": "media/engagement/engagement.csv",
  "target_len": 60.0
}
```

- `target_len` (optional): preferred clip length in seconds (default **60**).  
- **Response:**
```json
{
  "peak_time": 187.0,
  "clip_path": "media/output/demo_clip_157_60.mp4",
  "window": { "pre_sec": 30.0, "post_sec": 30.0, "total_sec": 60.0 },
  "peak_index": 187
}
```

## 5) How the dynamic window works (short‑form tuned)

1. Smooths the engagement series (median filter).  
2. Computes baseline (series median) and finds the **peak** (above a dynamic threshold).  
3. Uses **FWHM** around the peak to keep the “interesting” center.  
4. Scales **pre/post** to hit `target_len` (default 60s) while preserving left/right context ratio and respecting the stream boundaries.  
5. Enforces a minimum total length (**20s**) and maximum (**60s**) by default.

You can change `target_len` per request (e.g., 45s for faster social hooks).

## 6) Troubleshooting

- **ffmpeg not found** → install it & ensure it’s on PATH.  
- **Clip length not exactly 60s** → if the peak is too close to start/end, the window clamps to available media.  
- **CSV delimiter** → must include the header line; semicolon preferred (`;`).

---

**License:** MIT
