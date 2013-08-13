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


def init_orthos_and_3d():
    """ initialize a 2x2 plot grid consisting of 3 ortho views, and one 3-d view """
    fig = plt.figure()
    ax_array = [[None,None],[None,None]]

    ax_array[0][0] = fig.add_subplot(2,2,1)
    ax_array[0][0].set_xlabel('X')
    ax_array[0][0].set_ylabel('Z')

    ax_array[0][1] = fig.add_subplot(2,2,2)
    ax_array[0][1].set_xlabel('Y')
    ax_array[0][1].set_ylabel('Z')

    ax_array[1][0] = fig.add_subplot(2,2,3)
    ax_array[1][0].set_xlabel('X')
    ax_array[1][0].set_ylabel('Y')

    ax_array[1][1] = fig.add_subplot(2,2,4,projection='3d')
    ax_array[1][1].view_init(60,-60)
    ax_array[1][1].set_xlabel('X')
    ax_array[1][1].set_ylabel('Y')
    ax_array[1][1].set_zlabel('Z')

    return fig,ax_array

def plot_orthos_and_3d(ax_array, items, *args, **kwargs):
    """ add a set of 3-d elements to the plot """
    if not (len(ax_array) == 2) and (len(ax_array[0]) == 2) and (len(ax_array[1]) == 2):
        print('Error: expecting ax_array 2x2 list returned from init_orthos_and_3d')

    ax_array[0][0].plot(items[0,:], items[2,:], *args, **kwargs)
    
    ax_array[0][1].plot(items[1,:], items[2,:], *args, **kwargs)

    ax_array[1][0].plot(items[0,:], items[1,:], *args, **kwargs)

    ax_array[1][1].plot(items[0,:], items[1,:], items[2,:], *args, **kwargs)

    return


