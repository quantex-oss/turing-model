##############################################################################
# TODO: Allow an index curve to be passed in that is not same as discount curve
# TODO: Extend to allow term structure of volatility
# TODO: Extend to allow two fixed legs in underlying swap
# TODO: Cash settled swaptions
##############################################################################

import numpy as np

from turing_models.utilities.calendar import TuringCalendarTypes
from turing_models.utilities.calendar import TuringBusDayAdjustTypes
from turing_models.utilities.calendar import TuringDateGenRuleTypes
from turing_models.utilities.day_count import TuringDayCountTypes
from turing_models.utilities.frequency import TuringFrequencyTypes
from turing_models.utilities.global_variables import gDaysInYear
from turing_models.utilities.mathematics import ONE_MILLION
from turing_models.utilities.error import TuringError
from turing_models.utilities.helper_functions import labelToString, checkArgumentTypes
from turing_models.utilities.turing_date import TuringDate

from turing_models.products.rates.ibor_swap import TuringIborSwap

from turing_models.models.model_black import TuringModelBlack
from turing_models.models.model_black_shifted import TuringModelBlackShifted
from turing_models.models.model_sabr import TuringModelSABR
from turing_models.models.model_sabr_shifted import TuringModelSABRShifted
from turing_models.models.model_rates_hw import TuringModelRatesHW
from turing_models.models.model_rates_bk import TuringModelRatesBK
from turing_models.models.model_rates_bdt import TuringModelRatesBDT

from turing_models.utilities.global_types import TuringOptionTypes
from turing_models.utilities.global_types import TuringSwapTypes
from turing_models.utilities.global_types import TuringExerciseTypes

###############################################################################


class TuringIborSwaption():
    ''' This is the class for the European-style swaption, an option to enter
    into a swap (payer or receiver of the fixed coupon), that starts in the
    future and with a fixed maturity, at a swap rate fixed today. '''

    def __init__(self,
                 settlementDate: TuringDate,
                 exerciseDate: TuringDate,
                 maturityDate: TuringDate,
                 fixedLegType: TuringSwapTypes,
                 fixedCoupon: float,
                 fixedFrequencyType: TuringFrequencyTypes,
                 fixedDayCountType: TuringDayCountTypes,
                 notional: float = ONE_MILLION,
                 floatFrequencyType: TuringFrequencyTypes = TuringFrequencyTypes.QUARTERLY,
                 floatDayCountType: TuringDayCountTypes = TuringDayCountTypes.THIRTY_E_360,
                 calendarType: TuringCalendarTypes = TuringCalendarTypes.WEEKEND,
                 busDayAdjustType: TuringBusDayAdjustTypes = TuringBusDayAdjustTypes.FOLLOWING,
                 dateGenRuleType: TuringDateGenRuleTypes = TuringDateGenRuleTypes.BACKWARD):
        ''' Create a European-style swaption by defining the exercise date of
        the swaption, and all of the details of the underlying interest rate
        swap including the fixed coupon and the details of the fixed and the
        floating leg payment schedules. Bermudan style swaption should be
        priced using the TuringIborBermudanSwaption class. '''

        checkArgumentTypes(self.__init__, locals())

        if settlementDate > exerciseDate:
            raise TuringError("Settlement date must be before expiry date")

        if exerciseDate > maturityDate:
            raise TuringError("Exercise date must be before swap maturity date")

        self._settlementDate = settlementDate
        self._exerciseDate = exerciseDate
        self._maturityDate = maturityDate
        self._fixedLegType = fixedLegType

        self._notional = notional

        self._fixedCoupon = fixedCoupon
        self._fixedFrequencyType = fixedFrequencyType
        self._fixedDayCountType = fixedDayCountType
        self._floatFrequencyType = floatFrequencyType
        self._floatDayCountType = floatDayCountType

        self._calendarType = calendarType
        self._busDayAdjustType = busDayAdjustType
        self._dateGenRuleType = dateGenRuleType

        self._pv01 = None
        self._fwdSwapRate = None
        self._forwardDf = None
        self._underlyingSwap = None

