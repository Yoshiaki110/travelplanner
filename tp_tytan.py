# -*- coding: utf-8 -*-

from tytan import *
import numpy as np
from dwave.system import DWaveSampler, EmbeddingComposite

def tp_api(indexs, table, token):
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
                H += 0.1 * L[l, c] * (q[n, c] * q[n + 1, l])

    # スタートは
    H += (q[0, 0] - 1)**2

    # 最後は
    H += (q[N - 1, N - 1] - 1)**2

    # 最後はE
    H += (q[N - 1, N - 1] - 1) ** 2

    # コンパイル
    qubo, offset = Compile(H).get_qubo()
    print(f'offset\n{offset}')

    '''
    # サンプラー選択
    solver = sampler.SASampler()
    # サンプリング
    result = solver.run(qubo, shots=20)
    '''
    endpoint = "https://cloud.dwavesys.com/sapi/"
    solver = "Advantage_system4.1" #以下参照
    dw_sampler = DWaveSampler(solver = solver, token = token, endpoint = endpoint)
    #指定したD-Waveマシン上でのQBITの自動割当を準備
    sampler = EmbeddingComposite(dw_sampler)
    # quboの入力
    result = sampler.sample_qubo(qubo, num_reads=10).record

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
            return {}
    print(route)
    for i in range(len(route) - 1):
        print(route[i], route[i+1], L[route[i], route[i+1]])
        detail = {
            'from': int(M[route[i]]),
            'to': int(M[route[i+1]]),
            'distance': float(L[route[i], route[i+1]]),
        }
        details.append(detail)

    ret = {
        'route': rroute,
        'details': details
    }
    print(ret)
    return ret
