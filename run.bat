@echo off
echo Starting Document Knowledge Base...
echo.

REM Check if .env file exists
if not exist .env (
    echo ❌ .env file not found!
    echo Please copy .env.example to .env and add your OpenAI API key
    echo.
    pause
    exit /b 1
)

REM Check if virtual environment exists
if not exist venv (
    echo 📦 Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
call venv\Scripts\activate

REM Install requirements if needed
if not exist venv\Scripts\streamlit.exe (
    echo 📦 Installing requirements...
    pip install -r requirements.txt
)

REM Run the application
echo 🚀 Starting Streamlit application...
echo.
echo Open your browser and go to: http://localhost:8501
echo Press Ctrl+C to stop the application
echo.

streamlit run src/app.py

pause