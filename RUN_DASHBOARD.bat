@echo off
setlocal EnableExtensions
title SEJUMOTION Motor Selection Dashboard V0.1
cd /d "%~dp0"

set "PYEXE="

REM 1) Prefer Windows Python launcher
where py >nul 2>nul
if not errorlevel 1 (
    py --version >nul 2>nul
    if not errorlevel 1 set "PYEXE=py"
)

REM 2) Known local Python path
if not defined PYEXE if exist "%LOCALAPPDATA%\Python\bin\python.exe" set "PYEXE=%LOCALAPPDATA%\Python\bin\python.exe"

REM 3) Anaconda / Miniconda fallback
if not defined PYEXE if exist "%USERPROFILE%\anaconda3\envs\myenv\python.exe" set "PYEXE=%USERPROFILE%\anaconda3\envs\myenv\python.exe"
if not defined PYEXE if exist "%USERPROFILE%\Anaconda3\envs\myenv\python.exe" set "PYEXE=%USERPROFILE%\Anaconda3\envs\myenv\python.exe"
if not defined PYEXE if exist "%USERPROFILE%\miniconda3\envs\myenv\python.exe" set "PYEXE=%USERPROFILE%\miniconda3\envs\myenv\python.exe"

if not defined PYEXE goto :NO_PYTHON

echo.
echo Starting Motor Selection Dashboard...
echo Python: %PYEXE%
echo.
%PYEXE% -m streamlit run app.py
if errorlevel 1 goto :RUN_ERROR
exit /b 0

:NO_PYTHON
echo.
echo PYTHON NOT FOUND.
echo Please run INSTALL_FIRST.bat first.
echo.
pause
exit /b 1

:RUN_ERROR
echo.
echo Dashboard could not start.
echo Please copy this error text or take a screenshot and send it to ChatGPT.
echo.
pause
exit /b 1
