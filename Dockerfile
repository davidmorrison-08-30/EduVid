# Use uv's ARM64 Python base image
FROM python:3.12-slim-bookworm

# Install curl to download uv
RUN apt-get update && apt install -y --no-install-recommends \
    curl \
    ca-certificates \
    gcc \
    pkg-config \
    python3-dev \
    # System libraries required by pycairo and manimpango
    libcairo2-dev \
    libpango1.0-dev \
    # Media handling runtime requirements for Manim
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

ADD https://astral.sh/uv/install.sh /uv-installer.sh
RUN sh /uv-installer.sh && rm /uv-installer.sh

ENV PATH="/root/.local/bin/:$PATH"

WORKDIR /app

# Copy uv files
COPY pyproject.toml uv.lock ./

# Install dependencies (including strands-agents)
RUN uv sync --frozen --no-cache --no-install-project

# Copy agent file
COPY main.py ./

# Copy app
COPY app ./app

# Expose port
EXPOSE 8088

# Run application
CMD ["uv", "run", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8088"]