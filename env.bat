@echo off

if "%VSI%"=="2" exit /b
::Prevent multiple calls, it was just breaking the PATH variable mostly

set VSI=2

if defined PATH set PATH=%PATH%;%~dp0windows
if not defined PATH set PATH=%~dp0windows
REM Windows can't handle this in () because... I have no clue.
REM I bet it has something to do with lengths

if defined PYTHONPATH (
  set PYTHONPATH=%PYTHONPATH%;%~dp0python/python_util
) else (
  set PYTHONPATH=%~dp0python/python_util
)

if defined MATLABPATH (
  set MATLABPATH=%MATLABPATH%;%~dp0matlab
) else (
  set MATLABPATH=%~dp0matlab
)
