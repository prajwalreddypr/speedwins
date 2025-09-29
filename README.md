# ClipPulse - Video Engagement Analysis & Clip Generation

A full-stack application that analyzes video engagement data and automatically generates highlight clips from peak moments.

## Project Structure

```
speeeedwins/
├── backend/           # Python FastAPI backend
│   ├── main.py       # Main FastAPI application
│   ├── requirements.txt
│   ├── media/        # Video and CSV data
│   └── ...
├── Frontend/         # React TypeScript frontend
│   ├── src/
│   ├── package.json
│   └── ...
├── run_backend.py    # Python script to run backend
├── start_backend.bat # Windows batch file to run backend
└── README.md
```

## Quick Start

### Backend (Python/FastAPI)

```bash
# Option 1: Using Python script
python run_backend.py

# Option 2: Using batch file (Windows)
start_backend.bat

# Option 3: Manual
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend (React/TypeScript)

```bash
cd Frontend
npm install
npm run dev
```

## Features

- **Engagement Analysis**: Analyzes CSV data to find peak engagement moments
- **Dynamic Clip Generation**: Creates clips around peak moments with optimal timing
- **Modern UI**: Clean, responsive interface built with React and Tailwind CSS
- **Real-time Processing**: Fast API backend with automatic reload for development

## API Endpoints

- `GET /health` - Health check
- `POST /video/upload` - Upload video files
- `POST /engagement/upload` - Upload engagement CSV data
- `POST /process_csv` - Process video and CSV to generate clips

## Demo Data

The project includes demo data:

- Video: `backend/media/input/demo_video.mp4`
- Engagement: `backend/media/engagement/video_with_comments_with_scaled_engagement.csv`

## Requirements

- Python 3.10+
- Node.js 18+
- FFmpeg (optional, for video processing)

## Installation

1. **Backend**:

   ```bash
   cd backend
   pip install -r requirements.txt
   ```

2. **Frontend**:

   ```bash
   cd Frontend
   npm install
   ```

## Usage

1. Start the backend: `python run_backend.py`
2. Start the frontend: `cd Frontend && npm run dev`
3. Open <http://localhost:8080> in your browser
4. Click "Upload Files" and then "View Generated Clips"
