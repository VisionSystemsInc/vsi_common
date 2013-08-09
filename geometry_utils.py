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
    ray_lens = [np.sqrt(np.dot(r,r)) for r in rays]
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

def project_points(K, R, T, pts_3d):
    """ compute projection matrix from K,R,T and project pts_3d into image coordinates """
    P = np.dot( K, np.hstack((R, T.reshape(3, 1))) )  
    num_pts = len(pts_3d)
    # create 3xN matrix from set of 3d points
    pts_3d_m = np.array(pts_3d).transpose()
    # convert to homogeneous coordinates
    pts_3d_m_h = np.vstack((pts_3d_m, np.ones((1, num_pts))))
    pts_2d_m_h = np.dot(P, pts_3d_m_h)
    pts_2d = [ pts_2d_m_h[0:2,c] / pts_2d_m_h[2,c] for c in range(num_pts) ]
    return pts_2d

def create_K(focal_len, image_size):
    """ create calibration matrix K using the focal length and image.size
    Assumes 0 skew and principal point at center of image 
    Note that image_size = (width, height) """
    K = np.array([[focal_len, 0, image_size[0]/2.0], [0, focal_len, image_size[1]/2.0], [0, 0, 1]])
    return K


def spherical_to_euclidian(azimuth,elevation):
    """ convert az,el to euclidean vector 
    assumes: azimuth is measured in radians east of north
    assumes: Euclidean x-east y-north z-up coordinate system """
    x = np.sin(azimuth)*np.cos(elevation)
    y = np.cos(azimuth)*np.cos(elevation)
    z = np.sin(elevation)
    return (x,y,z)
    
def euclidian_to_spherical(x,y,z):
    """ convert a point in eucliean coordinate system to az, el
    assumes: azimuth is measured in radians east of north. 
    assumes: y-north, x-east z-up coordinate system """
    azimuth = np.arctan2(x,y)
    elevation = np.arcsin(z)
    return(azimuth,elevation)