###############################################################################

    def value(self,
              valuationDate,
              discountCurve,
              model):
        ''' Valuation of a Ibor European-style swaption using a choice of
        models on a specified valuation date. Models include TuringModelBlack,
        TuringModelBlackShifted, TuringModelSABR, TuringModelSABRShifted, FinModelHW,
        FinModelBK and FinModelBDT. The last two involved a tree-based
        valuation. '''

        floatSpread = 0.0

        # We create a swap that starts on the exercise date.
        swap = TuringIborSwap(self._exerciseDate,
                              self._maturityDate,
                              self._fixedLegType,
                              self._fixedCoupon,
                              self._fixedFrequencyType,
                              self._fixedDayCountType,
                              self._notional,
                              floatSpread,
                              self._floatFrequencyType,
                              self._floatDayCountType,
                              self._calendarType,
                              self._busDayAdjustType,
                              self._dateGenRuleType)

        k = self._fixedCoupon

        # The pv01 is the value of the swap cashflows as of the curve date
        pv01 = swap.pv01(valuationDate, discountCurve)

        # We need to calculate the forward swap rate on the swaption exercise
        # date that makes the forward swap worth par including principal
        s = swap.swapRate(valuationDate, discountCurve)

        texp = (self._exerciseDate - self._settlementDate) / gDaysInYear
        tmat = (self._maturityDate - self._settlementDate) / gDaysInYear

        # Discounting is done via the PV01 annuity so no discounting in Black
        df = 1.0

        #######################################################################
        # For the tree models we need to generate a vector of the coupons
        #######################################################################

        cpnTimes = [texp]
        cpnFlows = [0.0]

        # The first flow is on the day after the expiry date
        numFlows = len(swap.fixed_leg._paymentDates)

        for iFlow in range(0, numFlows):
            
            flowDate = swap.fixed_leg._paymentDates[iFlow]

            # Only flows occurring after option expiry are counted. 
            # Flows on the expiry date are not included
            if flowDate > self._exerciseDate:
                cpnTime = (flowDate - valuationDate) / gDaysInYear
                cpnFlow = swap.fixed_leg._payments[iFlow] / self._notional
                cpnTimes.append(cpnTime)
                cpnFlows.append(cpnFlow)

        cpnTimes = np.array(cpnTimes)
        cpnFlows = np.array(cpnFlows)

        dfTimes = discountCurve._times
        dfValues = discountCurve._dfs

        if np.any(cpnTimes < 0.0):
            raise TuringError("No coupon times can be before the value date.")

        strikePrice = 1.0
        faceAmount = 1.0

        #######################################################################

        if isinstance(model, TuringModelBlack):

            if self._fixedLegType == TuringSwapTypes.PAY:
                swaptionPrice = model.value(s, k, texp, df,
                                            TuringOptionTypes.EUROPEAN_CALL)
            elif self._fixedLegType == TuringSwapTypes.RECEIVE:
                swaptionPrice = model.value(s, k, texp, df,
                                            TuringOptionTypes.EUROPEAN_PUT)

        elif isinstance(model, TuringModelBlackShifted):

            if self._fixedLegType == TuringSwapTypes.PAY:
                swaptionPrice = model.value(s, k, texp, df,
                                            TuringOptionTypes.EUROPEAN_CALL)
            elif self._fixedLegType == TuringSwapTypes.RECEIVE:
                swaptionPrice = model.value(s, k, texp, df,
                                            TuringOptionTypes.EUROPEAN_PUT)

        elif isinstance(model, TuringModelSABR):

            if self._fixedLegType == TuringSwapTypes.PAY:
                swaptionPrice = model.value(s, k, texp, df,
                                            TuringOptionTypes.EUROPEAN_CALL)
            elif self._fixedLegType == TuringSwapTypes.RECEIVE:
                swaptionPrice = model.value(s, k, texp, df,
                                            TuringOptionTypes.EUROPEAN_PUT)

        elif isinstance(model, TuringModelSABRShifted):

            if self._fixedLegType == TuringSwapTypes.PAY:
                swaptionPrice = model.value(s, k, texp, df,
                                            TuringOptionTypes.EUROPEAN_CALL)
            elif self._fixedLegType == TuringSwapTypes.RECEIVE:
                swaptionPrice = model.value(s, k, texp, df,
                                            TuringOptionTypes.EUROPEAN_PUT)

        elif isinstance(model, TuringModelRatesHW):

            swaptionPx = model.europeanBondOptionJamshidian(texp,
                                                  strikePrice,
                                                  faceAmount, 
                                                  cpnTimes,
                                                  cpnFlows,
                                                  dfTimes,
                                                  dfValues)

            if self._fixedLegType == TuringSwapTypes.PAY:
                swaptionPrice = swaptionPx['put']
            elif self._fixedLegType == TuringSwapTypes.RECEIVE:
                swaptionPrice = swaptionPx['call']
            else:
                raise TuringError("Unknown swaption option type" +
                                  str(self._swapType))

            # Cancel the multiplication at the end below
            swaptionPrice /= pv01

        elif isinstance(model, TuringModelRatesBK):

            model.buildTree(tmat, dfTimes, dfValues)
            swaptionPx = model.bermudanSwaption(texp,
                                                tmat,
                                                strikePrice,
                                                faceAmount,
                                                cpnTimes,
                                                cpnFlows,
                                                TuringExerciseTypes.EUROPEAN)

            if self._fixedLegType == TuringSwapTypes.PAY:
                swaptionPrice = swaptionPx['pay']
            elif self._fixedLegType == TuringSwapTypes.RECEIVE:
                swaptionPrice = swaptionPx['rec']

            swaptionPrice /= pv01

        elif isinstance(model, TuringModelRatesBDT):

            model.buildTree(tmat, dfTimes, dfValues)
            swaptionPx = model.bermudanSwaption(texp,
                                                tmat,
                                                strikePrice,
                                                faceAmount,
                                                cpnTimes,
                                                cpnFlows,
                                                TuringExerciseTypes.EUROPEAN)

            if self._fixedLegType == TuringSwapTypes.PAY:
                swaptionPrice = swaptionPx['pay']
            elif self._fixedLegType == TuringSwapTypes.RECEIVE:
                swaptionPrice = swaptionPx['rec']

            swaptionPrice /= pv01
        else:
            raise TuringError("Unknown swaption model " + str(model))

        self._pv01 = pv01
        self._fwdSwapRate = s
        self._forwardDf = discountCurve.df(self._exerciseDate)
        self._underlyingSwap = swap

        # The exchange of cash occurs on the settlement date. However the
        # actual value is that on the specified valuation date which could
        # be the swaption settlement date.
        dfSettlement = discountCurve.df(self._settlementDate)
        swaptionPrice = swaptionPrice * pv01 * self._notional / dfSettlement
        return swaptionPrice

