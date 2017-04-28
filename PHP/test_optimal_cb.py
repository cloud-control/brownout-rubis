from nose.tools import assert_almost_equals

from localController import *

assert_almost_equals(compute_optimal_cb(1, 10, None, [1, 30]), 3.9)

xc = [0  , 1  , 2  , 3  , 4  , 5  , 6  ]
fc = [0.1, 0.1, 0.2, 0.3, 0.2, 0.1, 0.1]
assert_almost_equals(compute_optimal_cb(1, 10, fc, xc), 5)

assert_almost_equals(compute_optimal_cb(1, 2, fc, xc), 3)
