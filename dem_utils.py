"""
Utilities Related to loading,saving, and manipulating Digital Elevation Models
"""

import numpy as np
import struct


def load_srtm(directory, lat_min, lon_min, lat_max, lon_max):
    """ load a SRTM DEM file with the given lat,lon bounds from directory """

    NS = 'N'
    EW = 'E'
    if lat_min < 0:
        NS = 'S'
    if lon_min < 0:
        EW = 'W'

    file_lat_min = int(np.floor(lat_min))
    file_lat_max = file_lat_min + 1
    file_lon_min = int(np.floor(lon_min))

    fname_form = directory + '/' + NS + '%02d'+ EW + '%03d.hgt'
    fname = fname_form % (abs(file_lat_min), abs(file_lon_min))
    print('filename = ' + fname)
    fd = open(fname,'rb')
    srtm_str = fd.read()
    fd.close()
    print('len(strm_str) = ' + str(len(srtm_str)))
    srtm_array = struct.unpack('>' + str(1201*1201) + 'h',srtm_str)
    srtm = np.array(srtm_array,'float')
    srtm = np.reshape(srtm,(1201,1201),'C')
    interval = 1.0/1201
    i0 = int((file_lat_max - lat_max)/interval)
    i1 = int((file_lat_max - lat_min)/interval)
    j0 = int((lon_min - file_lon_min)/interval)
    j1 = int((lon_max - file_lon_min)/interval)

    print(str(i0) + ' ' + str(i1) + ' ' + str(j0) + ' ' + str(j1))
    lon_vals = file_lon_min + (np.arange(j0,j1)*interval)
    lat_vals = file_lat_max - (np.arange(i0,i1)*interval)
    elev_geoid = srtm[i0:i1,j0:j1]

    return(lon_vals, lat_vals, elev_geoid)

