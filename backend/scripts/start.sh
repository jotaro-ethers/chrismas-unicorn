#!/bin/bash

# FastAPI Supabase Backend Startup Script
# This script activates the virtual environment and starts the FastAPI server

set -e

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# Change to the project directory
cd "$PROJECT_DIR"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Error: Virtual environment not found!"
    echo "Please run: python -m venv venv"
    exit 1
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "Warning: .env file not found!"
    echo "Creating from template..."
    cp .env.example .env
    echo "Please edit .env with your Supabase credentials"
fi

# Install package in editable mode if not already installed
echo "Ensuring package is installed in editable mode..."
pip install -e . > /dev/null 2>&1

# Start the server
echo "Starting FastAPI server..."
echo "Server will be available at: http://${HOST:-0.0.0.0}:${PORT:-8000}"
echo "API docs at: http://${HOST:-0.0.0.0}:${PORT:-8000}/docs"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

# Run uvicorn with the correct module path
exec uvicorn main_app.main:app --reload --host ${HOST:-0.0.0.0} --port ${PORT:-8000}