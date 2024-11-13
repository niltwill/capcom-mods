@echo off

:: It's recommended to use the same version that your game used, for best compatibility (only some are supplied here)
:: You can find the FSB tool in: "<path to Unity Engine folder>\Editor\Data\Tools\FSBTool" (in "x64" and/or "x86" folders)
set UnityVer=.\Unity_FSBTools\Unity 2022.3.17f1

:: Check if UnityVer is set correctly
echo UnityVer is set to: %UnityVer%

:: Check if FSBTool64.exe exists at the given path
if not exist "%UnityVer%\FSBTool64.exe" (
    echo FSBTool64.exe not found at "%UnityVer%"
    exit /b 1
)

:: Convert the OGG (-q 9) files
:: You can set the quality to 100 if your source file is a WAV or FLAC (lossless) file (change extension too)
:: However if you use 320 kbps MP3 converted to "-q 9" OGG, use 90 to match the "-q 9"
for /r %%f in (.\Input\*.ogg) do (
    echo Processing file: %%f
    "%UnityVer%\FSBTool64.exe" -l "%UnityVer%" -c vorbis -C fsb -q 90 -i "%%f" -o ".\Output\%%~nf.resource"
)

:: Remove FSB cache directory
if exist .\.fsbcache (
    rd /s /q .\.fsbcache
)
