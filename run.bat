@echo off
setlocal
cd /d "%~dp0"

set "PY_CMD="
if exist ".venv\Scripts\python.exe" set "PY_CMD=.venv\Scripts\python.exe"
if not defined PY_CMD if exist "..\.venv\Scripts\python.exe" set "PY_CMD=..\.venv\Scripts\python.exe"
if not defined PY_CMD (
    where py >nul 2>nul && set "PY_CMD=py"
)

if not defined PY_CMD (
    echo ERROR: Python not found!
    pause
    exit /b 1
)

echo Using Python: %PY_CMD%
echo.

if not "%~1"=="" (
    echo %~1
    "%PY_CMD%" src/cli.py "%~1"
    if errorlevel 1 (
        echo FAIL on %~1
        pause
        exit /b 1
    )
    echo.
    echo Done
    pause
    exit /b 0
)

for %%f in (*.txt tests\basic_tests\*.txt) do (
    if exist "%%f" (
        echo ^<%%~nf^>
        "%PY_CMD%" src/cli.py "%%f"
        if errorlevel 1 (
            echo FAIL on %%f
            pause
            exit /b 1
        )
        echo.
    )
)

echo Done
pause