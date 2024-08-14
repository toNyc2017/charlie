# Use Python 3.8 as the base image
FROM python:3.8

# Set environment variables
ENV PORT=80
ENV REACT_APP_API_BASE_URL=http://localhost:80/api

# Install Node.js and npm
RUN apt-get update && apt-get install -y nodejs npm

# Create working directories
WORKDIR /app

# Copy frontend code
COPY frontend/ /app/frontend

# Install frontend dependencies and build the React app
WORKDIR /app/frontend
RUN npm install && npm run build

# Copy backend code
COPY backend/ /app/backend

# Install Python dependencies
WORKDIR /app/backend
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Serve the frontend static files using FastAPI
WORKDIR /app
RUN mkdir -p /app/frontend/build/static

# Set up FastAPI to serve on the desired port
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "80"]
