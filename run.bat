@echo off
echo Starting Corporate Law Document Generator...
echo.

REM Check if Ollama is running
echo Checking Ollama availability...
curl -s http://localhost:11434/api/tags >nul 2>&1
if %errorlevel% neq 0 (
    echo WARNING: Ollama does not appear to be running at http://localhost:11434
    echo The app will start but LLM features require Ollama.
    echo.
    echo To install Ollama: https://ollama.com/download
    echo To pull the model: ollama pull llama3.1:8b
    echo.
)

REM Check if .env file exists
if not exist .env (
    echo No .env file found. Copying from .env.example...
    if exist .env.example (
        copy .env.example .env >nul
        echo Created .env from .env.example. Edit it to set your configuration.
    ) else (
        echo WARNING: No .env.example found either. App will use defaults.
    )
    echo.
)

REM Check if virtual environment exists
if not exist venv (
    echo Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
call venv\Scripts\activate

REM Install requirements if needed
if not exist venv\Scripts\streamlit.exe (
    echo Installing requirements...
    pip install -r requirements.txt
)

REM Run the application
echo Starting Streamlit application...
echo.
echo Open your browser and go to: http://localhost:8501
echo Press Ctrl+C to stop the application
echo.

streamlit run streamlit_app.py

pause
