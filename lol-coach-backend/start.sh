#!/bin/bash
set -e

echo "--- Starting deployment script ---"

echo "Current working directory (before cd):"
pwd

# Navegar para o diretório do backend
# REMOVIDO: cd lol-coach-backend (pois o Root Directory já aponta para cá)

echo "Current working directory (after cd):"
pwd

echo "---"

echo "Listing files in current directory:"
ls -la

echo "---"

echo "PYTHONPATH variable:"
echo $PYTHONPATH

echo "---"

echo "Starting Gunicorn..."
gunicorn app:app
