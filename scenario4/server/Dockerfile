# Use official NVIDIA NeMo container (includes all ASR dependencies pre-installed)
# See: https://github.com/NVIDIA-NeMo/NeMo
FROM nvcr.io/nvidia/nemo:25.11.01

# Set working directory
WORKDIR /app

# Copy application code
COPY app.py .

# Expose port
EXPOSE 8000

# Run the application
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
