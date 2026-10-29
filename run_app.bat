@echo off
TITLE Little Millennium & Nest Daycare Kharadi - ERP & CRM Portal
COLOR 0B
echo ===============================================================================
echo        LITTLE MILLENNIUM - NEST DAYCARE (KHARADI BRANCH)
echo        Enterprise Preschool & Daycare ERP and CRM Web Application
echo ===============================================================================
echo.

cd /d "%~dp0"

set PYTHON_EXEC=C:\Python312\python.exe
if not exist "%PYTHON_EXEC%" (
    set PYTHON_EXEC=python
)

echo [1/3] Checking Python runtime...
"%PYTHON_EXEC%" --version
if errorlevel 1 (
    echo [ERROR] Python not found at %PYTHON_EXEC%. Please verify your Python installation.
    pause
    exit /b 1
)

echo.
echo [2/3] Initializing SQLite database and verifying seed data...
"%PYTHON_EXEC%" database.py
if not exist "preschool_erp.db" (
    "%PYTHON_EXEC%" seed_data.py
)

echo.
echo [3/3] Launching Flask Full-Page Web Application on http://127.0.0.1:5000 ...
echo.
echo ===============================================================================
echo  The portal is running!
echo  Open your browser at: http://127.0.0.1:5000
echo.
echo  Roles available on Login Screen (1-Click Demo Switcher):
echo   - Center Director (Chanchal Sharma)
echo   - Teacher (Ananya Deshmukh)
echo   - Parent (Vikram Mehta)
echo   - Student (Aarav Mehta)
echo ===============================================================================
echo.

start http://127.0.0.1:5000

"%PYTHON_EXEC%" app.py

pause
