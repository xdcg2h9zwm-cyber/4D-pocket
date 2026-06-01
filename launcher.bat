@echo off
echo ============================================
echo   飞书 Bot 启动器
echo ============================================

cd /d "%~dp0"

echo [1/2] 启动 cpolar 隧道...
start "cpolar" D:\cpolar\cpolar http 6666

echo    等待 cpolar 启动 (5s)...
timeout /t 5 /nobreak >nul

echo [2/2] 启动 Bot 服务...
python bot.py

pause
