@echo off
echo ============================================================
echo  Fine-Tuning Environment Setup
echo ============================================================
echo.

cd /d "%~dp0\.."

REM Check for Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python not found. Please install Python 3.10+ and add it to PATH.
    pause
    exit /b 1
)

REM Create virtual environment
if not exist finetune_venv (
    echo [1/4] Creating virtual environment...
    python -m venv finetune_venv
) else (
    echo [1/4] Virtual environment already exists.
)

REM Activate
echo [2/4] Activating virtual environment...
call finetune_venv\Scripts\activate

REM Install PyTorch with CUDA 12.8 (forward-compatible with CUDA driver 13.1)
echo [3/4] Installing PyTorch with CUDA support...
pip install torch --index-url https://download.pytorch.org/whl/cu128

REM Install remaining dependencies
echo [4/4] Installing fine-tuning dependencies...
pip install -r finetune\requirements-finetune.txt

REM Verify CUDA
echo.
echo ============================================================
echo  Verification
echo ============================================================
python -c "import torch; print(f'PyTorch {torch.__version__}'); print(f'CUDA available: {torch.cuda.is_available()}'); print(f'GPU: {torch.cuda.get_device_name(0)}' if torch.cuda.is_available() else 'No GPU detected')"

echo.
if %errorlevel% equ 0 (
    echo Setup complete! Run run_finetune.bat to start fine-tuning.
) else (
    echo WARNING: Verification failed. Check the output above.
)

pause
