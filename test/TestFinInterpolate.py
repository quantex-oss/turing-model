import numpy as np
import math
import matplotlib.pyplot as plt

import sys
sys.path.append("..")

from turing_models.market.curves.interpolator import TuringInterpolator, TuringInterpTypes

from TuringTestCases import TuringTestCases, globalTestCaseMode
testCases = TuringTestCases(__file__, globalTestCaseMode)

PLOT_GRAPHS = False

###############################################################################


def test_FinInterpolate():

    import time

    xValues = np.array([0.25, 0.5, 0.75, 1.0, 2.0, 3.0, 5.0, 10.0])
    a = -0.1
    b = 0.002

    yValues = []
    for x in xValues:
        y = math.exp(a * x + b * x * x)
        yValues.append(y)

    yValues = np.array(yValues)

    xInterpolateValues = np.linspace(0.0, 10.0, 20)

    testCases.header("METHOD", "X", "Y_INTERPOLATED")

    for interpType in TuringInterpTypes:

        yInterpValues = []
        start = time.time()

        interpolator = TuringInterpolator(interpType)
        interpolator.fit(xValues, yValues)

        for x in xInterpolateValues:
            y_int = interpolator.interpolate(x)
            testCases.print(interpType, x, y_int)
            yInterpValues.append(y_int)

        end = time.time()

        if PLOT_GRAPHS:
            plt.figure(figsize=(12, 10))
            plt.plot(xValues, yValues, color='r', marker='o')
            plt.plot(xInterpolateValues, yInterpValues, color='b',
                     label=str(interpType))
            plt.legend()

    xp = np.array([0.2, 0.4, 0.45, 0.6, 0.82, 0.93, 0.99])
    yp = np.array([0.4, 0.9, 0.32, 0.2, 0.22, 0.10, 0.28])
    n = 10000

    testCases.header("LABEL", "TIME")
    interpolator = TuringInterpolator(interpType)
    interpolator.fit(xp, yp)
    
    start = time.time()
    for i in range(0, n):
        interpolator.interpolate(0.8)
    end = time.time()
    testCases.print("10000 Interpolations", end - start)

###############################################################################


test_FinInterpolate()
testCases.compareTestCases()