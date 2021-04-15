##############################################################################
# Copyright (C) 2018, 2019, 2020 Dominic O'Kane
##############################################################################


from enum import Enum

from turing_models.turingutils.turing_global_variables import gDaysInYear
from turing_models.models.turing_model_black_scholes import TuringModelBlackScholes
from turing_models.market.curves.turing_discount_curve import TuringDiscountCurve
from turing_models.turingutils.turing_date import TuringDate

###############################################################################

bump = 1e-4

###############################################################################

class TuringEquityOptionModelTypes(Enum):
    BLACKSCHOLES = 1
    ANOTHER = 2

###############################################################################


class TuringEquityOption(object):
    ''' This class is a parent class for all option classes that require any
    perturbatory risk. '''

###############################################################################

    def value(self,
              valueDate: TuringDate,
              stockPrice: float,
              discountCurve: TuringDiscountCurve,
              dividendYield: float,
              model):

        print("You should not be here!")
        return 0.0

###############################################################################

    def delta(self,
              valueDate: TuringDate,
              stockPrice: float,
              discountCurve: TuringDiscountCurve,
              dividendCurve: TuringDiscountCurve,
              model):
        ''' Calculation of option delta by perturbation of stock price and
        revaluation. '''
        v = self.value(valueDate, stockPrice, discountCurve,
                       dividendCurve, model)

        vBumped = self.value(valueDate, stockPrice + bump, discountCurve,
                             dividendCurve, model)

        delta = (vBumped - v) / bump
        return delta

###############################################################################

    def gamma(self,
              valueDate: TuringDate,
              stockPrice: float,
              discountCurve: TuringDiscountCurve,
              dividendCurve: TuringDiscountCurve,
              model):
        ''' Calculation of option gamma by perturbation of stock price and
        revaluation. '''

        v = self.value(valueDate, stockPrice, discountCurve,
                       dividendCurve, model)

        vBumpedDn = self.value(valueDate, stockPrice - bump, discountCurve,
                               dividendCurve, model)

        vBumpedUp = self.value(valueDate, stockPrice + bump, discountCurve,
                               dividendCurve, model)

        gamma = (vBumpedUp - 2.0 * v + vBumpedDn) / bump / bump
        return gamma

###############################################################################

    def vega(self,
             valueDate: TuringDate,
             stockPrice: float,
             discountCurve: TuringDiscountCurve,
             dividendCurve: TuringDiscountCurve,
             model):
        ''' Calculation of option vega by perturbing vol and revaluation. '''

        v = self.value(valueDate, stockPrice, discountCurve,
                       dividendCurve, model)

        model = TuringModelBlackScholes(model._volatility + bump)

        vBumped = self.value(valueDate, stockPrice, discountCurve,
                             dividendCurve, model)

        vega = (vBumped - v) / bump
        return vega

###############################################################################

    def theta(self,
              valueDate: TuringDate,
              stockPrice: float,
              discountCurve: TuringDiscountCurve,
              dividendCurve: TuringDiscountCurve,
              model):
        ''' Calculation of option theta by perturbing value date by one 
        calendar date (not a business date) and then doing revaluation and 
        calculating the difference divided by dt = 1 / gDaysInYear. '''

        v = self.value(valueDate, stockPrice, 
                       discountCurve,
                       dividendCurve, model)

        nextDate = valueDate.addDays(1)

        # Need to do this carefully.

        discountCurve._valuationDate = nextDate
        bump = (nextDate - valueDate) / gDaysInYear

        vBumped = self.value(nextDate, stockPrice, 
                             discountCurve,
                             dividendCurve, model)

        discountCurve._valuationDate = valueDate
        theta = (vBumped - v) / bump
        return theta

###############################################################################

    def rho(self,
            valueDate: TuringDate,
            stockPrice: float,
            discountCurve: TuringDiscountCurve,
            dividendCurve: TuringDiscountCurve,
            model):
        ''' Calculation of option rho by perturbing interest rate and
        revaluation. '''

        v = self.value(valueDate, stockPrice, discountCurve,
                       dividendCurve, model)

        vBumped = self.value(valueDate, stockPrice, discountCurve.bump(bump),
                             dividendCurve, model)

        rho = (vBumped - v) / bump
        return rho

###############################################################################
