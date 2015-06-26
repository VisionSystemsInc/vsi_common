__kernel void sliding_ssd(__global const float *a,
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

    // Compute the Sum of Squared Differences for the two windows
    float ssd = 0.0f;
    for (int y = -window_radius; y <= window_radius; ++y) {
        int row_offset = (gid_y + y)*img_nx;
        for (int x = -window_radius; x <= window_radius; ++x) {
            int i = row_offset + gid_x + x;
            float diff = a[i] - b[i];
            ssd += diff*diff;
        }
    }
    result[idx] = ssd;
    return;
}

