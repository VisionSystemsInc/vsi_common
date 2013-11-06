""" Utility functions related to mesh processing """
import numpy as np
import vtk


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


