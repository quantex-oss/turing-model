


from math import exp, log, sqrt
import numpy as np


from turing_models.utilities.math import N
from turing_models.utilities.global_variables import gDaysInYear
from turing_models.utilities.error import TuringError
# from turing_models.products.equity.equity_option import FinOption
from turing_models.utilities.date import TuringDate
#from turing_models.products.fx.FinFXModelTypes import FinFXModel
from turing_models.models.model_black_scholes import TuringModelBlackScholes
from turing_models.utilities.helper_functions import labelToString, checkArgumentTypes
from turing_models.utilities.global_types import TuringOptionTypes

###############################################################################


class TuringFXDigitalOption():

    def __init__(self,
                 expiryDate: TuringDate,
                 strikePrice: float,  # 1 unit of foreign in domestic
                 currencyPair: str,  # FORDOM
                 optionType: TuringOptionTypes,
                 notional: float,
                 premCurrency: str):
        ''' Create the FX Digital Option object. Inputs include expiry date,
        strike, currency pair, option type (call or put), notional and the
        currency of the notional. And adjustment for spot days is enabled. All
        currency rates must be entered in the price in domestic currency of
        one unit of foreign. And the currency pair should be in the form FORDOM
        where FOR is the foreign currency pair currency code and DOM is the
        same for the domestic currency. '''

        checkArgumentTypes(self.__init__, locals())

        self._expiryDate = expiryDate
        self._strikePrice = float(strikePrice)
        self._currencyPair = currencyPair
        self._optionType = optionType

        self._currencyPair = currencyPair
        self._forName = self._currencyPair[0:3]
        self._domName = self._currencyPair[3:6]

        if premCurrency != self._domName and premCurrency != self._forName:
            raise TuringError("Notional currency not in currency pair.")

###############################################################################

    def value(self,
              valueDate,
              spotFXRate,  # 1 unit of foreign in domestic
              domDiscountCurve,
              forDiscountCurve,
              model):
        ''' Valuation of a digital option using Black-Scholes model. This
        allows for 4 cases - first upper barriers that when crossed pay out
        cash (calls) and lower barriers than when crossed from above cause a
        cash payout (puts) PLUS the fact that the cash payment can be in
        domestic or foreign currency. '''

        if type(valueDate) == TuringDate:
            spotDate = valueDate.addWeekDays(self._spotDays)
            tdel = (self._deliveryDate - spotDate) / gDaysInYear
            texp = (self._expiryDate - valueDate) / gDaysInYear
        else:
            tdel = valueDate
            texp = tdel

        if np.any(spotFXRate <= 0.0):
            raise TuringError("spotFXRate must be greater than zero.")

        if np.any(tdel < 0.0):
            raise TuringError("Option time to maturity is less than zero.")

        tdel = np.maximum(tdel, 1e-10)

        domDF = domDiscountCurve.df(tdel)
        rd = -np.log(domDF)/tdel

        forDF = forDiscountCurve.df(tdel)
        rf = -np.log(forDF)/tdel

        S0 = spotFXRate
        K = self._strikeFXRate

        if type(model) == TuringModelBlackScholes:

            volatility = model._volatility
            lnS0k = log(S0 / K)
            den = volatility * sqrt(texp)
            v2 = volatility * volatility
            mu = rd - rf
            d2 = (lnS0k + (mu - v2 / 2.0) * tdel) / den

            if self._optionType == TuringOptionTypes.DIGITAL_CALL and \
                self._forName == self._premCurrency:
                    v = S0 * exp(-rf * tdel) * N(d2)
            elif self._optionType == TuringOptionTypes.DIGITAL_PUT and \
                self._forName == self._premCurrency:
                    v = S0 * exp(-rf * tdel) * N(-d2)
            if self._optionType == TuringOptionTypes.DIGITAL_CALL and \
                self._domName == self._premCurrency:
                    v = exp(-rd * tdel) * N(d2)
            elif self._optionType == TuringOptionTypes.DIGITAL_PUT and \
                self._domName == self._premCurrency:
                    v = exp(-rd * tdel) * N(-d2)
            else:
                raise TuringError("Unknown option type")

            v = v * self.premNotional

        return v

###############################################################################
