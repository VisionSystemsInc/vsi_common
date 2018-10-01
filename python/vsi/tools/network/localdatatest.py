import socket
import argparse

import numpy as np

PORT = int(int('vsi'.encode('hex'), 16)**0.5)

import logging
logger = logging.getLogger(__name__)

from select import select

import time

RAISE=1

def testIp(host):
  try:
    socket.gethostbyaddr(host)
  except:
    return False
  return True

def testConnect(host,port, timeout=0.1):
  if not testIp(host):
    return False
  try:
    s = socket.create_connection((host, port), timeout=timeout)
  except:
    return False
  return s

class Average(object):
  def __init__(self, bufferSize=100):
    self.bufferSize = bufferSize
    self.values = np.empty(self.bufferSize)
    self.t = np.empty(self.bufferSize)
    self.index = 0
    self.used = 0
    self.total = 0
    self.t0 = None

    self.set_partial()

  def add_partial(self, value, t=time.time()):
    self.used += 1
    if self.used >= self.bufferSize:
      self.set_full()
    if self.t0 is None:
      t0 = t
    self.add_full(value, t)

  def add_full(self, value, t=time.time()):
    self.values[self.index] = value
    self.t[self.index] = t
    self.index += 1
    if self.index >= self.bufferSize:
      self.index = 0
    self.total += value

  def clear(self):
    self.index = 0
    self.used = 0
    self.set_partial()

  def average_partial(self):
    delta = self.t[self.used] -self.t[0]
    value = np.sum(self.values[0:self.used])
    return value/delta

  def average_full(self):
    delta =  self.t[self.index-1] - self.t[self.index]
    #should support wrap around
    value = np.sum(self.values)
    return value/delta

  def set_full(self):
    self.add = self.add_full
    self.average = self.average_full

  def set_partial(self):
    self.add = self.add_partial
    self.average = self.average_partial

MAX_SIZE = 2**32
MIN_SIZE = 1
MIN_DELAY = 0
MAX_DELAY = 0.1
MIN_SIZE2 = 1000
MAX_SIZE2 = 2

def streamData(sock, desired):
  printInteval = 1.0
  size = 1
  delay = 0.01
  delayGain = 0.001
  gain = 0.001 # 1%

  readBytes = 0
  writeBytes = 0
  startTime = time.time()
  timePrint = time.time()+printInteval

  reads = Average()
  writes = Average()

  try:
    t1 = time.time()
    while 1:
      tLeft = delay + t1 - time.time()
      if tLeft < 0:
        tLeft = 0

      (r,_,_) = select([sock], [],[], tLeft)
      if r:
        d = r[0].recv(MAX_SIZE*2)
        if len(d) == 0:
          logger.warning('Disconnect')
          break
        reads.add(len(d))

      tLeft = delay + t1 - time.time()
      if tLeft > 0:
        time.sleep(tLeft)
      writes.add(sock.send(' '*size))

      writeSpeed = writes.average()
      speedError = desired - writeSpeed

      size += gain * speedError
      size = int(min(MAX_SIZE, max(MIN_SIZE, size)))

      t1 += delay

      if time.time() > timePrint:
        print(reads.average())
        print(writeSpeed)
        print(writes.t[writes.index-1]-writes.t[writes.index])
        print(size, time.time()-startTime)
        print(writes.values)
        timePrint = time.time()+printInteval
  except:
    if RAISE:
      raise
    print('Disconnected... I guess')

def serveDataTest(port, desired):
  serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
  serverSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
  serverSocket.bind(('0.0.0.0', port))
  serverSocket.listen(1)
  while 1:
    s = select([serverSocket], [], [], 1)

    if s[0]:
      s2 = serverSocket.accept()[0]

      streamData(s2, desired)


def connectDataTest(ip, port, desired, timeout=1):
  clientSocket = socket.create_connection((ip, port), timeout=1)

  streamData(clientSocket, desired)

def scanSubnet(ip, port):
  ip = '.'.join(ip.split('.')[0:3])
  for x in range(1, 255):
    s = testConnect('.'.join((ip, str(x))), port)
    if s:
      s.close()
      return '.'.join((ip, str(x)))
  return None

if __name__=='__main__':
  parser = argparse.ArgumentParser()
  parser.add_argument('--port', '-p', type=int, default=PORT, help='Port to communicate on. Default %d' % PORT)
  parser.add_argument('--ip', '-i', type=str, default='127.0.0.1', help='IP to communicate with or ip to scan subnet/24 of')
  parser.add_argument('--server', '-s', action='store_true', default=False, help='Just be a server')
  parser.add_argument('--desired', '-d', type=int, default=1e6, help='Target bps')
  args = parser.parse_args()

  sh = logging.StreamHandler()
  sh.setLevel(logging.DEBUG)
  logger.addHandler(sh)
  logger.setLevel(logging.DEBUG)

  port = args.port
  ip = args.ip
  if not args.server and not testConnect(ip, port):
    ip = scanSubnet(ip, port)

  if args.server or ip is None:
    logger.info('No client found, serving data test server on %d', port)
    serveDataTest(port, args.desired)
  else:
    logger.info('Connecting to %s:%d...', ip, port)
    connectDataTest(ip, port, args.desired)

