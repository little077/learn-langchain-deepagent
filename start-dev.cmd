@echo off
setlocal
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8
"%~dp0.venv\Scripts\langgraph.exe" dev %*
endlocal
