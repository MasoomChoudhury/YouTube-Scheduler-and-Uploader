@echo off
TITLE YouTube Scheduler and Uploader

echo Starting YouTube Video Scheduler and Uploader...
echo.

REM Check if a Python virtual environment 'venv' exists in the current directory
IF EXIST venv\Scripts\activate.bat (
    echo Found 'venv' virtual environment. Attempting to activate...
    CALL venv\Scripts\activate.bat
    echo Virtual environment activated.
) ELSE (
    echo Virtual environment 'venv' not found in the current directory.
    echo Will attempt to run using the system's default Python interpreter.
    echo Please ensure all required packages (google-api-python-client, google-auth-oauthlib, etc.) are installed.
)
echo.

echo Launching the Python uploader script (youtube_uploader.py)...
echo If the script requires authorization, a web browser may open.
echo Please follow the on-screen prompts.
echo.
python youtube_uploader.py
echo.

echo ================================================
echo Script execution has finished.
echo Press any key to close this window.
echo ================================================
pause > nul
