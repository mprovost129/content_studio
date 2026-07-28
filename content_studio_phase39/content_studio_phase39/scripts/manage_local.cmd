@echo off
setlocal
set "USE_SQLITE=1"
set "DJANGO_SETTINGS_MODULE=config.Settings.dev"
set "PYTHON_PATH=%~dp0..\.venv\Runtime\python.exe"

if not exist "%PYTHON_PATH%" set "PYTHON_PATH=%~dp0..\.venv\Scripts\python.exe"

if not exist "%PYTHON_PATH%" (
    echo The local virtual environment is missing. Create .venv and install requirements first.
    exit /b 1
)

"%PYTHON_PATH%" -c "from PIL import Image" || (
    echo Pillow is installed but its native imaging module cannot load with %PYTHON_PATH%.
    echo Repair it with: "%PYTHON_PATH%" -m pip install --force-reinstall Pillow
    exit /b 1
)

"%PYTHON_PATH%" "%~dp0..\manage.py" %*
exit /b %ERRORLEVEL%
