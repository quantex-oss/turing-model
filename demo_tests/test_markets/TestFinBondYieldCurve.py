import datetime as dt
import os

import sys
sys.path.append("..")

from turing_models.utilities.frequency import TuringFrequencyTypes
from turing_models.utilities.day_count import TuringDayCountTypes
from turing_models.utilities.turing_date import TuringDate, fromDatetime
from turing_models.products.bonds.bond import TuringBond
from turing_models.products.bonds.bond_yield_curve import TuringBondYieldCurve
from turing_models.products.bonds.bond_yield_curve_model import *

from TuringTestCases import TuringTestCases, globalTestCaseMode
testCases = TuringTestCases(__file__, globalTestCaseMode)

###############################################################################
###############################################################################


def test_FinBondYieldCurve():

    ###########################################################################

    import pandas as pd
    path = os.path.join(os.path.dirname(__file__), './data/giltBondPrices.txt')
    bondDataFrame = pd.read_csv(path, sep='\t')
    bondDataFrame['mid'] = 0.5*(bondDataFrame['bid'] + bondDataFrame['ask'])

    freqType = TuringFrequencyTypes.SEMI_ANNUAL
    accrualType = TuringDayCountTypes.ACT_ACT_ICMA
    settlement = TuringDate(19, 9, 2012)

    bonds = []
    ylds = []

    for _, bond in bondDataFrame.iterrows():

        dateString = bond['maturity']
        matDatetime = dt.datetime.strptime(dateString, '%d-%b-%y')
        maturityDt = fromDatetime(matDatetime)
        issueDt = TuringDate(maturityDt._d, maturityDt._m, 2000)
        coupon = bond['coupon']/100.0
        cleanPrice = bond['mid']
        bond = TuringBond(issueDt, maturityDt, coupon, freqType, accrualType)
        yld = bond.yieldToMaturity(settlement, cleanPrice)
        bonds.append(bond)
        ylds.append(yld)

###############################################################################

    curveFitMethod = TuringCurveFitPolynomial()
    fittedCurve1 = TuringBondYieldCurve(settlement, bonds, ylds, curveFitMethod)
#    fittedCurve1.display("GBP Yield Curve")

    curveFitMethod = TuringCurveFitPolynomial(5)
    fittedCurve2 = TuringBondYieldCurve(settlement, bonds, ylds, curveFitMethod)
#    fittedCurve2.display("GBP Yield Curve")

    curveFitMethod = TuringCurveFitNelsonSiegel()
    fittedCurve3 = TuringBondYieldCurve(settlement, bonds, ylds, curveFitMethod)
#    fittedCurve3.display("GBP Yield Curve")

    curveFitMethod = TuringCurveFitNelsonSiegelSvensson()
    fittedCurve4 = TuringBondYieldCurve(settlement, bonds, ylds, curveFitMethod)
#    fittedCurve4.display("GBP Yield Curve")

    curveFitMethod = TuringCurveFitBSpline()
    fittedCurve5 = TuringBondYieldCurve(settlement, bonds, ylds, curveFitMethod)
#    fittedCurve5.display("GBP Yield Curve")

###############################################################################

    testCases.header("PARAMETER", "VALUE")
    testCases.print("beta1", fittedCurve3._curveFit._beta1)
    testCases.print("beta2", fittedCurve3._curveFit._beta2)
    testCases.print("beta3", fittedCurve3._curveFit._beta3)
    testCases.print("tau", fittedCurve3._curveFit._tau)

    testCases.header("PARAMETER", "VALUE")
    testCases.print("beta1", fittedCurve4._curveFit._beta1)
    testCases.print("beta2", fittedCurve4._curveFit._beta2)
    testCases.print("beta3", fittedCurve4._curveFit._beta3)
    testCases.print("beta4", fittedCurve4._curveFit._beta4)
    testCases.print("tau1", fittedCurve4._curveFit._tau1)
    testCases.print("tau2", fittedCurve4._curveFit._tau2)

###############################################################################

    maturityDate = TuringDate(19, 9, 2030)
    interpolatedYield = fittedCurve5.interpolatedYield(maturityDate)
    testCases.print(maturityDate, interpolatedYield)

###############################################################################


test_FinBondYieldCurve()
testCases.compareTestCases()
