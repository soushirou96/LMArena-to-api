@echo off
setlocal enabledelayedexpansion

REM 切换到脚本所在目录（项目根目录）
cd /d "%~dp0"

echo [INFO] 安装/校验 Python 依赖...
python -m pip install --upgrade pip >nul 2>&1
python -m pip install -r requirements.txt
if errorlevel 1 (
  echo [ERROR] 依赖安装失败，请检查 Python/pip 是否可用。
  exit /b 1
)

echo.
echo [INFO] 启动 Docker+noVNC 浏览器引导器...
echo       - 如果页面出现 Cloudflare 验证，终端会提示你打开 noVNC
echo       - noVNC: http://localhost:7900/?autoconnect=1^&resize=scale^&password=secret
echo.

REM 透传所有命令行参数到 Python 脚本，例如 --url https://lmarena.ai/
python scripts\docker_browser_runner.py %*
set ret=%ERRORLEVEL%

if "%ret%"=="0" (
  echo.
  echo [DONE] 运行结束。
) else (
  echo.
  echo [ERROR] 运行失败，退出码=%ret%
)

endlocal