#!/usr/bin/env python
""" record point correspondences """
import matplotlib.pyplot as plt
import numpy as np
import io_utils
import glob
import argparse
import os.path


class CorrClicker:
    """ keep track for correspondences """

    def __init__(self, img_filenames):
        """ constructor """
        if len(img_filenames) == 0:
            raise Exception('At least one image file needed')
        self.img_filenames = img_filenames
        self.points = [[] for _ in range(len(img_filenames))]
        self.fig = plt.figure()
        self.ax = self.fig.add_subplot(111)
        self.click_cid = self.fig.canvas.mpl_connect('button_press_event', self.onclick)
        self.key_cid = self.fig.canvas.mpl_connect('key_press_event', self.onkey)
        self.img_idx = None
        self.pt_idx = None

    def onkey(self, event):
        """ handle keyboard event """
        if event.key == 'left' and self.img_idx > 0:
            self.img_idx -= 1
        elif event.key == 'right' and self.img_idx < len(self.img_filenames) - 1:
            self.img_idx += 1
        elif event.key == 'down' and self.pt_idx is not None and self.pt_idx > 0:
            self.pt_idx -= 1
        elif event.key == 'up' and self.pt_idx is not None and self.pt_idx < len(self.points[0]) - 1:
            self.pt_idx += 1
        elif event.key == '+':
            self.pt_idx = -1
        elif event.key == 'q':
            plt.close(self.fig)
            return
        else:
            print("you pressed " + event.key)

        self.choose_corr()

    def onclick(self, event):
        """ handle mouse click """
        if self.pt_idx is not None:
            if event.button == 1:
                pt = np.array((event.xdata, event.ydata))
                self.points[self.img_idx][self.pt_idx] = pt 
            elif event.button == 2:
                print("left click to select point, right click for none")
            elif event.button == 3:
                self.points[self.img_idx][self.pt_idx] = None
            else:
                print('unrecognized button id ' + str(event.button))
            self.choose_corr()


    def write_corrs(self, filename):
        """ save the corresppondences out to file """
        try:
            fd = open(filename,'w')
        except IOError:
            print('Error opening file ' + filename)
            return

        num_imgs = len(self.points)
        num_pts = len(self.points[0])

        fd.write('%d\n' % num_imgs)
        fd.write('%d\n\n' % num_pts)

        for img_pts in self.points:
            for pt in img_pts:
                if pt is None:
                    fd.write('-1.0 -1.0')
                else:
                    fd.write(str(pt[0]) + ' ' + str(pt[1]))
                fd.write('\n')
            fd.write('\n')
        fd.close()

    def draw(self):
        """ draw the correct image and point location """
        img = io_utils.imread(self.img_filenames[self.img_idx])
        self.ax.clear()
        self.ax.imshow(img)
        self.ax.set_title('Image ' + str(self.img_idx) + ', Point ' + str(self.pt_idx))
        if self.pt_idx is not None:
            curr_pt = self.points[self.img_idx][self.pt_idx]
            if curr_pt is not None:
                self.ax.plot(curr_pt[0], curr_pt[1], 'ro')
        plt.axis('image')
        plt.draw()

    def choose_corr(self):
        """ choose a corresponence point """
        if self.pt_idx is not None and self.pt_idx < 0:
            self.pt_idx = len(self.points[0])
            for img_pts in self.points:
                img_pts.append(None)
        self.draw()

        print('Image ' + str(self.img_idx) + ' Point ' + str(self.pt_idx) + '? (left click to select, right click for none)')

    def start(self):
        """ startup the clicker UI. blocks until figure is closed """
        self.img_idx = 0
        if len(self.points[0]) > 0:
            self.pt_idx = 0
        else:
            self.pt_idx = None
        self.draw()
        plt.show()
        #self.choose_corr()


def read_corrs(filename):
    """ read the corresppondences from a file """
    with open(filename,'r') as fd:

        tokgen = io_utils.read_token(fd, ignore_char='#')

        num_images = int(next(tokgen))
        num_points = int(next(tokgen))
        print(str(num_images) + ' images')
        print(str(num_points) + ' points')
            
        points = [[] for _ in range(num_images)]
        for i in range(num_images):
            img_pts = []
            for _ in range(num_points):
                x = float(next(tokgen))
                y = float(next(tokgen))
                img_pts.append(np.array((x,y)))
            points[i] = img_pts

        return points


def main():
    """ main method """
    parser = argparse.ArgumentParser(description='Simple Image Correspondence Clicker Application')
    parser.add_argument('image_glob', help='Input image filenames (glob form, use quotes to avoid shell expansion)')
    parser.add_argument('output_filename', help='Output filename')
    args = parser.parse_args()

    img_glob = os.path.expandvars(os.path.expanduser(args.image_glob))
    img_fnames = glob.glob(img_glob)
    img_fnames.sort()

    corr_fname = args.output_filename

    clicker = CorrClicker(img_fnames)
    # load up existing corresponences if file exists
    if os.path.exists(corr_fname):
        points = read_corrs(corr_fname)
        if len(points) != len(img_fnames):
            raise Exception('Expecting %d images in %s, found %d' % (len(points),corr_fname,len(img_fnames)))
        clicker.points = points
    # this will block until clicker is quit
    clicker.start()

    print('choose_corr returned.')
    answer = None
    while not answer in ('y','n'):
        answer = raw_input('Save Corrs? (y/n): ')
    if answer == 'y':
        print('Saving corrs to ' + corr_fname)
        clicker.write_corrs(corr_fname)

if __name__ == "__main__":
    main()

