@echo off
setlocal EnableExtensions
title SEJUMOTION Motor Dashboard - First Install
cd /d "%~dp0"

echo.
echo ============================================
echo  SEJUMOTION Motor Dashboard - First Install
echo ============================================
echo.

set "PYEXE="

REM 1) Prefer Windows Python launcher. On this PC, "py" works correctly.
where py >nul 2>nul
if not errorlevel 1 (
    py --version >nul 2>nul
    if not errorlevel 1 set "PYEXE=py"
)

REM 2) Known local Python path used by this PC
if not defined PYEXE if exist "%LOCALAPPDATA%\Python\bin\python.exe" set "PYEXE=%LOCALAPPDATA%\Python\bin\python.exe"

REM 3) Anaconda / Miniconda fallback
if not defined PYEXE if exist "%USERPROFILE%\anaconda3\envs\myenv\python.exe" set "PYEXE=%USERPROFILE%\anaconda3\envs\myenv\python.exe"
if not defined PYEXE if exist "%USERPROFILE%\Anaconda3\envs\myenv\python.exe" set "PYEXE=%USERPROFILE%\Anaconda3\envs\myenv\python.exe"
if not defined PYEXE if exist "%USERPROFILE%\miniconda3\envs\myenv\python.exe" set "PYEXE=%USERPROFILE%\miniconda3\envs\myenv\python.exe"

if not defined PYEXE goto :NO_PYTHON

echo Python command found:
echo   %PYEXE%
echo.
%PYEXE% --version
if errorlevel 1 goto :NO_PYTHON

echo.
echo Installing required packages...
%PYEXE% -m pip install --upgrade pip
if errorlevel 1 goto :PIP_ERROR

%PYEXE% -m pip install -r requirements.txt
if errorlevel 1 goto :PIP_ERROR

echo.
echo ============================================
echo  INSTALLATION COMPLETED
echo ============================================
echo.
echo Next time, double-click RUN_DASHBOARD.bat
echo.
pause
exit /b 0

:NO_PYTHON
echo.
echo PYTHON NOT FOUND.
echo Please send a screenshot of this window to ChatGPT.
echo.
pause
exit /b 1

:PIP_ERROR
echo.
echo PACKAGE INSTALLATION FAILED.
echo Please copy the error text or take a screenshot and send it to ChatGPT.
echo.
pause
exit /b 1
