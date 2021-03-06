import os
import numpy as np
import matplotlib.pyplot as plt
import seaborn
import sys

keras_dir = '../../example/vgg16/keras/output/'
cqt_dir = '../../example/vgg16/c_fix/output/'
qp_file = '../../examplevgg16/c_fix/weight/'

fix16mode = True

def layer_dump(i, q, fnum = 3):
    """
    引数で指定されたレイヤーの、Keras出力と、コキュートス出力を
    比較して、画像に落とす。比較するフィルターは先頭から、fnum
    まで。
    出力はoutputディレクトリーに行われる。
    :param i:int レイヤー番号
    :param q:int 出力データのQ位置
    :param fnum:int 画像化するフィルター数
    :return:
    """

    for f in range(fnum):
        plt.figure()
        graph_name = 'l%02d_%d' % (i, f)
        kname = os.path.join(keras_dir+'l%02d_%d.npy' % (i, f))
        cname = os.path.join(cqt_dir+'l%02d_%d.npy' % (i, f))
        k_data_1 = np.load(kname)
        c_data_1 = np.load(cname)
        k_data = k_data_1.flatten()
        c_data = c_data_1.flatten()


        if fix16mode:
            c_data = c_data.astype(np.float32) / (2 ** q)

        x = np.arange(len(k_data))
        plt.plot(x, k_data, color='b', label='Keras')
        plt.plot(x, c_data, color='r', label='Cocytus')
        plt.title(graph_name)
        plt.legend()

        img_fname = os.path.join('output', graph_name+'.png')
        print('save %s' % img_fname)
        plt.savefig(img_fname)

        plt.figure()
        plt.plot(x, k_data - c_data, color='g', label='diff')
        plt.title(graph_name+'diff')
        plt.legend()
        img_fname = os.path.join('output', graph_name + '_diff.png')
        plt.savefig(img_fname)


def read_qpfile(odir):
    """qpファイルを読み込み、入力、出力、重みのＱ位置をリストにして返す"""
    iqs = []
    wqs = []
    oqs = []
    fname = os.path.join(odir, 'qp.txt')

    for i, l in enumerate(open(fname).readlines()):
        if i < 1:
            continue
        words = l.split(',')
        iqs.append(int(words[0]))
        oqs.append(int(words[1]))
        wqs.append(int(words[2]))

    return iqs, oqs, wqs


#iqs, oqs, wqs = read_qpfile(qp_file)

#for i in range(31):
#    layer_dump(i, oqs[i])
layer_dump(15, 3)

print('finish')