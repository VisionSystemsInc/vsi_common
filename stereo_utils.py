""" Utility Functions for various stereo vision-related operations """
import numpy as np
import skimage.measure
import geometry_utils
import camera_utils


def rectify_calibrated_2(camera0, camera1, image0_shape, image1_shape, max_dim):
    """ compute epipolar rectification homographies
    """
    plane_x = camera1.center - camera0.center
    plane_x /= np.linalg.norm(plane_x)
    plane_y = np.cross(camera0.principal_ray(), plane_x)
    plane_z = np.cross(plane_x, plane_y)

    R = np.vstack((plane_x.reshape((1,3)), plane_y.reshape((1,3)), plane_z.reshape((1,3))))
    K = (camera0.K + camera1.K)/2.0
    K[0,1] = 0  # no skew

    Tnew0 = -np.dot(R, camera0.center)
    Tnew1 = -np.dot(R, camera1.center)
    Pnew0 = np.dot(K,np.hstack((R, Tnew0.reshape(3,1))))
    Pnew1 = np.dot(K,np.hstack((R, Tnew1.reshape(3,1))))

    T0 = np.dot(Pnew0[0:3,0:3], np.linalg.inv(camera0.P[0:3,0:3]))
    T1 = np.dot(Pnew1[0:3,0:3], np.linalg.inv(camera1.P[0:3,0:3]))

    corners0 = [np.array((0,0)), np.array((0,image0_shape[0])), np.array((image0_shape[1], image0_shape[0])), np.array((image0_shape[1],0))]
    corners0 = np.vstack((np.array(corners0).T, np.ones((1,4))))
    corners1 = [np.array((0,0)), np.array((0,image1_shape[0])), np.array((image1_shape[1], image1_shape[0])), np.array((image1_shape[1],0))]
    corners1 = np.vstack((np.array(corners1).T, np.ones((1,4))))
    corners_plane0 = np.dot(T0, corners0)
    corners_plane0 = corners_plane0[0:2,:] / corners_plane0[2,:]
    corners_plane1 = np.dot(T1, corners1)
    corners_plane1 = corners_plane1[0:2,:] / corners_plane1[2,:]

    projected_min0 = corners_plane0.min(axis=1)
    projected_max0 = corners_plane0.max(axis=1)
    projected_min1 = corners_plane1.min(axis=1)
    projected_max1 = corners_plane1.max(axis=1)

    max_projected_x = max(projected_max0[0] - projected_min0[0], projected_max1[0] - projected_min1[0])
    projected_y = max(projected_max0[1], projected_max1[1]) - min(projected_min0[1], projected_min1[1])
    scale = max_dim / max(max_projected_x, projected_y)

    tx0 = -projected_min0[0] * scale
    tx1 = -projected_min1[0] * scale
    ty = -min(projected_min0[1], projected_min1[1]) * scale

    T0final = np.dot(geometry_utils.similarity_transform(scale, np.array((tx0, ty))), T0)
    T1final = np.dot(geometry_utils.similarity_transform(scale, np.array((tx1, ty))), T1)
    output_shape = (np.array((projected_y, max_projected_x)) * scale).astype(np.int)

    return T0final, T1final, output_shape


