# -*- coding: utf-8 -*-

import time
import numpy as np
from amplify import VariableGenerator, one_hot, Poly, einsum, FixstarsClient, solve

client = None

def tp_init(token):
    # クライアントの設定
    global client
    client = FixstarsClient()  # Fixstars Amplify AE
    client.parameters.timeout = 1000  # タイムアウト1秒
    client.token = token  # ご自身のトークンを入力

    #global dw_sampler
    #endpoint = "https://cloud.dwavesys.com/sapi/"
    #solver = "Advantage_system4.1" #以下参照
    tm4 = time.perf_counter()
    #dw_sampler = DWaveSampler(solver = solver, token = token, endpoint = endpoint)

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
    result = solver.run(qubo, shots=100)
    '''
    sp = []
    for i in range(N):
        for j in range(N):
            sp.append("q" + str(i) + "_" + str(j))
    Q = {}
    for i in range(N*N):
        for j in range(N*N):
            if ((sp[i], sp[j]) in qubo):
                Q[(i, j)] = qubo[(sp[i], sp[j])]

    f = BinaryPoly(Q)
    model0 = BinaryQuadraticModel(f)

    # マシンを実行
    solver = Solver(client)  # ソルバーに使用するクライアントを設定
    result = solver.solve(model0)  # 問題を入力してマシンを実行


    # 判り易いように
    route = []
    rroute = []
    details = []
    arr = np.array([result[0].values[j] for j in range(N*N)]).reshape(N, N)
    for i in arr:
        if 1 in i:
            idx = np.where(i==1)[0][0]
            route.append(int(idx))
            rroute.append(int(M[idx]))
        else:
            print('エラー')
            return {'time': [tm2-tm1,tm3-tm2]}
            #return {'time': [tm2-tm1,tm3-tm2,tm4-tm3,tm5-tm4]}
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
        'time': [tm2-tm1,tm3-tm2]
        #'time': [tm2-tm1,tm3-tm2,tm4-tm3,tm5-tm4,tm6-tm5]
    }
    #print(ret)
    return ret

def tp_tsp(table):
    L = np.array(table)
    N = L.shape[0]
    M = np.array(range(len(table[0])))

    gen = VariableGenerator()
    q = gen.array("Binary", (N, N))

    # スタートは
    q[0,0] = 1

    # 最後は
    q[N-1,N-1]=1

    # 1番目に訪れる都市は1つだけにしたい
    constraints2 = one_hot(q, axis=1)

    # 都市Aに訪れる順番は1つだけにしたい
    constraints3 = one_hot(q, axis=0)

    # 都市間の距離に比例したペナルティ
    # n番目からn+1番目への移動について
    # q1 = q[:-1]
    # q2 = q[1:]
    # route_length: Poly = einsum("ij,ki,kj->", L, q1, q2)
    route_length = 0
    for k in range(N-1):
        for i in range(N):
            for j in range(N):
                route_length += L[i, j] * q[k, i] * q[k + 1, j]

    # コンパイル
    model = route_length + (constraints2 + constraints3) * np.max(L)

    result = solve(model, client)

    # 判り易いように
    route = []
    rroute = []
    details = []
    arr = q.evaluate(result.best.values).reshape(N, N)
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
            'time': float(L[route[i], route[i+1]]),
        }
        details.append(detail)

    ret = {
        'route': rroute,
        'details': details,
    }
    #print(ret)
    return ret
