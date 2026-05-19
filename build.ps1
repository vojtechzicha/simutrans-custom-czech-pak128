#Requires -Version 5.1
$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
& python "$root\build.py" @args
exit $LASTEXITCODE
