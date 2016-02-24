""" Utility Functions for various geometric operations """
import numpy as np
import re


#for testing validity of axis order arguments
axis_order_re = re.compile('[XYZ][XYZ][XYZ]')


def axis_order_is_valid(order):
    """ return true if the axis order has valid form, e.g. 'XYZ'
    """
    if not axis_order_re.match(order):
        return False
    # check for repeats
    if order[0] == order[1] or order[0] == order[2]:
        return False
    if order[1] == order[2]:
        return False
    return True


def fit_plane_3_points(points):
    """ compute the plane that passes through all 3 points in the list """
    # compute normal direction which is perpendicular to vectors p1-p0, p2-p0
    # use np.subtact instead of "-" operator so that points can be any array-like type
    norm = np.cross(np.subtract(points[1],points[0]), np.subtract(points[2],points[0]))
    norm_mag = np.sqrt(np.dot(norm,norm))
    if norm_mag == 0:
        # points are co-linear: plane is ill-defined
        return np.array((0,0,0,np.inf))
    norm /= norm_mag
    d = -np.dot(norm,points[0])  # any of the three points should give same answer here
    return np.array((norm[0], norm[1], norm[2], d))


def fit_plane_3d(points):
    """ fit a plane to a set of 3-d points """

    num_pts = len(points)
    P = np.zeros((4, num_pts))
    P[0:3,:] = np.array(points).T

    p_mean = P.mean(axis=1)
    P -= p_mean.reshape(4,1)

    #radius = np.sqrt((P[0:3, :] * P[0:3, :]).sum(axis=0)).mean()
    #P = P / radius

    P[3, :] = 1

    A = np.dot(P, P.transpose())
    _, _, Vh = np.linalg.linalg.svd(A)
    V = Vh.conj().transpose()
    plane = V[:, -1]

    # normal is unit vector
    norm_mag = np.sqrt((plane[0:3]*plane[0:3]).sum())
    # points are colinear (or worse) - plane is undefined
    if norm_mag == 0:
        return np.array((0,0,0,np.inf))

    plane = plane / norm_mag

    # move plane away from origin
    d = plane[3] - np.dot(plane,p_mean)
    plane[3] = d

    return plane


def fit_plane_3d_RANSAC(points, inlier_thresh=1.0, max_draws=100):
    """ fit a plane to a noisy set of points. returns the plane and the indices of inliers """
    num_pts_total = len(points)
    best_inliers = np.zeros(num_pts_total,np.bool)
    best_inlier_sum = 0
    points_homg_np = np.hstack((np.array(points), np.ones((num_pts_total,1))))
    for _ in range(max_draws):
        # randomly select 3 points from the set
        selection = np.random.randint(0,num_pts_total,3)
        points_rand = [points[s] for s in selection]
        # fit plane to random selection of points
        plane_rand = fit_plane_3_points(points_rand)
        # compute distances from all points to the plane
        dists = np.dot(points_homg_np, plane_rand)
        inliers = np.abs(dists) < inlier_thresh
        inlier_sum = inliers.sum()
        if inlier_sum > best_inlier_sum:
            best_inliers = inliers
            best_inlier_sum = inlier_sum
        # no need to keep going if all points are inliers
        if inlier_sum == num_pts_total:
            break
    # now re-fit using all inliers
    points_good = [points[n] for n in range(num_pts_total) if best_inliers[n]]
    plane = fit_plane_3d(points_good)

    return plane, best_inliers


def axis_angle_to_matrix(axis,theta):
    """ Convert a rotation axis / angle pair to a 3x3 rotation matrix """
    return quaternion_to_matrix(axis_angle_to_quaternion(axis,theta))


def axis_angle_to_quaternion(axis, theta):
    """ Convert a rotation axis / angle pair to a quaternion """
    # make sure axis has unit length
    axis_u = axis / np.linalg.norm(axis)
    sin_half = np.sin(theta/2.0)
    cos_half = np.cos(theta/2.0)
    q = np.array((sin_half, sin_half, sin_half, cos_half)) * np.append(axis_u,1.0)
    return q


