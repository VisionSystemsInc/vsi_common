__kernel void sliding_ncc(__global const float *a,
                          __global const float *b,
                          __global float *result,
                          int img_nx, int img_ny, int window_radius)
{
    int gid_x = get_global_id(1);
    int gid_y = get_global_id(0);
    int idx = gid_y*img_nx + gid_x;

    // make sure we have enough room to compute a window around the current pixel
    if ( (gid_x < window_radius) || (gid_x >= (img_nx - window_radius)) || 
         (gid_y < window_radius) || (gid_y >= (img_ny - window_radius)) ) {
        result[idx] = NAN;
        return;
    }

    // compute the mean pixel value of each window
    float mean_a = 0.0f;
    float mean_b = 0.0f;
    for (int y = -window_radius; y <= window_radius; ++y) {
        int row_offset = (gid_y + y)*img_nx;
        for (int x = -window_radius; x <= window_radius; ++x) {
            int i = row_offset + gid_x + x;
            mean_a += a[i];
            mean_b += b[i];
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
        int row_offset = (gid_y + y)*img_nx;
        for (int x = -window_radius; x <= window_radius; ++x) {
            int i = row_offset + gid_x + x;
            float diff = a[i] - mean_a;
            mag_a += diff*diff;
            diff = b[i] - mean_b;
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
    if ( (mag_a < 1e-6) || (mag_b < 1e-6) ) {
        result[idx] = 0.0f;
        return;
    }
    // take the dot product of the normalized values
    float ncc = 0.0f;
    for (int y = -window_radius; y <= window_radius; ++y) {
        int row_offset = (gid_y + y)*img_nx;
        for (int x = -window_radius; x <= window_radius; ++x) {
            int i = row_offset + gid_x + x;
            float anorm = a[i] - mean_a;
            anorm /= mag_a;
            float bnorm = b[i] - mean_b;
            bnorm /= mag_b;
            ncc += anorm*bnorm;
        }
    }
    result[idx] = ncc;
    return;
}

