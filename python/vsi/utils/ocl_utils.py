""" OpenCL-related utility functions and classes """
import pyopencl as cl


def init_ocl(device_string=None, platform_idx=0, device_idx=0, verbose=False):
  """ create an OpenCL context using a device whose name matches device_string

  Parameters
  ----------
  device_string :
  platform_idx : int, optional
      The platform index. Default: 0
  device_idx : int, optional
      The device index. Default: 0
  verbose : bool
  
  Returns
  -------
  array_like
      The context

  Raises
  ------
  Exception
      When there are no devices whose name matches the string
  """
  platforms = cl.get_platforms()

  if verbose:
    print('Found %d OpenCL Platforms:' % len(platforms))
    print(platforms)

  devices = platforms[platform_idx].get_devices()

  if verbose:
    print('Found %d devices on platform %d:' % (len(devices), platform_idx))
    print(devices)

  if device_string is not None:
    matches = [dev for dev in devices if device_string in dev.name]
  else:
    matches = devices

  if verbose:
    print('Found %d devices matching <%s>. using device %d' % (len(matches), device_string, device_idx))

  if len(matches) == 0:
    err_str = 'ERROR: no devices containing string %s' % device_string
    raise Exception(err_str)
  ctx = cl.Context(devices=(matches[device_idx],))

  if verbose:
    print('Got OpenCL context on device ' + str(matches[device_idx]))

  return ctx


