import time
import signal


class WatchDog(object):
  # WatchDog(1).start()
  def __init__(self, timeout=20):
    self.timeout = timeout
    if hasattr(signal, 'CTRL_BREAK_EVENT'):
      signal.signal(signal.CTRL_BREAK_EVENT, self.reset)
    elif hasattr(signal, 'SIGUSR1'):
      signal.signal(signal.SIGUSR1, self.reset)
    else:
      raise Exception('No usable signal found')
    signal.signal(signal.SIGTERM, self.stop)
    signal.signal(signal.SIGINT, self.stop)

  def stop(self, signum, frame):
    self.watch = time.time() - 1

  def reset(self, signum, frame):
    self.watch = time.time() + self.timeout

  def start(self, poll_interval=1):
    self.watch = time.time() + self.timeout
    while time.time() < self.watch:
      time.sleep(poll_interval)