def rectify_calibrated_euclidean(camera0, camera1, img0_shape, img1_shape):
    """ compute epipolar rectification homographies by rotating image planes """
    baseline = camera1.center - camera0.center
    baseline /= np.linalg.norm(baseline)
    new_look = camera0.principal_ray() + camera1.principal_ray()
    new_look /= np.linalg.norm(new_look)
    new_y = np.cross(new_look, baseline)
    new_y /= np.linalg.norm(new_y)
    new_z = np.cross(baseline, new_y)

    newK = camera0.K
    newR = np.vstack((baseline, new_y, new_z))
    Q0 = camera0.P[0:3,0:3]
    Q1 = camera1.P[0:3,0:3]
    Qnew = np.dot(newK, newR)

    H0 = np.dot(Qnew, np.linalg.inv(Q0))
    H1 = np.dot(Qnew, np.linalg.inv(Q1))

    img0_centroid_homg = np.array((img0_shape[1]/2, img0_shape[0]/2, 1))
    img1_centroid_homg = np.array((img1_shape[1]/2, img1_shape[0]/2, 1))

    img0_centroid_rect = np.dot(H0, img0_centroid_homg)
    img0_centroid_rect /= img0_centroid_rect[2]

    img1_centroid_rect = np.dot(H1, img1_centroid_homg)
    img1_centroid_rect /= img1_centroid_rect[2]

    tx0 = img0_centroid_homg[0] - img0_centroid_rect[0]
    ty0 = img0_centroid_homg[1] - img0_centroid_rect[1]
    tx1 = img1_centroid_homg[0] - img1_centroid_rect[0]
    ty1 = img1_centroid_homg[1] - img1_centroid_rect[1]
    ty = np.mean((ty0, ty1))

    scale = np.array((1,1))
    H0final = np.dot(geometry_utils.similarity_transform(scale, np.array((tx0, ty))), H0)
    H1final = np.dot(geometry_utils.similarity_transform(scale, np.array((tx1, ty))), H1)

    return H0final, H1final, img0_shape, img1_shape


def rectify_calibrated_plane(camera0, camera1, img0_shape, img1_shape, plane, img_scale=1.0, mask0=None, mask1=None, check_angles=False, min_graze_angle_degrees=15):
    """ compute epipolar rectification relative to a scene plane.
        Points on the plane will be in identical positions in both images.
    """
    # reverse plane normal if facing away from mean look direction
    mean_look = camera0.principal_ray() + camera1.principal_ray()
    if np.dot(mean_look, plane[0:3]) > 0:
        plane *= -1

    # start with a standard epipolar calibration
    H0, H1, rect_shape0, _ = rectify_calibrated_fov(camera0, camera1, img0_shape, img1_shape, img_scale, None, mask0, mask1, check_angles, min_graze_angle_degrees)

    # create PinholeCameras for rectified images
    K0_rect = np.dot(H0, camera0.K)
    K0_rect /= K0_rect[2,2]
    cam0_rect = camera_utils.PinholeCamera(K0_rect, camera0.R, camera0.T)
    K1_rect = np.dot(H1, camera1.K)
    K1_rect /= K1_rect[2,2]
    cam1_rect = camera_utils.PinholeCamera(K1_rect, camera1.R, camera1.T)

    # backproject principal point onto plane to get plane origin - (location doesn't matter in theory)
    plane_origin = camera0.backproject_point_plane(np.array((img0_shape[1]/2.0, img0_shape[0]/2.0)), plane)
    plane_x = cam0_rect.x_axis()
    plane_y = np.cross(plane[0:3], plane_x)
    plane_y /= np.linalg.norm(plane_y)
    plane_x = np.cross(plane_y, plane[0:3])

    # compute homography from (rectified) img1 to img0 via plane
    H1_plane = np.dot(cam0_rect.plane2image(plane_origin, plane_x, plane_y), cam1_rect.image2plane(plane_origin, plane_x, plane_y))
    H1_final = np.dot(H1_plane, H1)

    return H0, H1_final, rect_shape0, rect_shape0


