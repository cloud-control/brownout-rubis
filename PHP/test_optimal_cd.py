from __future__ import print_function

from nose.tools import assert_almost_equals
import numpy as np

from localController import *

def toNpArray(line):
    return np.array(map(float, line.split(',')[:-1]))

core_cap = 2926
gamma = 0.08/(12*core_cap)
rev = Revenue(gamma=gamma, beta=1, k=0.7)
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
    cb_o, cd_o = compute_optimal_cb_cd(rev, pb, pd, fc, xc)
    assert_almost_equals(cb_o, cb)
    assert_almost_equals(cd_o, cd)
