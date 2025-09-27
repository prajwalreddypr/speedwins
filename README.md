# ClipPulse Backend (Ultra-Minimal, Hackathon Happy Path)

Solves tickets **SH-BE-0 .. SH-BE-6**:
- SH-BE-0: Bootstrap service (`/health`, constants CLIP_PRE/POST)
- SH-BE-1: `/process` endpoint (JSON: `video_path`, `events` with `t` and optional `weight`)
- SH-BE-2: Aggregation counts/sec
- SH-BE-3: Robust peak detection (median + rolling median & MAD w/ K=3, fallback to global max)
- SH-BE-4: Clip cutter using `ffmpeg` (±30s around peak)
- SH-BE-5: Orchestrator wiring inside `/process`
- SH-BE-6: `/chat/mock` endpoint (sinusoid+noise + one spike)

## Run
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# start api
uvicorn main:app --reload
```

## Test quickly
1) Put a small MP4 at: `/mnt/data/clippulse_backend_min/media/input/demo.mp4`
2) Generate mock events:
```bash
curl -s -X POST http://localhost:8000/chat/mock -H "Content-Type: application/json"   -d '{"duration_sec":120,"fps":1,"peak_at":60}' > events.json
```
3) Process:
```bash
curl -s -X POST http://localhost:8000/process -H "Content-Type: application/json" -d @- << 'EOF'
{
  "video_path": "/mnt/data/clippulse_backend_min/media/input/demo.mp4",
  "events": $(cat events.json | jq '.events')
}
EOF
```

### Notes
- No validation — happy path only.
- Requires `ffmpeg` to be installed on the host.
- Output clips land in: `/mnt/data/clippulse_backend_min/media/output/`