def rectify_calibrated_fov(camera0, camera1, img0_shape, img1_shape, img_scale=1.0, plane=None, mask0=None, mask1=None, check_angles=True, min_graze_angle_degrees=15):
    """ compute epipolar rectification homographies based on an (optional) plane of interest
    """
    def image_corners(img_shape):
        """ return x,y coordinates of the 4 image corners """
        return np.array(((0,0),(img_shape[1],0),(img_shape[1],img_shape[0]),(0,img_shape[0])))

    def compute_mask_corners(mask):
        """ compute the corners of the bounding box of the mask """
        mask_int = np.zeros_like(mask,dtype=np.int)
        mask_int[mask] = 1
        mask_props = skimage.measure.regionprops(mask_int, properties=['BoundingBox',])
        if len(mask_props) == 0:
            return None
        mask_bbox = mask_props[0]['BoundingBox']
        return np.array(((mask_bbox[1],mask_bbox[0]),(mask_bbox[1],mask_bbox[2]),(mask_bbox[3],mask_bbox[0]),(mask_bbox[3],mask_bbox[2])))

    mean_look = camera0.principal_ray() + camera1.principal_ray()
    mean_look /= np.linalg.norm(mean_look)

    if plane is None:
        # guess that viewing directions are perpendicular to scene
        plane = -mean_look
    else:
        # make sure plane normal points towards cameras
        if np.dot(plane[0:3], mean_look) > 0:
            plane *= -1

    plane /= np.linalg.norm(plane[0:3])
    plane_normal = plane[0:3]

    # create image of viewing ray directions
    if check_angles:
        print('checking angles')
        x,y = np.meshgrid(range(0,img0_shape[1]),range(0,img0_shape[0]))
        xypairs = [np.array((xv,yv)) for xv,yv in zip(x.flat,y.flat)]
        rays = camera0.viewing_rays(xypairs)
        angles = np.arccos(np.dot(rays, -plane_normal)).reshape(img0_shape[0:2])
        angle_mask0 = angles <= np.deg2rad(90.0 - min_graze_angle_degrees)

        x,y = np.meshgrid(range(0,img1_shape[1]),range(0,img1_shape[0]))
        xypairs = [np.array((xv,yv)) for xv,yv in zip(x.flat,y.flat)]
        rays = camera1.viewing_rays(xypairs)
        angles = np.arccos(np.dot(rays, -plane_normal)).reshape(img1_shape)
        angle_mask1 = angles <= np.deg2rad(90.0 - min_graze_angle_degrees)
    else:
        angle_mask0 = None
        angle_mask1 = None

    if mask0 is not None:
        rect_mask0 = mask0 > 0
        if angle_mask0 is not None:
            rect_mask0 &= angle_mask0
    elif angle_mask0 is not None:
        rect_mask0 = angle_mask0
    else:
        rect_mask0 = None

    if mask1 is not None:
        rect_mask1 = mask1 > 0
        if angle_mask1 is not None:
            rect_mask1 &= angle_mask1
    elif angle_mask1 is not None:
        rect_mask1 = angle_mask1
    else:
        rect_mask1 = None

    if rect_mask0 is None:
        img0_corners = image_corners(img0_shape)
    else:
        img0_corners = compute_mask_corners(rect_mask0)

    if rect_mask1 is None:
        img1_corners = image_corners(img1_shape)
    else:
        img1_corners = compute_mask_corners(rect_mask1)

    if img0_corners is None or img1_corners is None:
        return np.eye(3), np.eye(3), np.array((0,0)), np.array((0,0))

    mean_cam_center = (camera0.center + camera1.center)/2.0
    if len(plane) == 3:
        # normal only, no distance
        # default to 10x the baseline distance
        plane_dist = 10.0*np.linalg.norm(camera1.center - camera0.center)
        point_on_plane = mean_cam_center + plane_dist * -plane_normal
        plane_d = -np.dot(plane_normal, point_on_plane)
        plane = np.append(plane, plane_d)
        plane_origin = point_on_plane
    elif len(plane) == 4:
        plane_origin = mean_cam_center + np.dot(plane,np.append(mean_cam_center,1)) * -plane_normal
    else:
        raise Exception('expecting None, 3 element numpy array, or 4 element numpy array for plane argument')

    plane_x = camera1.center - camera0.center
    plane_x /= np.linalg.norm(plane_x)
    plane_y = np.cross(-plane_normal, plane_x)
    plane_y /= np.linalg.norm(plane_y)

    # scale plane_x and plane_y so that pixel size in center of image is preserved
    plane_origin = camera0.backproject_point_plane(camera0.principal_point(), plane)
    plane_origin_dx = camera0.backproject_point_plane(camera0.principal_point() + np.array((1,0)), plane)
    plane_origin_dy = camera0.backproject_point_plane(camera0.principal_point() + np.array((0,1)), plane)
    plane_dx = np.linalg.norm(plane_origin_dx - plane_origin)
    plane_dy = np.linalg.norm(plane_origin_dy - plane_origin)
    scale_factor = (plane_dx + plane_dy)/2.0 / img_scale

    plane_x *= scale_factor
    plane_y *= scale_factor

    H0plane = camera0.image2plane(plane_origin, plane_x, plane_y)
    H1plane = camera1.image2plane(plane_origin, plane_x, plane_y)

    # now compute backprojection of images onto plane
    c0 = camera0.backproject_point_plane(img0_corners.mean(axis=0), plane)
    c1 = camera1.backproject_point_plane(img1_corners.mean(axis=0), plane)
    offset_3d = c0 - c1
    # we can't change y coordinate w/out violating epipolar constraint, ,but x is free to move
    offset_plane = np.array((np.dot(offset_3d, plane_x), 0 ))
    H1_trans = geometry_utils.similarity_transform(1.0, offset_plane)

    H0 = H0plane
    H1 = np.dot(H1_trans, H1plane)

    img0_corners_homg = np.vstack((img0_corners.T, np.ones((1,4))))
    img1_corners_homg = np.vstack((img1_corners.T, np.ones((1,4))))

    img0_corners_plane = np.dot(H0, img0_corners_homg)
    img0_corners_plane = img0_corners_plane[0:2,:] / img0_corners_plane[2,:]
    img1_corners_plane = np.dot(H1, img1_corners_homg)
    img1_corners_plane = img1_corners_plane[0:2,:] / img1_corners_plane[2,:]

    min_y_plane = max(np.min(img0_corners_plane[1,:]), np.min(img1_corners_plane[1,:]))
    max_y_plane = min(np.max(img0_corners_plane[1,:]), np.max(img1_corners_plane[1,:]))

    min_x_plane0 = np.min(img0_corners_plane[0,:])
    min_x_plane1 = np.min(img1_corners_plane[0,:])
    max_x_plane0 = np.max(img0_corners_plane[0,:])
    max_x_plane1 = np.max(img1_corners_plane[0,:])

    bbox0 = np.array(((min_x_plane0, min_y_plane), (max_x_plane0, max_y_plane)))
    bbox1 = np.array(((min_x_plane1, min_y_plane), (max_x_plane1, max_y_plane)))

    extents0 = bbox0[1] - bbox0[0]
    extents1 = bbox1[1] - bbox1[0]

    scale = np.array((1,1))

    tx0 = -bbox0[0][0] * scale[0]
    tx1 = -bbox1[0][0] * scale[0]
    ty = -min(bbox0[0][1], bbox1[0][1]) * scale[1]

    H0final = np.dot(geometry_utils.similarity_transform(scale, np.array((tx0, ty))), H0)
    H1final = np.dot(geometry_utils.similarity_transform(scale, np.array((tx1, ty))), H1)

    output_shape0 = (np.array((extents0[1], extents0[0])) * np.array((scale[1],scale[0]))).astype(np.int)
    output_shape1 = (np.array((extents1[1], extents1[0])) * np.array((scale[1],scale[0]))).astype(np.int)

    return H0final, H1final, output_shape0, output_shape1


