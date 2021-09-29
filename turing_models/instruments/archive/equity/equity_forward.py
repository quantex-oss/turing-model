import numpy as np

from turing_models.utilities.turing_date import TuringDate
from turing_models.utilities.global_variables import gDaysInYear
from turing_models.utilities.global_types import TuringLongShort
from turing_models.utilities.error import TuringError
from turing_models.utilities.helper_functions import to_string, checkArgumentTypes

###############################################################################
# ADD START DATE TO CLASS ?
###############################################################################


class TuringEquityForward():
    ''' Contract to buy or sell a stock in future at a price agreed today. '''

    def __init__(self,
                 expiryDate: TuringDate,
                 forwardPrice: float,  # PRICE OF 1 UNIT OF FOREIGN IN DOM CCY
                 notional: float,
                 longShort: TuringLongShort = TuringLongShort.LONG):
        ''' Creates a TuringEquityForward which allows the owner to buy the stock
        at a price agreed today. Need to specify if LONG or SHORT.'''

        checkArgumentTypes(self.__init__, locals())

        self._expiryDate = expiryDate
        self._forwardPrice = forwardPrice
        self._notional = notional
        self._longShort = longShort
        
###############################################################################

    def value(self,
              valueDate,
              stockPrice,  # Current stock price
              discountCurve,
              dividendCurve):
        ''' Calculate the value of an equity forward contract from the stock 
        price and discound and dividend curves. '''

        if type(valueDate) == TuringDate:
            t = (self._expiryDate - valueDate) / gDaysInYear
        else:
            t = valueDate

        if np.any(stockPrice <= 0.0):
            raise TuringError("Stock price must be greater than zero.")

        if np.any(t < 0.0):
            raise TuringError("Time to expiry must be positive.")

        t = np.maximum(t, 1e-10)

        fwdStockPrice = self.forward(valueDate,
                                     stockPrice,
                                     discountCurve,
                                     dividendCurve)

        discountDF = discountCurve._df(t)

        v = (fwdStockPrice - self._forwardPrice)
        v = v * self._notional * discountDF
        
        if self._longShort == TuringLongShort.SHORT:
            v = v * (-1.0)

        return v

###############################################################################

    def forward(self,
                valueDate,
                stockPrice,  # Current stock price
                discountCurve,
                dividendCurve):
        ''' Calculate the forward price of the equity forward contract. '''

        if type(valueDate) == TuringDate:
            t = (self._expiryDate - valueDate) / gDaysInYear
        else:
            t = valueDate

        if np.any(stockPrice <= 0.0):
            raise TuringError("spotFXRate must be greater than zero.")

        if np.any(t < 0.0):
            raise TuringError("Time to expiry must be positive.")

        t = np.maximum(t, 1e-10)

        discountDF = discountCurve._df(t)
        dividendDF = dividendCurve._df(t)

        fwdStockPrice = stockPrice * dividendDF / discountDF
        return fwdStockPrice

###############################################################################

    def __repr__(self):
        s = to_string("OBJECT TYPE", type(self).__name__)
        s += to_string("EXPIRY DATE", self._expiryDate)
        s += to_string("FORWARD PRICE", self._forwardPrice)
        s += to_string("LONG OR SHORT", self._longShort)
        s += to_string("NOTIONAL", self._notional, "")
        return s

###############################################################################

    def _print(self):
        ''' Simple print function for backward compatibility. '''
        print(self)

###############################################################################

