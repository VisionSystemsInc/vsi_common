import functools
from time import time


def format_time_string(seconds):
  """
  Format a time string the way I want it.
  You would think I wouldn't have to write this myself!

  Parameters
  ----------
  seconds : float

  Returns
  -------
  str
      E.g. "1 hour, 42 minutes, and 7 seconds"
  """
  if seconds < 0:
    raise ValueError("")
  if seconds < 1:
    return "{} seconds".format(seconds)

  # truncate float to nearest int
  seconds = int(seconds)
  minutes, seconds = divmod(seconds, 60)
  hours, minutes = divmod(minutes, 60)
  days, hours = divmod(hours, 24)

  # construct string, start at the largest element
  s = "{} second{}".format(seconds, 's' if seconds != 1 else '')
  if minutes > 0:
    s = "{} minute{}, and ".format(minutes, 's' if minutes != 1 else '') + s
  if hours > 0:
    s = "{} hour{}, ".format(hours, 's' if hours != 1 else '') + s
  if days > 0:
    s = "{} day{}, ".format(days, 's' if days != 1 else '') + s

  return s


class TaskTimer(object):
  def __init__(self, task_name, num_tasks=1, logging_func=print):
    self.task_name = task_name
    self.logging_func = logging_func
    if num_tasks > 0:
      self.num_tasks = num_tasks
    else:
      raise ValueError("Cannot have a non-positive number of tasks.")

  def __enter__(self):
    self.start = time()
    return self

  def __exit__(self, exc_type, exc_value, traceback):

    # print out the duration as long as no exception has occurred
    if exc_type is None:
      duration = time() - self.start

      plural = 's' if self.num_tasks != 1 else ''
      total_duration_str = format_time_string(duration)
      avg_duration = duration / self.num_tasks
      avg_duration_str = format_time_string(avg_duration)

      self.logging_func(f'Finished {self.num_tasks} {self.task_name} '
                        f'task{plural} in {total_duration_str} for an average time of '
                        f'{avg_duration_str} per task.')


class GenericTimer(object):
  def __init__(self, msg, logging_func=print):
    self.msg = msg
    self.logging_func = logging_func

  def __enter__(self):
    self.start = time()

  def __exit__(self, exc_type, exc_value, traceback):

    # Print out the duration as long as no exception has occurred
    if exc_type is None:
      duration = time() - self.start
      time_str = format_time_string(duration)

      self.logging_func(f'{self.msg} took {time_str}.')


def timeThisFunc(msg = None):
  """
  Generic decorator to time function execution
  """
  def decorator(func):

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
      _msg = msg or func.__name__
      with GenericTimer(_msg):
        return func(*args, **kwargs)

    return wrapper
  return decorator
