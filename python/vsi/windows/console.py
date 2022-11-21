import os
from ctypes import byref
if os.name == "nt":
  from ctypes.wintypes import DWORD
  from ctypes import windll


def fix_ansi():
  """
  There is an issue in Windows consoles with TTY support where Windows mangles
  ANSI codes on stdout and stderr. This function will prevent this mangling for
  the current python process by setting the console mode to
  ``ENABLE_ECHO_INPUT`` if ``ENABLE_LINE_INPUT`` is enabled, which fixes the
  problem.
  """

  # https://stackoverflow.com/a/60194390/4166604
  if os.name == "nt":
    mode = DWORD(0)
    # Even though stdout is -11, stderr (-12) doesn't need to be set also, as
    # this command is for accessing the console, not a file handle
    stdout = windll.kernel32.GetStdHandle(-11)
    windll.kernel32.GetConsoleMode(stdout, byref(mode))
    # In tests on Windows 11:
    # - Non-TTYs work. This includes "| cat" and "Git for Windows". (Mode 0)
    # - TTYs with Mode 7 work. This includes WSL in Windows Terminal and
    #   Windows Console Host
    # - TTYs with Mode 3 are the problem. (Specifically the 0b1 bit). Git for
    #   Windows Bash, cmd, powershell, cygwin, etc... all running in Windows
    #   Console Host or Windows Terminal all default to Mode 3 (may be Code
    #   page related).
    # Setting the 0b100 bit for Mode 3 fixes the ANSI issue
    if mode.value & 0b1 and not mode.value & 0b100:
      windll.kernel32.SetConsoleMode(stdout, mode.value | 0b100)
