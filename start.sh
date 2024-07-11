#!/bin/bash

# Navigate to backend directory and start the backend server
cd ~/charlie/backend
source venv/bin/activate
uvicorn main:app --host 0.0.0.0 --port 8000 &

# Navigate to frontend directory and start the frontend server
cd ~/charlie/frontend
npm start &
