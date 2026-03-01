FROM python:3.11-slim

WORKDIR /app

# System deps for opencv, Pillow, etc.
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 libglib2.0-0 libsm6 libxrender1 libxext6 \
    && rm -rf /var/lib/apt/lists/*

# Python deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY *.py ./
COPY story.txt ./
COPY db/ db/

# Ensure data directory exists
RUN mkdir -p data

EXPOSE 7860

ENTRYPOINT ["python", "unified_ui.py"]
