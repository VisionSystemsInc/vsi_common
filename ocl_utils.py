""" OpenCL-related utility functions and classes """
import pyopencl as cl


def init_ocl(device_string=None):
    """ create an OpenCL context using a device whose name matches device_string """
    platforms = cl.get_platforms()
    # use first platform for now
    devices = platforms[0].get_devices()
    if device_string is not None:
        matches = [dev for dev in devices if device_string in dev.name]
    else:
        matches = devices
    # choose first matching device for now
    if len(matches) == 0:
        err_str = 'ERROR: no devices containing string %s' % device_string
        raise Exception(err_str)
    ctx = cl.Context(devices=(matches[0],))

    return ctx


