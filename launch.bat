@echo off
chcp 65001 >nul
title TalentMatch 启动器
cd /d "%~dp0"
echo [INFO] 正在启动 TalentMatch...
powershell -ExecutionPolicy Bypass -File "launch.ps1"
