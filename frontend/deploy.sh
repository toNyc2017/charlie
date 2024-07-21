#!/bin/bash

# Navigate to the frontend directory
cd /home/azureuser/charlie/frontend

# Build the frontend
npm run build

# Copy the build files to the Nginx root directory
sudo cp -r /home/azureuser/charlie/frontend/build/* /var/www/html/

# Restart Nginx
sudo systemctl restart nginx

echo "Deployment completed successfully."
