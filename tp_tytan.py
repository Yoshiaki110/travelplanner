# -*- coding: utf-8 -*-

import time
from tytan import *
import numpy as np
from dwave.system import DWaveSampler, EmbeddingComposite

dw_sampler = {}

def tp_init(token):
    global dw_sampler
    endpoint = "https://cloud.dwavesys.com/sapi/"
    solver = "Advantage_system4.1" #以下参照
    tm4 = time.perf_counter()
    dw_sampler = DWaveSampler(solver = solver, token = token, endpoint = endpoint)

def tp_api(indexs, table):
    tm1 = time.perf_counter()
    L = np.array(table)
    L = np.delete(L, indexs, 0)
    L = np.delete(L, indexs, 1)

    N = L.shape[0]

    M = np.array(range(len(table[0])))
    M = np.delete(M, indexs, 0)

    # 量子ビットを用意する
    q = symbols_list([N, N], 'q{}_{}')
    #print(q)

    H = 0

    # 1番目に訪れる都市は1つだけにしたい
    for l in range(N):
        H += (sum(q[l, c]  for c in range(N)) - 1) ** 2

    # 都市Aに訪れる順番は1つだけにしたい
    for c in range(N):
        H += (sum(q[l, c]  for l in range(N)) - 1) ** 2

    # 都市間の距離に比例したペナルティ
    # n番目からn+1番目への移動について
    for l in range(N):
        for c in range(N):
            for n in range(N - 1):
                H += 0.01 * L[l, c] * (q[n, c] * q[n + 1, l])

    # スタートは
    H += (q[0, 0] - 1) ** 2

    # 最後は
    H += (q[N - 1, N - 1] - 1) ** 2

    # コンパイル
    tm2 = time.perf_counter()
    qubo, offset = Compile(H).get_qubo()
    print(f'offset\n{offset}')
    tm3 = time.perf_counter()

    '''
    # サンプラー選択
    solver = sampler.SASampler()
    # サンプリング
    result = solver.run(qubo, shots=20)
    '''
    #指定したD-Waveマシン上でのQBITの自動割当を準備
    sampler = EmbeddingComposite(dw_sampler)
    tm4 = time.perf_counter()
    # quboの入力
    result = sampler.sample_qubo(qubo, num_reads=10).record
    tm5 = time.perf_counter()

    # 上位5件
    for r in result[:1]:
        print(r)
    #print(np.array(list(r[0].values())).reshape(N, N))
    print(np.array(list(r[0])).reshape(N, N))

    # 判り易いように
    route = []
    rroute = []
    details = []
    #arr = np.array(list(result[0][0].values())).reshape(N, N)
    arr = np.array(list(result[0][0])).reshape(N, N)
    for i in arr:
        if 1 in i:
            idx = np.where(i==1)[0][0]
            route.append(int(idx))
            rroute.append(int(M[idx]))
        else:
            print('エラー')
            return {'time': [tm2-tm1,tm3-tm2,tm4-tm3,tm5-tm4]}
    print(route)
    for i in range(len(route) - 1):
        print(route[i], route[i+1], L[route[i], route[i+1]])
        detail = {
            'from': int(M[route[i]]),
            'to': int(M[route[i+1]]),
            'distance': float(L[route[i], route[i+1]]),
        }
        details.append(detail)

    tm6 = time.perf_counter()
    ret = {
        'route': rroute,
        'details': details,
        'time': [tm2-tm1,tm3-tm2,tm4-tm3,tm5-tm4,tm6-tm5]
    }
    #print(ret)
    return ret
