""" Utility functions related to mesh processing """
import numpy as np
import io_utils
import vtk
import glob
import os.path


def write_grid_vtk(image_stack_glob, output_filename, origin=(0,0,0), vox_len=1.0):
    """ write out an image stack to a VTK "Structured Points" format """
    image_fnames = glob.glob(image_stack_glob)
    image_fnames.sort()
    nk = len(image_fnames)
    if nk == 0:
        raise Exception('No images matching ' + image_stack_glob)

    # read first image to get x,y dimensions
    img0 = io_utils.imread(image_fnames[0])

    ni = img0.shape[1]
    nj = img0.shape[0]

    fd = open(output_filename, 'w')
    fd.write('# vtk DataFile Version 3.1\n')
    fd.write('a voxel grid\n')
    fd.write('ASCII\n')
    fd.write('DATASET STRUCTURED_POINTS\n')
    fd.write('DIMENSIONS %d %d %d\n' % (ni,nj,nk))
    fd.write('ORIGIN %f %f %f\n' % (origin[0], origin[1], origin[2]))
    fd.write('SPACING %f %f %f\n' % (vox_len, vox_len, vox_len))
    fd.write('POINT_DATA %d\n' % (ni*nj*nk))
    fd.write('SCALARS values float 1\n')
    fd.write('LOOKUP_TABLE default\n')
    for k in range(nk):
        img = io_utils.imread(image_fnames[k])
        for j in range(nj):
            for i in range(ni):
                fd.write('%f\n' % (float(img[j,i]) / 255.0))
    fd.write('\n')
    fd.close()


def marching_cubes(grid_fname_vtk, mesh_filename_ply, value=0.5):
    """ read in a grid in vtk format, run marching cubes, save the result as ply mesh """
    reader = vtk.vtkStructuredPointsReader()
    reader.SetFileName(grid_fname_vtk)
    reader.Update()
    points = reader.GetOutput()

    mcubes = vtk.vtkMarchingCubes()
    mcubes.SetInput(points)
    mcubes.SetValue(0, value)
    mcubes.Update()
    mesh = mcubes.GetOutput()

    writer = vtk.vtkPLYWriter()
    writer.SetInput(mesh)
    writer.SetFileName(mesh_filename_ply)
    writer.Update()
    writer.Write()


def colorize_verts_ply(ply_in_filename, ply_out_filename, image, camera):
    """ add per-vertex color information based on projections into images """
    # read in PLY file
    reader = vtk.vtkPLYReader()
    reader.SetFileName(ply_in_filename)
    reader.Update()
    data = reader.GetOutput()

    # create Color data
    colors = vtk.vtkUnsignedCharArray()
    colors.SetNumberOfComponents(3)
    colors.SetName("Colors")

    num_pts = data.GetNumberOfPoints()
    for n in range(num_pts):
        pt3d = data.GetPoint(n)
        pt2d = camera.project_point(pt3d).astype(np.int)
        img_size = np.array((image.shape[1], image.shape[0]))
        if np.any(pt2d < 0) or np.any(pt2d >= img_size):
            color = (128, 128, 128)
        else:
            color = image[pt2d[1], pt2d[0], :]
        # convert gray to RGB
        if len(color) == 1:
            color = (color, color, color)
        colors.InsertNextTuple3(color[0], color[1], color[2])

    data.GetPointData().SetScalars(colors)
    data.Update()

    # write new PLY
    writer = vtk.vtkPLYWriter()
    writer.SetFileName(ply_out_filename)
    writer.SetInput(data)
    writer.SetArrayName("Colors")
    writer.Update()
    writer.Write()


def get_mesh_vertices(mesh_filename):
    """ read a ply file, return vertices in form of 3xN numpy array """
    # read in PLY file
    mesh_ext = os.path.splitext(mesh_filename)[1].lower()
    if mesh_ext == '.ply':
        reader = vtk.vtkPLYReader()
    elif mesh_ext == '.obj':
        reader = vtk.vtkOBJReader()
    else:
        raise Exception('Unsupported filename extension ' + mesh_ext)
    reader.SetFileName(mesh_filename)
    reader.Update()
    data = reader.GetOutput()

    num_pts = data.GetNumberOfPoints()
    vert_matrix = np.zeros((3,num_pts))
    for n in range(num_pts):
        pt3d = data.GetPoint(n)
        vert_matrix[:,n] = pt3d

    return vert_matrix


