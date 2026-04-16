@echo off
chcp 65001 >nul 2>&1
title Compilando Sistema Area de Alimentos...

echo.
echo ================================================================
echo   Compilador — Sistema Area de Alimentos
echo   Genera un .exe standalone (no requiere Python en la otra PC)
echo ================================================================
echo.

:: Ir a la carpeta del proyecto
cd /d "%~dp0"

:: Verificar Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python no encontrado. Instala Python 3.10+ primero.
    pause
    exit /b 1
)

:: Instalar PyInstaller si no está
echo [1/3] Verificando PyInstaller...
pip show pyinstaller >nul 2>&1
if errorlevel 1 (
    echo   Instalando PyInstaller...
    pip install pyinstaller --quiet
)
echo   OK

:: Instalar dependencias del sistema
echo [2/3] Instalando dependencias...
pip install sqlalchemy reportlab --quiet
echo   OK

:: Compilar
echo [3/3] Compilando .exe (puede tardar 2-5 minutos)...
echo.
pyinstaller sistema_alimentos.spec --clean --noconfirm

if errorlevel 1 (
    echo.
    echo [ERROR] La compilacion fallo. Ver mensajes arriba.
    pause
    exit /b 1
)

echo.
echo ================================================================
echo   Listo! El ejecutable esta en:
echo   %~dp0dist\SistemaAlimentos\SistemaAlimentos.exe
echo.
echo   Copia la carpeta completa "SistemaAlimentos" a la otra PC.
echo   No hace falta instalar nada mas.
echo ================================================================
echo.
pause
