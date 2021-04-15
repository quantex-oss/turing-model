###############################################################################
# Copyright (C) 2018, 2019, 2020 Dominic O'Kane
###############################################################################

import numpy as np

import sys
sys.path.append("..")

from turing_models.products.credit.turing_cds import TuringCDS
from turing_models.products.rates.turing_ibor_swap import TuringIborSwap
from turing_models.products.credit.turing_cds_curve import TuringCDSCurve
from turing_models.products.rates.turing_ibor_single_curve import TuringIborSingleCurve
from turing_models.turingutils.turing_frequency import TuringFrequencyTypes
from turing_models.turingutils.turing_day_count import TuringDayCountTypes
from turing_models.turingutils.turing_date import TuringDate
from turing_models.turingutils.turing_global_types import TuringSwapTypes

from TuringTestCases import TuringTestCases, globalTestCaseMode
testCases = TuringTestCases(__file__, globalTestCaseMode)

###############################################################################


def test_FinCDSCurve():

    curveDate = TuringDate(20, 12, 2018)

    swaps = []
    depos = []
    fras = []

    fixedDCC = TuringDayCountTypes.ACT_365F
    fixedFreq = TuringFrequencyTypes.SEMI_ANNUAL
    fixedCoupon = 0.05

    for i in range(1, 11):

        maturityDate = curveDate.addMonths(12 * i)
        swap = TuringIborSwap(curveDate,
                              maturityDate,
                              TuringSwapTypes.PAY,
                              fixedCoupon,
                              fixedFreq,
                              fixedDCC)
        swaps.append(swap)

    libor_curve = TuringIborSingleCurve(curveDate, depos, fras, swaps)

    cdsContracts = []

    for i in range(1, 11):
        maturityDate = curveDate.addMonths(12 * i)
        cds = TuringCDS(curveDate, maturityDate, 0.005 + 0.001 * (i - 1))
        cdsContracts.append(cds)

    issuerCurve = TuringCDSCurve(curveDate,
                                 cdsContracts,
                                 libor_curve,
                                 recoveryRate=0.40,
                                 useCache=False)

    testCases.header("T", "Q")
    n = len(issuerCurve._times)
    for i in range(0, n):
        testCases.print(issuerCurve._times[i], issuerCurve._values[i])

    testCases.header("CONTRACT", "VALUE")
    for i in range(1, 11):
        maturityDate = curveDate.addMonths(12 * i)
        cds = TuringCDS(curveDate, maturityDate, 0.005 + 0.001 * (i - 1))
        v = cds.value(curveDate, issuerCurve)
        testCases.print(i, v)

    if 1 == 0:
        x = [0.0, 1.2, 1.6, 1.7, 10.0]
        qs = issuerCurve.survProb(x)
        print("===>", qs)

        x = [0.3, 1.2, 1.6, 1.7, 10.0]
        xx = np.array(x)
        qs = issuerCurve.survProb(xx)
        print("===>", qs)

        x = [0.3, 1.2, 1.6, 1.7, 10.0]
        dfs = issuerCurve.df(x)
        print("===>", dfs)

        x = [0.3, 1.2, 1.6, 1.7, 10.0]
        xx = np.array(x)
        dfs = issuerCurve.df(xx)
        print("===>", dfs)

###############################################################################


test_FinCDSCurve()
testCases.compareTestCases()
