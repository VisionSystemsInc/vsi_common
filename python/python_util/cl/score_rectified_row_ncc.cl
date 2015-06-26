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

    // compute the mean pixel value of each window
    float mean_a = 0.0f;
    float mean_b = 0.0f;
    for (int y = -window_radius; y <= window_radius; ++y) {
        int row_offset_a = (row + y)*ncols_a;
        int row_offset_b = (row + y)*ncols_b;
        for (int x = -window_radius; x <= window_radius; ++x) {
            int ia = row_offset_a + a_col + x;
            int ib = row_offset_b + b_col + x;
            mean_a += a[ia];
            mean_b += b[ib];
        }
    }
    const int window_pix = 4*window_radius*window_radius + 4*window_radius + 1;
    mean_a /= window_pix;
    mean_b /= window_pix;
#if 1
    // compute the magnitude of the translated vector
    float mag_a = 0.0f;
    float mag_b = 0.0f;
    for (int y = -window_radius; y <= window_radius; ++y) {
        int row_offset_a = (row + y)*ncols_a;
        int row_offset_b = (row + y)*ncols_b;
        for (int x = -window_radius; x <= window_radius; ++x) {
            int ia = row_offset_a + a_col + x;
            int ib = row_offset_b + b_col + x;
            float diff = a[ia] - mean_a;
            mag_a += diff*diff;
            diff = b[ib] - mean_b;
            mag_b += diff*diff;
        }
    }
    mag_a = sqrt(mag_a);
    mag_b = sqrt(mag_b);
#else
    const float mag_a = 1.0f;
    const float mag_b = 1.0f;
#endif
    // protect against divide by zero
    if ( (mag_a < 1e-6f) || (mag_b < 1e-6f) ) {
        result[idx] = 0.0f;
        return;
    }
    // take the dot product of the normalized values
    float ncc = 0.0f;
    for (int y = -window_radius; y <= window_radius; ++y) {
        int row_offset_a = (row + y)*ncols_a;
        int row_offset_b = (row + y)*ncols_b;
        for (int x = -window_radius; x <= window_radius; ++x) {
            int ia = row_offset_a + a_col + x;
            int ib = row_offset_b + b_col + x;
            float anorm = a[ia] - mean_a;
            anorm /= mag_a;
            float bnorm = b[ib] - mean_b;
            bnorm /= mag_b;
            ncc += anorm*bnorm;
        }
    }
    result[idx] = ncc;
    return;
}

