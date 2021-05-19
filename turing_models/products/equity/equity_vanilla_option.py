import numpy as np
from numba import njit
# from tunny import model, compute

# from scipy import optimize
from turing_models.utilities.solvers_1d import newton_secant, bisection, newton

from turing_models.utilities.turing_date import TuringDate
from turing_models.utilities.global_variables import gDaysInYear
from turing_models.utilities.error import TuringError
from turing_models.utilities.global_types import TuringOptionTypes
from turing_models.utilities.helper_functions import checkArgumentTypes, labelToString
from turing_models.market.curves.discount_curve import TuringDiscountCurve

from turing_models.models.model import TuringModel
from turing_models.models.model_black_scholes import TuringModelBlackScholes
from turing_models.models.model_black_scholes_analytical import bsValue
from turing_models.models.model_black_scholes_analytical import bsDelta
from turing_models.models.model_black_scholes_analytical import bsVega
from turing_models.models.model_black_scholes_analytical import bsGamma
from turing_models.models.model_black_scholes_analytical import bsRho
from turing_models.models.model_black_scholes_analytical import bsTheta
from turing_models.models.model_black_scholes_analytical import bsImpliedVolatility
from turing_models.models.model_black_scholes_analytical import bsIntrinsic


from turing_models.models.model_black_scholes_mc import _valueMC_NONUMBA_NONUMPY
from turing_models.models.model_black_scholes_mc import _valueMC_NUMPY_NUMBA
from turing_models.models.model_black_scholes_mc import _valueMC_NUMBA_ONLY
from turing_models.models.model_black_scholes_mc import _valueMC_NUMPY_ONLY
from turing_models.models.model_black_scholes_mc import _valueMC_NUMBA_PARALLEL

from turing_models.utilities.mathematics import N

###############################################################################

@njit(fastmath=True, cache=True)
def _f(v, args):

    optionTypeValue = int(args[0])
    texp = args[1]
    s0 = args[2]
    r = args[3]
    q = args[4]
    k = args[5]
    price = args[6]

    objFn = bsValue(s0, texp, k, r, q, v, optionTypeValue)
    objFn = objFn - price
    return objFn

###############################################################################


def _fvega(v, *args):

    self = args[0]
    texp = args[1]
    s0 = args[2]
    r = args[3]
    q = args[4]
    k = args[5]

    fprime = bsVega(s0, texp, k, r, q, v, self._optionType.value)
    return fprime

###############################################################################


# @model
class TuringEquityVanillaOption():
    ''' Class for managing plain vanilla European calls and puts on equities.
    For American calls and puts see the TuringEquityAmericanOption class. '''

    def __init__(self,
                 expiryDate: (TuringDate, list),
                 strikePrice: (float, np.ndarray),
                 optionType: (TuringOptionTypes, list)):
        ''' Create the Equity Vanilla option object by specifying the expiry
        date, the option strike, the option type and the number of options. '''

        checkArgumentTypes(self.__init__, locals())

        if optionType != TuringOptionTypes.EUROPEAN_CALL and \
           optionType != TuringOptionTypes.EUROPEAN_PUT:
            raise TuringError("Unknown Option Type" + str(optionType))

        self._expiryDate = expiryDate
        self._strikePrice = strikePrice
        self._optionType = optionType
        self._texp = None

###############################################################################

    def intrinsic(self,
                  valueDate: (TuringDate, list),
                  stockPrice: (np.ndarray, float),
                  discountCurve: TuringDiscountCurve,
                  dividendCurve: TuringDiscountCurve):
        ''' Equity Vanilla Option valuation using Black-Scholes model. '''

        if type(valueDate) == TuringDate:
            texp = (self._expiryDate - valueDate) / gDaysInYear
        else:
            texp = valueDate

        self._texp = texp

        s0 = stockPrice
        texp = np.maximum(texp, 1e-10)

        df = discountCurve.df(self._expiryDate)
        r = -np.log(df)/texp

        dq = dividendCurve.df(self._expiryDate)
        q = -np.log(dq)/texp

        k = self._strikePrice

        intrinsicValue = bsIntrinsic(s0, texp, k, r, q,
                                     self._optionType.value)

        return intrinsicValue

