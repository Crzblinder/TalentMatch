# TalentMatch 一键启动器
# 功能：
#   1. 自动检测并启动后端、前端服务
#   2. 服务就绪后自动打开浏览器
#   3. 首次运行时询问是否在桌面创建快捷方式
#
# 用法：
#   直接双击运行 launch.bat
#   或在 PowerShell 中执行： .\launch.ps1

$ErrorActionPreference = "Stop"

$ROOT = Split-Path -Parent $MyInvocation.MyCommand.Path
$DESKTOP = [Environment]::GetFolderPath("Desktop")
$SHORTCUT_NAME = "TalentMatch.lnk"
$SHORTCUT_PATH = Join-Path $DESKTOP $SHORTCUT_NAME

function Write-Info($msg) { Write-Host "[INFO] $msg" -ForegroundColor Cyan }
function Write-Ok($msg) { Write-Host "[OK] $msg" -ForegroundColor Green }
function Write-Warn($msg) { Write-Host "[WARN] $msg" -ForegroundColor Yellow }

# 检测 Python 和虚拟环境
$PYTHON = Join-Path $ROOT "backend\.venv\Scripts\python.exe"
if (-not (Test-Path $PYTHON)) {
    $PYTHON = Get-Command python -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Source
    if (-not $PYTHON) {
        Write-Warn "未找到 Python，请先运行一次安装流程：python scripts/start.py"
        Read-Host "按回车键退出"
        exit 1
    }
}

# 首次运行：询问是否创建桌面快捷方式
if (-not (Test-Path $SHORTCUT_PATH)) {
    Write-Host ""
    Write-Host "是否要在桌面创建 TalentMatch 快捷方式？方便以后一键启动（Y/n）" -ForegroundColor Yellow -NoNewline
    $answer = Read-Host
    if ($answer -eq "" -or $answer -match "^[Yy]") {
        try {
            $WshShell = New-Object -ComObject WScript.Shell
            $Shortcut = $WshShell.CreateShortcut($SHORTCUT_PATH)
            $Shortcut.TargetPath = "powershell.exe"
            $Shortcut.Arguments = "-ExecutionPolicy Bypass -WindowStyle Minimized -File `"$($MyInvocation.MyCommand.Path)`""
            $Shortcut.WorkingDirectory = $ROOT
            $Shortcut.IconLocation = "powershell.exe,0"
            $Shortcut.Description = "TalentMatch 智能人才匹配系统"
            $Shortcut.Save()
            Write-Ok "桌面快捷方式已创建：$SHORTCUT_PATH"
        } catch {
            Write-Warn "创建快捷方式失败：$_"
        }
    }
}

Write-Info "正在启动 TalentMatch..."
Write-Info "项目目录：$ROOT"
Write-Info "Python：$PYTHON"

# 启动服务（前台阻塞，Ctrl+C 停止）
try {
    & $PYTHON "$ROOT\scripts\start.py" --open-browser --skip-deps
} catch {
    Write-Warn "启动过程异常：$_"
}

Write-Host ""
Read-Host "按回车键退出"
