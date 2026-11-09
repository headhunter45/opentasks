@echo off
set "PROJ_ROOT=%~dp0"
for /f "delims=" %%v in ('python -c "import json,pathlib; p=pathlib.Path(r'%PROJ_ROOT%.ot\config.json'); print(json.loads(p.read_text()).get('system',{}).get('toolVersion','') if p.is_file() else '')" 2^>nul') do set "OT_VER=%%v"
if defined OT_VER (
    if exist "%PROJ_ROOT%.ot\bin\%OT_VER%\ot.zipapp" (
        python "%PROJ_ROOT%.ot\bin\%OT_VER%\ot.zipapp" %*
        exit /b %ERRORLEVEL%
    )
)
set "BIN=%PROJ_ROOT%.ot\bin\ot.zipapp"
if exist "%BIN%" (
    python "%BIN%" %*
) else (
    ot %*
)

