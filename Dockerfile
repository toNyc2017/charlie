# Start from a base image with Python and Node.js installed
FROM python:3.8

# Set environment variables
ENV PORT=8000

# Install Node.js and npm
RUN apt-get update && apt-get install -y nodejs npm

# Create working directories
WORKDIR /app

# Copy frontend code
COPY frontend/ /app/frontend/

# Install frontend dependencies and build the React app
WORKDIR /app/frontend
RUN npm install && npm run build

# Copy backend code
COPY backend/ /app/backend/

# Install Python dependencies
WORKDIR /app/backend
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Set the static files directory in FastAPI
ENV STATIC_FILES_DIR=/app/frontend/build

# Expose port 80 for the app
EXPOSE 80

# Set up FastAPI to serve static files and the React app
RUN mkdir -p /app/frontend/build/static

# Serve the frontend through FastAPI
RUN echo "from fastapi.staticfiles import StaticFiles" > /app/backend/serve_frontend.py
RUN echo "from fastapi.responses import FileResponse" >> /app/backend/serve_frontend.py
RUN echo "from backend.main import app" >> /app/backend/serve_frontend.py
RUN echo "app.mount('/static', StaticFiles(directory='/app/frontend/build/static'), name='static')" >> /app/backend/serve_frontend.py
RUN echo "@app.get('/')" >> /app/backend/serve_frontend.py
RUN echo "async def read_index():" >> /app/backend/serve_frontend.py
RUN echo "    return FileResponse('/app/frontend/build/index.html')" >> /app/backend/serve_frontend.py

# Run uvicorn server
CMD ["uvicorn", "backend.serve_frontend:app", "--host", "0.0.0.0", "--port", "80"]
