@echo off
echo ============================================================
echo  Llama 3.1 8B Legal Fine-Tuning Pipeline
echo ============================================================
echo.

cd /d "%~dp0\.."

REM Check virtual environment
if not exist finetune_venv\Scripts\activate (
    echo ERROR: Virtual environment not found.
    echo Run setup_env.bat first.
    pause
    exit /b 1
)

REM Activate
call finetune_venv\Scripts\activate

REM Check Ollama
echo Checking Ollama availability...
ollama list >nul 2>&1
if %errorlevel% neq 0 (
    echo WARNING: Ollama does not appear to be running.
    echo Export step will fail without Ollama.
    echo.
)

REM ============================================================
REM Step 1: Prepare training data
REM ============================================================
echo.
echo [STEP 1/3] Preparing training data...
echo ------------------------------------------------------------
python finetune\prepare_data.py
if %errorlevel% neq 0 (
    echo.
    echo ERROR: Data preparation failed. See output above.
    pause
    exit /b 1
)

REM ============================================================
REM Step 2: Train
REM ============================================================
echo.
echo [STEP 2/3] Training model (this may take several hours)...
echo ------------------------------------------------------------
python finetune\train.py
if %errorlevel% neq 0 (
    echo.
    echo Training failed. Retrying with fallback settings...
    echo.
    python finetune\train.py --fallback
    if %errorlevel% neq 0 (
        echo.
        echo ERROR: Training failed even with fallback settings.
        pause
        exit /b 1
    )
)

REM ============================================================
REM Step 3: Export to Ollama
REM ============================================================
echo.
echo [STEP 3/3] Exporting to Ollama...
echo ------------------------------------------------------------
python finetune\export_to_ollama.py
if %errorlevel% neq 0 (
    echo.
    echo ERROR: Export failed. See output above.
    pause
    exit /b 1
)

echo.
echo ============================================================
echo  PIPELINE COMPLETE
echo ============================================================
echo.
echo  The fine-tuned model is now available as: llama3.1-legal:8b
echo  Open the Streamlit app and select it from the Settings dropdown.
echo.

pause
