from __future__ import print_function

from nose.tools import assert_almost_equals
import numpy as np

from localController import *

pb=5
pd=10

capacity_scaling_factor=3.03810674805e-05
revenue = Revenue(gamma=2.28e-6/capacity_scaling_factor, k=0.7, beta=1.0)
compute_optimal_cd(pd, revenue, None, [1, 30])

xc = np.array([0  , 1  , 2  , 3  , 4  , 5  , 6  ])
fc = np.array([0.1, 0.1, 0.2, 0.3, 0.2, 0.1, 0.1])
compute_optimal_cd(pd, revenue, fc, xc)

def toNpArray(line):
    return np.array(map(float, line.split(',')[:-1]))

rev = Revenue(gamma=2.28e-6, beta=1, k=0.7)
for i, pb, pd, cb, cd, xc, fc in zip(
        xrange(100),
        map(float, open('pricing_tests/pb.out').readlines()),
        map(float, open('pricing_tests/pd.out').readlines()),
        map(float, open('pricing_tests/gd_or_cb.out').readlines()),
        map(float, open('pricing_tests/gd_or_cd.out').readlines()),
        map(toNpArray, open('pricing_tests/xc.out').readlines()),
        map(toNpArray, open('pricing_tests/fc.out').readlines()),
    ):
    
    print('Test', i)
    assert_almost_equals(compute_optimal_cb(pb, pd, fc, xc), cb)
    assert_almost_equals(compute_optimal_cd(pd, rev, fc, xc), cd)
