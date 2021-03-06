
int $func_name (CQT_LAYER *lp, void *inp, void *outp)
{
    $weight_type filter3x3[3][3];
    $input_type data3x3[3][3];
    $weight_type bias;

    LY_Conv2D *cnvp;
    cnvp = lp->param_p;

    $input_type *ip = ($input_type *)inp;
    $output_type *op = outp;
    $weight_type *wp = cnvp->weight_p;
    $weight_type *bp = cnvp->bias_p;

    int fill_num = cnvp->filters;
    int input_size_x;
    int input_size_y;
    int input_size_num;
    int data_size_x;
    int data_size_y;
    int padding;

    int f, x, y, n;
    int idx_i,idx_o;
    $weight_type w_data;
    $output_type o_data;

    input_size_x = lp->cqt_input_shape[1];  //画像サイズ
    input_size_y = lp->cqt_input_shape[2];  //画像サイズ
    input_size_num = lp->cqt_input_shape[3]; //入力の数

    padding = lp->neon_padding_hi;

    data_size_x = NEON_HTR + input_size_x + padding; //確保している画像サイズ
    data_size_y = input_size_y + NEON_VTR * 3; //確保している画像サイズ


    //parameter check o_data
    assert(cnvp->kernel_size[0]==3);
    assert(cnvp->kernel_size[1]==3);
    assert(cnvp->padding==PD_SAME);
    assert(cnvp->strides[0]==1);
    assert(cnvp->strides[1]==1);
    assert(fill_num==lp->cqt_output_shape[3]);

    memset(op, 0.0, fill_num * data_size_y * data_size_x * sizeof($output_type));

    for(f=0;f<fill_num;f++) {
        for(n=0;n<input_size_num;n++){
            // get filter
            for(x=0;x<3;x++) {
                for(y=0;y<3;y++) {
                    idx_i = (f * input_size_num * 3 * 3) + (n * 3 * 3) + (y * 3) + x;
                    w_data = *(wp+idx_i);
                    filter3x3[x][y] = w_data;
                }
            }
            bias = *(bp+f);

            //apply filter
            for(y=0;y<input_size_y;y++) {
                for(x=0;x<input_size_x;x++) {
                    //get data
                    idx_i = n * (data_size_y * data_size_x) + (((y + NEON_VTR)-1) * data_size_x) + (x + NEON_HTR);
                    idx_o = f * (data_size_y * data_size_x) + ((y + NEON_VTR) * data_size_x) + (x + NEON_HTR);
                    o_data = *(op + idx_o);

                    data3x3[0][0] = *(ip + idx_i - 1);
                    data3x3[0][1] = *(ip + idx_i);
                    data3x3[0][2] = *(ip + idx_i + 1);

                    idx_i = n * (data_size_y * data_size_x) + (y + NEON_VTR) * data_size_x + (x + NEON_HTR);
                    data3x3[1][0] = *(ip + idx_i - 1);
                    data3x3[1][1] = *(ip + idx_i);
                    data3x3[1][2] = *(ip + idx_i + 1);

                    idx_i = n * (data_size_y * data_size_x) + ((y + NEON_VTR) + 1) * data_size_x + (x + NEON_HTR);
                    data3x3[2][0] = *(ip + idx_i - 1);
                    data3x3[2][1] = *(ip + idx_i);
                    data3x3[2][2] = *(ip + idx_i + 1);

                    //border == 'same
                    //入力データ側で０パディングをしてあるため、パディング処理不要

                    o_data += filter3x3[0][0] * data3x3[0][0];
                    o_data += filter3x3[0][1] * data3x3[0][1];
                    o_data += filter3x3[0][2] * data3x3[0][2];
                    o_data += filter3x3[1][0] * data3x3[1][0];
                    o_data += filter3x3[1][1] * data3x3[1][1];
                    o_data += filter3x3[1][2] * data3x3[1][2];
                    o_data += filter3x3[2][0] * data3x3[2][0];
                    o_data += filter3x3[2][1] * data3x3[2][1];
                    o_data += filter3x3[2][2] * data3x3[2][2];

                    if(n==(input_size_num-1)) {
                        //bais
                        if(cnvp->use_bias) {
                                o_data += bias;
                        }

                        //activattion
                        if(cnvp->activation == ACT_RELU) {
                            if(o_data < 0) {
                                o_data = 0.0;
                            }
                        }
                    }

                    *(op + idx_o) = o_data;
                }
            }
        }
    }
    return CQT_RET_OK;
}