def axis_from_string(axis_string):
    if axis_string == 'X':
        return np.array((1,0,0))
    elif axis_string == 'Y':
        return np.array((0,1,0))
    elif axis_string == 'Z':
        return np.array((0,0,1))
    else:
        raise Exception('Expecting one of [X,Y,Z], got ' + axis_string)


def Euler_angles_to_quaternion(theta1, theta2, theta3, order='XYZ'):
    """ default order applies rotation around x axis first, y second, and z third.
    """
    if not axis_order_is_valid(order):
        raise Exception('Invalid order string: ' + str(order))

    e1 = axis_from_string(order[0])
    e2 = axis_from_string(order[1])
    e3 = axis_from_string(order[2])

    q1 = np.append(e1 * np.sin(theta1/2.0), np.cos(theta1/2.0))
    q2 = np.append(e2 * np.sin(theta2/2.0), np.cos(theta2/2.0))
    q3 = np.append(e3 * np.sin(theta3/2.0), np.cos(theta3/2.0))

    return compose_quaternions((q1,q2,q3))


def quaternion_to_Euler_angles(q, order='XYZ'):
    """ convert q to Euler angles
        angles are returned in the order of application, specified by order
        adapted and generalized based on code available at the following url:
        http://bediyap.com/programming/convert-quaternion-to-euler-rotations/
    """
    if not axis_order_is_valid(order):
        raise Exception('Invalid order string: ' + str(order))
    p0 = q[3]  # real component
    p1 = q[0]
    if order[0] == 'Y':
        p1 = q[1]
    elif order[0] == 'Z':
        p1 = q[2]
    p2 = q[1]
    if order[1] == 'X':
        p2 = q[0]
    elif order[1] == 'Z':
        p2 = q[2]
    p3 = q[2]
    if order[2] == 'X':
        p3 = q[0]
    elif order[2] == 'Y':
        p3 = q[1]

    e1 = axis_from_string(order[0])
    e2 = axis_from_string(order[1])
    e3 = axis_from_string(order[2])

    e = np.sign(np.dot(np.cross(e3,e2),e1))

    theta1 = np.arctan2(e*2*(p2*p3 + e*p0*p1), p0*p0 - p1*p1 - p2*p2 + p3*p3)
    theta2 = np.arcsin(-e*2*(p1*p3 - e*p0*p2))
    theta3 = np.arctan2(e*2*(p1*p2 + e*p0*p3), p0*p0 + p1*p1 - p2*p2 - p3*p3)

    return theta1, theta2, theta3


def quaternion_to_matrix(q):
    """ Convert a quaternion to an orthogonal rotation matrix """
    # normalize quaternion
    norm = np.sqrt((q*q).sum())
    q /= norm
    # fill in rotation matrix
    R = np.zeros((3, 3))

    # save as a,b,c,d for easier reading of conversion math
    x = q[0]
    y = q[1]
    z = q[2]
    w = q[3]

    R[0,0] = 1 - 2*y*y - 2*z*z
    R[0,1] = 2*x*y - 2*z*w
    R[0,2] = 2*x*z + 2*y*w

    R[1,0] = 2*x*y + 2*z*w
    R[1,1] = 1 - 2*x*x - 2*z*z
    R[1,2] = 2*y*z - 2*x*w

    R[2,0] = 2*x*z - 2*y*w
    R[2,1] = 2*y*z + 2*x*w
    R[2,2] = 1 - 2*x*x - 2*y*y

    return R


