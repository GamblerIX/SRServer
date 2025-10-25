@echo off
setlocal EnableExtensions

for /f "tokens=2 delims=: " %%a in ('chcp') do set "_ORIG_CP=%%a"
chcp 65001 >nul

cd /d "%~dp0"

title 星穹铁道 私服启动器

if "%~1"=="elevated" goto :main

echo.
echo ========================================
echo   星穹铁道 私服启动器
echo ========================================
echo.
echo [DEBUG] 当前工作目录: %CD%
echo [DEBUG] 脚本路径: %~dp0
echo.

net session >nul 2>&1
if %errorLevel% neq 0 (
    echo [INFO] 需要管理员权限
    echo [INFO] 将弹出 UAC 升权窗口，请点击“是”...
    echo.
    powershell -NoProfile -Command "Start-Process -FilePath '%~f0' -ArgumentList 'elevated' -Verb RunAs" 2>nul
    if %errorLevel% equ 0 (
        echo [INFO] 已发起 UAC 升权，新窗口将以管理员权限运行
        echo [INFO] 当前窗口将自动关闭
        timeout /t 2 /nobreak >nul
        if defined _ORIG_CP chcp %_ORIG_CP% >nul 2>&1
        exit /b 0
    ) else (
        echo [错误] UAC 升权失败或被取消
        echo [提示] 也可右键文件选择“以管理员身份运行”
        echo.
        pause
        if defined _ORIG_CP chcp %_ORIG_CP% >nul 2>&1
        exit /b 1
    )
) else (
    echo [INFO] 已确认管理员权限
)

:main
echo.
echo ========================================
echo   星穹铁道 私服启动器
echo ========================================
echo.
echo [INFO] 已确认管理员权限
echo [INFO] 正在初始化私服环境...
echo.
echo [DEBUG] 当前工作目录: %CD%
echo.

echo [DEBUG] 正在校验文件路径...
echo [DEBUG] 服务器管理器路径: %CD%\Server\manager\manager.exe
echo [DEBUG] 客户端启动器路径: %CD%\Patch\manager\client_launcher.exe
echo.

if not exist "Server\manager\manager.exe" (
    echo [错误] 未找到服务器管理器: %CD%\Server\manager\manager.exe
    echo [DEBUG] 当前目录内容:
    dir /b
    echo.
    echo [DEBUG] Server 目录内容:
    if exist "Server" (
        dir /b Server
        echo.
        echo [DEBUG] Server\manager 目录内容:
        if exist "Server\manager" (
            dir /b Server\manager
        ) else (
            echo Server\manager 目录不存在
        )
    ) else (
        echo Server 目录不存在
    )
    echo.
    echo 请确认文件完整
    pause
    if defined _ORIG_CP chcp %_ORIG_CP% >nul 2>&1
    exit /b 1
)

if not exist "Patch\manager\client_launcher.exe" (
    echo [错误] 未找到客户端启动器: %CD%\Patch\manager\client_launcher.exe
    echo [DEBUG] Patch 目录内容:
    if exist "Patch" (
        dir /b Patch
        echo.
        echo [DEBUG] Patch\manager 目录内容:
        if exist "Patch\manager" (
            dir /b Patch\manager
        ) else (
            echo Patch\manager 目录不存在
        )
    ) else (
        echo Patch 目录不存在
    )
    echo.
    echo 请确认文件完整
    pause
    if defined _ORIG_CP chcp %_ORIG_CP% >nul 2>&1
    exit /b 1
)

echo [INFO] 文件校验通过
echo.

echo ----------------------------------------
echo 1. 启动服务器管理器...
echo ----------------------------------------
echo.
echo [INFO] 以非阻塞模式启动服务器管理器，稍候...
echo [DEBUG] 执行: start "服务器管理器" /D "%CD%\Server\manager" "manager.exe" --run

start "服务器管理器" /D "%CD%\Server\manager" "manager.exe" --run
if %errorLevel% neq 0 (
    echo [错误] 启动服务器管理器失败，错误码: %errorLevel%
    pause
    if defined _ORIG_CP chcp %_ORIG_CP% >nul 2>&1
    exit /b 1
)

timeout /t 3 /nobreak >nul

echo.
echo ----------------------------------------
echo 2. 启动客户端启动器...
echo ----------------------------------------
echo.
echo [INFO] 以非阻塞模式启动客户端启动器，稍候...
echo [DEBUG] 执行: start "客户端启动器" /D "%CD%\Patch\manager" "client_launcher.exe"

start "客户端启动器" /D "%CD%\Patch\manager" "client_launcher.exe"
if %errorLevel% neq 0 (
    echo [错误] 启动客户端启动器失败，错误码: %errorLevel%
    pause
    if defined _ORIG_CP chcp %_ORIG_CP% >nul 2>&1
    exit /b 1
)

echo.
echo ========================================
echo           操作完成
echo ========================================
echo.
echo 使用须知:
echo.
echo 1. 请先注册游戏账号
echo    访问地址: http://127.0.0.1:20100/account/register
echo.
echo 2. 使用注册账号登录游戏客户端
echo.
echo 3. 通过服务器管理器在控制台查看日志
echo.
echo 4. 若遇到问题可切换“兼容模式/控制台模式”
echo.
echo 注意事项:
echo    - 仅供学习交流使用
echo    - 禁止用于任何违法违规用途
echo.
echo 更多说明请查看 README.md
echo.
echo 按任意键关闭本窗口...
pause >nul

:end
if defined _ORIG_CP chcp %_ORIG_CP% >nul 2>&1
endlocal
