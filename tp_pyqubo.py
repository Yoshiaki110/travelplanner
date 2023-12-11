# -*- coding: utf-8 -*-

import numpy as np
from openjij import SQASampler

def tp_api(indexs, table):
    L = np.array(table)
    L = np.delete(L, indexs, 0)
    L = np.delete(L, indexs, 1)
    #L = np.array([[1000, 30, 20, 50, 40],
    #            [30, 1000, 10, 30, 20],
    #            [20, 10, 1000, 30, 20],
    #            [50, 30, 30, 1000, 10],
    #            [40, 20, 20, 10, 1000]])

    # 都市数
    N = L.shape[0]

    M = np.array(range(len(table[0])))
    M = np.delete(M, indexs, 0)

    #quboの定式
    from pyqubo import Array, Constraint, Placeholder
    x = Array.create('x', shape=(N+1, N), vartype='BINARY')

    # 目的関数
    cost = 0
    for t in range(N):
        for j in range(N):
            for k in range(N):
                cost = cost + L[j][k]*x[t][j]*x[t+1][k]

    # 制約条件1(出発都市以外は1度だけ訪れる)
    constr_1 = 0
    for j in range(1, N):
        constr_1 += (np.sum(x.T[j])-1)**2

    # 制約条件2(出発都市と到着都市の指定)
    #constr_2 = 2-x[0][0]-x[4][0]
    constr_2 = 2-x[0][0]-x[N][0]

    # 制約条件3(同時に複数都市を訪れない)¶
    constr_3 = 0
    for i in range(N+1):
        constr_3 += (np.sum(x[i])-1)**2
        
    # 制約条件4(出発都市の来訪回数)
    # constr_4 = (np.sum(x.T[0])-2)**2

    # コスト関数
    cost_func = cost + Placeholder('lam1')*Constraint(constr_1, label='constr_1') \
                    + Placeholder('lam2')*Constraint(constr_2, label='constr_2') \
                    + Placeholder('lam3')*Constraint(constr_3, label='constr_3') # \
                    # + Placeholder('lam4')*Constraint(constr_3, label='constr_4')
    model = cost_func.compile()

    # パラメータの設定
    feed_dict = {'lam1': 200.0, 
                'lam2': 300.0, 
                'lam3': 100.0}
                # 'lam4': 300.0} # penalty係数

    # dict形式のQUBO
    qubo, offset = model.to_qubo(feed_dict=feed_dict)

    sampler = SQASampler()

    # quboの入力
    sampleset = sampler.sample_qubo(qubo, num_reads=100)
    # 結果出力
    print(sampleset.record)
    # 00 h 00 m 00.013 s


    # 制約条件を守っているかどうかの情報を得ることができる
    decoded_samples = model.decode_sampleset(sampleset=sampleset, feed_dict=feed_dict)

    # 後半の5つの出力結果が制約条件破ってる
    for sample in decoded_samples:
        print(sample.constraints(only_broken=True))
    # {}
    # {'constr_3': (False, 1.0)}
    # {'constr_3': (False, 1.0)}

    # 出力結果の確認
    # 順路：A→D→C→B→A
    print(sampleset.record[0][0].reshape(N+1, N))

    route = []
    rroute = []
    details = []
    arr = sampleset.record[0][0].reshape(N+1, N)
    for i in arr:
        if 1 in i:
            idx = np.where(i==1)[0][0]
            route.append(int(idx))
            rroute.append(int(M[idx]))
        else:
            print('エラー')
            return {}
    #print(route)
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
    #print(ret)
    '''
    ret = {
        'route': [0, 2, 4, 3, 1, 0],
        'details': [
            {'from': 0, 'to': 2, 'distance': 20},
            {'from': 2, 'to': 4, 'distance': 20},
            {'from': 4, 'to': 3, 'distance': 10},
            {'from': 3, 'to': 1, 'distance': 30},
            {'from': 1, 'to': 0, 'distance': 30}
        ]
    }
    print(ret)
    '''
    return ret
