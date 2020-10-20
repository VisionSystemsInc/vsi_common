""" Utility functions related to mesh processing """
import numpy as np


def save_point_cloud_ply(output_fname, pts, normals=None, colors=None):
    """ Save a 3D point cloud in PLY acii format

    Parameters
    ----------
    output_fname : str
        Filename to save to
    pts : array_like
        The 3D points. Shape = Nx3
    normals : array_like
        The 3D normals. Shape = Nx3 (optional)
    colors : array_like
        RGB colors of points.  Shape = Nx3 (optional)

    """
    num_pts = len(pts)

    with open(output_fname, 'w') as fd:
        fd.write('ply\n')
        fd.write('format ascii 1.0\n')
        fd.write('element vertex %d\n' % num_pts)
        fd.write('property float x\n')
        fd.write('property float y\n')
        fd.write('property float z\n')
        if normals is not None:
            assert len(normals) == num_pts, "different number of points and normals"
            fd.write('property float nx\n')
            fd.write('property float ny\n')
            fd.write('property float nz\n')
        if colors is not None:
            assert len(colors) == num_pts, "different number of points and colors"
            fd.write('property uint8 red\n')
            fd.write('property uint8 green\n')
            fd.write('property uint8 blue\n')
        fd.write('element face 0\n')
        fd.write('end_header\n')

        pt_strs = [f'{pt[0]} {pt[1]} {pt[2]}' for pt in pts]

        if normals is None:
            normal_strs = ['' for pt in pts]
        else:
            normal_strs = [f'{n[0]} {n[1]} {n[2]}' for n in normals]

        if colors is None:
            color_strs = ['' for pt in pts]
        else:
            color_strs = [f'{c[0]} {c[1]} {c[2]}' for c in colors]

        for (pt_str, n_str, c_str) in zip(pt_strs, normal_strs, color_strs):
            fd.write(f"{pt_str} {n_str} {c_str}\n")


def save_mesh_ply(output_fname, verts, faces, vert_colors=None):
    """ Save a polygonal mesh in ascii PLY format

    Parameters
    ----------
    output_fname : str
        filename to write to
    verts : array_like
        Vertices of the mesh. Shape = Nx3
    faces : array_like
        Faces of the mesh.
        Shape = NxV, where V is the number of vertices per face.
    vert_colors : array_like
        Per-vertex RGB colors.
        Shape = Nx3
    """
    num_verts = len(verts)
    num_faces = len(faces)

    with open(output_fname, 'w') as fd:
        fd.write('ply\n')
        fd.write('format ascii 1.0\n')
        fd.write(f'element vertex {num_verts}\n')
        fd.write('property float x\n')
        fd.write('property float y\n')
        fd.write('property float z\n')
        if vert_colors is not None:
            fd.write('property uint8 red\n')
            fd.write('property uint8 green\n')
            fd.write('property uint8 blue\n')
        fd.write(f'element face {num_faces}\n')
        fd.write('property list uchar int vertex_index\n')
        fd.write('end_header\n')

        if vert_colors is None:
            for vert in verts:
                fd.write(f'{vert[0]} {vert[1]} {vert[2]}\n')
        else:
            assert len(vert_colors) == num_verts, "different number of vertices and colors"
            for vert,c in zip(verts, vert_colors):
                fd.write(f'{vert[0]} {vert[1]} {vert[2]} {c[0]} {c[1]} {c[2]}\n')

        for face in faces:
            fd.write(f'{len(face)} {face[0]} {face[1]} {face[2]}\n')


def save_cameras_ply(filename, cam_Ks, cam_Rs, cam_Ts, img_sizes, scale=1.0):
    """ Save perspective cameras as meshes in ascii PLY format for visualization
    Note that all input lists should have equal length

    Parameters
    ----------
    filename : str
        filename to write
    cam_Ks : list
        list of camera intrinisic matrices. Each should be array_like with shape 3x3
    cam_Rs : list
        list of camera rotation matrices.  Each should be array_like with shape 3x3
    cam_Ts : list
        list of camera translation vectors.  Each should be array_like with length 3
    img_sizes : list
        list of image dimensions.  Each should be array_like with form (width, height)
    scale : float
        size of visualized camera.  Specifically, the distance from the image plane to the camera center.
    """
    camera_verts = []
    camera_faces = []
    vert_offset = 0
    for cam_K, cam_R, cam_T, img_size in zip(cam_Ks, cam_Rs, cam_Ts, img_sizes):
        camera_center = np.dot(-cam_R.transpose(), cam_T)
        cam_z = cam_R[2,:]
        cam_x = cam_R[0,:]
        cam_y = cam_R[1,:]
        x_len = (scale / cam_K[0,0]) * img_size[0]
        y_len = (scale / cam_K[1,1]) * img_size[1]
        verts = [camera_center,]
        verts.append(camera_center + scale*cam_z - x_len*cam_x - y_len*cam_y)
        verts.append(camera_center + scale*cam_z + x_len*cam_x - y_len*cam_y)
        verts.append(camera_center + scale*cam_z + x_len*cam_x + y_len*cam_y)
        verts.append(camera_center + scale*cam_z - x_len*cam_x + y_len*cam_y)
        faces = [(f[0]+vert_offset, f[1]+vert_offset, f[2]+vert_offset) for f in [(0,1,2), (0,2,3), (0,3,4), (0,4,1)]]
        vert_offset += len(verts)
        camera_verts.extend(verts)
        camera_faces.extend(faces)

    save_mesh_ply(filename, camera_verts, camera_faces)
