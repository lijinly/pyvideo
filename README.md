# PyVideo - AI Video Processing Platform

An AI-powered video processing platform built with Flask, featuring video generation, avatar creation, and marketing content automation.

## Features

- **Video Asset Management**: Index, search, and manage video/audio assets with ChromaDB vector database
- **Avatar Generation**: Create AI avatars using GFPGAN and Wav2Lip for face enhancement and lip-sync
- **Marketing Content**: Automated marketing video generation with scene extraction and script writing
- **Voice Synthesis**: Text-to-speech using Sambert and other AI voice models
- **Background Music**: AI-generated background music using Qwen
- **Video Composition**: Professional video editing and composition using MoviePy
- **Douyin Integration**: Download and process videos from Douyin (TikTok)

## Tech Stack

- **Backend**: Flask 3.1.2, Flask-JWT-Extended, Flask-SQLAlchemy
- **AI/ML**: PyTorch 2.3.0 (CUDA 12.1), Transformers, OpenCV
- **Vector DB**: ChromaDB for semantic video/audio search
- **Video Processing**: MoviePy, FFmpeg, OpenCV
- **LLM APIs**: DashScope (Qwen), Volcengine (Doubao), OpenAI
- **Database**: SQLAlchemy ORM with TinyDB for KV storage
- **Deployment**: Docker, Docker Compose, Gunicorn

## Project Structure

```
.
├── domains/              # Core business logic modules
│   ├── asset_*.py        # Asset management (video/audio/index)
│   ├── avatar_*.py       # Avatar generation (GFPGAN, Wav2Lip)
│   ├── create_*.py       # Content creation (image, video, voice, BGM)
│   ├── scene_*.py        # Scene processing and marketing
│   ├── work_flow_*.py    # Workflow automation
│   └── tools.py          # Utility functions
├── web/                  # Flask web application
│   ├── routes/           # API route handlers
│   ├── models/           # Database models
│   └── *.py              # App factory, config, extensions
├── utils/                # Utility modules (logs, DB helpers)
├── frame_work/           # Framework core
├── BasicSR/              # Super-resolution models
├── GFPGAN/               # Face enhancement models
├── Wav2Lip/              # Lip-sync models
├── run.py                # Application entry point
├── requirements.txt      # Python dependencies
└── docker-compose.yml    # Docker deployment config
```

## Quick Start

### Prerequisites

- Python 3.10+
- CUDA 12.1 (for GPU acceleration)
- FFmpeg installed

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd pyvideo
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure environment variables in `.env`:
```env
JWT_SECRET_KEY=your-secret-key
ARK_API_KEY=your-volcengine-key
dashscope_api_key=your-dashscope-key
apihz_uid=your-apihz-uid
apihz_key=your-apihz-key
```

4. Run the application:
```bash
python run.py
```

The server will start at `http://localhost:5000`

### Docker Deployment

```bash
docker-compose up -d
```

The application will be available at `http://localhost:8000`

## API Endpoints

| Endpoint | Description |
|----------|-------------|
| `/auth/*` | Authentication (login, register, token refresh) |
| `/asset/*` | Asset management (upload, search, delete) |
| `/avatar/*` | Avatar generation and processing |
| `/marketing/*` | Marketing content generation |
| `/copywrite_structures/*` | Copywriting templates and structures |
| `/static/*` | Static file serving |

## Configuration

Key configuration options in `domains/config.py`:

- `DEVICE`: Auto-detected CUDA or CPU
- `asset_space_dir`: Asset storage location
- `frame_interval`: Frame extraction interval
- `stop_words`: Text processing stop words
- `product_categories`: Product categories for marketing

## License

MIT License
