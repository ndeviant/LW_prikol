adb connect localhost:21503
set "SCRIPT_DIR=%~dp0"
python "%SCRIPT_DIR%cli.py" auto %*
echo.
echo Script finished. Press any key to close this window...
pause > nul