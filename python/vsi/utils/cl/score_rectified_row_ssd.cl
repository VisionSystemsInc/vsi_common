__kernel void score_rectified_row(__global const float *a,
                                  __global const float *b,
                                  __global float *result,
                                  int row, int nrows,
                                  int ncols_a, int ncols_b,
                                  int window_radius)
{
    int a_col = get_global_id(0);
    int b_col = get_global_id(1);
    int idx = a_col*ncols_b + b_col;

    // make sure we have enough room to compute a window around the current pixel
    if ( (a_col < window_radius) || (a_col >= (ncols_a - window_radius)) || 
         (b_col < window_radius) || (b_col >= (ncols_b - window_radius)) ||
         (row < window_radius) || (row >= (nrows - window_radius)) ) {
        result[idx] = NAN;
        return;
    }

    // sum the squared differences
    float ssd = 0.0f;
    for (int y = -window_radius; y <= window_radius; ++y) {
        int row_offset_a = (row + y)*ncols_a;
        int row_offset_b = (row + y)*ncols_b;
        for (int x = -window_radius; x <= window_radius; ++x) {
            int ia = row_offset_a + a_col + x;
            int ib = row_offset_b + b_col + x;
            float diff = a[ia] - b[ib];
            ssd += diff*diff;
        }
    }
    const int window_pix = 4*window_radius*window_radius + 4*window_radius + 1;
    // assumes that image intensities are in the range (0,1)
    result[idx] = 1.0 - ssd / window_pix;
    return;
}

