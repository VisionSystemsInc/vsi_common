""" Utility Functions for various geometric operations """
import numpy as np

def fit_plane_3d(x_vals, y_vals, z_vals):
    """ fit a plane to a set of 3-d points """

    num_pts = len(x_vals)
    P = np.zeros((4, num_pts))
    P[0, :] = x_vals - x_vals.mean()
    P[1, :] = y_vals - y_vals.mean()
    P[2, :] = z_vals - z_vals.mean()

    radius = np.sqrt((P[0:3, :] * P[0:3, :]).sum(0)).mean()
    P = P / radius
    P[3, :] = 1 
    
    A = np.dot(P, P.transpose())
    
    U, S, Vh = np.linalg.linalg.svd(A)
    V = Vh.conj().transpose()
    plane = V[:, -1]

    # normal is unit vector
    plane[0:3] = plane[0:3] / np.sqrt((plane[0:3]*plane[0:3]).sum())
    # TODO: un-normalize!!

    return plane

def backproject_points(K, R, T, pts_2d, depths):
    """ backproject a point given camera params, image position, and depth """
    invK = np.linalg.inv(K)
    cam_center = np.dot(-R.transpose(), T)
    KRinv = np.dot(R.transpose(), invK)

    rays = [np.dot(KRinv, [x[0], x[1], 1.0]) for x in pts_2d]
    ray_lens = [np.sqrt(r*r).sum() for r in rays]
    unit_rays = [ r / rlen for (r, rlen) in zip(rays, ray_lens)]

    pts_3d = [cam_center + ur*d for (ur, d) in zip(unit_rays, depths)]

    return pts_3d

