import numpy as np

from turing_models.utilities.turing_date import TuringDate
from turing_models.utilities.error import TuringError
from turing_models.utilities.mathematics import testMonotonicity
from turing_models.utilities.frequency import FrequencyType
from turing_models.utilities.day_count import DayCountType
from turing_models.market.curves.discount_curve import TuringDiscountCurve
from turing_models.utilities.helper_functions import to_string, checkArgumentTypes, timesFromDates

###############################################################################


class TuringDiscountCurvePWL(TuringDiscountCurve):
    ''' Curve is made up of a series of sections assumed to each have a
    piece-wise linear zero rate. The zero rate has a specified frequency
    which defaults to continuous. This curve inherits all of the extra methods
    from TuringDiscountCurve. '''

    def __init__(self,
                 valuationDate: TuringDate,
                 zeroDates: list,
                 zeroRates: (list, np.ndarray),
                 freqType: FrequencyType = FrequencyType.CONTINUOUS,
                 dayCountType: DayCountType = DayCountType.ACT_ACT_ISDA):
        ''' Curve is defined by a vector of increasing times and zero rates.'''

        checkArgumentTypes(self.__init__, locals())

        self._valuationDate = valuationDate

        if len(zeroDates) != len(zeroRates):
            raise TuringError("Dates and rates vectors must have same length")

        if len(zeroDates) == 0:
            raise TuringError("Dates vector must have length > 0")

        self._zeroRates = np.array(zeroRates)
        self._zeroDates = zeroDates
        self._freqType = freqType
        self._dayCountType = dayCountType

        dcTimes = timesFromDates(zeroDates,
                                 self._valuationDate,
                                 self._dayCountType)

        self._times = np.array(dcTimes)

        if testMonotonicity(self._times) is False:
            raise TuringError("Times are not sorted in increasing order")

###############################################################################

    def _zeroRate(self,
                  times: (list, np.ndarray)):
        ''' Calculate the piecewise linear zero rate. This is taken from the
        initial inputs. A simple linear interpolation scheme is used. If the
        user supplies a frequency type then a conversion is done. '''

        if isinstance(times, float):
            times = np.array([times])

        if np.any(times < 0.0):
            raise TuringError("All times must be positive")

        times = np.maximum(times, 1e-6)

        zeroRates = []

        for t in times:
            l_index = 0
            found = 0

            numTimes = len(self._times)
            for i in range(1, numTimes):
                if self._times[i] > t:
                    l_index = i - 1
                    found = 1
                    break

            t0 = self._times[l_index]
            r0 = self._zeroRates[l_index]
            t1 = self._times[l_index+1]
            r1 = self._zeroRates[l_index+1]

            if found == 1:
                zeroRate = ((t1 - t) * r0 + (t - t0) * r1)/(t1 - t0)
            else:
                zeroRate = self._zeroRates[-1]

            zeroRates.append(zeroRate)

        return np.array(zeroRates)

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

    # def _df(self,
    #         t: (float, np.ndarray)):
    #     ''' Returns the discount factor at time t taking into account the
    #     piecewise flat zero rate curve and the compunding frequency. '''

    #     r = self._zeroRate(t, self._freqType)
    #     df = zeroToDf(r, t, self._freqType)
    #     return df

###############################################################################

    def __repr__(self):

        s = to_string("OBJECT TYPE", type(self).__name__)
        s += to_string("DATE", "ZERO RATE")
        for i in range(0, len(self._zeroDates)):
            s += to_string(self._zeroDates[i], self._zeroRates[i])
        s += to_string("FREQUENCY", (self._freqType))
        return s

###############################################################################

    def _print(self):
        ''' Simple print function for backward compatibility. '''
        print(self)

###############################################################################