###############################################################################

    # @compute
    def value(self,
              valueDate: (TuringDate, list),
              stockPrice: (np.ndarray, float),
              discountCurve: TuringDiscountCurve,
              dividendCurve: TuringDiscountCurve,
              model: TuringModel):
        ''' Equity Vanilla Option valuation using Black-Scholes model. '''

        if type(valueDate) == TuringDate:
            texp = (self._expiryDate - valueDate) / gDaysInYear
        else:
            texp = valueDate

        self._texp = texp

        if np.any(stockPrice <= 0.0):
            raise TuringError("Stock price must be greater than zero.")

        if np.any(texp < 0.0):
            raise TuringError("Time to expiry must be positive.")

        s0 = stockPrice

        texp = np.maximum(texp, 1e-10)

        df = discountCurve.df(self._expiryDate)
        r = -np.log(df)/texp

        dq = dividendCurve.df(self._expiryDate)
        q = -np.log(dq)/texp

        k = self._strikePrice

        if isinstance(model, TuringModelBlackScholes):

            v = model._volatility
            value = bsValue(s0, texp, k, r, q, v, self._optionType.value)

        else:
            raise TuringError("Unknown Model Type")

        return value

###############################################################################

    def delta(self,
              valueDate: TuringDate,
              stockPrice: float,
              discountCurve: TuringDiscountCurve,
              dividendCurve: TuringDiscountCurve,
              model):
        ''' Calculate the analytical delta of a European vanilla option. '''

        if type(valueDate) == TuringDate:
            texp = (self._expiryDate - valueDate) / gDaysInYear
        else:
            texp = valueDate

        self._texp = texp

        if np.any(stockPrice <= 0.0):
            raise TuringError("Stock price must be greater than zero.")

        if np.any(texp < 0.0):
            raise TuringError("Time to expiry must be positive.")

        s0 = stockPrice
        texp = np.maximum(texp, 1e-10)

        df = discountCurve.df(self._expiryDate)
        r = -np.log(df)/texp

        dq = dividendCurve.df(self._expiryDate)
        q = -np.log(dq)/texp

        k = self._strikePrice

        if isinstance(model, TuringModelBlackScholes):

            v = model._volatility
            delta = bsDelta(s0, texp, k, r, q, v, self._optionType.value)

        else:
            raise TuringError("Unknown Model Type")

        return delta

###############################################################################

    def gamma(self,
              valueDate: TuringDate,
              stockPrice: float,
              discountCurve: TuringDiscountCurve,
              dividendCurve: TuringDiscountCurve,
              model:TuringModel):
        ''' Calculate the analytical gamma of a European vanilla option. '''

        if type(valueDate) == TuringDate:
            texp = (self._expiryDate - valueDate) / gDaysInYear
        else:
            texp = valueDate

        if np.any(stockPrice <= 0.0):
            raise TuringError("Stock price must be greater than zero.")

        if np.any(texp < 0.0):
            raise TuringError("Time to expiry must be positive.")

        s0 = stockPrice

        texp = np.maximum(texp, 1e-10)

        df = discountCurve.df(self._expiryDate)
        r = -np.log(df)/texp

        dq = dividendCurve.df(self._expiryDate)
        q = -np.log(dq)/texp

        k = self._strikePrice

        if isinstance(model, TuringModelBlackScholes):

            v = model._volatility
            gamma = bsGamma(s0, texp, k, r, q, v, self._optionType.value)

        else:
            raise TuringError("Unknown Model Type")

        return gamma

###############################################################################

    def vega(self,
             valueDate: TuringDate,
             stockPrice: float,
             discountCurve: TuringDiscountCurve,
             dividendCurve: TuringDiscountCurve,
             model:TuringModel):
        ''' Calculate the analytical vega of a European vanilla option. '''

        if type(valueDate) == TuringDate:
            texp = (self._expiryDate - valueDate) / gDaysInYear
        else:
            texp = valueDate

        if np.any(stockPrice <= 0.0):
            raise TuringError("Stock price must be greater than zero.")

        if np.any(texp < 0.0):
            raise TuringError("Time to expiry must be positive.")

        s0 = stockPrice
        texp = np.maximum(texp, 1e-10)

        df = discountCurve.df(self._expiryDate)
        r = -np.log(df)/texp

        dq = dividendCurve.df(self._expiryDate)
        q = -np.log(dq)/texp

        k = self._strikePrice

        if isinstance(model, TuringModelBlackScholes):

            v = model._volatility
            vega = bsVega(s0, texp, k, r, q, v, self._optionType.value)

        else:
            raise TuringError("Unknown Model Type")

        return vega

