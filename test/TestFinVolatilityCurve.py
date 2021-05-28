import numpy as np
import sys
sys.path.append("..")

from fundamental.market.volatility.equity_vol_curve import TuringEquityVolCurve
from turing_models.utilities.turing_date import TuringDate

from TuringTestCases import TuringTestCases, globalTestCaseMode
testCases = TuringTestCases(__file__, globalTestCaseMode)

PLOT_GRAPHS = False

###############################################################################


def test_FinVolatilityCurve():

    valueDate = TuringDate(20, 6, 2012)
    expiryDate = TuringDate(20, 12, 2012)
    strikes = np.linspace(70, 130, 7)
    vols = np.array([0.23, 0.24, 0.267, 0.29, 0.31, 0.33, 0.35])
    polynomial = 5
    volCurve = TuringEquityVolCurve(valueDate, expiryDate,
                                    strikes, vols, polynomial)

    interpStrikes = np.linspace(50, 150, 10)
    interpVols = volCurve.volatility(interpStrikes)

    if PLOT_GRAPHS:
        import matplotlib.pyplot as plt
        plt.plot(strikes, vols, 'o', interpStrikes, interpVols)
        plt.show()

###############################################################################


test_FinVolatilityCurve()
testCases.compareTestCases()
