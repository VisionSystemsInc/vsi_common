# based on https://gist.github.com/tacaswell/3144287
# add scroll-based zooming to matplotlib plots
# usage: import mpl_zoom
import matplotlib.pyplot as plt


def zoom_factory(ax=None,base_scale=1.5):
    if ax is None: ax = plt.gca()

    def zoom_fun(event):
        # make this figure the current figure
        plt._figure(ax.get_figure().number)
        # push the current view to define home if stack is empty
        toolbar = ax.get_figure().canvas.toolbar # only set the home state
        if toolbar._views.empty():
            toolbar.push_current()

        # get the current x and y limits
        cur_xlim = ax.get_xlim()
        cur_ylim = ax.get_ylim()
        xdata = event.xdata # get event x location
        ydata = event.ydata # get event y location
        # hat tip to @giadang
        # Get distance from the cursor to the edge of the figure frame
        x_left = xdata - cur_xlim[0]
        x_right = cur_xlim[1] - xdata
        y_top = ydata - cur_ylim[0]
        y_bottom = cur_ylim[1] - ydata
        if event.button == 'up':
            # deal with zoom in
            scale_factor = 1/base_scale
        elif event.button == 'down':
            # deal with zoom out
            scale_factor = base_scale
        else:
            # deal with something that should never happen
            scale_factor = 1
            print event.button
        # set new limits
        ax.set_xlim([xdata - x_left*scale_factor,
                     xdata + x_right*scale_factor])
        ax.set_ylim([ydata - y_top*scale_factor,
                     ydata + y_bottom*scale_factor])

        # push the current view limits and position onto the stack
        # REVIEW perhaps this should participate in a drag_zoom like
        # matplotlib/backend_bases.py:NavigationToolbar2:drag_zoom()
        toolbar.push_current()

        ax.figure.canvas.draw() # force re-draw

    fig = ax.get_figure() # get the figure of interest
    # attach the call back
    fig.canvas.mpl_connect('scroll_event',zoom_fun)

    #return the function
    return zoom_fun


def figure_with_zoom(*args, **kwargs):
    # add zooming capabilities to figures
    f = plt._figure(*args, **kwargs)
    z = zoom_factory()
    return f
plt._figure = plt.figure
plt.figure = figure_with_zoom
