import unittest
import threading

from vsi.windows.named_pipes import Pipe

class PipeTest(unittest.TestCase):
  def test_server_client(self):
    self.start_server_thread()
    Pipe.wait_for('test_named_pipes', 1000)
    
    pipe = Pipe('test_named_pipes', server=False)
    pipe.write('clientToServer')
    self.assertEqual(pipe.read(), 'serverToClient')
    self.server_thread.join(5)
    self.assertFalse(self.server_thread.is_alive())

  def test_server_client_byte_read(self):
    self.start_server_thread()
    Pipe.wait_for('test_named_pipes', 1000)
    
    pipe = Pipe('test_named_pipes', server=False)
    pipe.write('clientToServer')
    str = ''

    while 1:
      byte = pipe.read(1)
      if byte is None:
        break
      self.assertEqual(len(byte), 1)
      str += byte
    self.assertEqual(str, 'serverToClient')
  
    self.server_thread.join(5)
    self.assertFalse(self.server_thread.is_alive())

    
  def start_server_thread(self):
    self.server_thread = threading.Thread(target=self.server, name='server');
    self.server_thread.start()
    
  def server(self):
    pipe = Pipe('test_named_pipes', server=True)
    self.assertEqual(pipe.read(), 'clientToServer')
    pipe.write('serverToClient')
    pipe.close();