###############################################################################

    def cashSettledValue(self,
                         valuationDate: TuringDate,
                         discountCurve,
                         swapRate: float,
                         model):
        ''' Valuation of a Ibor European-style swaption using a cash settled
        approach which is a market convention that used Black's model and that
        discounts all of the future payments at a flat swap rate. Note that the
        Black volatility for this valuation should in general not equal the
        Black volatility for the standard arbitrage-free valuation. '''

        floatSpread = 0.0

        swap = TuringIborSwap(self._exerciseDate,
                              self._maturityDate,
                              self._fixedLegType,
                              self._fixedCoupon,
                              self._fixedFrequencyType,
                              self._fixedDayCountType,
                              self._notional,
                              floatSpread,
                              self._floatFrequencyType,
                              self._floatDayCountType,
                              self._calendarType,
                              self._busDayAdjustType,
                              self._dateGenRuleType)

        k = self._fixedCoupon
        s = swapRate

        pv01 = swap.cashSettledPV01(valuationDate,
                                    swapRate,
                                    self._fixedFrequencyType)

        texp = (self._exerciseDate - self._settlementDate) / gDaysInYear

        # Discounting is done via the PV01 annuity so no discounting in Black
        df = 1.0

        if isinstance(model, TuringModelBlack):

            if self._fixedLegType == TuringSwapTypes.PAY:
                swaptionPrice = model.value(s, k, texp, df,
                                            TuringOptionTypes.EUROPEAN_CALL)
            elif self._fixedLegType == TuringSwapTypes.RECEIVE:
                swaptionPrice = model.value(s, k, texp, df,
                                            TuringOptionTypes.EUROPEAN_PUT)
        else:
            raise TuringError("Cash settled swaptions must be priced using"
                              + " Black's model.")

        self._fwdSwapRate = swapRate
        self._forwardDf = discountCurve.df(self._exerciseDate)
        self._underlyingSwap = swap
        # The annuity needs to be discounted to today using the correct df
        self._pv01 = pv01 * self._forwardDf

        # The exchange of cash occurs on the settlement date but we need to 
        # value the swaption on the provided valuation date - which could be
        # the settlement date or may be a different date.
        dfValuation = discountCurve.df(valuationDate)
        swaptionPrice = swaptionPrice * self._pv01 * self._notional / dfValuation
        return swaptionPrice

###############################################################################

    def printSwapFixedLeg(self):

        if self._underlyingSwap is None:
            raise TuringError("Underlying swap has not been set. Do a valuation.")

        self._underlyingSwap.printFixedLegPV()

###############################################################################

    def printSwapFloatLeg(self):

        if self._underlyingSwap is None:
            raise TuringError("Underlying swap has not been set. Do a valuation.")

        self._underlyingSwap.printFloatLegPV()

###############################################################################

    def __repr__(self):
        ''' Function to allow us to print the swaption details. '''

        s = labelToString("OBJECT TYPE", type(self).__name__)
        s += labelToString("SETTLEMENT DATE", self._settlementDate)
        s += labelToString("EXERCISE DATE", self._exerciseDate)
        s += labelToString("SWAP FIXED LEG TYPE", str(self._fixedLegType))
        s += labelToString("SWAP MATURITY DATE", self._maturityDate)
        s += labelToString("SWAP NOTIONAL", self._notional)
        s += labelToString("FIXED COUPON", self._fixedCoupon * 100)
        s += labelToString("FIXED FREQUENCY", str(self._fixedFrequencyType))
        s += labelToString("FIXED DAY COUNT", str(self._fixedDayCountType))
        s += labelToString("FLOAT FREQUENCY", str(self._floatFrequencyType))
        s += labelToString("FLOAT DAY COUNT", str(self._floatDayCountType))

        if self._pv01 is not None:
            s += labelToString("PV01", self._pv01)
            s += labelToString("FWD SWAP RATE", self._fwdSwapRate*100)
            s += labelToString("FWD DF TO EXPIRY", self._forwardDf, "")

        return s

###############################################################################

    def _print(self):
        ''' Alternative print method. '''

        print(self)

###############################################################################
