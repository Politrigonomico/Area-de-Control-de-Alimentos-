@echo off
setlocal
chcp 65001 >nul 2>&1
title Respaldo — Sistema Área de Alimentos

set DB_PATH=%USERPROFILE%\SistemaAlimentos\alimentos_fighiera.db
set BACKUP_DIR=%USERPROFILE%\SistemaAlimentos\respaldos

if not exist "%DB_PATH%" (
    echo [ERROR] No se encontró la base de datos en:
    echo   %DB_PATH%
    pause
    exit /b 1
)

:: Crear carpeta de respaldos
if not exist "%BACKUP_DIR%" mkdir "%BACKUP_DIR%"

:: Nombre con fecha y hora
for /f "tokens=1-3 delims=/ " %%a in ("%date%") do (
    set DIA=%%a
    set MES=%%b
    set ANIO=%%c
)
for /f "tokens=1-2 delims=:." %%a in ("%time%") do (
    set HORA=%%a
    set MIN=%%b
)
set HORA=%HORA: =0%

set BACKUP_NAME=backup_%ANIO%%MES%%DIA%_%HORA%%MIN%.db
set BACKUP_PATH=%BACKUP_DIR%\%BACKUP_NAME%

copy "%DB_PATH%" "%BACKUP_PATH%" >nul

if errorlevel 1 (
    echo [ERROR] No se pudo crear el respaldo.
    pause
    exit /b 1
)

echo.
echo ================================================================
echo   Respaldo creado correctamente:
echo   %BACKUP_PATH%
echo ================================================================
echo.

:: Listar respaldos existentes
echo Respaldos disponibles:
dir /b /o-d "%BACKUP_DIR%\*.db" 2>nul | head -10

:: Borrar respaldos con más de 30 días
forfiles /p "%BACKUP_DIR%" /m *.db /d -30 /c "cmd /c del @path" >nul 2>&1

echo.
echo (Los respaldos de más de 30 días se eliminan automáticamente.)
echo.
pause
