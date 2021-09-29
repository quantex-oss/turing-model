import sys
sys.path.append("..")

import os
import datetime as dt

from turing_models.utilities.frequency import TuringFrequencyTypes
from turing_models.utilities.day_count import TuringDayCountTypes
from turing_models.utilities.turing_date import TuringDate, fromDatetime
from turing_models.instruments.archive.bonds import TuringBond
from turing_models.instruments.archive.bonds.bond_zero_curve import TuringBondZeroCurve

from TuringTestCases import TuringTestCases, globalTestCaseMode
testCases = TuringTestCases(__file__, globalTestCaseMode)

plotGraphs = False

###############################################################################


def test_FinBondZeroCurve():

    import pandas as pd
    path = os.path.join(os.path.dirname(__file__), './data/giltBondPrices.txt')
    bondDataFrame = pd.read_csv(path, sep='\t')
    bondDataFrame['mid'] = 0.5*(bondDataFrame['bid'] + bondDataFrame['ask'])

    freqType = TuringFrequencyTypes.SEMI_ANNUAL
    accrualType = TuringDayCountTypes.ACT_ACT_ICMA
    settlement = TuringDate(19, 9, 2012)

    bonds = []
    cleanPrices = []

    for _, bondRow in bondDataFrame.iterrows():
        dateString = bondRow['maturity']
        matDatetime = dt.datetime.strptime(dateString, '%d-%b-%y')
        maturityDt = fromDatetime(matDatetime)
        issueDt = TuringDate(maturityDt._d, maturityDt._m, 2000)
        coupon = bondRow['coupon']/100.0
        cleanPrice = bondRow['mid']
        bond = TuringBond(issueDt, maturityDt, coupon, freqType, accrualType)
        bonds.append(bond)
        cleanPrices.append(cleanPrice)

###############################################################################

    bondCurve = TuringBondZeroCurve(settlement, bonds, cleanPrices)

    testCases.header("DATE", "ZERO RATE")

    for _, bond in bondDataFrame.iterrows():

        dateString = bond['maturity']
        matDatetime = dt.datetime.strptime(dateString, '%d-%b-%y')
        maturityDt = fromDatetime(matDatetime)
        zeroRate = bondCurve.zeroRate(maturityDt)
        testCases.print(maturityDt, zeroRate)

    if plotGraphs:
        bondCurve.plot("BOND CURVE")

###############################################################################


test_FinBondZeroCurve()
testCases.compareTestCases()
