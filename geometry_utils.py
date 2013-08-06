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

def quaternion_to_matrix(q):
    """ Convert a quaternion to an orthogonal rotation matrix """
    # normalize quaternion
    norm = np.sqrt((q*q).sum())
    q /= norm
    # fill in rotation matrix
    R = np.zeros((3, 3))

    # save as a,b,c,d for easier reading of conversion math
    a = q[0]; b = q[1]; c = q[2]; d = q[3]

    R[0,0] = a*a + b*b - c*c - d*d
    R[0,1] = 2*b*c - 2*a*d
    R[0,2] = 2*b*d + 2*a*c

    R[1,0] = 2*b*c + 2*a*d
    R[1,1] = a*a - b*b + c*c - d*d
    R[1,2] = 2*c*d - 2*a*b

    R[2,0] = 2*b*d - 2*a*c
    R[2,1] = 2*c*d + 2*a*b
    R[2,2] = a*a - b*b - c*c + d*d

    return R



