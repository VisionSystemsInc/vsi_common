""" Utility classes for modeling cameras """
import numpy as np


def construct_K(focal_len, image_size):
    """ create calibration matrix K using the focal length and image.size
    Assumes 0 skew and principal point at center of image
    Note that image_size = (width, height) """
    K = np.array([[focal_len, 0, image_size[0]/2.0], [0, focal_len, image_size[1]/2.0], [0, 0, 1]])
    return K


class PinholeCamera:
    """ Models a pinhole camera, i.e. one with a single center of projection and no lens distortion """
    def __init__(self, K, R, T):
        self.K = K
        self.R = R
        self.T = T
        # compute projection matrix
        self.P = np.dot( K, np.hstack((R, T.reshape(3, 1))) )
        # compute and store camera center
        self.center = np.dot(-R.transpose(), T)
        # compute inverse projection matrix for backprojection
        invK = np.linalg.inv(K)
        self.KRinv = np.dot(R.transpose(), invK)

    def backproject_points(self, pts_2d, depths):
        """ backproject a point given camera params, image position, and depth """
        rays = [np.dot(self.KRinv, [x[0], x[1], 1.0]) for x in pts_2d]
        ray_lens = [np.sqrt(np.dot(r, r)) for r in rays]
        unit_rays = [r / rlen for (r, rlen) in zip(rays, ray_lens)]

        pts_3d = [self.center + ur * d for (ur, d) in zip(unit_rays, depths)]

        return pts_3d

    def project_points(self, pts_3d):
        """ compute projection matrix from K,R,T and project pts_3d into image coordinates """
        num_pts = len(pts_3d)
        # create 3xN matrix from set of 3d points
        pts_3d_m = np.array(pts_3d).transpose()
        # convert to homogeneous coordinates
        pts_3d_m_h = np.vstack((pts_3d_m, np.ones((1, num_pts))))
        pts_2d_m_h = np.dot(self.P, pts_3d_m_h)
        pts_2d = [pts_2d_m_h[0:2, c] / pts_2d_m_h[2, c] for c in range(num_pts)]
        return pts_2d

