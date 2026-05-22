FROM python:3.10-slim

WORKDIR /code

# Install system dependencies needed for compiling some Python packages
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

# Install Python dependencies without caching to keep image size small
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY ./app /code/app

# Ensure data and db directories exist
RUN mkdir -p /code/data /code/chroma_db

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]