def matrix_to_quaternion(rot):
    """ convert rotation matrix rot to quaternion
        Adapted from vnl_quaternion.txx in vxl
    """
    d0 = rot[0,0]
    d1 = rot[1,1]
    d2 = rot[2,2]
    xx = 1.0 + d0 - d1 - d2
    yy = 1.0 - d0 + d1 - d2
    zz = 1.0 - d0 - d1 + d2
    rr = 1.0 + d0 + d1 + d2

    vals = (xx,yy,zz,rr)
    imax = np.argmax(np.abs(vals))

    q_re = 0
    q_im = [0,0,0]

    if 3 == imax:
        r4 = np.sqrt(rr)*2
        q_re = r4 / 4
        ir4 = 1.0 / r4
        q_im[0] = (rot[2,1] - rot[1,2]) * ir4
        q_im[1] = (rot[0,2] - rot[2,0]) * ir4
        q_im[2] = (rot[1,0] - rot[0,1]) * ir4

    elif 0 == imax:
        x4 = np.sqrt(xx)*2
        q_im[0] = x4 / 4
        ix4 = 1.0 / x4
        q_im[1] = (rot[1,0] + rot[0,1]) * ix4
        q_im[2] = (rot[2,0] + rot[0,2]) * ix4
        q_re = (rot[2,1] - rot[1,2]) * ix4

    elif 1 == imax:
        y4 = np.sqrt(yy)*2
        q_im[1] = y4 / 4
        iy4 = 1.0 / y4
        q_im[0] = (rot[1,0] + rot[0,1]) * iy4
        q_im[2] = (rot[2,1] + rot[1,2]) * iy4
        q_re = (rot[0,2] - rot[2,0]) * iy4

    elif 2 == imax:
        z4 = np.sqrt(zz)*2
        q_im[2] = z4 / 4
        iz4 = 1.0 / z4
        q_im[0] = (rot[2,0] + rot[0,2]) * iz4
        q_im[1] = (rot[2,1] + rot[1,2]) * iz4
        q_re = (rot[1,0] - rot[0,1]) * iz4

    return np.array((q_im[0], q_im[1], q_im[2], q_re))


def compose_quaternions(quaternion_list):
    """ return the composition of a list of quaternions
    """
    qtotal = np.array((0,0,0,1))
    for q in quaternion_list:
        q1 = qtotal
        q2 = q
        re = q1[3]*q2[3] - np.dot(q1[0:3],q2[0:3])
        imag = np.cross(q1[0:3],q2[0:3]) + q2[0:3]*q1[3] + q1[0:3]*q2[3]
        qtotal = np.array((imag[0], imag[1], imag[2], re))
    return qtotal


def Euler_angles_to_matrix(theta1, theta2, theta3, order='XYZ'):
    """ Convert Euler angles to a rotation matrix. Angles are specified in the order of application.
    """
    return quaternion_to_matrix(Euler_angles_to_quaternion(theta1, theta2, theta3, order=order))


def matrix_to_Euler_angles(M, order='XYZ'):
    """ Convert a rotation matrix to Euler angles. Angles are returned in the order of application.
    """
    return quaternion_to_Euler_angles(matrix_to_quaternion(M),order=order)


def rotate_vector(v, axis, angle):
    """ rotate the vector v around axis by angle radians """
    R = axis_angle_to_matrix(axis,angle)
    return np.dot(R,v)


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


def patch_corners_3d(c, xv, yv):
    """ given a centroid and "x" and "y" vectors, return the four corners """
    return [c-xv-yv, c-xv+yv, c+xv+yv, c+xv-yv]


def unitize(v):
    """ return the unit vector in the same direction as v """
    return v / np.sqrt(np.dot(v,v))


def nonhomogeneous(pt_homg):
    """ convert from homogeneous coordinates to non-homogenous """
    tolerance = 1e-6
    if abs(pt_homg[-1]) < tolerance:
        raise Exception('Cannot convert ideal point to non-homogenous coordinates')
    return pt_homg[0:-1] / pt_homg[-1]


def intersect_plane_ray(plane, ray_origin, ray_vector):
    """ Compute and return the intersection point of a plane and ray.
        plane: The parameters (a,b,c,d) of the plane,  ax + by + cz + d = 0
        ray_origin and ray_vector can be 3-d vectors or 4-d homogeneous.
    """
    # convert to homogeneous coordinates
    ray_origin_h = ray_origin
    if len(ray_origin_h) == 3:
        ray_origin_h = np.append(ray_origin,1)
    ray_vector_h = ray_vector
    if len(ray_vector_h) == 3:
        ray_vector_h = np.append(ray_vector,0)

    dist = -np.dot(plane,ray_origin_h) / np.dot(plane,ray_vector_h)

    return ray_origin + dist * ray_vector


