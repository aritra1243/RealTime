FROM python:3.10-slim

# Install system dependencies required for OpenCV and PyTorch
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    libgomp1 \
    ffmpeg \
    libsm6 \
    libxext6 \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Create non-root user (Hugging Face standard UID 1000)
RUN useradd -m -u 1000 user
USER user
ENV HOME=/home/user \
    PATH=/home/user/.local/bin:$PATH \
    PORT=7860 \
    PYTHONUNBUFFERED=1

# Install python dependencies
COPY --chown=user:user requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Copy application source code
COPY --chown=user:user . .

# Expose standard Hugging Face Spaces port
EXPOSE 7860

# Launch FastAPI / Gradio application with Uvicorn
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "7860", "--workers", "1"]
