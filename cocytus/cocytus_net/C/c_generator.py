import os
import shutil
import datetime
from compiler.compiler import CQT_Dtype

class CGenerator:
    def __init__(self, compiler):
        self.compiler = compiler
        self.config = self.compiler.config

    def generate(self):
        """
        Cソースファイルを作成する
        """
        # ディレクトリの作成
        target_dir = self.config['Cocyuts']['output_dir']
        create_c_dir(target_dir)

        # ヘッダーファイルの作成、コピー
        template_dir = self.config['Cocyuts']['c_lib_dir']

        self.generate_hedarfiles(target_dir, template_dir)

        # Cソースの作成
        target_dir = self.config['Cocyuts']['output_dir']
        self.generate_cqt_gen(target_dir, template_dir)

        # ライブラリの作成
        self.generate_cqt_lib(target_dir, template_dir)

    def generate_hedarfiles(self, target_dir, template_dir):
        """
        template_dirから、target_dirへヘッダファイルをコピーする。
        :param target_dir: str
        :param template_dir: str
        :return:
        """
        headers = ['cqt.h', 'cqt_type.h', 'cqt_keras.h', 'numpy.h', 'cqt_net.h']
        for h in headers:
            shutil.copy(os.path.join(template_dir, h),
                        os.path.join(target_dir, 'inc'))

    def generate_cqt_gen(self, target_dir, template_dir):
        """
        target_dirで指定されたディレクトリ/cqt_gen以下にcqt_gen.hとcqt_gen.cのファイルを作成する。
        :param target_dir: str
        :return:
        """
        cqt_gen_h_path = os.path.join(target_dir, 'cqt_gen', 'cqt_gen.h')
        print("making %s" % cqt_gen_h_path)
        cqt_gen_h = CqtGenH(cqt_gen_h_path, self.compiler)
        cqt_gen_h.generate()

        cqt_gen_c_path = os.path.join(target_dir, 'cqt_gen', 'cqt_gen.c')
        print("making %s" % cqt_gen_c_path)
        cqt_gen_c = CqtGenC(cqt_gen_c_path, self.compiler)
        cqt_gen_c.generate()

        files = ['numpy.c', 'cqt_lib.c']
        for f in files:
            shutil.copy(os.path.join(template_dir, f),
                        os.path.join(target_dir, 'cqt_lib'))

    def generate_cqt_lib(self, target_dir, template_dir):
        """
        ## Ｃライブラリ(cqt_lib)
        ### cqt_lib.h
        ### cqt_lib.c
        ### numpy.c
        """
        cqt_lib_h_path = os.path.join(target_dir, 'inc', 'cqt_lib.h')
        print("making %s" % cqt_lib_h_path)
        cqt_lib_h = CqtLibH(cqt_lib_h_path, self.compiler)
        cqt_lib_h.generate()


