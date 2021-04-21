import numpy as np

from turing_models.utilities.turing_date import TuringDate
from turing_models.utilities.frequency import TuringFrequencyTypes
from turing_models.utilities.global_variables import gSmall
from turing_models.utilities.error import TuringError
from turing_models.market.curves.discount_curve import TuringDiscountCurve
from turing_models.utilities.helper_functions import checkArgumentTypes
from turing_models.utilities.helper_functions import labelToString
from turing_models.utilities.day_count import TuringDayCountTypes
from turing_models.utilities.helper_functions import timesFromDates

###############################################################################


class TuringDiscountCurveNS(TuringDiscountCurve):
    ''' Implementation of Nelson-Siegel parametrisation of a discount curve.
    The internal rate is a continuously compounded rate but you can calculate
    alternative frequencies by providing a corresponding compounding frequency.
    A day count convention is needed to ensure that dates are converted to the
    correct time in years. The class inherits methods from TuringDiscountCurve.'''

    def __init__(self,
                 valuationDate: TuringDate,
                 beta0: float,
                 beta1: float,
                 beta2: float,
                 tau: float,
                 freqType: TuringFrequencyTypes = TuringFrequencyTypes.CONTINUOUS,
                 dayCountType: TuringDayCountTypes = TuringDayCountTypes.ACT_ACT_ISDA):
        ''' Creation of a TuringDiscountCurveNS object. Parameters are provided
        individually for beta0, beta1, beta2 and tau. The zero rates produced
        by this parametrisation have an implicit compounding convention that
        defaults to continuous but which can be overridden. '''

        checkArgumentTypes(self.__init__, locals())

        if tau <= 0:
            raise TuringError("Tau must be positive")

        self._valuationDate = valuationDate
        self._beta0 = beta0
        self._beta1 = beta1
        self._beta2 = beta2
        self._tau = tau
        self._freqType = freqType
        self._dayCountType = dayCountType

###############################################################################

    def zeroRate(self,
                 dates: (list, TuringDate),
                 freqType: TuringFrequencyTypes = TuringFrequencyTypes.CONTINUOUS,
                 dayCountType: TuringDayCountTypes = TuringDayCountTypes.ACT_360):
        ''' Calculation of zero rates with specified frequency according to
        NS parametrisation. This method overrides that in TuringDiscountCurve.
        The parametrisation is not strictly in terms of continuously compounded
        zero rates, this function allows other compounding and day counts.
        This function returns a single or vector of zero rates given a vector
        of dates so must use Numpy functions. The default frequency is a
        continuously compounded rate and ACT ACT day counting. '''

        if isinstance(freqType, TuringFrequencyTypes) is False:
            raise TuringError("Invalid Frequency type.")

        if isinstance(dayCountType, TuringDayCountTypes) is False:
            raise TuringError("Invalid Day Count type.")

        # Get day count times to use with curve day count convention
        dcTimes = timesFromDates(dates,
                                 self._valuationDate,
                                 self._dayCountType)

        # We now get the discount factors using these times
        zeroRates = self._zeroRate(dcTimes)

        # Now get the discount factors using curve conventions
        dfs = self._zeroToDf(self._valuationDate,
                             zeroRates,
                             dcTimes,
                             self._freqType,
                             self._dayCountType)

        # Convert these to zero rates in the required frequency and day count
        zeroRates = self._dfToZero(dfs,
                                   dates,
                                   freqType,
                                   dayCountType)

        return zeroRates

###############################################################################

    def _zeroRate(self,
                  times: (float, np.ndarray)):
        ''' Zero rate for Nelson-Siegel curve parametrisation. This means that
        the t vector must use the curve day count.'''

        t = np.maximum(times, gSmall)

        theta = t / self._tau
        e = np.exp(-theta)
        zeroRate = self._beta0
        zeroRate += self._beta1 * (1.0 - e) / theta
        zeroRate += self._beta2 * ((1.0 - e) / theta - e)
        return zeroRate

###############################################################################

    def df(self,
           dates: (TuringDate, list)):
        ''' Return discount factors given a single or vector of dates. The
        discount factor depends on the rate and this in turn depends on its
        compounding frequency and it defaults to continuous compounding. It
        also depends on the day count convention. This was set in the
        construction of the curve to be ACT_ACT_ISDA. '''

        # Get day count times to use with curve day count convention
        dcTimes = timesFromDates(dates,
                                 self._valuationDate,
                                 self._dayCountType)

        zeroRates = self._zeroRate(dcTimes)

        df = self._zeroToDf(self._valuationDate,
                            zeroRates,
                            dcTimes,
                            self._freqType,
                            self._dayCountType)

        return df

###############################################################################

    def __repr__(self):

        s = labelToString("OBJECT TYPE", type(self).__name__)
        s += labelToString("PARAMETER", "VALUE")
        s += labelToString("BETA0", self._beta0)
        s += labelToString("BETA1", self._beta1)
        s += labelToString("BETA2", self._beta2)
        s += labelToString("TAU", self._tau)
        s += labelToString("FREQUENCY", (self._freqType))
        s += labelToString("DAY_COUNT", (self._dayCountType))
        return s

###############################################################################

    def _print(self):
        ''' Simple print function for backward compatibility. '''
        print(self)

###############################################################################
