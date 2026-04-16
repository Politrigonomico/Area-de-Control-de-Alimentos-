@echo off
setlocal EnableDelayedExpansion
chcp 65001 >nul 2>&1
title Migración de datos — Sistema Área de Alimentos

echo.
echo ================================================================
echo   Migración desde sistema Access (.mdb)
echo   Sistema Área de Alimentos — Fighiera
echo ================================================================
echo.

:: ── Pedir archivo .mdb ──────────────────────────────────────────
set /p MDB_PATH="Ingresá la ruta completa al archivo .mdb: "

if not exist "%MDB_PATH%" (
    echo.
    echo [ERROR] No se encontró el archivo: %MDB_PATH%
    pause
    exit /b 1
)

echo.
echo Archivo encontrado: %MDB_PATH%
echo.

:: ── Preparar carpeta CSV ─────────────────────────────────────────
set SCRIPT_DIR=%~dp0
set CSV_DIR=%SCRIPT_DIR%data_export

if not exist "%CSV_DIR%" mkdir "%CSV_DIR%"

:: ── Exportar con Python usando pyodbc (si está disponible) ──────
echo Exportando tablas a CSV...
echo.

python "%SCRIPT_DIR%migration\export_mdb.py" "%MDB_PATH%" "%CSV_DIR%"

if errorlevel 1 (
    echo.
    echo [ERROR] No se pudieron exportar los datos.
    echo.
    echo Necesitás tener instalado el driver de Microsoft Access:
    echo   Microsoft Access Database Engine 2016 Redistributable
    echo   https://www.microsoft.com/en-us/download/details.aspx?id=54920
    echo.
    echo O bien exportá las tablas manualmente desde Access como CSV
    echo y copiálas a la carpeta: %CSV_DIR%
    echo.
    pause
    exit /b 1
)

echo.
echo ================================================================
echo   Importando datos a SQLite...
echo ================================================================
echo.

cd /d "%SCRIPT_DIR%"
python -m migration.migrate --csv-dir "%CSV_DIR%"

if errorlevel 1 (
    echo.
    echo [ERROR] La migración falló. Revisá los mensajes anteriores.
    pause
    exit /b 1
)

echo.
echo ================================================================
echo   Migración completada. Podés iniciar el sistema con INICIAR.bat
echo ================================================================
echo.
pause