def rasterize_plane(grid_origin, grid_dims, vox_len, plane):
    """ Visit each cell of a 3-d grid that intersects the plane.
    grid_origin: 3-D position of voxel grid origin point (ox, oy, oz)
    grid_dims: number of voxels in x,y,z dimensions.  (nx, ny, nz)
    vox_len: The side length of a single voxel (voxels assumed to be cubes)
    plane: The parameters (a,b,c,d) of the plane.  ax + by + cz + d = 0
    """

    #plane = plane / np.sqrt(np.sum(plane[0:3] * plane[0:3]))
    # get dimensions of normal in ascending order
    sorted_dims = np.argsort(np.abs(plane[0:3]))
    d0 = sorted_dims[0]
    d1 = sorted_dims[1]
    d2 = sorted_dims[2]

    for i in range(grid_dims[d0]):
        # rasterize a line in the [d1,d2] plane
        d0_val = grid_origin[d0] + vox_len * i
        for j in range(grid_dims[d1]):
            d1_val = grid_origin[d1] + vox_len * j
            d2_val = -(plane[d0]*d0_val + plane[d1]*d1_val + plane[3]) / plane[d2]
            k = np.int(np.floor((d2_val - grid_origin[d2])/vox_len))
            #if (k >= 0) and (k < grid_dims[d2]):
            if 0 <= k < grid_dims[d2]:
                p = [0,0,0]
                p[d0] = i
                p[d1] = j
                p[d2] = k
                yield p


class AxisAlignedBox(object):
    """  an N-D axis-aligned box """

    def __init__(self, min_pt, max_pt):
        """ constructor """
        self.min_pt = np.array(min_pt)
        self.max_pt = np.array(max_pt)
        # make sure max_pt >= min_pt in all dimensions
        invalid = self.max_pt < self.min_pt
        self.max_pt[invalid] = self.min_pt[invalid]

    def area(self):
        """ area of the 2d box """
        diff = self.max_pt - self.min_pt
        if any(diff <= 0):
            return 0
        return np.prod(diff)

    def centroid(self):
        """ centroid of 2d box """
        return np.mean((self.min_pt, self.max_pt), axis=0)

    def dims(self):
        """ dimensions of the box """
        return self.max_pt - self.min_pt

    def __str__(self):
        """ return human-readable string representation """
        return 'Box2D: (' + str(self.min_pt) + ', ' + str(self.max_pt) + ')'

    def __repr__(self):
        """ return string representation """
        return '%s(%s, %s)' % (self.__class__, self.min_pt, self.max_pt)


class Box2D(AxisAlignedBox):
    """ an 2-D axis-aligned bounding box """

    def __str__(self):
        """ return human-readable string representation """
        return 'Box2D: (' + str(self.min_pt) + ', ' + str(self.max_pt) + ')'

    def __repr__(self):
        """ return string representation """
        return '%s(%s, %s)' % (self.__class__, self.min_pt, self.max_pt)


def intersection(box0, box1):
    """ intersection of two bounding boxes """
    if box0 is None or box1 is None:
        return None
    min_pt = np.max((box0.min_pt, box1.min_pt), axis=0)
    max_pt = np.min((box0.max_pt, box1.max_pt), axis=0)
    return Box2D(min_pt, max_pt)


def union(box0, box1):
    """ union of two bounding boxes """
    if box0 is None:
        return box1
    if box1 is None:
        return box0
    min_pt = np.min((box0.min_pt, box1.min_pt), axis=0)
    max_pt = np.max((box0.max_pt, box1.max_pt), axis=0)
    return Box2D(min_pt, max_pt)


def compute_bounding_box(pts):
    """ compute the bounding box of a list of points
        returns (min_pt, max_pt)
    """
    if len(pts) == 0:
        return None

    min_pt = pts[0]
    max_pt = pts[0]
    for p in pts:
        min_pt = np.min(np.vstack((p,min_pt)),axis=0)
        max_pt = np.max(np.vstack((p,max_pt)),axis=0)
    return (min_pt, max_pt)


