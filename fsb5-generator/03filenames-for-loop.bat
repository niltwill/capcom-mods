@echo off

:: Check if Output folder exists
if not exist ".\Output" (
    echo Output folder not found!
    exit /b
)

:: Check if there are any .resource files in the Output folder and its subdirectories
dir ".\Output\*.resource" /s > nul 2>&1
if %errorlevel% neq 0 (
    echo No .resource files found in the Output folder or its subdirectories.
    exit /b
)

:: Loop through all .resource files in the Output directory and subdirectories
for /r %%f in ("*.resource") do (
    echo python add_fsb_loop.py "%%f" 0 0
)

echo Done processing. Use above lines in a new batch script and add the loop as needed.