class CFile:
    def __init__(self, file, compier):
        self.file = file
        self.fp = open(file, 'w')
        self.compiler = compier
        self.pd_dic = {'valid': 'PD_VALID', 'same': 'PD_SAME'}
        self.df_dic = {'channels_last' : 'DF_CHANNELS_LAST', 'channels_first': 'DF_CHANNELS_FIRST'}
        self.act_dic = {'linear': 'ACT_LINEAR', 'softmax': 'ACT_SOFTMAX', 'elu': 'ACT_ELU', 'softplus': 'ACT_SOFTPLUS',
                        'softsign': 'ACT_SOFTSIGN', 'relu': 'ACT_RELU', 'tanh': 'ACT_TANH', 'sigmoid': 'ACT_SIGMOID',
                        'hard_sigmoid': 'ACT_HARD_SIGMOID'
                        }
        self.bool_dic = {True: 'true', False: 'false'}

    def __del__(self):
        self.fp.close()

    def wr(self, s):
        """
        ファイルに文字列を書き込む
        :param s: str
        :return:
        """
        self.fp.write(s)

    def wr_file_header(self):
        """
        自走生成されるファイルにつけられるヘッダー。
        :return:
        """
        # TODO コピーライトやコキュートスのバージョンを追加したい
        today = datetime.date.today()
        self.fp.write("//----------------------------------------------------------------------------------------------------\n")
        self.fp.write("// This file is automatically generated.\n")
        self.fp.write("// %s\n" % today.strftime('%Y/%m/%d %H:%M:%S'))
        self.fp.write("//----------------------------------------------------------------------------------------------------\n")

    def wr_include(self, file, stdlib=False):
        """
        include分を挿入する。
        stdlib = True　の時は #include <file>　形式を、stdlib = Falseの時は
        #include "file" 形式で書き込む。

        :param file: str
        :param stdlib: bool
        :return:
        """
        if stdlib:
            self.wr('#include <%s>\n' % file)
        else:
            self.wr('#include "%s"\n' % file)

    def cr(self):
        """
        改行の挿入
        :return:
        """
        self.wr('\n')

    def write_cqt_network(self, scope=None):
        """
        コキュートスニューラルネットの定義を行う。
        scopeを変更する場合は、scope引数に"extern"もしくは"static"を指定する。
        """
        name = self.compiler.get_model_name()
        scope_s = add_space(scope)

        self.wr('// cocytus network\n')
        self.wr('%sCQT_NET %s;\n' % (scope_s, name))


    def wr_layer_defination(self, scope=None):
        """
        レイヤー変数の定義を行う。
        scopeを変更する場合は、scope引数に"extern"もしくは"static"を指定する。
        :return:
        """
        self.wr("//Layers\n")
        model_config = self.get_config()
        for l in model_config['layers']:
            name = l['name']
            class_name = l['class_name']
            scope_s = add_space(scope)
            s = "%sLY_%s %s;\n" % (scope_s, class_name, name)
            self.wr(s)

    def wr_weight_defination(self, scope=None):
        """
        weight変数の定義を行う。
        scopeを変更する場合は、scope引数に"extern"もしくは"static"を指定する。
        :return:
        """
        self.wr("//weights\n")
        model_config = self.get_config()
        for l in model_config['layers']:
            name = l['name']
            class_name = l['class_name']
            if class_name == 'Conv2D':
                layer_detal = self.compiler.get_cqt_layer_obj(name)
                w_shape = layer_detal.get_Wshape()
                w_name, w_nph_name, b_name, b_nph_name = layer_detal.get_conv2d_weight_variable_name()
                w_dim_s = dim_str_from_keras_4d_shape(w_shape)
                b_dim_s = dim_str_from_keras_4d_shape_bias(w_shape)
                scope_s = add_space(scope)

                w_type = layer_detal.get_weight_type_str()

                self.wr('%sNUMPY_HEADER %s;\n' % (scope_s, w_nph_name))
                self.wr('%sNUMPY_HEADER %s;\n' % (scope_s, b_nph_name))
                self.wr("%s%s %s%s;\n" % (scope_s, w_type, w_name, w_dim_s))
                self.wr("%s%s %s%s;\n" % (scope_s, w_type, b_name, b_dim_s))
            elif class_name == 'Dense':
                layer_detal = self.compiler.get_cqt_layer_obj(name)
                w_shape = layer_detal.get_Wshape()
                input_dim = w_shape[0]
                output_dim = w_shape[1]
                scope_s = add_space(scope)

                w_name, w_nph_name, b_name, b_nph_name = layer_detal.get_conv2d_weight_variable_name()

                w_type = layer_detal.get_weight_type_str()

                self.wr('%sNUMPY_HEADER %s;\n' % (scope_s, w_nph_name))
                self.wr('%sNUMPY_HEADER %s;\n' % (scope_s, b_nph_name))
                self.wr("%s%s %s[%d][%d];\n" % (scope_s, w_type, w_name, output_dim, input_dim))
                self.wr("%s%s %s[%s];\n" % (scope_s, w_type, b_name, output_dim))

    def wr_output_defination(self, scope=None):
        """
        output変数の定義を行う。
        scopeを変更する場合は、scope引数に"extern"もしくは"static"を指定する。
        :return:
        """
        self.wr("//outputs\n")
        model_config = self.get_config()
        for l in model_config['layers']:
            name = l['name']
            class_name = l['class_name']
            layer_detal = self.compiler.get_cqt_layer_obj(name)
            o_shape = layer_detal.get_output_shape()
            dim_s = dim_str_from_keras_4d_shape_output(o_shape)

            o_name = layer_detal.get_output_variable_name()
            o_type = layer_detal.get_output_type_str()
            scope_s = add_space(scope)

            self.wr('%s%s %s%s;\n' % (scope_s, o_type, o_name, dim_s))

    def wr_assign(self, variable_name, value, tab=1):
        """
        Cの代入分を書き出す。tabでタブの個数を指定できる。
        :param variable_name: str
        :param value: str
        :param tab: int
        :return:
        """
        tabs = '\t' * tab
        if isinstance(value, list) or isinstance(value, tuple):
            for i, v in enumerate(value):
                self.wr('%s%s[%d] = %s;\n' % (tabs, variable_name, i, str(v)))
        else:
            self.wr('%s%s = %s;\n' % (tabs, variable_name, str(value)))



    def get_config(self):
        """
        Keras Modelのコンフィグ情報を返す。
        :return:
        """
        return self.compiler.model.get_config()


