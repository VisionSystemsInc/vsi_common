""" A set of utility functions related to plotting
"""
import matplotlib as mpl
import matplotlib.cm
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from mpl_toolkits.axes_grid1 import make_axes_locatable
import numpy as np

def lblshow(label_img, labels_str, f=None, cmap=None, *args, **kwargs):
    ''' display a labeled image with associated legend

	Parameters
	----------
	label_img : labeled image [nrows, ncols] = numpy.array.shape
	labels_str : a list of labels
    f : (optional) a figure handle
    cmap : the color of each label (optional). like a list of colors, e.g.,
            ['Red','Green',...] or a matplotlib.colors.ListedColormap)
    '''

    f,ax = plt.subplots(1,1) if f is None else (f, f.gca())

    nlabels = len(labels_str)
    if type(cmap) is mpl.colors.ListedColormap:
        pass
    elif hasattr(cmap, '__iter__'):
        if not kwargs.has_key('norm'):
            bounds = range(0,len(cmap)+1)
            kwargs['norm'] = mpl.colors.BoundaryNorm(bounds, len(cmap)) # HACKY
        cmap = mpl.colors.ListedColormap(cmap)
    elif cmap is None:
        colors = mpl.cm.spectral(np.linspace(0, 1, nlabels))
        cmap = mpl.colors.ListedColormap(colors)
    else:
        assert False, 'invalid color map'


    im = ax.imshow(label_img, cmap=cmap, *args, **kwargs); ax.axis('off')

    # create an axes on the right side of ax. The width of cax will be 5%
    # of ax and the padding between cax and ax will be fixed at 0.05 inch.
    divider = make_axes_locatable(ax)
    cax = divider.append_axes("right", size="5%", pad=0.05)
    cbar = plt.colorbar(im, cax=cax)

    cbar.ax.get_yaxis().set_ticks([])
    for j, lab in enumerate(labels_str):
        cbar.ax.text(1.3, float(2 * j + 1) / (nlabels*2), lab, ha='left', va='center')

    return f
        
def imshow(X, *args, **kwargs):
    """ modify the coordinate formatter to report the image "z"
        from http://matplotlib.org/examples/api/image_zcoord.html
    """
    
    fig, ax = plt.subplots()
    ax.imshow(X, *args, **kwargs)

    numrows, numcols = X.shape[0:2]
    def format_coord(x, y):
        col = int(x+0.5)
        row = int(y+0.5)
        if col>=0 and col<numcols and row>=0 and row<numrows:
            z = X[row,col]
            return 'x=%1.4f, y=%1.4f, z=%s'%(x, y, repr(z.tolist()))
        else:
            return 'x=%1.4f, y=%1.4f'%(x, y)

    ax.format_coord = format_coord
    plt.show()
    
def plot_vector(x, axis, axis_order, *args, **kwargs):
    """ conveniance method for plotting 2 or 3-d data stored in numpy array """

    if len(x.shape) == 1:
        x = x.reshape((x.shape[0],1))

    if x.shape[0] == 2:
        axis.plot(x[axis_order[0],:], x[axis_order[1],:], *args, **kwargs)
    else:
        axis.plot(x[axis_order[0],:], x[axis_order[1],:], x[axis_order[2],:], *args, **kwargs)


def plot_rectangle(x, y, width, height, *args, **kwargs):
    """ plot a 2-d box """
    xvec = [x, x+width, x+width, x, x]
    yvec = [y, y, y+height, y+height, y]
    plt.plot(xvec, yvec, *args, **kwargs)

def plot_cube(x, y, z, width, height, depth, *args, **kwargs):
    # TODO
    pass

def plot_camera(cam, img_dims=(1280,720), axis=None, axis_order=(0,1,2), img_plane_depth=1.0):
    """ plot a 3-d representation of a perspective camera with image plane """
    if axis == None:
        axis = plt.gca()
    # plot camera center
    #axis.plot((cam.center[ao[0]],),(cam.center[ao[1]],),(cam.center[ao[2]],),'b.',markersize=10)
    plot_vector(cam.center, axis, axis_order, 'b.', markersize=10 )
    # compute backprojected corners of image plane
    img_corners = (np.array((0,0)), np.array((img_dims[0],0)),
                   np.array((img_dims[0],img_dims[1])), np.array((0,img_dims[1])))
    corners_3d = cam.backproject_points(img_corners, [img_plane_depth,]*4)
    c3d_np = np.array(corners_3d).T
    c3d_np = np.hstack((c3d_np, c3d_np[:,0:1]))
    # plot the image plane
    #axis.plot(c3d_np[ao[0],:], c3d_np[ao[1],:], c3d_np[ao[2],:],'k-')
    plot_vector(c3d_np, axis, axis_order, 'k-')
    # plot connecting lines from the center to the image plane
    for x in corners_3d:
        plot_vector(np.array((cam.center, x)).T, axis, axis_order, 'k-') 


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

