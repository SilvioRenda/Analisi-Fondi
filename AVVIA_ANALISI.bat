@echo off
chcp 65001 >nul
echo ========================================
echo ANALISI COMPARATIVA FONDI HEALTHCARE
echo ========================================
echo.
cd /d "%~dp0"
python main.py
echo.
echo Premere un tasto per chiudere...
pause >nul
