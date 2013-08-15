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

class OrthoAnd3DPlot:
    """ 2x2 array of plots consisting of 3 ortho views, plus one 3-d view """
    def __init__(self, fig, aligned_x_dim=0, aligned_y_dim=2, dim_labels=('X','Y','Z')):
        self.fig = fig
        self.ax_array = [[None,None],[None,None]]
        self.ax_array[0][0] = fig.add_subplot(2,2,1)
        self.ax_array[0][1] = fig.add_subplot(2,2,2)
        self.ax_array[1][0] = fig.add_subplot(2,2,3)
        self.ax_array[1][1] = fig.add_subplot(2,2,4,projection='3d')
        self.aligned_x_dim = aligned_x_dim
        self.aligned_y_dim = aligned_y_dim
        self.dim_labels = dim_labels
        # figure out the third axis
        aligned_dims = (aligned_x_dim, aligned_y_dim)
        self.extra_dim = 1
        if not 0 in aligned_dims:
            self.extra_dim = 0
        elif not 2 in aligned_dims:
            self.extra_dim = 2

        self.label_axes()

    def label_axes(self):
        """ label the axes using self.dim_labels """
        self.ax_array[0][0].set_xlabel(self.dim_labels[self.aligned_x_dim])
        self.ax_array[0][0].set_ylabel(self.dim_labels[self.aligned_y_dim])

        self.ax_array[0][1].set_xlabel(self.dim_labels[self.extra_dim])
        self.ax_array[0][1].set_ylabel(self.dim_labels[self.aligned_y_dim])

        self.ax_array[1][0].set_xlabel(self.dim_labels[self.aligned_x_dim])
        self.ax_array[1][0].set_ylabel(self.dim_labels[self.extra_dim])

        self.ax_array[1][1].set_xlabel(self.dim_labels[self.aligned_x_dim])
        self.ax_array[1][1].set_ylabel(self.dim_labels[self.extra_dim])
        self.ax_array[1][1].set_zlabel(self.dim_labels[self.aligned_y_dim])


    def plot(self, items, *args, **kwargs):
        """ add a set of 3-d elements to the plot. """

        self.ax_array[0][0].plot(items[self.aligned_x_dim,:],
                            items[self.aligned_y_dim,:], *args, **kwargs)
        
        self.ax_array[0][1].plot(items[self.extra_dim,:],
                            items[self.aligned_y_dim,:], *args, **kwargs)

        self.ax_array[1][0].plot(items[self.aligned_x_dim,:],
                            items[self.extra_dim,:], *args, **kwargs)

        self.ax_array[1][1].plot(items[self.aligned_x_dim,:],
                            items[self.extra_dim,:],
                            items[self.aligned_y_dim,:], *args, **kwargs)

    def setlim(self, dim, dmin, dmax):
        """ set the axis limits on all plots for the given data dimension """
        if dim == self.aligned_x_dim:
            self.ax_array[0][0].set_xlim(dmin, dmax)
            self.ax_array[1][0].set_xlim(dmin, dmax)
            self.ax_array[1][1].set_xlim3d(dmin, dmax)
        elif dim == self.aligned_y_dim:
            self.ax_array[0][0].set_ylim(dmin, dmax)
            self.ax_array[0][1].set_ylim(dmin, dmax)
            self.ax_array[1][1].set_zlim3d(dmin, dmax)
        else:
            self.ax_array[0][1].set_xlim(dmin, dmax)
            self.ax_array[1][0].set_ylim(dmin, dmax)
            self.ax_array[1][1].set_ylim3d(dmin, dmax)

    def invert_axis(self, dim):
        """ invert the display of the given data dimension """
        if dim == self.aligned_x_dim:
            self.ax_array[0][0].invert_xaxis()
            self.ax_array[1][0].invert_xaxis()
            self.ax_array[1][1].invert_xaxis()
        elif dim == self.aligned_y_dim:
            self.ax_array[0][0].invert_yaxis()
            self.ax_array[0][1].invert_yaxis()
            self.ax_array[1][1].invert_zaxis()
        else:
            self.ax_array[0][1].invert_xaxis()
            self.ax_array[1][0].invert_yaxis()
            self.ax_array[1][1].invert_yaxis()

