# syntax=docker/dockerfile:1

FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

WORKDIR /app

# Install git for wiki cloning, tesseract for PDF OCR, poppler for pdf2image
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    tesseract-ocr \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/*

# Enable bytecode compilation for faster startup
ENV UV_COMPILE_BYTECODE=1
ENV UV_NO_PROGRESS=1

# Copy project files
COPY pyproject.toml ./
COPY README.md ./
COPY src ./src
COPY uv.lock ./uv.lock

# Install dependencies and project
RUN uv sync --frozen --no-cache

# Set up PATH
ENV PATH="/app/.venv/bin:$PATH"

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import httpx; httpx.get('http://localhost:8000/health').raise_for_status()"

# Run the server
CMD ["python", "-m", "bark.server"]