###############################################################################

    def theta(self,
              valueDate: TuringDate,
              stockPrice: float,
              discountCurve: TuringDiscountCurve,
              dividendCurve: TuringDiscountCurve,
              model:TuringModel):
        ''' Calculate the analytical theta of a European vanilla option. '''

        if type(valueDate) == TuringDate:
            texp = (self._expiryDate - valueDate) / gDaysInYear
        else:
            texp = valueDate

        if np.any(stockPrice <= 0.0):
            raise TuringError("Stock price must be greater than zero.")

        if np.any(texp < 0.0):
            raise TuringError("Time to expiry must be positive.")

        s0 = stockPrice
        texp = np.maximum(texp, 1e-10)

        df = discountCurve.df(self._expiryDate)
        r = -np.log(df)/texp

        dq = dividendCurve.df(self._expiryDate)
        q = -np.log(dq)/texp

        k = self._strikePrice

        if isinstance(model, TuringModelBlackScholes):

            v = model._volatility
            theta = bsTheta(s0, texp, k, r, q, v, self._optionType.value)

        else:
            raise TuringError("Unknown Model Type")

        return theta

###############################################################################

    def rho(self,
            valueDate: TuringDate,
            stockPrice: float,
            discountCurve: TuringDiscountCurve,
            dividendCurve: TuringDiscountCurve,
            model:TuringModel):
        ''' Calculate the analytical rho of a European vanilla option. '''

        if type(valueDate) == TuringDate:
            texp = (self._expiryDate - valueDate) / gDaysInYear
        else:
            texp = valueDate

        if np.any(stockPrice <= 0.0):
            raise TuringError("Stock price must be greater than zero.")

        if np.any(texp < 0.0):
            raise TuringError("Time to expiry must be positive.")

        s0 = stockPrice
        texp = np.maximum(texp, 1e-10)

        df = discountCurve.df(self._expiryDate)
        r = -np.log(df)/texp

        dq = dividendCurve.df(self._expiryDate)
        q = -np.log(dq)/texp

        k = self._strikePrice

        if isinstance(model, TuringModelBlackScholes):

            v = model._volatility
            rho = bsRho(s0, texp, k, r, q, v, self._optionType.value)

        else:
            raise TuringError("Unknown Model Type")

        return rho

###############################################################################

    def impliedVolatility(self,
                          valueDate: TuringDate,
                          stockPrice: (float, list, np.ndarray),
                          discountCurve: TuringDiscountCurve,
                          dividendCurve: TuringDiscountCurve,
                          price):
        ''' Calculate the Black-Scholes implied volatility of a European
        vanilla option. '''

        texp = (self._expiryDate - valueDate) / gDaysInYear

        if texp < 1.0 / 365.0:
            print("Expiry time is too close to zero.")
            return -999

        df = discountCurve.df(self._expiryDate)
        r = -np.log(df)/texp

        dq = dividendCurve.df(self._expiryDate)
        q = -np.log(dq)/texp

        k = self._strikePrice
        s0 = stockPrice

        sigma = bsImpliedVolatility(s0, texp, k, r, q, price,
                                    self._optionType.value)

        return sigma

###############################################################################

    def valueMC_NUMPY_ONLY(self,
                           valueDate: TuringDate,
                           stockPrice: float,
                           discountCurve: TuringDiscountCurve,
                           dividendCurve: TuringDiscountCurve,
                           model:TuringModel,
                           numPaths: int = 10000,
                           seed: int = 4242,
                           useSobol: int = 0):

        texp = (self._expiryDate - valueDate) / gDaysInYear

        df = discountCurve.df(self._expiryDate)
        r = -np.log(df)/texp

        dq = dividendCurve.df(self._expiryDate)
        q = -np.log(dq)/texp

        vol = model._volatility

        v = _valueMC_NUMPY_ONLY(stockPrice,
                           texp,
                           self._strikePrice,
                           self._optionType.value,
                           r,
                           q,
                           vol,
                           numPaths,
                           seed,
                           useSobol)

        return v

###############################################################################

    def valueMC_NUMBA_ONLY(self,
                           valueDate: TuringDate,
                           stockPrice: float,
                           discountCurve: TuringDiscountCurve,
                           dividendCurve: TuringDiscountCurve,
                           model:TuringModel,
                           numPaths: int = 10000,
                           seed: int = 4242,
                           useSobol: int = 0):

        texp = (self._expiryDate - valueDate) / gDaysInYear

        df = discountCurve.df(self._expiryDate)
        r = -np.log(df)/texp

        dq = dividendCurve.df(self._expiryDate)
        q = -np.log(dq)/texp

        vol = model._volatility

        v = _valueMC_NUMBA_ONLY(stockPrice,
                           texp,
                           self._strikePrice,
                           self._optionType.value,
                           r,
                           q,
                           vol,
                           numPaths,
                           seed,
                           useSobol)

        return v

