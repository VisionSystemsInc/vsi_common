@echo off

if defined PATH (
  set PATH=%PATH%;%~dp0batch
) else (
  set PATH=%~dp0batch
)

if defined PYTHONPATH (
  set PYTHONPATH=%PYTHONPATH%;%~dp0batch
) else (
  set PYTHONPATH=%~dp0python
)

if defined MATLABPATH (
  set MATLABPATH=%MATLABPATH%;%~dp0batch
) else (
  set MATLABPATH=%~dp0matlab
)