class CqtGenH(CFile):
    def __init__(self, file, compiler):
        super().__init__(file, compiler)

    def __del__(self):
        super().__del__()

    def generate(self):
        self.wr_file_header()
        self.wr_include('stdio.h', stdlib=True)
        self.wr_include('string.h', stdlib=True)
        self.wr_include('assert.h', stdlib=True)
        self.wr_include('cqt.h')
        self.wr_include('cqt_net.h')
        self.cr()

        self.wr('CQT_NET* cqt_init(void);\n')
        self.wr('int cqt_load_weight_from_files(CQT_NET* np, const char *path);\n')
        self.wr('int cqt_run(CQT_NET* np, void *dp);\n')
        self.cr()

        self.write_cqt_network(scope='extern')
        self.cr()

        self.wr_layer_defination(scope='extern')
        self.cr()

        self.wr_weight_defination(scope='extern')
        self.cr()

        self.wr_output_defination(scope='extern')
        self.cr()

        self.fp.write('\n')


class CqtGenC(CFile):
    def __init__(self, file, compiler):
        super().__init__(file, compiler)

    def __del__(self):
        super().__del__()

    def generate(self):
        self.wr_file_header()
        self.wr_include('cqt_gen.h')
        self.wr_include('cqt_lib.h')
        self.cr()

        self.write_cqt_network()
        self.cr()

        self.wr_layer_defination()
        self.cr()

        self.wr_weight_defination()
        self.cr()

        self.wr_output_defination()
        self.cr()

        self.write_cqt_init()
        self.cr()
        self.write_cqt_load_weight_from_files()
        self.cr()
        self.write_cqt_run()
        self.cr()

    def write_cqt_init(self):
        """
        cqt_init関数を書き出す。
        :return:
        """
        self.wr('CQT_NET* cqt_init(void) {\n')
        model_config = self.get_config()

        layer_num = len(model_config['layers'])
        cqt_net_name = self.compiler.get_model_name()
        self.wr('\t%s.layernum = %d;\n' % (cqt_net_name, layer_num))
        self.cr()

        for (i, l) in enumerate(model_config['layers']):
            name = l['name']
            class_name = l['class_name']
            layer_detal = self.compiler.get_cqt_layer_obj(name)
            self.wr('\tstrcpy(%s.layer[%d].name, "%s");\n' % (cqt_net_name, i, name))
            self.wr('\t%s.layer[%d].type = LT_%s;\n' % (cqt_net_name, i, class_name))

            # レイヤー毎の処理
            if class_name == 'InputLayer' or class_name == 'Flatten':
                # 何もしない
                pass
            elif class_name == 'Conv2D':
                self.write_conv2d_init(l)
            elif class_name == 'MaxPooling2D':
                self.write_maxpooling2d(l)
            elif class_name == 'Dense':
                self.write_dense(l)
            else:
                raise ValueError("Error layer %s tpye is not supported" % class_name)

            # 共通の処理
            for j in range(4):
                if j < len(layer_detal.input_dtypes):
                    c_type = conv_type_cqt_to_c(layer_detal.input_dtypes[j])
                    self.wr('\t%s.layer[%d].input_dtypes[%d] = %s;\n' % (cqt_net_name, i, j, c_type))
                else:
                    self.wr('\t%s.layer[%d].input_dtypes[%d] = CQT_DTYPE_NONE;\n' % (cqt_net_name, i, j))

            for j in range(4):
                    if j < len(layer_detal.weight_dtypes):
                        c_type = conv_type_cqt_to_c(layer_detal.weight_dtypes[j])
                        self.wr('\t%s.layer[%d].weight_dtypes[%d] = %s;\n' % (cqt_net_name, i, j, c_type))
                    else:
                        self.wr('\t%s.layer[%d].weight_dtypes[%d] = CQT_DTYPE_NONE;\n' % (cqt_net_name, i, j))

            for j in range(4):
                if j < len(layer_detal.output_dtypes):
                    c_type = conv_type_cqt_to_c(layer_detal.output_dtypes[j])
                    self.wr('\t%s.layer[%d].output_dtypes[%d] = %s;\n' % (cqt_net_name, i, j, c_type))
                else:
                    self.wr('\t%s.layer[%d].output_dtypes[%d] = CQT_DTYPE_NONE;\n' % (cqt_net_name, i, j))

            i_shape = [0 if x is None else x for x in layer_detal.get_input_shape()]
            if len(i_shape) == 4:
                self.wr('\t%s.layer[%d].cqt_input_shape[0] = %d;\n' % (cqt_net_name, i, i_shape[0]))
                self.wr('\t%s.layer[%d].cqt_input_shape[1] = %d;\n' % (cqt_net_name, i, i_shape[1]))
                self.wr('\t%s.layer[%d].cqt_input_shape[2] = %d;\n' % (cqt_net_name, i, i_shape[2]))
                self.wr('\t%s.layer[%d].cqt_input_shape[3] = %d;\n' % (cqt_net_name, i, i_shape[3]))
            elif len(o_shape) == 3:
                self.wr('\t%s.layer[%d].cqt_input_shape[0] = %d;\n' % (cqt_net_name, i, i_shape[0]))
                self.wr('\t%s.layer[%d].cqt_input_shape[1] = %d;\n' % (cqt_net_name, i, i_shape[1]))
                self.wr('\t%s.layer[%d].cqt_input_shape[2] = %d;\n' % (cqt_net_name, i, i_shape[2]))
                self.wr('\t%s.layer[%d].cqt_input_shape[3] = 0;\n' % (cqt_net_name, i))
            elif len(o_shape) == 2:
                self.wr('\t%s.layer[%d].cqt_input_shape[0] = %d;\n' % (cqt_net_name, i, i_shape[0]))
                self.wr('\t%s.layer[%d].cqt_input_shape[1] = %d;\n' % (cqt_net_name, i, i_shape[1]))
                self.wr('\t%s.layer[%d].cqt_input_shape[2] = 0;\n' % (cqt_net_name, i))
                self.wr('\t%s.layer[%d].cqt_input_shape[3] = 0;\n' % (cqt_net_name, i))
            elif len(o_shape) == 1:
                self.wr('\t%s.layer[%d].cqt_input_shape[0] = %d;\n' % (cqt_net_name, i, i_shape[0]))
                self.wr('\t%s.layer[%d].cqt_input_shape[1] = 0;\n' % (cqt_net_name, i))
                self.wr('\t%s.layer[%d].cqt_input_shape[2] = 0;\n' % (cqt_net_name, i))
                self.wr('\t%s.layer[%d].cqt_input_shape[3] = 0;\n' % (cqt_net_name, i))
            else:
                raise ValueError("ERROR unsupported shape %s %s", (name, str(o_shape)))

            # Noneを0に置き換え
            o_shape = [0 if x is None else x for x in layer_detal.get_output_shape()]
            if len(o_shape) == 4:
                self.wr('\t%s.layer[%d].cqt_output_shape[0] = %d;\n' % (cqt_net_name, i, o_shape[0]))
                self.wr('\t%s.layer[%d].cqt_output_shape[1] = %d;\n' % (cqt_net_name, i, o_shape[1]))
                self.wr('\t%s.layer[%d].cqt_output_shape[2] = %d;\n' % (cqt_net_name, i, o_shape[2]))
                self.wr('\t%s.layer[%d].cqt_output_shape[3] = %d;\n' % (cqt_net_name, i, o_shape[3]))
            elif len(o_shape) == 3:
                self.wr('\t%s.layer[%d].cqt_output_shape[0] = %d;\n' % (cqt_net_name, i, o_shape[0]))
                self.wr('\t%s.layer[%d].cqt_output_shape[1] = %d;\n' % (cqt_net_name, i, o_shape[1]))
                self.wr('\t%s.layer[%d].cqt_output_shape[2] = %d;\n' % (cqt_net_name, i, o_shape[2]))
                self.wr('\t%s.layer[%d].cqt_output_shape[3] = 0;\n' % (cqt_net_name, i))
            elif len(o_shape) == 2:
                self.wr('\t%s.layer[%d].cqt_output_shape[0] = %d;\n' % (cqt_net_name, i, o_shape[0]))
                self.wr('\t%s.layer[%d].cqt_output_shape[1] = %d;\n' % (cqt_net_name, i, o_shape[1]))
                self.wr('\t%s.layer[%d].cqt_output_shape[2] = 0;\n' % (cqt_net_name, i))
                self.wr('\t%s.layer[%d].cqt_output_shape[3] = 0;\n' % (cqt_net_name, i))
            elif len(o_shape) == 1:
                self.wr('\t%s.layer[%d].cqt_output_shape[0] = %d;\n' % (cqt_net_name, i, o_shape[0]))
                self.wr('\t%s.layer[%d].cqt_output_shape[1] = 0;\n' % (cqt_net_name, i))
                self.wr('\t%s.layer[%d].cqt_output_shape[2] = 0;\n' % (cqt_net_name, i))
                self.wr('\t%s.layer[%d].cqt_output_shape[3] = 0;\n' % (cqt_net_name, i))
            else:
                raise ValueError("ERROR unsupported shape %s %s", (name, str(o_shape)))

            o_name = layer_detal.get_output_variable_name()
            self.wr('\t%s.layer[%d].param_p = &%s;\n' % (cqt_net_name, i, name))
            self.wr('\t%s.layer[%d].data_p = &%s;\n' % (cqt_net_name, i, o_name))
            self.cr()

        self.wr('\treturn NULL;\n')
        self.wr('}\n')

    def write_conv2d_init(self, l):
        """
        LY_Conv2dの初期化を書き出す。
        :param l:
        :return:
        """
        name = l['name']
        config = l['config']
        class_name = l['class_name']
        layer_detal = self.compiler.get_cqt_layer_obj(name)

        self.wr_assign("%s.filters" % name, config['filters'])
        self.wr_assign("%s.kernel_size" % name, config['kernel_size'])
        self.wr_assign("%s.strides" % name, config['strides'])
        self.wr_assign("%s.padding" % name, self.pd_dic[config['padding']])
        self.wr_assign("%s.data_format" % name, self.df_dic[config['data_format']])
        self.wr_assign("%s.dilation_rate" % name, config['dilation_rate'])
        self.wr_assign("%s.activation" % name, self.act_dic[config['activation']])
        self.wr_assign("%s.use_bias" % name, self.bool_dic[config['use_bias']])

    def write_maxpooling2d(self, l):
        """
        LY_MaxPooling2Dの初期化を書き出す。
        :param l:
        :return:
        """
        name = l['name']
        config = l['config']
        class_name = l['class_name']
        layer_detal = self.compiler.get_cqt_layer_obj(name)

        self.wr_assign("%s.strides" % name, config['strides'])
        self.wr_assign("%s.padding" % name, self.pd_dic[config['padding']])
        self.wr_assign("%s.data_format" % name, self.df_dic[config['data_format']])
        self.wr_assign("%s.pool_size" % name, config['pool_size'])

    def write_dense(self, l):
        """
        LY_Denseの初期化を書き出す。
        :param l:
        :return:
        """
        name = l['name']
        config = l['config']
        class_name = l['class_name']
        layer_detal = self.compiler.get_cqt_layer_obj(name)

        self.wr_assign("%s.units" % name, config['units'])
        self.wr_assign("%s.activation" % name, self.act_dic[config['activation']])
        self.wr_assign("%s.use_bias" % name, self.bool_dic[config['use_bias']])

    def write_cqt_load_weight_from_files(self):
        self.wr('int cqt_load_weight_from_files(CQT_NET* np, const char *path) {\n')
        self.wr('\tchar buf[CQT_MAX_PATH];\n')
        self.wr('\tsize_t path_len;\n')
        self.wr('\tsize_t fname_w_len;\n')
        self.wr('\tsize_t fname_b_len;\n')
        self.wr('\tint ret;\n')
        self.wr('\n')

        model_config = self.get_config()

        for i, l in enumerate(model_config['layers']):
            class_name = l['class_name']
            config = l['config']
            name = config['name']
            layer_detal = self.compiler.get_cqt_layer_obj(name)

            if class_name in ['Conv2D', 'Dense']:
                fname_w = name + '_W_1_z.npy'
                fname_b = name + '_b_1_z.npy'
                [variable_name_w, variable_name_w_header, variable_name_b,
                 variable_name_b_header] = layer_detal.get_conv2d_weight_variable_name()

                if class_name == 'Conv2D':
                    prev_dim = layer_detal.get_prev_layer_output_dimension(i)
                    kernel_size = config['kernel_size']
                    w_size = kernel_size[0] * kernel_size[1] * config['filters'] * prev_dim
                    b_size = config['filters']
                else:
                    # dense
                    prev_dim = layer_detal.get_prev_layer_output_dimension(i)
                    i_shape = layer_detal.get_input_shape()
                    o_shape = layer_detal.get_output_shape()
                    w_size = i_shape[-1] * o_shape[-1]
                    b_size = o_shape[-1]

                self.wr('// %s\n' % name)
                self.wr('\tpath_len = strlen(path);\n')
                self.wr('\tfname_w_len = strlen("%s");\n' % fname_w)
                self.wr('\tfname_b_len = strlen("%s");\n' % fname_b)
                self.wr('\tassert(path_len+fname_w_len<CQT_MAX_PATH);\n')
                self.wr('\tassert(path_len+fname_b_len<CQT_MAX_PATH);\n')
                self.cr()
                self.wr('\tstrcpy(buf, path);\n')
                self.wr('\tstrcat(buf, "%s");\n' % fname_w)
                self.wr(
                    '\tret = load_from_numpy(%s, buf, %d, &%s);\n' % (variable_name_w, w_size, variable_name_w_header))
                self.wr('\tif(ret != CQT_RET_OK){\n')
                self.wr('\t\treturn ret;\n')
                self.wr('\t}\n')
                self.wr('\tstrcpy(buf, path);\n')
                self.wr('\tstrcat(buf, "%s");\n' % fname_b)
                self.wr('\tret = load_from_numpy(%s, buf, %d, &%s);\n' % (variable_name_b, b_size, variable_name_b_header))
                self.wr('\tif(ret != CQT_RET_OK){\n')
                self.wr('\t\treturn ret;\n')
                self.wr('\t}\n')

                self.cr()

        self.wr('\treturn CQT_RET_OK;\n')
        self.wr('}\n')

    def write_cqt_run(self):
        self.wr('int cqt_run(CQT_NET* np, void *dp) {\n')
        self.wr('\tint ret;\n')
        self.cr()

        model_config = self.get_config()
        cqt_net_name = self.compiler.get_model_name()

        for i, l in enumerate(model_config['layers']):
            class_name = l['class_name']
            config = l['config']
            name = config['name']
            layer_detal = self.compiler.get_cqt_layer_obj(name)

            inp = self.compiler.get_prev_layer_output_name(i)
            outp = layer_detal.get_output_variable_name()
            func_name = layer_detal.make_func_name()
            self.wr('\t//%s\n' % name)
            self.wr("\tret = %s(&(%s.layer[%d]), %s, %s);\n" % (func_name, cqt_net_name, i, inp, outp))
            self.wr('\tif(ret != CQT_RET_OK){\n')
            self.wr('\t\treturn ret;\n')
            self.wr('\t}\n')
            self.wr('\n')

        self.wr('\treturn CQT_RET_OK;\n')
        self.wr('}\n')


