###############################################################################
# Copyright (C) 2018, 2019, 2020 Dominic O'Kane
###############################################################################

import sys
sys.path.append("..")

from financepy.turingutils.turing_date import TuringDate
from financepy.turingutils.turing_frequency import TuringFrequencyTypes
from financepy.turingutils.turing_day_count import TuringDayCountTypes

from financepy.turingutils.turing_global_types import TuringOptionTypes

from financepy.market.curves.turing_discount_curve_flat import TuringDiscountCurveFlat
from financepy.models.turing_model_black_scholes import FinModelBlackScholes
from financepy.models.turing_model_black_scholes import FinModelBlackScholesTypes

from financepy.products.equity.turing_equity_vanilla_option import FinEquityVanillaOption
from financepy.products.equity.turing_equity_american_option import TuringEquityAmericanOption

from TuringTestCases import TuringTestCases, globalTestCaseMode
testCases = TuringTestCases(__file__, globalTestCaseMode)

##############################################################################

# TODO Complete output of results to log files

def testFinModelBlackScholes():

    valueDate = TuringDate(8, 5, 2015)
    expiryDate = TuringDate(15, 1, 2016)

    strikePrice = 130.0
    stockPrice = 127.62
    volatility = 0.20
    interestRate = 0.001
    dividendYield = 0.0163

    optionType = TuringOptionTypes.AMERICAN_CALL
    euOptionType = TuringOptionTypes.EUROPEAN_CALL
    
    amOption = TuringEquityAmericanOption(expiryDate, strikePrice,
                                          optionType)
    
    ameuOption = TuringEquityAmericanOption(expiryDate, strikePrice,
                                            euOptionType)
    
    euOption = FinEquityVanillaOption(expiryDate, strikePrice,
                                      euOptionType)
    
    discountCurve = TuringDiscountCurveFlat(valueDate, interestRate,
                                            TuringFrequencyTypes.CONTINUOUS,
                                            TuringDayCountTypes.ACT_365F)

    dividendCurve = TuringDiscountCurveFlat(valueDate, dividendYield,
                                            TuringFrequencyTypes.CONTINUOUS,
                                            TuringDayCountTypes.ACT_365F)
    
    numStepsPerYear = 400
    
    modelTree = FinModelBlackScholes(volatility, 
                                     FinModelBlackScholesTypes.CRR_TREE, 
                                     numStepsPerYear)
    
    v = amOption.value(valueDate, stockPrice, discountCurve, 
                           dividendCurve, modelTree)
#    print(v)

    modelApprox = FinModelBlackScholes(volatility, 
                                       FinModelBlackScholesTypes.BARONE_ADESI)

    v = amOption.value(valueDate, stockPrice, discountCurve, 
                       dividendCurve, modelApprox)

#    print(v)

    v = ameuOption.value(valueDate, stockPrice, discountCurve, 
                           dividendCurve, modelTree)

#    print(v)

    v = euOption.value(valueDate, stockPrice, discountCurve, 
                         dividendCurve, modelTree)

#    print(v)

    amTreeValue = []
    amBAWValue = []
    euTreeValue = []
    euAnalValue = []
    volatility = 0.20

    # numStepsPerYear = range(5, 200, 1)
    
    # for numSteps in numStepsPerYear:

    #     modelTree = FinModelBlackScholes(volatility,
    #                                      FinModelBlackScholesTypes.CRR_TREE,
    #                                      {'numStepsPerYear':numSteps})

    #     modelAnal = FinModelBlackScholes(volatility, 
    #                                      FinModelBlackScholesTypes.ANALYTICAL)

    #     modelBAW = FinModelBlackScholes(volatility, 
    #                                     FinModelBlackScholesTypes.BARONE_ADESI)


    #     v_am = amOption.value(valueDate, stockPrice, discountCurve, 
    #                           dividendYield, modelTree)

    #     v_eu = ameuOption.value(valueDate, stockPrice, discountCurve, 
    #                             dividendYield, modelTree)
 
    #     v_bs = euOption.value(valueDate, stockPrice, discountCurve, 
    #                           dividendYield, modelAnal)

    #     v_am_baw = amOption.value(valueDate, stockPrice, discountCurve, 
    #                               dividendYield, modelBAW)
        
    #     amTreeValue.append(v_am)
    #     euTreeValue.append(v_eu)
    #     euAnalValue.append(v_bs)
    #     amBAWValue.append(v_am_baw)
        
    
    # plt.title("American PUT Option Price Convergence Analysis")
    # plt.plot(numStepsPerYear, amTreeValue, label="American Tree")
    # plt.plot(numStepsPerYear, amBAWValue, label="American BAW")
    # plt.plot(numStepsPerYear, euTreeValue, label="European Tree")
    # plt.plot(numStepsPerYear, euAnalValue, label="European Anal", lw =2)
    # plt.xlabel("Num Steps")
    # plt.ylabel("Value")
    # plt.legend();

###############################################################################


testFinModelBlackScholes()
testCases.compareTestCases()
