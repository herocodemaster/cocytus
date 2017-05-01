
int $func_name (CQT_LAYER *lp, void *inp, void *outp)
{
    $weight_type filter;
    $input_type data;
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
    int idx_i,idx_o, idx_w;
    $output_type o_data;

    input_size_x = lp->cqt_input_shape[1];  //画像サイズ
    input_size_y = lp->cqt_input_shape[2];  //画像サイズ
    input_size_num = lp->cqt_input_shape[3]; //入力の数

    //parameter check o_data
    assert(cnvp->kernel_size[0]==1);
    assert(cnvp->kernel_size[1]==1);
    assert(cnvp->padding==PD_SAME);
    assert(cnvp->strides[0]==1);
    assert(cnvp->strides[1]==1);
    assert(fill_num==lp->cqt_output_shape[3]);

    memset(op, 0.0, fill_num * input_size_y * input_size_x);

    for(f=0;f<fill_num;f++) {
        for(n=0;n<input_size_num;n++){
            idx_w = (f * input_size_num) + n;
            filter = *(wp+idx_w);
            bias = *(bp+f);

            //apply filter
            for(y=0;y<input_size_y;y++) {
                for(x=0;x<input_size_x;x++) {
                    //get data
                    idx_i = n * (input_size_y * input_size_x) + (y * input_size_y) + x;
                    idx_o = f * (input_size_y * input_size_x) + (y * input_size_x) + x;

                    o_data = *(op + idx_o);
                    data = *(ip + idx_i);

                    o_data += filter * data;

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
