@echo off
title MappEduc v2.3

echo 🎓 MappEduc - Mapeamento de Projeção Educacional
echo Autor: Edson Ricardo dos Santos da Silva
echo Licenca: GNU GPL v3.0
echo.

echo Verificando Python...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Python nao encontrado! Instale em: https://www.python.org/downloads/
    pause
    exit /b 1
)

echo ✅ Python OK!

if not exist "venv\" (
    echo 📦 Criando ambiente virtual...
    python -m venv venv
)

echo 🔧 Ativando ambiente virtual...
call venv\Scripts\activate.bat

echo 📥 Instalando dependencias...
pip install --quiet PySide6 PyOpenGL opencv-python numpy

echo.
echo 🚀 Iniciando MappEduc...
python mappeduc.py

call deactivate 2>nul
pause
