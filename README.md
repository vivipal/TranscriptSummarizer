# Offline Audio Transcription and Summarization using Large Language Model

A Docker-based pipeline that transcribes audio recordings and generates refined summaries/notes using AI LLM Models. It leverages:
* **NVIDIA GPU** for accelerating **Whisper** (transcription) and **Phi** (summarization) within **Docker** containers
* **FastAPI** + **Uvicorn** for a RESTful backend
* **Streamlit** for a user-friendly frontend UI
* **Ollama** for hosting the LLM model (Phi-4) and performing advanced text summarization. Note the biggest reason for using Ollama is for the fact we are using GGUF models. The quantized Q4_K_M model provides quality and performance.

## Table of Contents
* [Overview](#overview)
* [Architecture](#architecture)
* [Features](#features)
* [Folder Structure](#folder-structure)
* [Installation Requirements](#installation-requirements)
* [Environment Variables](#environment-variables)
* [Usage](#usage)
* [Technical Details](#technical-details)
* [Export Options](#export-options)
* [Logging & Monitoring](#logging--monitoring)
* [Additional Notes](#additional-notes)
* [Troubleshooting](#troubleshooting)
* [License](#license)

## Overview

This project aims to provide an **end-to-end** solution for:
1. **Transcribing** long or short audio recordings via **OpenAI Whisper Medium Model**
2. **Summarizing** those transcripts using **Microsoft Phi-4** (14B parameters, Q4_K_M quantized) running inside an **Ollama** container

### Key Features
* Simple **Docker Compose** stack with two services:
  1. **app**: Runs both FastAPI and Streamlit in one container
  2. **ollama**: Provides the Summarization Large Language Model
* Automatic GPU offloading if NVIDIA drivers and the **NVIDIA Container Toolkit** are available
* **Streamlit** frontend for easy user interaction: drag-and-drop audio, see transcription & summary
* **Export capabilities**: PDF and Word document generation for summaries and full reports
* **Real-time progress tracking** during audio processing
* **Processing statistics** with performance metrics
* Support for multiple audio formats: MP3, WAV, M4A, FLAC, OGG

## Architecture

```
+----------------------------+
| Docker Container (ollama)  |
| LLM Summarization         |
| (Microsoft Phi-4)         |
+--------------^------------+
               |
+----------------------------------+
|     Docker Container (app)        |
|  +----------------------------+   |
|  | FastAPI     |  Streamlit  |   |
|  | (Uvicorn)   |  (web UI)   |   |
|  | :8000       |   :8501     |   |
|  +----------------------------+   |
|          |            |          |
|    (Whisper)    (User Uploads)   |
+----------------------------------+
           |
+----------------------+
| Whisper Transcription |
|   (GPU-accelerated)   |
+----------------------+
```

## Features

### Core Functionality
* **Audio Transcription**: OpenAI Whisper Medium model with GPU acceleration
* **AI Summarization**: Microsoft Phi-4 (14B parameters) with structured output
* **Real-time Processing**: Live progress indicators and processing statistics
* **File Information**: Automatic extraction of audio metadata (duration, bitrate, size)

### Export Options
* **PDF Export**: 
  - Summary-only PDF with structured sections
  - Full report PDF with transcription and summary
* **Word Export**: Complete transcription and summary in .docx format
* **Text Export**: Plain text transcription download
* **Clipboard Integration**: Easy copy-to-clipboard functionality

### User Interface
* **Modern UI**: Responsive design with dark/light mode toggle
* **Drag & Drop**: Intuitive file upload with format validation
* **Processing Metrics**: Real-time statistics including words per minute
* **Tabbed Results**: Organized display of transcription and summary results

## Folder Structure

```
LocalAudioTran-LLM-Summar/
├─ .dockerignore
├─ .env
├─ .gitignore
├─ README.md
├─ docker-compose.yml
├─ Dockerfile
├─ backend/
│  ├─ requirements.txt
│  └─ app/
│     ├─ main.py
│     ├─ services/
│     │  ├─ transcription.py
│     │  ├─ summarization.py
│     │  └─ __init__.py
│     ├─ utils/
│     │  └─ logger.py
│     ├─ models/
│     │  ├─ schemas.py
│     │  └─ __init__.py
│     └─ __init__.py
├─ frontend/
│  ├─ requirements.txt
│  └─ src/
│     └─ app.py
└─ logs/
```

### Key Directories

* **`backend/`**: Houses the FastAPI application
  * `main.py` - Primary endpoints
  * `transcription.py` - Whisper-based audio transcription
  * `summarization.py` - Ollama integration and multi-step summary approach
  * `logger.py` - Rotating logs setup

* **`frontend/`**: Contains the Streamlit interface
* **`docker-compose.yml`**: Defines `app` and `ollama` services
* **`Dockerfile`**: System setup and dependencies

## Installation Requirements

### 1. Docker & Docker Compose
* Install [Docker](https://docs.docker.com/get-docker/)
* Install Docker Compose plugin
* Verify installation:
  ```bash
  docker --version
  docker-compose --version
  ```

### 2. NVIDIA GPU Setup (Optional but Recommended)
* Install [NVIDIA Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html)
* Verify GPU visibility:
  ```bash
  nvidia-smi
  ```

### 3. System Requirements
* **Disk Space:**
  * Docker images: ~2-3GB
  * Phi-4 model (Q4_K_M): ~8GB
  * Full environment + models: ~12-15GB
* **RAM:** Minimum 16GB, 32GB+ recommended for optimal performance
* **GPU Memory:** 12-16GB VRAM recommended (Phi-4 14B Q4_K_M quantized)
* **CPU:** Fallback support for systems without GPU
* **Internet connection:** Required for initial model downloads

### 4. Environment Setup (Mandatory Step)
Create a `.env` file at the repository root:

```env
HF_TOKEN=hf_123yourhuggingfacetoken
PYTHONPATH=/app
NVIDIA_VISIBLE_DEVICES=all
```

**Important**: Never commit sensitive tokens to public repositories.

## Usage

### 1. Building & Running

```bash
# Build Docker images
docker-compose build

# Start services
docker-compose up
```

This creates two containers:
* `app`: FastAPI (`:8000`) + Streamlit (`:8501`)
* `ollama`: LLM server (`:11434`)

### 2. Accessing Services
* Frontend (Streamlit): `http://localhost:8501`
* Backend (FastAPI): `http://localhost:8000`
* Ollama: Port `11434` (internal use only)

### 3. Processing Audio
1. Open Streamlit interface at `http://localhost:8501`
2. Upload audio file (supported: MP3, WAV, M4A, FLAC, OGG - max 200MB)
3. Review file information (duration, size, estimated processing time)
4. Click "🚀 Start Processing"
5. Monitor real-time progress through transcription and summarization stages
6. View results in "📝 Transcription" and "📋 Summary" tabs
7. Export results using various format options
## Technical Details

### Transcription Flow
1. FastAPI receives `UploadFile`
2. File saved to temporary storage
3. Whisper processes audio (GPU-accelerated if available)
4. Results returned to client

### Summarization Flow
1. **Direct Processing**: Transcript processed in a single pass using Phi-4 model with 131K context window to ensure the model can process the entire transcript without truncation, chunking, or overlapping sections as quality gets deteriorated with chunking
2. **Structured Output**: Summary organized into clear sections:
   - Overview
   - Main Points
   - Key Insights
   - Action Items / Decisions
   - Open Questions / Next Steps
   - Conclusions
3. **Advanced Parsing**: AI-generated summary is parsed and structured for both display and export

## Export Options

### PDF Export
* **Summary PDF**: Contains only the AI-generated summary with structured sections
* **Full Report PDF**: Includes both complete transcription and summary
* **Professional Formatting**: Clean layout with proper headings and bullet points

### Document Export
* **Word (.docx)**: Complete transcription and summary in Microsoft Word format
* **Text (.txt)**: Plain text transcription for simple text processing
* **Structured Layout**: Organized sections with clear headings and formatting

### Interactive Features
* **Copy to Clipboard**: Easy text selection and copying from the web interface
* **Download Buttons**: One-click downloads with timestamp-based filenames
* **Processing Statistics**: Export includes metadata like processing time and file information

## Logging & Monitoring

### Log Locations
* Backend:
  * `logs/api.log`
  * `logs/transcription.log`
  * `logs/summarization.log`
* Frontend: `logs/frontend.log`

View combined logs:
```bash
docker-compose logs -f
```

### Performance Monitoring
The UI displays real-time processing statistics including:
* **Processing Speed**: Real-time vs audio duration ratio
* **Words per Second**: Transcription throughput
* **Processing Efficiency**: Overall system performance metrics
* **File Analysis**: Automatic format detection, duration calculation, and processing time estimation

## Troubleshooting

### GPU Issues
```bash
# Verify Docker GPU access
docker run --rm --gpus all nvidia/cuda:12.1.0-runtime-ubuntu22.04 nvidia-smi

# Check environment
nvidia-smi
```

### Common Problems & Solutions

#### Slow Transcription
* Check for CPU fallback
* Try smaller Whisper model in `transcription.py`

#### Memory Issues
* Reduce model size
* Lower context window (default: 131,072 tokens)
* Ensure sufficient GPU memory (16-24GB for Phi-4 14B model)

#### Port Conflicts
Default ports:
* FastAPI: `:8000`
* Streamlit: `:8501`

Solution: Edit port mappings in `docker-compose.yml`

## License

MIT License

Copyright (c) [2025] [AskAresh.com]

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.