###############################################################################

    def valueMC_NUMBA_PARALLEL(self,
                               valueDate: TuringDate,
                               stockPrice: float,
                               discountCurve: TuringDiscountCurve,
                               dividendCurve: TuringDiscountCurve,
                               model:TuringModel,
                               numPaths: int = 10000,
                               seed: int = 4242,
                               useSobol: int = 0):

        texp = (self._expiryDate - valueDate) / gDaysInYear

        df = discountCurve.df(self._expiryDate)
        r = -np.log(df)/texp

        dq = dividendCurve.df(self._expiryDate)
        q = -np.log(dq)/texp

        vol = model._volatility

        v = _valueMC_NUMBA_PARALLEL(stockPrice,
                           texp,
                           self._strikePrice,
                           self._optionType.value,
                           r,
                           q,
                           vol,
                           numPaths,
                           seed,
                           useSobol)

#        _valueMC_NUMBA_ONLY.parallel_diagnostics(level=4)

        return v

###############################################################################

    def valueMC_NUMPY_NUMBA(self,
                            valueDate: TuringDate,
                            stockPrice: float,
                            discountCurve: TuringDiscountCurve,
                            dividendCurve: TuringDiscountCurve,
                            model:TuringModel,
                            numPaths: int = 10000,
                            seed: int = 4242,
                            useSobol: int = 0):

        texp = (self._expiryDate - valueDate) / gDaysInYear

        df = discountCurve.df(self._expiryDate)
        r = -np.log(df)/texp

        dq = dividendCurve.df(self._expiryDate)
        q = -np.log(dq)/texp

        vol = model._volatility

        v = _valueMC_NUMPY_NUMBA(stockPrice,
                           texp,
                           self._strikePrice,
                           self._optionType.value,
                           r,
                           q,
                           vol,
                           numPaths,
                           seed,
                           useSobol)

        return v

###############################################################################

    def valueMC_NONUMBA_NONUMPY(self,
                                valueDate: TuringDate,
                                stockPrice: float,
                                discountCurve: TuringDiscountCurve,
                                dividendCurve: TuringDiscountCurve,
                                model:TuringModel,
                                numPaths: int = 10000,
                                seed: int = 4242,
                                useSobol: int = 0):

        texp = (self._expiryDate - valueDate) / gDaysInYear

        df = discountCurve.df(self._expiryDate)
        r = -np.log(df)/texp

        dq = dividendCurve.df(self._expiryDate)
        q = -np.log(dq)/texp

        vol = model._volatility

        v = _valueMC_NONUMBA_NONUMPY(stockPrice,
                           texp,
                           self._strikePrice,
                           self._optionType.value,
                           r,
                           q,
                           vol,
                           numPaths,
                           seed,
                           useSobol)

        return v

###############################################################################

    def valueMC(self,
                valueDate: TuringDate,
                stockPrice: float,
                discountCurve: TuringDiscountCurve,
                dividendCurve: TuringDiscountCurve,
                model:TuringModel,
                numPaths: int = 10000,
                seed: int = 4242,
                useSobol: int = 0):
        ''' Value European style call or put option using Monte Carlo. This is
        mainly for educational purposes. Sobol numbers can be used. '''

        texp = (self._expiryDate - valueDate) / gDaysInYear

        df = discountCurve.df(self._expiryDate)
        r = -np.log(df)/texp

        dq = dividendCurve.df(self._expiryDate)
        q = -np.log(dq)/texp

        vol = model._volatility

        v = _valueMC_NUMBA_ONLY(stockPrice,
                                texp,
                                self._strikePrice,
                                self._optionType.value,
                                r,
                                q,
                                vol,
                                numPaths,
                                seed,
                                useSobol)

        return v

###############################################################################

    def __repr__(self):
        s = labelToString("OBJECT TYPE", type(self).__name__)
        s += labelToString("EXPIRY DATE", self._expiryDate)
        s += labelToString("STRIKE PRICE", self._strikePrice)
        s += labelToString("OPTION TYPE", self._optionType)
        return s

###############################################################################

    def _print(self):
        ''' Simple print function for backward compatibility. '''
        print(self)

###############################################################################
