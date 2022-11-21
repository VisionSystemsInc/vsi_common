import os
from ctypes import byref, sizeof, Structure
if os.name == "nt":
  from ctypes.wintypes import DWORD
  from ctypes import windll


  class FILE_NAME_INFO(Structure):
    _fields_ = [('FileNameLength', wintypes.DWORD),
    #             ('FileName', wintypes.WCHAR*1)]
    # The correct way does not work with ctypes, so a hack is imposed
    # https://stackoverflow.com/a/8745869/4166604
                ('FileName', wintypes.WCHAR*wintypes.MAX_PATH)]


def GetFileInformationByHandleEx_FileNameInfo(file_handle):
  """
  Calls the ``FileNameInfo`` version of ``GetFileInformationByHandleEx`` and
  returns the filename

  ``file_handle`` should be a kernel32 HANDLE, such as
  ``kernel32.GetStdHandle``

  Parameters
  ----------
  file_handle : HANDLE

  Returns
  -------
  str
  """
  fileNameInfo = FILE_NAME_INFO()

  windll.kernel32.GetFileInformationByHandleEx(file_handle,
                                               2,
                                               byref(fileNameInfo),
                                               sizeof(fileNameInfo))
  return fileNameInfo.FileName

