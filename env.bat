@echo off

if defined PATH (
  set PATH=%PATH%;%~dp0windows
) else (
  set PATH=%~dp0windows
)

if defined PYTHONPATH (
  set PYTHONPATH=%PYTHONPATH%;%~dp0python
) else (
  set PYTHONPATH=%~dp0python
)

if defined MATLABPATH (
  set MATLABPATH=%MATLABPATH%;%~dp0matlab
) else (
  set MATLABPATH=%~dp0matlab
)

