@echo off
setlocal EnableDelayedExpansion
chcp 65001 >nul 2>&1
title Sistema Área de Alimentos — Fighiera

echo.
echo ================================================================
echo   Sistema Área de Alimentos — Municipalidad de Fighiera
echo ================================================================
echo.

:: ── Verificar Python ─────────────────────────────────────────────
echo [1/5] Verificando Python...
python --version
if errorlevel 1 (
    echo.
    echo [ERROR] Python no encontrado en el PATH.
    echo Instalalo desde https://www.python.org/downloads/
    echo IMPORTANTE: marcar "Add Python to PATH" al instalar.
    echo.
    pause
    exit /b 1
)

:: ── Verificar pip ────────────────────────────────────────────────
echo.
echo [2/5] Verificando pip...
pip --version
if errorlevel 1 (
    echo [ERROR] pip no disponible.
    pause
    exit /b 1
)

:: ── Instalar dependencias ────────────────────────────────────────
echo.
echo [3/5] Instalando dependencias...
pip install sqlalchemy reportlab
if errorlevel 1 (
    echo [ERROR] Fallo la instalacion de dependencias.
    pause
    exit /b 1
)
echo [OK] Dependencias instaladas.

:: ── Migración ────────────────────────────────────────────────────
echo.
echo [4/5] Verificando base de datos...
set DB_PATH=%USERPROFILE%\SistemaAlimentos\alimentos_fighiera.db

if not exist "%DB_PATH%" (
    echo    Base de datos no encontrada. Ejecutando migracion...
    set CSV_DIR=%~dp0data_export
    if exist "!CSV_DIR!" (
        echo    Carpeta data_export encontrada: !CSV_DIR!
        cd /d "%~dp0"
        python -m migration.migrate --csv-dir "!CSV_DIR!"
        if errorlevel 1 (
            echo [ERROR] La migracion fallo. Ver mensajes arriba.
            pause
            exit /b 1
        )
        echo [OK] Datos migrados correctamente.
    ) else (
        echo [ADVERTENCIA] No se encontro la carpeta data_export en:
        echo    !CSV_DIR!
        echo    El sistema arrancara vacio.
    )
) else (
    echo [OK] Base de datos encontrada: %DB_PATH%
)

:: ── Lanzar sistema ───────────────────────────────────────────────
echo.
echo [5/5] Iniciando el sistema...
echo.
cd /d "%~dp0"
python main.py
if errorlevel 1 (
    echo.
    echo [ERROR] El sistema cerro con un error. Ver mensajes arriba.
    pause
)
