@echo off
REM FastAPI Supabase Backend Startup Script for Windows
REM This script activates the virtual environment and starts the FastAPI server

setlocal enabledelayedexpansion

REM Get the directory where this script is located
set SCRIPT_DIR=%~dp0
set PROJECT_DIR=%SCRIPT_DIR%..

REM Change to the project directory
cd /d "%PROJECT_DIR%"

REM Check if virtual environment exists
if not exist "venv\" (
    echo Error: Virtual environment not found!
    echo Please run: python -m venv venv
    exit /b 1
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Check if .env file exists
if not exist ".env" (
    echo Warning: .env file not found!
    echo Creating from template...
    copy .env.example .env > nul
    echo Please edit .env with your Supabase credentials
)

REM Install package in editable mode if not already installed
echo Ensuring package is installed in editable mode...
pip install -e . > nul 2>&1

REM Start the server
echo Starting FastAPI server...
echo Server will be available at: http://%HOST%:%PORT%
echo API docs at: http://%HOST%:%PORT%/docs
echo.
echo Press Ctrl+C to stop the server
echo.

REM Run uvicorn with the correct module path
uvicorn main_app.main:app --reload --host %HOST% --port %PORT%