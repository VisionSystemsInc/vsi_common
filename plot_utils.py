""" A set of utility functions related to plotting
"""
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import numpy as np

def plot_box(x, y, width, height, *args, **kwargs):
    """ plot a 2-d box """
    xvec = [x, x+width, x+width, x, x]
    yvec = [y, y, y+height, y+height, y]
    plt.plot(xvec, yvec, *args, **kwargs)


def plot_cameras(Ks, Rs, Ts, axis_len=1.0, plot_look=True):
    """ plot a 3-d representation of a perspective camera """
    centers = [-R.transpose().dot(T) for (R, T) in zip(Rs, Ts)]
    centers_mat = np.array(centers).transpose()
    # plot center of projection 
    plt.plot(centers_mat[0, :], centers_mat[1, :], centers_mat[2, :],'ro')
    if plot_look:
        # plot a line in the direction of the principal axis
        cam_zs = [R[2, :] for R in Rs]
        for (center, cam_z) in zip(centers, cam_zs):
            zax = np.vstack((center, center + axis_len*cam_z))
            plt.plot(zax[:, 0], zax[:, 1], zax[:, 2],'g-')

