import numpy as np

import sys
sys.path.append("..")

from turing_models.market.curves.discount_curve_poly import TuringDiscountCurvePoly
from turing_models.utilities.turing_date import TuringDate

from TuringTestCases import TuringTestCases, globalTestCaseMode
testCases = TuringTestCases(__file__, globalTestCaseMode)

##############################################################################
# TODO
# Inherit from TuringDiscountCurve and add df method
# Put in a convention for the rate
# Use Frequency object
##############################################################################

PLOT_GRAPHS = False

def test_FinDiscountCurvePolynomial():

    times = np.linspace(0.00, 10.0, 21)
    curveDate = TuringDate(2, 2, 2019)
    dates = curveDate.addYears(times)
    coeffs = [0.0004, -0.0001, 0.00000010]
    curve1 = TuringDiscountCurvePoly(curveDate, coeffs)
    zeros = curve1.zeroRate(dates)
    fwds = curve1.fwd(dates)

    if PLOT_GRAPHS:
        import matplotlib.pyplot as plt
        plt.figure(figsize=(6, 4))
        plt.plot(times, zeros, label="Zeros")
        plt.plot(times, fwds, label="Forwards")
        plt.xlabel('Time (years)')
        plt.ylabel('Zero Rate')
        plt.legend(loc='best')


test_FinDiscountCurvePolynomial()
testCases.compareTestCases()
