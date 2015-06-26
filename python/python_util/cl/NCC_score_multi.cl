#define MAX_IMAGES 32
#define MIN_SCORES 3

__kernel void NCC_score_multi(__global const float *image_stack,
                              __global const unsigned char *mask_stack,
                              __global float *result,
                              int num_images, int img_nx, int img_ny, int window_radius)
{
    int gid_x = get_global_id(1);
    int gid_y = get_global_id(0);
    int pix_offset = gid_y*img_nx + gid_x;

    // make sure we have enough room to compute a window around the current pixel
    if ( (gid_x < window_radius) || (gid_x >= (img_nx - window_radius)) || 
         (gid_y < window_radius) || (gid_y >= (img_ny - window_radius)) ) {
        result[pix_offset] = 0;
        return;
    }

    const int window_pix = 4*window_radius*window_radius + 4*window_radius + 1;
    const int num_pix = img_nx * img_ny;

    float means[MAX_IMAGES];
    float mags[MAX_IMAGES];
    bool valid[MAX_IMAGES];

    for (int i=0; i<num_images; ++i) {
        valid[i] = true;
        int img_offset = i * num_pix;
        // compute the mean pixel value of each window
        float mean = 0.0f;
        for (int y = -window_radius; y <= window_radius; ++y) {
            int row_offset = (gid_y + y)*img_nx;
            for (int x = -window_radius; x <= window_radius; ++x) {
                int idx = img_offset + row_offset + gid_x + x;
                if (!mask_stack[idx]) {
                    valid[i] = false;
                }
                mean += image_stack[idx];
            }
        }
        //if (!valid[i]) {
        //    break;
        //}
        mean /= window_pix;
        means[i] = mean;

        // compute the magnitude of the translated vector
        float mag = 0.0f;
        for (int y = -window_radius; y <= window_radius; ++y) {
            int row_offset = (gid_y + y)*img_nx;
            for (int x = -window_radius; x <= window_radius; ++x) {
                int idx = img_offset + row_offset + gid_x + x;
                float diff = image_stack[idx] - mean;
                mag += diff*diff;
            }
        }
        if (mag == 0) {
            mag = 1.0;
        }
        mag = sqrt(mag);
        mags[i] = mag;
    }
    float scores[(MAX_IMAGES*MAX_IMAGES - MAX_IMAGES)/2];
    int num_scores = 0;
    for (int i=0; i<num_images; ++i) {
        //if (!valid[i]) {
        //    continue;
        //}
        int img_offset1 = i * num_pix;
        for (int j=0; j<i; ++j) {
            //if (!valid[j]){
            //    continue;
            //}
            int img_offset2 = j * num_pix;
            // take the dot product of the normalized values
            float ncc = 0.0f;
            for (int y = -window_radius; y <= window_radius; ++y) {
                int row_offset = (gid_y + y)*img_nx;
                for (int x = -window_radius; x <= window_radius; ++x) {
                    int idx1 = img_offset1 + row_offset + gid_x + x;
                    int idx2 = img_offset2 + row_offset + gid_x + x;
                    float anorm = image_stack[idx1] - means[i];
                    anorm /= mags[i];
                    float bnorm = image_stack[idx2] - means[j];
                    bnorm /= mags[j];
                    ncc += anorm*bnorm;
                }
            }
            if (valid[i] && valid[j]) {
                scores[num_scores++] = ncc;
            }
        }
    }
    float score_sum = 0.0;
    for (int i=0; i<num_scores; ++i) {
        score_sum += scores[i];
    }
    if (num_scores < MIN_SCORES) {
        result[pix_offset] = 0.0f;
    }
    else {
        result[pix_offset] = score_sum/num_scores;
    }
    return;
}

