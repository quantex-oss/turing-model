##############################################################################
# Copyright (C) 2018, 2019, 2020 Dominic O'Kane
##############################################################################

import sys
sys.path.append("..")

from financepy.finutils.turing_amount import TuringAmount
from financepy.finutils.turing_currency import TuringCurrencyTypes

from TuringTestCases import TuringTestCases, globalTestCaseMode
testCases = TuringTestCases(__file__, globalTestCaseMode)

##########################################################################

def test_FinAmount():

    testCases.header("LABEL", "AMOUNT")
    x = TuringAmount(101000.232)

    testCases.print("Amount", x)

    x = TuringAmount(101000.232, TuringCurrencyTypes.CAD)

    testCases.print("Amount", x)

###############################################################################

test_FinAmount()

testCases.compareTestCases()
