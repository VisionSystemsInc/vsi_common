#Can this be replaced with multiprocessing.connections.PipeListener, and PipeClient?!

#based off of http://code.activestate.com/lists/python-list/446422/

from ctypes import *

PIPE_ACCESS_DUPLEX = 0x3
PIPE_TYPE_MESSAGE = 0x4
PIPE_READMODE_MESSAGE = 0x2
PIPE_WAIT = 0
PIPE_UNLIMITED_INSTANCES = 255
BUFSIZE = 4096
NMPWAIT_USE_DEFAULT_WAIT = 0
INVALID_HANDLE_VALUE = -1
ERROR_PIPE_CONNECTED = 535

GENERIC_READ = 0x80000000
GENERIC_WRITE = 0x40000000
OPEN_EXISTING = 0x3
PIPE_READMODE_MESSAGE = 0x2
ERROR_PIPE_BUSY = 231
ERROR_MORE_DATA = 234

PIPE_PREFIX=r'\\.\pipe'+'\\'

class PipeException(Exception):
  pass

def open(name, server=False):
  ''' Helper open function

  Parameters
  ----------
  name : str

  Returns
  -------
  :class:`Pipe`
      The pipe


  Give it the look and feel of python's open command
  '''
  pipe = Pipe(name, server)
  return pipe

class Pipe(object):
  ''' Windows Named Pipe class similar to File objects '''
  def __init__(self, name, server=False):
    self.server = server
    self.name = PIPE_PREFIX+name
    self.open()

  def open(self):
    """
    Raises
    ------
    PipeException
        For an invalid handle value
    PipeException
        Could not connect to the named pipe
    PipeException
        Error pipe busy
    PipeException
        SetNamedPipeHandleState failed
    """
    if self.server:
      self.hPipe = windll.kernel32.CreateNamedPipeA(self.name,
                    PIPE_ACCESS_DUPLEX,
                    PIPE_TYPE_MESSAGE | PIPE_READMODE_MESSAGE | PIPE_WAIT,
                    PIPE_UNLIMITED_INSTANCES, BUFSIZE, BUFSIZE,
                    NMPWAIT_USE_DEFAULT_WAIT, None)

      if (self.hPipe == INVALID_HANDLE_VALUE):
        raise PipeException('Invalid Handle Value')

      fConnected = windll.kernel32.ConnectNamedPipe(self.hPipe, None)
      if ((fConnected == 0) and (windll.kernel32.GetLastError() == ERROR_PIPE_CONNECTED)):
        fConnected = 1

      if fConnected != 1:
        self.close()
        raise PipeException("Could not connect to the Named Pipe")

    else:
      self.hPipe = windll.kernel32.CreateFileA(self.name, GENERIC_READ | GENERIC_WRITE, 0, None, OPEN_EXISTING, 0, None)

      if (self.hPipe == INVALID_HANDLE_VALUE):
        if (windll.kernel32.GetLastError() != ERROR_PIPE_BUSY):
          raise PipeException('Error Pipe Busy')
        else:
          raise PipeException('Invalid Handle Value')


      dwMode = c_ulong(PIPE_READMODE_MESSAGE)
      fSuccess = windll.kernel32.SetNamedPipeHandleState(self.hPipe, byref(dwMode), None, None)
      if (not fSuccess):
        raise PipeException('SetNamedPipeHandleState failed')


  def read(self, bufferSize=4096):
    ''' Read up to bufferSize bytes '''

    chBuf = create_string_buffer(bufferSize)
    cbRead = c_ulong(0)

    fSuccess = windll.kernel32.ReadFile(self.hPipe, chBuf, bufferSize,
                                        byref(cbRead), None)
    if fSuccess == 1 or windll.kernel32.GetLastError() == ERROR_MORE_DATA:
    #ERROR_MORE_DATA is only important in message mode, currently only using
    #byte mode
      return chBuf.value

  @staticmethod
  def wait_for(name, timeout__ms):
    """

    Parameters
    ----------
    name : str
    timeout__ms : int
        The timeout in milliseconcds

    Returns
    -------
    bool
    """
    return windll.kernel32.WaitNamedPipeA(PIPE_PREFIX+name, timeout__ms)

  def disconnect(self):
    ''' Send disconnect to client, forcing them to disconnect from the pipe '''
    windll.kernel32.DisconnectNamedPipe(self.hPipe)

  def write(self, message):
    """

    Parameters
    ----------
    message : str
        The message
    """
    cbWritten = c_ulong(0)
    fSuccess = windll.kernel32.WriteFile(self.hPipe, c_char_p(message),
                                         len(message), byref(cbWritten), None)
    if not fSuccess:
      return None
#    if len(message) != cbWritten.value:
#      raise PipeException('Number of byte written does not match string length')
    return cbWritten.value


  def close(self):
    windll.kernel32.CloseHandle(self.hPipe)
