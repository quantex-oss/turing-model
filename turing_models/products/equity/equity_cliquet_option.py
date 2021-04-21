



import numpy as np

from turing_models.utilities.frequency import TuringFrequencyTypes
from turing_models.utilities.global_variables import gDaysInYear
from turing_models.utilities.error import TuringError
from turing_models.utilities.global_types import TuringOptionTypes

from turing_models.utilities.helper_functions import labelToString, checkArgumentTypes
from turing_models.utilities.turing_date import TuringDate
from turing_models.utilities.day_count import TuringDayCountTypes
from turing_models.utilities.calendar import TuringBusDayAdjustTypes
from turing_models.utilities.calendar import TuringCalendarTypes,  TuringDateGenRuleTypes
from turing_models.utilities.schedule import TuringSchedule
from turing_models.products.equity.equity_option import TuringEquityOption
from turing_models.market.curves.discount_curve_flat import TuringDiscountCurve

from turing_models.models.model_black_scholes import bsValue, TuringModelBlackScholes
from turing_models.models.model import TuringModel

###############################################################################
# TODO: Do we need to day count adjust option payoffs ?
# TODO: Monte Carlo pricer
###############################################################################

class TuringEquityCliquetOption(TuringEquityOption):
    ''' A TuringEquityCliquetOption is a series of options which start and stop at
    successive times with each subsequent option resetting its strike to be ATM
    at the start of its life. This is also known as a reset option.'''

    def __init__(self,
                 startDate: TuringDate,
                 finalExpiryDate: TuringDate,
                 optionType: TuringOptionTypes,
                 freqType: TuringFrequencyTypes,
                 dayCountType: TuringDayCountTypes = TuringDayCountTypes.THIRTY_E_360,
                 calendarType: TuringCalendarTypes = TuringCalendarTypes.WEEKEND,
                 busDayAdjustType: TuringBusDayAdjustTypes = TuringBusDayAdjustTypes.FOLLOWING,
                 dateGenRuleType: TuringDateGenRuleTypes = TuringDateGenRuleTypes.BACKWARD):
        ''' Create the TuringEquityCliquetOption by passing in the start date
        and the end date and whether it is a call or a put. Some additional
        data is needed in order to calculate the individual payments. '''

        checkArgumentTypes(self.__init__, locals())

        if optionType != TuringOptionTypes.EUROPEAN_CALL and \
           optionType != TuringOptionTypes.EUROPEAN_PUT:
            raise TuringError("Unknown Option Type" + str(optionType))

        if finalExpiryDate < startDate:
            raise TuringError("Expiry date precedes start date")

        self._startDate = startDate
        self._finalExpiryDate = finalExpiryDate
        self._optionType = optionType
        self._freqType = freqType
        self._dayCountType = dayCountType
        self._calendarType = calendarType
        self._busDayAdjustType = busDayAdjustType
        self._dateGenRuleType = dateGenRuleType

        self._expiryDates = TuringSchedule(self._startDate,
                                           self._finalExpiryDate,
                                           self._freqType,
                                           self._calendarType,
                                           self._busDayAdjustType,
                                           self._dateGenRuleType)._generate()

###############################################################################

    def value(self,
              valueDate: TuringDate,
              stockPrice: float,
              discountCurve: TuringDiscountCurve,
              dividendCurve: TuringDiscountCurve,
              model:TuringModel):
        ''' Value the cliquet option as a sequence of options using the Black-
        Scholes model. '''

        if valueDate > self._finalExpiryDate:
            raise TuringError("Value date after final expiry date.")

        s = stockPrice
        v_cliquet = 0.0

        self._v_options = []
        self._dfs = []
        self._actualDates = []

        CALL = TuringOptionTypes.EUROPEAN_CALL
        PUT = TuringOptionTypes.EUROPEAN_PUT

        if isinstance(model, TuringModelBlackScholes):

            v = model._volatility
            v = max(v, 1e-6)
            tprev = 0.0

            for dt in self._expiryDates:

                if dt > valueDate:

                    df = discountCurve.df(dt)
                    texp = (dt - valueDate) / gDaysInYear
                    r = -np.log(df) / texp

                    # option life
                    tau = texp - tprev

                    # The deflator is out to the option reset time
                    dq = dividendCurve._df(tprev)

                    # The option dividend is over the option life
                    dqMat = dividendCurve._df(texp)

                    q = -np.log(dqMat/dq)/tau

                    if self._optionType == CALL:
                        v_fwd_opt = s * dq * bsValue(1.0, tau, 1.0, r, q, v, CALL.value)
                        v_cliquet += v_fwd_opt
                    elif self._optionType == PUT:
                        v_fwd_opt = s * dq * bsValue(1.0, tau, 1.0, r, q, v, PUT.value)
                        v_cliquet += v_fwd_opt
                    else:
                        raise TuringError("Unknown option type")

#                    print(dt, r, df, q, v_fwd_opt, v_cliquet)

                    self._dfs.append(df)
                    self._v_options.append(v)
                    self._actualDates.append(dt)
                    tprev = texp
        else:
            raise TuringError("Unknown Model Type")

        return v_cliquet

###############################################################################

    def printFlows(self):
        numOptions = len(self._v_options)
        for i in range(0, numOptions):
            print(self._actualDates[i], self._dfs[i], self._v_options[i])

###############################################################################

    def __repr__(self):
        s = labelToString("OBJECT TYPE", type(self).__name__)
        s += labelToString("START DATE", self._startDate)
        s += labelToString("FINAL EXPIRY DATE", self._finalExpiryDate)
        s += labelToString("OPTION TYPE", self._optionType)
        s += labelToString("FREQUENCY TYPE", self._freqType)
        s += labelToString("DAY COUNT TYPE", self._dayCountType)
        s += labelToString("CALENDAR TYPE", self._calendarType)
        s += labelToString("BUS DAY ADJUST TYPE", self._busDayAdjustType)
        s += labelToString("DATE GEN RULE TYPE", self._dateGenRuleType, "")
        return s

###############################################################################

    def _print(self):
        ''' Simple print function for backward compatibility. '''
        print(self)

###############################################################################
