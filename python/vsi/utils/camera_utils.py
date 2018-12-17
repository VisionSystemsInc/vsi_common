""" Utility classes for modeling cameras """
import numpy as np
import vsi.utils.geometry_utils as geometry_utils


def construct_K(image_size, focal_len=None, fov_degrees=None, fov_radians=None):
  """ Create calibration matrix K using the image size and focal length or
      field of view angle.

      Parameters
      ----------
      image_size : array_like
          The Image Size. Note that image_size = (width, height)
      focal_len : float
          The Focal Length
      fov_degrees : float
          The Field of View Angle in Degrees
      fov_radians : float
          The Field of View Angle in Radians

      Raises
      ------
      Exception
        Specify exactly one of [focal_len, fov_degrees, fov_radians]

      Assumes 0 skew and principal point at center of image

      Notes
      -----
      The fov is assumed to be measured horizontally
  """
  if not np.sum([focal_len is not None, fov_degrees is not None, fov_radians is not None]) == 1:
    raise Exception('Specify exactly one of [focal_len, fov_degrees, fov_radians]')

  if fov_degrees is not None:
    fov_radians = np.deg2rad(fov_degrees)
  if fov_radians is not None:
    focal_len = image_size[0] / (2.0 * np.tan(fov_radians/2.0))

  K = np.array([[focal_len, 0, image_size[0]/2.0], [0, focal_len, image_size[1]/2.0], [0, 0, 1]])
  return K


