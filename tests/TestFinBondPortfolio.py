import os
import datetime as dt

import sys
sys.path.append("..")

from turing_models.utilities.date import TuringDate, fromDatetime
from turing_models.products.bonds.bond import TuringBond
from turing_models.utilities.frequency import TuringFrequencyTypes
from turing_models.utilities.day_count import TuringDayCountTypes

from TuringTestCases import TuringTestCases, globalTestCaseMode
testCases = TuringTestCases(__file__, globalTestCaseMode)

###############################################################################

def test_FinBondPortfolio():

    import pandas as pd
    path = os.path.join(os.path.dirname(__file__), './data/giltBondPrices.txt')
    bondDataFrame = pd.read_csv(path, sep='\t')
    bondDataFrame['mid'] = 0.5*(bondDataFrame['bid'] + bondDataFrame['ask'])

    freqType = TuringFrequencyTypes.SEMI_ANNUAL
    accrualType = TuringDayCountTypes.ACT_ACT_ICMA

    settlement = TuringDate(19, 9, 2012)

    testCases.header("DCTYPE", "MATDATE", "CPN", "PRICE", "ACCD", "YTM")

    for accrualType in TuringDayCountTypes:

        for _, bond in bondDataFrame.iterrows():

            dateString = bond['maturity']
            matDatetime = dt.datetime.strptime(dateString, '%d-%b-%y')
            maturityDt = fromDatetime(matDatetime)
            issueDt = TuringDate(maturityDt._d, maturityDt._m, 2000)
            coupon = bond['coupon']/100.0
            cleanPrice = bond['mid']
            bond = TuringBond(issueDt, maturityDt,
                              coupon, freqType, accrualType)

            ytm = bond.yieldToMaturity(settlement, cleanPrice)
            accd = bond._accruedInterest

            testCases.print(accrualType, maturityDt, coupon*100.0,
                            cleanPrice, accd, ytm*100.0)

##########################################################################


test_FinBondPortfolio()
testCases.compareTestCases()