def rectify_calibrated_volume(camera0, camera1, vol_origin, vol_extent, max_dim, plane_normal=None):
    """ compute epipolar rectification homographies based on volume of interest
    """
    if plane_normal is None:
        # guess that viewing directions are perpendicular to scene
        plane_normal = camera0.principal_ray() + camera1.principal_ray()
    vol_centroid = vol_origin + vol_extent/2.0
    plane_x = camera1.center - camera0.center
    plane_x /= np.linalg.norm(plane_x)
    plane_y = np.cross(plane_normal, plane_x)
    plane_y /= np.linalg.norm(plane_y)
    plane_origin = vol_centroid

    # project volume corners onto new image plane
    vol_corners = geometry_utils.volume_corners(vol_origin, vol_extent)
    vol_corners_plane = [(np.dot(c - plane_origin, plane_x), np.dot(c - plane_origin, plane_y)) for c in vol_corners]

    H0 = camera0.image2plane(plane_origin, plane_x, plane_y)
    H1 = camera1.image2plane(plane_origin, plane_x, plane_y)

    #img_corners_homg = np.vstack((np.array(vol_corners_plane).T, np.ones((1,8))))
    #corners_plane0 = np.dot(H0, vol_corners_plane_homg)
    #corners_plane0 = corners_plane0[0:2,:] / corners_plane0[2,:]
    #corners_plane1 = np.dot(H1, vol_corners_plane_homg)
    #corners_plane1 = corners_plane1[0:2,:] / corners_plane1[2,:]

    corners_plane0 = np.array(vol_corners_plane).T
    corners_plane1 = np.array(vol_corners_plane).T

    bbox0 = (np.min(corners_plane0,axis=1), np.max(corners_plane0,axis=1))
    extents0 = bbox0[1] - bbox0[0]

    bbox1 = (np.min(corners_plane1,axis=1), np.max(corners_plane1,axis=1))
    extents1 = bbox1[1] - bbox1[0]

    max_extent = np.max((extents0, extents1),axis=0)
    scale = max_dim / max_extent.max()

    tx0 = -bbox0[0][0] * scale
    tx1 = -bbox1[0][0] * scale
    ty = -min(bbox0[0][1], bbox1[0][1]) * scale

    H0final = np.dot(geometry_utils.similarity_transform(scale, np.array((tx0, ty))), H0)
    H1final = np.dot(geometry_utils.similarity_transform(scale, np.array((tx1, ty))), H1)
    #output_shape = (np.array((max_extent[1], max_extent[0])) * scale).astype(np.int)
    output_shape0 = (np.array((extents0[1], extents0[0])) * scale).astype(np.int)
    output_shape1 = (np.array((extents1[1], extents1[0])) * scale).astype(np.int)
    return H0final, H1final, output_shape0, output_shape1


