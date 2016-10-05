#define MAX_BINS 8
__kernel void local_entropy(__global const float *img,
                            __global float *result,
                            int img_nx, int img_ny,
                            int window_radius, int num_bins,
                            float min_val, float max_val)
{
    int gid_x = get_global_id(1);
    int gid_y = get_global_id(0);
    int idx = gid_y*img_nx + gid_x;

    // make sure we're not trying to use too many bins
    if (num_bins > MAX_BINS) {
        result[idx] = NAN;
        return;
    }

    // make sure we have enough room to compute a window around the current pixel
    if ( (gid_x < window_radius) || (gid_x >= (img_nx - window_radius)) || 
         (gid_y < window_radius) || (gid_y >= (img_ny - window_radius)) ) {
        result[idx] = NAN;
        return;
    }

    const float range = max_val - min_val;

    // initialize bin counters
    int bin_counts[MAX_BINS];
    for (int b=0; b<num_bins; ++b){
        bin_counts[b] = 0;
    }
    // traverse pixels in window
    int num_pixels = 0;
    for (int y = -window_radius; y <= window_radius; ++y) {
        int row_offset = (gid_y + y)*img_nx;
        for (int x = -window_radius; x <= window_radius; ++x) {
            int i = row_offset + gid_x + x;
            if(!isnan(img[i])) {
                int bin_idx = convert_int(((img[i] - min_val) / range) * num_bins);
                if (bin_idx >= num_bins) {
                    bin_idx = num_bins - 1;
                }
                ++bin_counts[bin_idx];
                ++num_pixels;
            }
        }
    }
    // Compute the local entropy inside the current window
    float entropy = 0.0f;
    for (int b=0; b<num_bins; ++b) {
        float bin_prob = convert_float(bin_counts[b]) / num_pixels;
        if (bin_prob > 0.0f) {
            entropy += bin_prob * -log2(bin_prob);
        }
    }
    result[idx] = num_pixels * entropy;
    return;
}