def compute_transform_3d_plane_to_2d(plane_origin, plane_x, plane_y, nx, ny):
    """ compute a 3x3 perspective transform from a planar segment in 3-d to a 2-d image.
        plane_origin: the 3-d point corresponding to the upper left of the image
        plane_x: a 3-d vector that spans the image "x" direction
        plane_y: a 3-d vector that spans the image "y" direction (assumed perpendicular to plane_x)
        nx: number of pixels in the image x dimension
        ny: number of pixels in the image y dimension
    """
    plane_xlen = np.sqrt(np.dot(plane_x, plane_x))
    plane_ylen = np.sqrt(np.dot(plane_y, plane_y))
    plane_xu = plane_x / plane_xlen
    plane_yu = plane_y / plane_ylen
    plane_normal = np.cross(plane_xu, plane_yu)
    plane_R = np.vstack((plane_xu, plane_yu, plane_normal))
    plane_T = -np.dot(plane_R.transpose(),plane_origin)

    plane2img = np.array(((nx/plane_xlen, 0, 0),(0, ny/plane_ylen, 0),(0, 0, 0)))

    xform = np.dot(plane2img, np.hstack((plane_R, plane_T.reshape(3,1))))
    return xform


def sample_unit_sphere(N):
    """ generate a set of points distributed on the unit sphere """
    dlong = np.pi*(3-np.sqrt(5))
    dz = 2.0/N
    lon = 0
    z = 1 - dz/2
    points = []
    for _ in range(N):
        r = np.sqrt(1-z*z)
        points.append(np.array((np.cos(lon)*r, np.sin(lon)*r, z)))
        z = z - dz
        lon = lon + dlong
    return points


def stack_RT(R,T):
    """ convert a 3x3 rotation / 3x1 translation combination
        to a 4x4 homogeneous transform [R T; 0 0 0 1]
    """
    return np.vstack((np.hstack((R,T.reshape(3,1))), np.array((0,0,0,1))))


def similarity_transform(scale, translation):
    """ Compute a similarity transform matrix.
        Dimensionality determined from length of translation vector
    """
    D = len(translation.squeeze())
    S = np.zeros((D+1,D+1))
    np.fill_diagonal(S,scale)
    S[D,D] = 1
    S[0:D,D] = translation.reshape((D,))
    return S


def volume_corners(vol_origin, vol_extent):
    """ return the 8 corners of the axis-aligned volume defined by origin and extent
    """
    corners = []
    for zi in (0,1):
        for yi in (0,1):
            for xi in (0,1):
                corners.append(vol_origin + vol_extent*np.array((xi,yi,zi)))
    return corners


def compute_2D_affine_xform(from_points, to_points):
    """ find H such that:
    to_points = H * from_points, H is of form [a b c; d e f; 0 0 1]
    """
    from_points_M = np.vstack((np.array(from_points).T, np.ones(len(from_points))))
    to_points_M = np.vstack((np.array(to_points).T, np.ones(len(to_points))))

    if from_points_M.shape != to_points_M.shape:
        raise Exception('number of points do not match')

    #condition points
    m = np.mean(from_points_M, axis=1)
    maxstd = np.max(np.std(from_points_M, axis=1))
    C1 = np.diag([1/maxstd, 1/maxstd, 1])
    C1[0:2, 2] = -m[0:2]/maxstd
    fp_cond = np.dot(C1,from_points_M)

    #-to points-
    m = np.mean(to_points_M, axis=1)
    C2 = C1.copy()  # must use same scaling for both point sets
    C2[0:2, 2] = -m[0:2]/maxstd
    tp_cond = np.dot(C2,to_points_M)

    #conditioned points have mean zero, so translation is zero
    A = np.concatenate((fp_cond[:2],tp_cond[:2]), axis=0)
    U,S,V = np.linalg.svd(A.T)

    #create B and C matrices as Hartley-Zisserman (2nd ed) p 130.
    tmp = V[:2].T
    B = tmp[:2]
    C = tmp[2:4]

    tmp2 = np.concatenate((np.dot(C,np.linalg.pinv(B)),np.zeros((2,1))), axis=1)
    H = np.vstack((tmp2,[0,0,1]))

    #decondition
    H = np.dot(np.linalg.inv(C2),np.dot(H,C1))

    return H / H[2,2]
