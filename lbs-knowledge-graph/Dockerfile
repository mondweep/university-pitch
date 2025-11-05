# Multi-stage build for LBS Knowledge Graph Development Environment
FROM python:3.11-slim as base

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    curl \
    build-essential \
    libssl-dev \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*

# Create app directory
WORKDIR /app

# Development stage
FROM base as development

# Install development dependencies
RUN apt-get update && apt-get install -y \
    vim \
    less \
    tree \
    htop \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt requirements-dev.txt ./

# Install Python dependencies
RUN pip install --upgrade pip && \
    pip install -r requirements.txt && \
    pip install -r requirements-dev.txt

# Copy application code
COPY . .

# Install pre-commit hooks
RUN git init && \
    pre-commit install || true

# Expose port for development server
EXPOSE 8000

# Default command for development
CMD ["python", "-m", "src.api.server"]

# Production stage
FROM base as production

# Copy only production requirements
COPY requirements.txt ./

# Install production dependencies
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Copy only necessary application files
COPY src/ ./src/
COPY data/ ./data/
COPY scripts/ ./scripts/

# Create non-root user
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app

USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Production command
CMD ["python", "-m", "src.api.server", "--host", "0.0.0.0", "--port", "8000"]

# Lambda deployment stage
FROM public.ecr.aws/lambda/python:3.11 as lambda

# Copy requirements
COPY requirements.txt ./

# Install dependencies in Lambda layer
RUN pip install --target "${LAMBDA_TASK_ROOT}" -r requirements.txt

# Copy Lambda handler and source code
COPY lambda/ ${LAMBDA_TASK_ROOT}/
COPY src/ ${LAMBDA_TASK_ROOT}/src/

# Set the CMD to Lambda handler
CMD ["lambda_handler.handler"]
