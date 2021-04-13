###############################################################################
# Copyright (C) 2018, 2019, 2020 Dominic O'Kane
###############################################################################


import numpy as np

###############################################################################

from financepy.turingutils.turing_date import TuringDate
from financepy.turingutils.turing_day_count import TuringDayCountTypes
from financepy.turingutils.turing_frequency import TuringFrequencyTypes
from financepy.turingutils.turing_helper_functions import labelToString
from financepy.turingutils.turing_helper_functions import checkArgumentTypes
from financepy.market.curves.turing_discount_curve import TuringDiscountCurve
from financepy.turingutils.turing_helper_functions import timesFromDates
from financepy.market.curves.turing_interpolator import FinInterpTypes

###############################################################################
# TODO: Do I need to add a day count to ensure rate and times are linked in
#       the correct way URGENT
###############################################################################


class TuringDiscountCurveFlat(TuringDiscountCurve):
    ''' A very simple discount curve based on a single zero rate with its
    own specified compounding method. Hence the curve is assumed to be flat.
    It is used for quick and dirty analysis and when limited information is
    available. It inherits several methods from TuringDiscountCurve. '''

###############################################################################

    def __init__(self,
                 valuationDate: TuringDate,
                 flatRate: (float, np.ndarray),
                 freqType: TuringFrequencyTypes = TuringFrequencyTypes.CONTINUOUS,
                 dayCountType: TuringDayCountTypes = TuringDayCountTypes.ACT_ACT_ISDA):
        ''' Create a discount curve which is flat. This is very useful for
        quick testing and simply requires a curve date a rate and a compound
        frequency. As we have entered a rate, a corresponding day count
        convention must be used to specify how time periods are to be measured.
        As the curve is flat, no interpolation scheme is required.
        '''

        checkArgumentTypes(self.__init__, locals())

        self._valuationDate = valuationDate
        self._flatRate = flatRate
        self._freqType = freqType
        self._dayCountType = dayCountType

        # This is used by some inherited functions so we choose the simplest
        self._interpType = FinInterpTypes.FLAT_FWD_RATES

        # Need to set up a grid of times and discount factors
        years = np.linspace(0.0, 10.0, 41)
        dates = self._valuationDate.addYears(years)

        # Set up a grid of times and discount factors for functions
        self._dfs = self.df(dates)
        self._times = timesFromDates(dates, self._valuationDate, dayCountType)

###############################################################################

    def bump(self,
             bumpSize: float):
        ''' Creates a new TuringDiscountCurveFlat object with the entire curve
        bumped up by the bumpsize. All other parameters are preserved.'''

        rBumped = self._flatRate + bumpSize
        discCurve = TuringDiscountCurveFlat(self._valuationDate,
                                            rBumped,
                                            freqType=self._freqType,
                                            dayCountType=self._dayCountType)
        return discCurve

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

        dfs = self._zeroToDf(self._valuationDate,
                             self._flatRate,
                             dcTimes,
                             self._freqType,
                             self._dayCountType)

        if isinstance(dates, TuringDate):
            return dfs[0]
        else:
            return np.array(dfs)

###############################################################################

    def __repr__(self):
        s = labelToString("OBJECT TYPE", type(self).__name__)
        s += labelToString("FLAT RATE", (self._flatRate))
        s += labelToString("FREQUENCY", (self._freqType))
        s += labelToString("DAY COUNT", (self._dayCountType))
        return s

###############################################################################

    def _print(self):
        ''' Simple print function for backward compatibility. '''
        print(self)

###############################################################################
