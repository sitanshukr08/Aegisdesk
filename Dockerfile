FROM python:3.10-slim

WORKDIR /code

# Install system dependencies needed for compiling some Python packages
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

# Install Python dependencies without caching to keep image size small
RUN pip install --no-cache-dir -r requirements.txt

# Pre-download the Semantic Router Model (22MB) so cold starts are instant
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"

# Copy application files
COPY ./src /code/src

# Ensure data and db directories exist and are owned by the new user
RUN mkdir -p /code/data /code/chroma_db && \
    useradd -m aegis && \
    chown -R aegis:aegis /code

USER aegis

EXPOSE 8000

CMD ["uvicorn", "aegisdesk.app.main:app", "--host", "0.0.0.0", "--port", "8000"]