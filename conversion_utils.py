import numpy as np

# assumes azimuth is measured in radians east of north and y-north, x-east z-up coordinate system
def spherical_to_euclidian(azimuth,elevation):
    x = np.sin(azimuth)*np.cos(elevation)
    y = np.cos(azimuth)*np.cos(elevation)
    z = np.sin(elevation)
    return (x,y,z)
    
# azimuth is measured in radians east of north. assumes y-north, x-east z-up coordinate system
def euclidian_to_spherical(x,y,z):
    azimuth = np.arctan2(x,y)
    elevation = np.arcsin(z)
    return(azimuth,elevation)