class CqtLibH(CFile):
    def __init__(self, file, compiler):
        super().__init__(file, compiler)

    def __del__(self):
        super().__del__()

    def generate(self):
        self.wr_file_header()
        self.wr_include('cqt.h')
        self.wr_include('cqt_net.h')
        self.cr()

        model_config = self.get_config()
        cqt_net_name = self.compiler.get_model_name()

        func_list = []

        for i, l in enumerate(model_config['layers']):
            class_name = l['class_name']
            config = l['config']
            name = config['name']
            layer_detal = self.compiler.get_cqt_layer_obj(name)

            func_name = layer_detal.make_func_name()
            if not func_name in func_list:
                self.wr('int %s(CQT_LAYER *lp, void *inp, void *outp);\n' % func_name)
                func_list.append(func_name)

        self.cr()


def create_c_dir(tdir):
    """
    tdir以下に以下のディレクトリを作成する。
    inc, cqt_gen, cqt_lib, weight
    :param tdir: str
    :return:
    """
    dirs = ['inc', 'cqt_gen', 'cqt_lib', 'weight']
    for d in dirs:
        path = os.path.join(tdir, d)
        if not os.path.isdir(path):
            os.makedirs(path)


def dim_str_from_keras_4d_shape(shape):
    assert(len(shape)==4)
    if shape[3] is None:
        return "[%d][%d][%d]" % (shape[2], shape[1], shape[0])
    else:
        return "[%d][%d][%d][%d]" % (shape[3], shape[2], shape[1], shape[0])


