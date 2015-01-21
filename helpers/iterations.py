# -*- coding:utf-8 -*-
__author__ = u'Joël Vogt'
# from multiprocessing import Process, Pool
# import numpy as np
# def rmap(func, args, kwargs):
#     pool = Pool(3)
#     def onCall(*args, **kwargs):
#         p = Process(func, args=args,kwargs=kwargs)
#         results = p.start()
#         return results
#     # print(func)
#     # print(data)
#     results = pool.map(m.sum_matrix, [np.random.rand(100,2),np.random.rand(100,2),np.random.rand(100,2)])
#
#     print(results)
#     pool.close()
#     pool.join()
#     return results
#
# def onCall(func, *args, **kwargs):
#     def wrapper(func):
#         def ret(r, *args, **kwargs):
#             r.append(func(*args, **kwargs))
#         return ret
#     returnval = []
#     p = Process(target=wrapper(func), args=(returnval *args),kwargs=kwargs)
#     results = p.start()
#
#     return results
#
# def foo(a):
#     print a
#     return a + 10
#
#
# print onCall(foo, 2)