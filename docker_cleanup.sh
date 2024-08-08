#!/bin/bash

echo "Stopping all running containers..."
docker stop $(docker ps -aq)

echo "Removing all containers..."
docker rm $(docker ps -aq)

echo "Removing all unused images..."
docker rmi -f $(docker images -aq)

echo "Removing all unused volumes..."
docker volume prune -f

echo "Removing all unused networks..."
docker network prune -f

echo "Removing all unused build cache..."
docker builder prune -f

echo "Docker cleanup completed."