class ProjectiveCamera(object):
  """ Models a general projective camera with a 3x4 projection matrix """
  def __init__(self,P):
    self.P = P
    # normalize s.t. P[3,4] = 1
    if abs(self.P[2,3]) > 1e-6:
      self.P /= self.P[2,3]

  def as_P(self, fd):
    """ write the projection matrix to an ascii text file

        Parameters
        ----------
        fd : file_like
          The output file
  """
    # write 3x4 projection matrix
    for row in self.P:
      fd.write('%f %f %f %f\n' % (row[0],row[1],row[2],row[3]))

  def saveas_P(self, filename):
    """ write the projection matrix to an ascii text file

        Parameters
        ----------
        filename : str
            The File Name of the Projection Matrix
    """
    with open(filename, 'w') as fd:
      self.as_P(fd)

  def project_points(self, pts_3d):
    """ project pts_3d into image coordinates

        Parameters
        ----------
        pts_3d : array_like
            The 3D Points. Shape = N x 3.

        Returns
        -------
        numpy.array
            A 2 Dimensional array of coordinates.
    """
    num_pts = len(pts_3d)
    # create 3xN matrix from set of 3d points
    pts_3d_m = np.array(pts_3d).transpose()
    # convert to homogeneous coordinates
    pts_3d_m_h = np.vstack((pts_3d_m, np.ones((1, num_pts))))
    pts_2d_m_h = np.dot(self.P, pts_3d_m_h)
    #pts_2d = [pts_2d_m_h[0:2, c] / pts_2d_m_h[2, c] for c in range(num_pts)]
    pts_2d = [col[0:2] / col[2] for col in pts_2d_m_h.transpose()]
    return pts_2d

  def project_point(self, pt_3d):
    """ convenience wrapper around project_points

        Parameters
        ----------
        pt_3d : array_like
            The 3D Point

        Returns
        -------
        numpy.array
            The First Point
    """
    pts = self.project_points((pt_3d,))
    return pts[0]

  def project_vectors(self, vecs_3d):
    """ compute projection matrix from K,R,T and project vecs_3d into image
        coordinates

        Parameters
        ----------
        vecs_3d : array_like
            The 3D Vectors

        Returns
        -------
        numpy.array
            Two Dimensional Vectors
    """
    num_vecs = len(vecs_3d)
    # create 3xN matrix from set of 3d vectors
    vecs_3d_m = np.array(vecs_3d).transpose()
    # convert to homogeneous coordinates
    vecs_3d_m_h = np.vstack((vecs_3d_m, np.zeros((1, num_vecs))))
    vecs_2d_m_h = np.dot(self.P, vecs_3d_m_h)
    #vecs_2d = [vecs_2d_m_h[0:2, c] / vecs_2d_m_h[2, c] for c in range(num_vecs)]
    vecs_2d = [col[0:2] / col[2] for col in vecs_2d_m_h.transpose()]
    return vecs_2d

  def project_vector(self, vecs_3d):
    """ convenience wrapper around project_vectors
        Parameters
        ----------
        vecs_3d : array_like
            The 3D Vectors

        Returns
        -------
        array_like
            The First Point
    """
    pts = self.project_vectors((vecs_3d,))
    return pts[0]

  def backproject_point_plane(self, pt_2d, plane, return_homogeneous=False):
    """ backproject a point onto a 3-d plane

        Parameters
        ----------
        pt_2d : array_like
            Two Dimensional Point
        plane : array_like
            The 3-D Plane
        return_homogeneous : bool
            If True it returns a homogenous point

        Returns
        -------
        array_like
            The Point
    """
    A = np.zeros((3,4))
    A[0,:] = self.P[0,:] - self.P[2,:]*pt_2d[0]
    A[1,:] = self.P[1,:] - self.P[2,:]*pt_2d[1]
    A[2,:] = plane.reshape((1,4))

    _, _, Vh = np.linalg.svd(A)
    V = Vh.conj().transpose()

    point = V[:,-1]

    if not return_homogeneous:
      point = geometry_utils.nonhomogeneous(point)

    return point

  def backproject_points_plane(self, pts_2d, plane, return_homogeneous=False):
    """ backproject points onto a 3-d plane to mimic interface to PinholeCamera

        Parameters
        ----------
        pt_2d : array_like
            Two Dimensional Point
        plane : array_like
            The 3-D Plane
        return_homogeneous : bool

        Returns
        -------
        array_like
            The 3D Points
    """
    pts_3d = [self.backproject_point_plane(p, plane, return_homogeneous) for p in pts_2d]
    return pts_3d

  def plane2image(self, plane_origin, plane_x, plane_y):
    """ compute the transformation from points on a 3-d plane to image
        coordinates

        Parameters
        ----------
        plane_origin : array_like
          The Plane Origin
        plane_x : array_like
          3D vector describing the first axis of the plane coordinate system.
        plane_y : array_like
          3D vector describing the second axis of the plane coordinate system.

        Returns
        -------
        numpy.array
            3x3 homography matrix
    """
    # normalize plane_x and plane_y to unit vectors
    plane_xlen = np.sqrt(np.dot(plane_x, plane_x))
    plane_ylen = np.sqrt(np.dot(plane_y, plane_y))
    plane_xu = plane_x / plane_xlen
    plane_yu = plane_y / plane_ylen

    # compute plane normal
    plane_normal = np.cross(plane_xu, plane_yu)

    # compute rotation and translation components of the transformation
    plane2world_R = np.vstack((plane_xu, plane_yu, plane_normal)).transpose()
    plane2world_T = plane_origin

    # put x,y scale back in in case plane_x and plane_y were not unit vectors
    plane_xy_scale = np.eye(4)
    np.fill_diagonal(plane_xy_scale, (plane_xlen, plane_ylen, 1.0, 1.0))

    # compose matrix mapping plane coordinates to world coordinates
    plane2world_RT = np.vstack((np.hstack((plane2world_R, plane2world_T.reshape(3,1))),np.array((0,0,0,1))))
    plane2world = np.dot(plane2world_RT, plane_xy_scale)

    # compose matrix mapping plane coordinates to image coordinates
    plane2img = np.dot(self.P, plane2world)
    # we can remove the 3rd column since the "Z" coordinates of points on the plane are 0
    plane2img3x3 = plane2img[:,(0,1,3)]
    return plane2img3x3

  def image2plane(self, plane_origin, plane_x, plane_y):
    """ compute the transformation from image coordinates to points on a 3-d
        plane

        Parameters
        ----------
        plane_origin : array_like
          The Plane Origin
        plane_x : array_like
          Plane x
        plane_y : array_like
          Plane y

        Returns
        -------
        array_like
            The Plane Image Coordinates

    """
    #plane_xlen = np.sqrt(np.dot(plane_x, plane_x))
    #plane_ylen = np.sqrt(np.dot(plane_y, plane_y))
    #plane_xu = plane_x / plane_xlen
    #plane_yu = plane_y / plane_ylen
    #plane_normal = np.cross(plane_xu, plane_yu)
    #world2plane_R = np.vstack((plane_xu, plane_yu, plane_normal))
    #world2plane_T = -np.dot(world2plane_R, plane_origin)
    #world2plane = np.vstack((np.hstack((world2plane_R, world2plane_T.reshape(3,1))),np.array((0,0,0,1))))

    #cam2world_R = self.R.transpose()
    #cam2world_T = -np.dot(cam2world_R, self.T)
    #cam2world = np.vstack((np.hstack((cam2world_R, cam2world_T.reshape(3,1))),np.array((0,0,0,1))))
    #Kinv4x3 = np.vstack((self.Kinv, np.zeros((1,3))))

    #img2plane = np.dot(np.dot(world2plane, cam2world), Kinv4x3)
    ## since the "Z" coordinate of the plane is 0, we can remove the 3rd row of the transform
    ## make a deep copy so that matrix is contiguous
    #img2plane3x3 = img2plane[(0,1,3),:].copy()

    #return img2plane3x3
    p2i = self.plane2image(plane_origin, plane_x, plane_y)
    return np.linalg.inv(p2i)


def triangulate_point(cameras, projections, return_homogeneous=True):
  """ Triangulate a 3-d point given it's projection in two images

      Parameters
      ----------
      cameras : array_like
      projections : array_like
      return_homogeneous : bool
          Default: True

      Returns
      -------
      array_like
          The Point

      Raises
      ------
      Exception
          When the number of cameras and 2-d projections are not the same.
  """
  num_obs = len(cameras)
  if len(projections) != num_obs:
    raise Exception('Expecting same number of cameras and 2-d projections')

  A = np.zeros((2*num_obs,4))
  for i in range(num_obs):
    A[2*i,:] = cameras[i].P[0,:] - cameras[i].P[2,:]*projections[i][0]
    A[2*i + 1,:] = cameras[i].P[1,:] - cameras[i].P[2,:]*projections[i][1]

  _, _, Vh = np.linalg.svd(A)
  V = Vh.conj().transpose()

  point = V[:,-1]

  if not return_homogeneous:
    point = geometry_utils.nonhomogeneous(point)

  return point


