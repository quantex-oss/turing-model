import sys
sys.path.append("..")

from turing_models.products.equity.equity_chooser_option import TuringEquityChooserOption
from turing_models.models.model_black_scholes import TuringModelBlackScholes
from turing_models.market.curves.discount_curve_flat import TuringDiscountCurveFlat
from turing_models.utilities.turing_date import TuringDate

from TuringTestCases import TuringTestCases, globalTestCaseMode
testCases = TuringTestCases(__file__, globalTestCaseMode)

##############################################################################


def test_FinEquityChooserOptionHaug():
    ''' Following example in Haug Page 130 '''

    valueDate = TuringDate(1, 1, 2015)
    chooseDate = TuringDate(2, 4, 2015)
    callExpiryDate = TuringDate(1, 7, 2015)
    putExpiryDate = TuringDate(2, 8, 2015)
    callStrike = 55.0
    putStrike = 48.0
    stockPrice = 50.0
    volatility = 0.35
    interestRate = 0.10
    dividendYield = 0.05

    model = TuringModelBlackScholes(volatility)
    discountCurve = TuringDiscountCurveFlat(valueDate, interestRate)
    dividendCurve = TuringDiscountCurveFlat(valueDate, dividendYield)

    chooserOption = TuringEquityChooserOption(chooseDate,
                                              callExpiryDate,
                                              putExpiryDate,
                                              callStrike,
                                              putStrike)

    v = chooserOption.value(valueDate,
                            stockPrice,
                            discountCurve,
                            dividendCurve,
                            model)

    v_mc = chooserOption.valueMC(valueDate,
                                 stockPrice,
                                 discountCurve,
                                 dividendCurve,
                                 model, 20000)

    v_haug = 6.0508
    testCases.header("", "", "", "", "", "")
    testCases.print("Turing_models", v, "HAUG", v_haug, "MC", v_mc)

##########################################################################


def test_FinEquityChooserOptionMatlab():
    '''https://fr.mathworks.com/help/fininst/chooserbybls.html '''

    valueDate = TuringDate(1, 6, 2007)
    chooseDate = TuringDate(31, 8, 2007)
    callExpiryDate = TuringDate(2, 12, 2007)
    putExpiryDate = TuringDate(2, 12, 2007)
    callStrike = 60.0
    putStrike = 60.0
    stockPrice = 50.0
    volatility = 0.20
    interestRate = 0.10
    dividendYield = 0.05

    model = TuringModelBlackScholes(volatility)

    discountCurve = TuringDiscountCurveFlat(valueDate, interestRate)
    dividendCurve = TuringDiscountCurveFlat(valueDate, dividendYield)

    chooserOption = TuringEquityChooserOption(chooseDate,
                                              callExpiryDate,
                                              putExpiryDate,
                                              callStrike,
                                              putStrike)

    v = chooserOption.value(valueDate,
                            stockPrice,
                            discountCurve,
                            dividendCurve,
                            model)

    v_mc = chooserOption.valueMC(valueDate,
                                 stockPrice,
                                 discountCurve,
                                 dividendCurve,
                                 model, 20000)

    v_matlab = 8.9308
    testCases.header("", "", "", "", "", "")
    testCases.print("Turing_models", v, "MATLAB", v_matlab, "MC", v_mc)

##########################################################################


def test_FinEquityChooserOptionDerivicom():
    '''http://derivicom.com/support/finoptionsxl/index.html?complex_chooser.htm '''

    valueDate = TuringDate(1, 1, 2007)
    chooseDate = TuringDate(1, 2, 2007)
    callExpiryDate = TuringDate(1, 4, 2007)
    putExpiryDate = TuringDate(1, 5, 2007)
    callStrike = 40.0
    putStrike = 35.0
    stockPrice = 38.0
    volatility = 0.20
    interestRate = 0.08
    dividendYield = 0.0625

    model = TuringModelBlackScholes(volatility)
    discountCurve = TuringDiscountCurveFlat(valueDate, interestRate)
    dividendCurve = TuringDiscountCurveFlat(valueDate, dividendYield)

    chooserOption = TuringEquityChooserOption(chooseDate,
                                              callExpiryDate,
                                              putExpiryDate,
                                              callStrike,
                                              putStrike)

    v = chooserOption.value(valueDate,
                            stockPrice,
                            discountCurve,
                            dividendCurve,
                            model)

    v_mc = chooserOption.valueMC(valueDate,
                                 stockPrice,
                                 discountCurve,
                                 dividendCurve,
                                 model, 20000)

    v_derivicom = 1.0989
    testCases.header("", "", "", "", "", "")
    testCases.print("Turing_models", v, "DERIVICOM", v_derivicom, "MC", v_mc)

##########################################################################


test_FinEquityChooserOptionHaug()
test_FinEquityChooserOptionMatlab()
test_FinEquityChooserOptionDerivicom()
testCases.compareTestCases()
