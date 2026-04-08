FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .

# Install dependencies required
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir openenv-core

# Copy all source files
COPY . .

# Set entrypoint for HF Spaces / normal running
EXPOSE 8000
CMD ["uvicorn", "server.app:app", "--host", "0.0.0.0", "--port", "8000"]
