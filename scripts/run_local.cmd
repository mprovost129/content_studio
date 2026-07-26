@echo off
call "%~dp0manage_local.cmd" migrate --noinput
if errorlevel 1 exit /b %ERRORLEVEL%

call "%~dp0manage_local.cmd" runserver 127.0.0.1:8000
exit /b %ERRORLEVEL%
