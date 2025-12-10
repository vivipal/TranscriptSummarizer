# File: Dockerfile
FROM nvidia/cuda:12.1.0-runtime-ubuntu22.04

# Environment variables
ENV PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive \
    PYTORCH_CUDA_ALLOC_CONF=max_split_size_mb:512

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3.11 \
    python3.11-dev \
    python3.11-venv \
    python3-pip \
    ffmpeg \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create a virtual environment
RUN python3.11 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

WORKDIR /app
RUN mkdir -p frontend/src backend

# Install backend dependencies
COPY backend/requirements.txt backend/
RUN pip install --no-cache-dir -r backend/requirements.txt

# Install frontend dependencies
COPY frontend/requirements.txt frontend/
RUN pip install --no-cache-dir -r frontend/requirements.txt

# Copy your actual code
COPY backend/ backend/
COPY frontend/ frontend/

# Create a startup script that checks and downloads models if needed
RUN echo '#!/bin/bash\n\
# Check and download models if not present in volumes\n\
# python3 -c "import whisper; whisper.load_model('\''medium'\'')" & \n\
uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 & \n\
streamlit run frontend/src/app.py --server.port=8501 --server.address=0.0.0.0\n\
wait' > /start.sh && chmod +x /start.sh

CMD ["/start.sh"]
