import numpy as np

from turing_models.utilities.date import TuringDate
from turing_models.utilities.global_variables import gDaysInYear
from turing_models.utilities.error import TuringError
from turing_models.utilities.global_types import TuringOptionTypes
from turing_models.utilities.helper_functions import checkArgumentTypes, labelToString
from turing_models.market.curves.discount_curve import TuringDiscountCurve
from turing_models.products.equity.equity_option import TuringEquityOption

from turing_models.models.model import TuringModel

###############################################################################
# TODO: Implement some analytical approximations
# TODO: Tree with discrete dividends
# TODO: Other dynamics such as SABR
###############################################################################


class TuringEquityAmericanOption(TuringEquityOption):
    ''' Class for American (and European) style options on simple vanilla
    calls and puts - a tree valuation model is used that can handle both. '''

    def __init__(self,
                 expiryDate: TuringDate,
                 strikePrice: float,
                 optionType: TuringOptionTypes,
                 numOptions: float = 1.0):
        ''' Class for American style options on simple vanilla calls and puts.
        Specify the expiry date, strike price, whether the option is a call or
        put and the number of options. '''

        checkArgumentTypes(self.__init__, locals())

        if optionType != TuringOptionTypes.EUROPEAN_CALL and \
            optionType != TuringOptionTypes.EUROPEAN_PUT and \
            optionType != TuringOptionTypes.AMERICAN_CALL and \
                optionType != TuringOptionTypes.AMERICAN_PUT:
            raise TuringError("Unknown Option Type" + str(optionType))

        self._expiryDate = expiryDate
        self._strikePrice = strikePrice
        self._optionType = optionType
        self._numOptions = numOptions

###############################################################################

    def value(self,
              valueDate: TuringDate,
              stockPrice: (np.ndarray, float),
              discountCurve: TuringDiscountCurve,
              dividendCurve: TuringDiscountCurve,
              model: TuringModel):
        ''' Valuation of an American option using a CRR tree to take into
        account the value of early exercise. '''

        if type(valueDate) == TuringDate:
            texp = (self._expiryDate - valueDate) / gDaysInYear
        else:
            texp = valueDate

        if np.any(stockPrice <= 0.0):
            raise TuringError("Stock price must be greater than zero.")

        if isinstance(model, TuringModel) is False:
            raise TuringError("Model is not inherited off type TuringModel.")

        if np.any(texp < 0.0):
            raise TuringError("Time to expiry must be positive.")

        texp = np.maximum(texp, 1e-10)

        r = discountCurve.ccRate(self._expiryDate)        
        q = dividendCurve.ccRate(self._expiryDate)

        s = stockPrice
        k = self._strikePrice

        v = model.value(s, texp, k, r, q, self._optionType)
                    
        v = v * self._numOptions

        if isinstance(s, float):
            return v
        else:
            return v[0]

###############################################################################

    def __repr__(self):
        s = labelToString("OBJECT TYPE", type(self).__name__)
        s += labelToString("EXPIRY DATE", self._expiryDate)
        s += labelToString("STRIKE PRICE", self._strikePrice)
        s += labelToString("OPTION TYPE", self._optionType)
        s += labelToString("NUMBER", self._numOptions, "")
        return s

###############################################################################

    def _print(self):
        ''' Simple print function for backward compatibility. '''
        print(self)

###############################################################################