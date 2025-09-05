# AI Medical Scheduling Agent - Production Docker Image
# RagaAI Assignment - Healthcare Booking System
# Multi-stage build for optimized production image

# Build stage
FROM python:3.9-slim as builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

# Production stage
FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONPATH=/app
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PATH=/root/.local/bin:$PATH

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy Python packages from builder stage
COPY --from=builder /root/.local /root/.local

# Copy application code
COPY . .

# Create necessary directories and set permissions
RUN mkdir -p data exports logs forms && \
    chmod +x deployment/scripts/*.sh 2>/dev/null || true

# Generate sample data during build (for demo)
RUN python data/generate_data.py 2>/dev/null || echo "Sample data will be generated at runtime"

# Create non-root user for security
RUN useradd --create-home --shell /bin/bash app && \
    chown -R app:app /app
USER app

# Expose Streamlit port
EXPOSE 8501

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8501/_stcore/health || exit 1

# Default command - can be overridden
CMD ["streamlit", "run", "ui/streamlit_app.py", "--server.address", "0.0.0.0", "--server.port", "8501", "--server.headless", "true", "--server.fileWatcherType", "none"]