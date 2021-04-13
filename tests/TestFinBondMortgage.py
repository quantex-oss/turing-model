###############################################################################
# Copyright (C) 2018, 2019, 2020 Dominic O'Kane
###############################################################################

import sys
sys.path.append("..")

from turingmodel.turingutils.turing_date import TuringDate

from turingmodel.products.bonds.turing_bond_mortgage import TuringBondMortgage
from turingmodel.products.bonds.turing_bond_mortgage import TuringBondMortgageTypes
from turingmodel.products.rates.turing_ibor_single_curve import TuringIborSingleCurve

from TuringTestCases import TuringTestCases, globalTestCaseMode
testCases = TuringTestCases(__file__, globalTestCaseMode)


###############################################################################


def test_FinBondMortgage():

    principal = 130000
    startDate = TuringDate(23, 2, 2018)
    endDate = startDate.addTenor("10Y")
    mortgage = TuringBondMortgage(startDate, endDate, principal)

    rate = 0.035
    mortgage.generateFlows(rate, TuringBondMortgageTypes.REPAYMENT)

    numFlows = len(mortgage._schedule._adjustedDates)

    testCases.header("PAYMENT DATE", "INTEREST", "PRINCIPAL", "OUTSTANDING",
                     "TOTAL")

    for i in range(0, numFlows):
        testCases.print(mortgage._schedule._adjustedDates[i],
                        mortgage._interestFlows[i],
                        mortgage._principalFlows[i],
                        mortgage._principalRemaining[i],
                        mortgage._totalFlows[i])

    mortgage.generateFlows(rate, TuringBondMortgageTypes.INTEREST_ONLY)

    testCases.header("PAYMENT DATE", "INTEREST", "PRINCIPAL", "OUTSTANDING",
                     "TOTAL")

    for i in range(0, numFlows):
        testCases.print(mortgage._schedule._adjustedDates[i],
                        mortgage._interestFlows[i],
                        mortgage._principalFlows[i],
                        mortgage._principalRemaining[i],
                        mortgage._totalFlows[i])


###############################################################################


test_FinBondMortgage()
testCases.compareTestCases()
