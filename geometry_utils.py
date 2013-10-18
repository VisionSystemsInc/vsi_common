""" Utility Functions for various geometric operations """
import numpy as np


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


def quaternion_to_matrix(q):
    """ Convert a quaternion to an orthogonal rotation matrix """
    # normalize quaternion
    norm = np.sqrt((q*q).sum())
    q /= norm
    # fill in rotation matrix
    R = np.zeros((3, 3))

    # save as a,b,c,d for easier reading of conversion math
    a = q[0]
    b = q[1]
    c = q[2]
    d = q[3]

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


def rectify_calibrated(camera0, camera1, look_pt, image0_shape, image1_shape, max_dim):
    """ compute epipolar rectification homographies
    """
    plane_x = camera1.center - camera0.center
    plane_x /= np.linalg.norm(plane_x)
    plane_y = np.cross(plane_x, (camera0.center + camera1.center)/2 - look_pt)
    plane_y /= np.linalg.norm(plane_y)

    H0 = camera0.image2plane(look_pt, plane_x, plane_y)
    H1 = camera1.image2plane(look_pt, plane_x, plane_y)

    corners0 = [np.array((0,0)), np.array((0,image0_shape[0])), np.array((image0_shape[1], image0_shape[0])), np.array((image0_shape[1],0))]
    corners0 = np.vstack((np.array(corners0).T, np.ones((1,4))))
    corners1 = [np.array((0,0)), np.array((0,image1_shape[0])), np.array((image1_shape[1], image1_shape[0])), np.array((image1_shape[1],0))]
    corners1 = np.vstack((np.array(corners1).T, np.ones((1,4))))
    corners_plane0 = np.dot(H0, corners0)
    corners_plane0 = corners_plane0[0:2,:] / corners_plane0[2,:]
    corners_plane1 = np.dot(H1, corners1)
    corners_plane1 = corners_plane1[0:2,:] / corners_plane1[2,:]

    projected_min0 = corners_plane0.min(axis=1)
    projected_max0 = corners_plane0.max(axis=1)
    projected_min1 = corners_plane1.min(axis=1)
    projected_max1 = corners_plane1.max(axis=1)

    max_projected_x = max(projected_max0[0] - projected_min0[0], projected_max1[0] - projected_min1[0])
    projected_y = max(projected_max0[1], projected_max1[1]) - min(projected_min0[1], projected_min1[1])
    scale = max_dim / max(max_projected_x, projected_y)

    ty = -min(projected_min0[1], projected_min1[1]) * scale
    tx0 = -projected_min0[0] * scale
    tx1 = -projected_min1[0] * scale

    H0final = np.dot(similarity_transform(scale, np.array((tx0, ty))), H0)
    H1final = np.dot(similarity_transform(scale, np.array((tx1, ty))), H1)
    output_shape = (np.array((projected_y, max_projected_x)) * scale).astype(np.int)

    return H0final, H1final, output_shape





