from nose.tools import assert_almost_equals
import numpy as np

from localController import *

pb=5
pd=10

capacity_scaling_factor=0.000303810674805
revenue = Revenue(gamma=2.28e-6/capacity_scaling_factor, k=0.7, beta=1.0)
assert_almost_equals(compute_optimal_cd(pd, revenue, None, [1, 30]), 1) # ???

xc = np.array([0  , 1  , 2  , 3  , 4  , 5  , 6  ])
fc = np.array([0.1, 0.1, 0.2, 0.3, 0.2, 0.1, 0.1])
assert_almost_equals(compute_optimal_cd(pd, revenue, fc, xc), 0)