def rectify_calibrated(camera0, camera1, image0_shape, image1_shape, max_dim):
    """ compute epipolar rectification homographies
    """
    plane_x = camera1.center - camera0.center
    plane_x /= np.linalg.norm(plane_x)
    plane_y = np.cross(plane_x, (camera0.principal_ray() + camera1.principal_ray()))
    plane_y /= np.linalg.norm(plane_y)
    plane_z = np.cross(plane_x, plane_y)
    look_pt = (camera1.center + camera0.center)/2.0 + plane_z
    print("look_at = " + str(look_pt) + " plane_x = " + str(plane_x) + " plane_y = " + str(plane_y))

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

    tx0 = -projected_min0[0] * scale
    tx1 = -projected_min1[0] * scale
    ty = -min(projected_min0[1], projected_min1[1]) * scale

    H0final = np.dot(geometry_utils.similarity_transform(scale, np.array((tx0, ty))), H0)
    H1final = np.dot(geometry_utils.similarity_transform(scale, np.array((tx1, ty))), H1)
    output_shape = (np.array((projected_y, max_projected_x)) * scale).astype(np.int)

    return H0final, H1final, output_shape


def compute_scale_image(img, max_scale=6, thresh=0.01):
    """ determine minimum patch size across image """

    img_byte = skimage.img_as_ubyte(img)
    dog = [im for im in skimage.transform.pyramid_laplacian(img_byte, max_layer=max_scale)]
    dog_stack = np.zeros((img.shape[0],img.shape[1],len(dog)))
    for i in range(len(dog)):
        dog_stack[:,:,i] = abs(skimage.transform.resize(dog[i],img.shape,mode='nearest'))

    dog_cum = np.zeros_like(dog_stack)
    dog_cum[:,:,0] = dog_stack[:,:,0]
    for i in range(1,len(dog)):
        dog_cum[:,:,i] = dog_cum[:,:,i-1] + dog_stack[:,:,i]

    scale_img = np.zeros_like(img,dtype=np.uint8) + len(dog)
    for i in reversed(range(len(dog))):
        scale_img[dog_cum[:,:,i] > thresh] = i
    return scale_img

