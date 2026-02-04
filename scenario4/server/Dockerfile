# Use NVIDIA CUDA base image for GPU support
FROM nvidia/cuda:12.1.0-runtime-ubuntu22.04

# Set working directory
WORKDIR /app

# Install Python 3.12 and system dependencies
RUN apt-get update && apt-get install -y \
    python3.12 \
    python3.12-venv \
    python3-pip \
    libsndfile1 \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Create symbolic link for python
RUN ln -sf /usr/bin/python3.12 /usr/bin/python

# Copy requirements first for better caching
COPY requirements.txt .

# Install PyTorch with CUDA support first
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cu121

# Install remaining dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy lhotse fix from root (if available)
COPY ../../fix_lhotse.py /tmp/fix_lhotse.py
RUN python /tmp/fix_lhotse.py || true

# Copy application code
COPY app.py .

# Expose port
EXPOSE 8000

# Run the application
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
