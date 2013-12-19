""" Utility Functions for various stereo vision-related operations """
import numpy as np
import skimage.measure
import geometry_utils


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


def rectify_calibrated_fov(camera0, camera1, vol_origin, vol_extent, max_dim, img0_shape, img1_shape, plane_normal=None, mask0=None, mask1=None, min_graze_angle_degrees=15):
    """ compute epipolar rectification homographies based on volume of interest
    """
    if plane_normal is None:
        # guess that viewing directions are perpendicular to scene
        plane_normal = camera0.principal_ray() + camera1.principal_ray()
    plane_x = camera1.center - camera0.center
    plane_x /= np.linalg.norm(plane_x)
    plane_y = np.cross(-plane_normal, plane_x)
    plane_y /= -np.linalg.norm(plane_y)

    mean_cam_center = (camera0.center + camera1.center)/2.0
    #TODO: estimate aoi_center using camera geometry only
    aoi_center = vol_origin + vol_extent/2.0
    plane_dist = np.linalg.norm(mean_cam_center - aoi_center)
    plane_origin = mean_cam_center + plane_dist * -plane_normal

    # project fov corners onto new image plane
    #fov_corners =
    #vol_corners = volume_corners(vol_origin, vol_extent)
    #vol_corners_plane = [(np.dot(c - plane_origin, plane_x), np.dot(c - plane_origin, plane_y)) for c in vol_corners]

    H0 = camera0.image2plane(plane_origin, plane_x, plane_y)
    H1 = camera1.image2plane(plane_origin, plane_x, plane_y)

    img0_corners = np.array(((0,0),(0,img0_shape[0]),(img0_shape[1],0),(img0_shape[1],img0_shape[0])))
    img1_corners = np.array(((0,0),(0,img1_shape[0]),(img1_shape[1],0),(img1_shape[1],img1_shape[0])))

    # create image of viewing ray directions
    x,y = np.meshgrid(range(0,img0_shape[1]),range(0,img0_shape[0]))
    xypairs = [np.array((xv,yv)) for xv,yv in zip(x.flat,y.flat)]
    rays = camera0.viewing_rays(xypairs)
    angles = np.arccos(np.dot(rays, plane_normal)).reshape(img0_shape)
    rect_mask0 = angles >= np.deg2rad(90.0 + min_graze_angle_degrees)

    x,y = np.meshgrid(range(0,img1_shape[1]),range(0,img1_shape[0]))
    xypairs = [np.array((xv,yv)) for xv,yv in zip(x.flat,y.flat)]
    rays = camera1.viewing_rays(xypairs)
    angles = np.arccos(np.dot(rays, plane_normal)).reshape(img1_shape)
    rect_mask1 = angles >= np.deg2rad(90.0 + min_graze_angle_degrees)

    if mask0 is not None: 
        rect_mask0 &= mask0 > 0
    if mask1 is not None:
        rect_mask1 &= mask1 > 0

    def compute_mask_corners(mask):
        """ compute the corners of the bounding box of the mask """
        mask_int = np.zeros_like(mask,dtype=np.int)
        mask_int[mask] = 1
        mask_props = skimage.measure.regionprops(mask_int, properties=['BoundingBox',])
        mask_bbox = mask_props[0]['BoundingBox']
        return np.array(((mask_bbox[1],mask_bbox[0]),(mask_bbox[1],mask_bbox[2]),(mask_bbox[3],mask_bbox[0]),(mask_bbox[3],mask_bbox[2])))

    img0_corners = compute_mask_corners(rect_mask0)
    img1_corners = compute_mask_corners(rect_mask1)

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

    #img_corners_homg = np.vstack((np.array(vol_corners_plane).T, np.ones((1,8))))
    #corners_plane0 = np.dot(H0, vol_corners_plane_homg)
    #corners_plane0 = corners_plane0[0:2,:] / corners_plane0[2,:]
    #corners_plane1 = np.dot(H1, vol_corners_plane_homg)
    #corners_plane1 = corners_plane1[0:2,:] / corners_plane1[2,:]

    #corners_plane0 = np.array(vol_corners_plane).T
    #corners_plane1 = np.array(vol_corners_plane).T

    #bbox0 = (np.min(corners_plane0,axis=1), np.max(corners_plane0,axis=1))

    extents0 = bbox0[1] - bbox0[0]
    #bbox1 = (np.min(corners_plane1,axis=1), np.max(corners_plane1,axis=1))
    extents1 = bbox1[1] - bbox1[0]
    max_extent = np.max((extents0, extents1),axis=0)
    #scale = max_dim / max_extent.max()
    scale = np.array((max_dim, max_dim)) / max_extent

    tx0 = -bbox0[0][0] * scale[0]
    tx1 = -bbox1[0][0] * scale[0]
    ty = -min(bbox0[0][1], bbox1[0][1]) * scale[1]

    H0final = np.dot(geometry_utils.similarity_transform(scale, np.array((tx0, ty))), H0)
    H1final = np.dot(geometry_utils.similarity_transform(scale, np.array((tx1, ty))), H1)
    #output_shape0 = (np.array((max_extent[1], max_extent[0])) * scale).astype(np.int)
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

