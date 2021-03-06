
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

    int f, x, y, n;
    int idx_i,idx_o;
    int xf, yf;
    $weight_type w_data;
    $output_type o_data;

    input_size_x = lp->cqt_input_shape[1];  //画像サイズ
    input_size_y = lp->cqt_input_shape[2];  //画像サイズ
    input_size_num = lp->cqt_input_shape[3]; //入力の数

    //parameter check o_data
    assert(cnvp->kernel_size[0]==3);
    assert(cnvp->kernel_size[1]==3);
    assert(cnvp->padding==PD_SAME);
    assert(cnvp->strides[0]==1);
    assert(cnvp->strides[1]==1);
    assert(fill_num==lp->cqt_output_shape[3]);

    memset(op, 0.0, fill_num * input_size_y * input_size_x * sizeof($output_type));

    //apply filter
    for(y=0;y<input_size_y;y++) {
         for(x=0;x<input_size_x;x++) {

           	for(f=0;f<fill_num;f++) {
                idx_o = y * (input_size_x * fill_num) + (x * fill_num) + f;
                o_data = *(op+idx_o);
                //o_data = 0.0;

                bias = *(bp+f);

                for(n=0;n<input_size_num;n++){
                    for(xf=0;xf<3;xf++) {
                        for(yf=0;yf<3;yf++) {
                            //フィルターはchannel_lastではない
                            idx_i = (f * input_size_num * 3 * 3) + (n * 3 * 3) + (yf * 3) + xf;
                            w_data = *(wp+idx_i);
                            filter3x3[xf][yf] = w_data;
                        }
                    }

                    //get data
                    idx_i = (y-1) * (input_size_x * input_size_num) + (x * input_size_num) + n;

                    data3x3[0][0] = *(ip + idx_i - input_size_num);
                    data3x3[0][1] = *(ip + idx_i);
                    data3x3[0][2] = *(ip + idx_i + input_size_num);

                    idx_i = y * (input_size_x * input_size_num) + (x * input_size_num) + n;
                    data3x3[1][0] = *(ip + idx_i - input_size_num);
                    data3x3[1][1] = *(ip + idx_i);
                    data3x3[1][2] = *(ip + idx_i + input_size_num);

                    idx_i = (y+1) * (input_size_x * input_size_num) + (x * input_size_num) + n;
                    data3x3[2][0] = *(ip + idx_i - input_size_num);
                    data3x3[2][1] = *(ip + idx_i);
                    data3x3[2][2] = *(ip + idx_i + input_size_num);

                    //border == 'same
                    //zero padding
                    if (x == 0) {
                        data3x3[0][0] = 0;
                        data3x3[1][0] = 0;
                        data3x3[2][0] = 0;
                    }
                    if (x == (input_size_x - 1)) {
                        data3x3[0][2] = 0;
                        data3x3[1][2] = 0;
                        data3x3[2][2] = 0;
                    }
                    if (y == 0) {
                        data3x3[0][0] = 0;
                        data3x3[0][1] = 0;
                        data3x3[0][2] = 0;
                    }
                    if (y == (input_size_y - 1)) {
                        data3x3[2][0] = 0;
                        data3x3[2][1] = 0;
                        data3x3[2][2] = 0;
                    }


                    o_data += filter3x3[0][0] * data3x3[0][0];
                    o_data += filter3x3[0][1] * data3x3[0][1];
                    o_data += filter3x3[0][2] * data3x3[0][2];
                    o_data += filter3x3[1][0] * data3x3[1][0];
                    o_data += filter3x3[1][1] * data3x3[1][1];
                    o_data += filter3x3[1][2] * data3x3[1][2];
                    o_data += filter3x3[2][0] * data3x3[2][0];
                    o_data += filter3x3[2][1] * data3x3[2][1];
                    o_data += filter3x3[2][2] * data3x3[2][2];
                }

                 if(cnvp->use_bias) {
                     o_data += bias;
                 }

                 //activattion
                if(cnvp->activation == ACT_RELU) {
                     if(o_data < 0) {
                         o_data = 0.0;
                     }
                }
                *(op + idx_o) = o_data;
            }

        }
    }
    return CQT_RET_OK;
}