def dim_str_from_keras_4d_shape_output(shape):
    if len(shape) == 4:
        return "[%d][%d][%d]" % (shape[3], shape[2], shape[1])
    elif len(shape) == 3:
        return "[%d][%d]" % (shape[2], shape[1])
    elif len(shape) == 2:
        return "[%d]" % shape[1]
    else:
        return ""


def dim_str_from_keras_4d_shape_bias(shape):
    assert(len(shape)==4)
    if (shape[3] is None) and (shape[2] is None) and (shape[1] is None):
        return "[%d]" % shape[0]
    elif (shape[3] is None) and (shape[2] is None):
        return "[%d]" % shape[1]
    elif shape[3] is None:
        return "[%d]" % shape[2]
    else:
        return "[%d]" % shape[3]


def add_space(s):
    """
    引数の文字列が空文字列でなかったら、末尾にスペースを追加した文字列を返す。
    引数が空文字列の場合は、空文字列を返す。
    :param s: str
    :return: str
    """
    if s is None:
        return  ''
    else:
        return s + ' '

def conv_type_cqt_to_c(cqt_type):
    """
    コキュートスの型情報から、Ｃの型情報（NN_DTYPE 文字列）を返す。
    :param cqt_type:
    :return:  str
    """
    dic = {CQT_Dtype.INT8: 'CQT_INT8', CQT_Dtype.UINT8: 'CQT_UINT8',
           CQT_Dtype.FLOAT32: 'CQT_FLOAT32', CQT_Dtype.NONE: 'CQT_DTYPE_NONE'}
    return dic[cqt_type]

