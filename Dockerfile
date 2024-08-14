# Use Python 3.8 as the base image
FROM python:3.8

# Set environment variables
ENV PORT=80
ENV RESULTS_DIR=results
ENV REACT_APP_API_BASE_URL=http://localhost:80/api

# Install Node.js and npm
RUN apt-get update && apt-get install -y nodejs npm

# Create working directory
WORKDIR /app

# Copy frontend code
COPY frontend/ /app/frontend

# Install frontend dependencies and build the React app
WORKDIR /app/frontend
RUN npm install && npm run build

# Copy the requirements file from the backend directory into the container
WORKDIR /app/backend
COPY backend/requirements.txt /app/requirements.txt

# Print the contents of requirements.txt for verification
RUN cat /app/requirements.txt

# Install Python dependencies specified in requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copy the rest of the backend code
COPY backend/ /app/backend

# Serve the frontend static files using FastAPI
WORKDIR /app
RUN mkdir -p /app/frontend/build/static

# Set up FastAPI to serve on the desired port
CMD ["uvicorn", "backend.dummymain:app", "--host", "0.0.0.0", "--port", "80"]
