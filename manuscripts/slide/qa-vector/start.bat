@echo off
cd /d "%~dp0"
where python >nul 2>&1 && (python serve.py & goto :eof)
where py >nul 2>&1 && (py serve.py & goto :eof)
echo Khong tim thay Python. Cai Python 3 roi chay lai file nay.
pause
