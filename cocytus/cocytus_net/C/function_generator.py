import datetime
import os
import string

from compiler.compiler import CQT_Dtype

ctype_dic = {CQT_Dtype.FLOAT32: 'float', CQT_Dtype.UINT8: 'unsigned char'}


class FunctionGenerator:
    def __init__(self, compiler, config, target_dir, template_dir):
        self.compiler = compiler
        self.config = config
        self.target_dir = target_dir
        self.template_dir = template_dir

        self.conv2d_same_3x3_first = True
        self.maxpoolong2d_first = True
        self.flatten_first = True
        self.dense_first = True


    def get_config(self):
        """
        Keras Modelのコンフィグ情報を返す。
        :return:
        """
        return self.compiler.model.get_config()

    def generate(self):
        print('function generate')
        model_config = self.get_config()

        func_list = []
        layers = self.compiler.get_layers()

        for i, l in enumerate(layers):
            name = l.name
            config = l.get_config()
            layer_detal = self.compiler.get_cqt_layer_obj(name)
            class_name = layer_detal.keras_layer_type

            func_name = layer_detal.make_func_name()
            if not func_name in func_list:
                print('generating int %s(CQT_LAYER *lp, void *inp, void *outp);' % func_name)
                if class_name == 'InputLayer':
                    self.generate_input_layer(layer_detal)
                elif class_name == 'Conv2D':
                    self.generate_conv2d(layer_detal)
                elif class_name == 'MaxPooling2D':
                    self.generate_maxpooling2d(layer_detal)
                elif class_name == 'Flatten':
                    self.generate_flatten(layer_detal)
                elif class_name == 'Dense':
                    self.generate_dense(layer_detal)
                elif class_name == 'BatchNormalization':
                    self.generate_batchNormalization(layer_detal)

                func_list.append(func_name)

    def generate_input_layer(self, layer_detail):
        func_name = layer_detail.make_func_name()
        output_file = os.path.join(self.target_dir, 'cqt_lib', 'InputLayer.c')
        template_file = os.path.join(self.template_dir, 'InputLayer', 'InputLayer.c')

        with open(output_file, 'w') as fpout:
            t = string.Template(open(template_file).read())
            func_str = t.substitute(func_name=func_name)
            fpout.write(func_str)

    def generate_conv2d(self, layer_detail):

        kernel_size = layer_detail.l.kernel_size
        padding = layer_detail.l.padding
        func_name = layer_detail.make_func_name()
        input_type = layer_detail.input_dtypes[0]
        weight_type = layer_detail.weight_dtypes[0]
        output_type = layer_detail.output_dtypes[0]

        if kernel_size == (3, 3) and padding == 'same':
            output_file = os.path.join(self.target_dir, 'cqt_lib', 'Conv2d_same_3x3.c')

            opt_level = self.compiler.get_conv2d_optlevel()
            if opt_level == 'dash':
                conv2d_template_fname = 'Conv2d_same_3x3_dash.c'
            else:
                if opt_level != '':
                    print("WARNING unkown Conv2d optimze level %s, use dafalut(no optimize)." % opt_level)
                conv2d_template_fname = 'Conv2d_same_3x3.c'

            template_file = os.path.join(self.template_dir, 'Conv2d', conv2d_template_fname)

            if self.conv2d_same_3x3_first:
                with open(output_file, 'w') as fp:
                    fp.write('#include <string.h>\n')
                    fp.write('#include <assert.h>\n')
                    fp.write('#include "cqt.h"\n')
                    fp.write('#include "cqt_net.h"\n')
                    fp.write('\n')
                self.conv2d_same_3x3_first = False
        else:
            name = layer_detail.l.name
            print('ERROR unsupported Conv2d %s kernel = %s padding = %s' % (name, str(kernel_size), padding))
            return

        with open(output_file, 'a') as fpout:
            t = string.Template(open(template_file).read())
            func_str = t.substitute(func_name=func_name,
                                    input_type=ctype_dic[input_type],
                                    weight_type=ctype_dic[weight_type],
                                    output_type=ctype_dic[output_type])
            fpout.write(func_str)

    def generate_maxpooling2d(self, layer_detail):

        func_name = layer_detail.make_func_name()
        input_type = layer_detail.input_dtypes[0]
        output_type = layer_detail.output_dtypes[0]

        output_file = os.path.join(self.target_dir, 'cqt_lib', 'MaxPooling2D.c')
        template_file = os.path.join(self.template_dir, 'MaxPooling2D', 'MaxPooling2D.c')

        if self.maxpoolong2d_first:
            with open(output_file, 'w') as fp:
                fp.write('#include <string.h>\n')
                fp.write('#include <assert.h>\n')
                fp.write('#include "cqt.h"\n')
                fp.write('#include "cqt_net.h"\n')
                fp.write('\n')
            self.maxpoolong2d_first = False

        with open(output_file, 'a') as fpout:
            t = string.Template(open(template_file).read())
            func_str = t.substitute(func_name=func_name,
                                    input_type=ctype_dic[input_type],
                                    output_type=ctype_dic[output_type])
            fpout.write(func_str)

    def generate_flatten(self, layer_detail):

        func_name = layer_detail.make_func_name()
        input_type = layer_detail.input_dtypes[0]
        output_type = layer_detail.output_dtypes[0]

        output_file = os.path.join(self.target_dir, 'cqt_lib', 'Flatten.c')
        template_file = os.path.join(self.template_dir, 'Flatten', 'Flatten.c')

        if self.flatten_first:
            with open(output_file, 'w') as fp:
                fp.write('#include <string.h>\n')
                fp.write('#include <assert.h>\n')
                fp.write('#include "cqt.h"\n')
                fp.write('#include "cqt_net.h"\n')
                fp.write('\n')
            self.flatten_first = False

        with open(output_file, 'a') as fpout:
            t = string.Template(open(template_file).read())
            func_str = t.substitute(func_name=func_name,
                                    input_type=ctype_dic[input_type],
                                    output_type=ctype_dic[output_type])
            fpout.write(func_str)

    def generate_dense(self, layer_detail):

        func_name = layer_detail.make_func_name()
        input_type = layer_detail.input_dtypes[0]
        output_type = layer_detail.output_dtypes[0]
        weight_type = layer_detail.weight_dtypes[0]

        output_file = os.path.join(self.target_dir, 'cqt_lib', 'Dense.c')
        template_file = os.path.join(self.template_dir, 'Dense', 'Dense.c')

        if self.dense_first:
            with open(output_file, 'w') as fp:
                fp.write('#include <string.h>\n')
                fp.write('#include <assert.h>\n')
                fp.write('#include <math.h>\n')
                fp.write('#include "cqt.h"\n')
                fp.write('#include "cqt_net.h"\n')
                fp.write('\n')
            self.dense_first = False

        with open(output_file, 'a') as fpout:
            t = string.Template(open(template_file).read())
            func_str = t.substitute(func_name=func_name,
                                    input_type=ctype_dic[input_type],
                                    weight_type=ctype_dic[weight_type],
                                    output_type=ctype_dic[output_type])
            fpout.write(func_str)

    def generate_batchNormalization(self, layer_detail):

        func_name = layer_detail.make_func_name()
        input_type = layer_detail.input_dtypes[0]
        output_type = layer_detail.output_dtypes[0]
        weight_type = layer_detail.weight_dtypes[0]

        output_file = os.path.join(self.target_dir, 'cqt_lib', 'BatchNormalization.c')
        template_file = os.path.join(self.template_dir, 'BatchNormalization', 'BatchNormalization.c')

        if self.dense_first:
            with open(output_file, 'w') as fp:
                fp.write('#include <string.h>\n')
                fp.write('#include <assert.h>\n')
                fp.write('#include <math.h>\n')
                fp.write('#include "cqt.h"\n')
                fp.write('#include "cqt_net.h"\n')
                fp.write('\n')
            self.dense_first = False

        with open(output_file, 'a') as fpout:
            t = string.Template(open(template_file).read())
            func_str = t.substitute(func_name=func_name,
                                    input_type=ctype_dic[input_type],
                                    weight_type=ctype_dic[weight_type],
                                    output_type=ctype_dic[output_type])
            fpout.write(func_str)

