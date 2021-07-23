import numpy as np

from turing_models.utilities.error import TuringError
from turing_models.utilities.turing_date import TuringDate
from turing_models.utilities.global_variables import gSmall
from turing_models.utilities.day_count import TuringDayCountTypes
from turing_models.utilities.frequency import TuringFrequencyTypes, TuringFrequency
from turing_models.utilities.calendar import TuringCalendarTypes,  TuringDateGenRuleTypes
from turing_models.utilities.calendar import TuringCalendar, TuringBusDayAdjustTypes
from turing_models.utilities.helper_functions import checkArgumentTypes, to_string
from turing_models.utilities.mathematics import ONE_MILLION
from turing_models.utilities.global_types import TuringSwapTypes
from fundamental.market.curves.discount_curve import TuringDiscountCurve

from .fixed_leg import TuringFixedLeg
from .float_leg import TuringFloatLeg

##########################################################################


class TuringIborSwap(object):
    ''' Class for managing a standard Fixed vs IBOR swap. This is a contract
    in which a fixed payment leg is exchanged for a series of floating rates
    payments linked to some IBOR index rate. There is no exchange of principal.
    The contract is entered into at zero initial cost. The contract lasts from
    a start date to a specified maturity date.

    The floating rate is not known fully until the end of the preceding payment
    period. It is set in advance and paid in arrears.

    The value of the contract is the NPV of the two coupon streams. Discounting
    is done on a supplied discount curve which is separate from the curve from
    which the implied index rates are extracted. '''

    def __init__(self,
                 effectiveDate: TuringDate,  # Date interest starts to accrue
                 terminationDateOrTenor: (TuringDate, str),  # Date contract ends
                 fixedLegType: TuringSwapTypes,
                 fixedCoupon: float,  # Fixed coupon (annualised)
                 fixedFreqType: TuringFrequencyTypes,
                 fixedDayCountType: TuringDayCountTypes,
                 notional: float = ONE_MILLION,
                 floatSpread: float = 0.0,
                 floatFreqType: TuringFrequencyTypes = TuringFrequencyTypes.QUARTERLY,
                 floatDayCountType: TuringDayCountTypes = TuringDayCountTypes.THIRTY_E_360,
                 calendarType: TuringCalendarTypes = TuringCalendarTypes.WEEKEND,
                 busDayAdjustType: TuringBusDayAdjustTypes = TuringBusDayAdjustTypes.FOLLOWING,
                 dateGenRuleType: TuringDateGenRuleTypes = TuringDateGenRuleTypes.BACKWARD):
        ''' Create an interest rate swap contract giving the contract start
        date, its maturity, fixed coupon, fixed leg frequency, fixed leg day
        count convention and notional. The floating leg parameters have default
        values that can be overwritten if needed. The start date is contractual
        and is the same as the settlement date for a new swap. It is the date
        on which interest starts to accrue. The end of the contract is the
        termination date. This is not adjusted for business days. The adjusted
        termination date is called the maturity date. This is calculated. '''

        checkArgumentTypes(self.__init__, locals())

        if type(terminationDateOrTenor) == TuringDate:
            self.termination_date = terminationDateOrTenor
        else:
            self.termination_date = effectiveDate.addTenor(terminationDateOrTenor)

        calendar = TuringCalendar(calendarType)
        self.maturity_date = calendar.adjust(self.termination_date,
                                             busDayAdjustType)

        if effectiveDate > self.maturity_date:
            raise TuringError("Start date after maturity date")

        self.effective_date = effectiveDate

        floatLegType = TuringSwapTypes.PAY
        if fixedLegType == TuringSwapTypes.PAY:
            floatLegType = TuringSwapTypes.RECEIVE

        paymentLag = 0
        principal = 0.0

        self.fixed_leg = TuringFixedLeg(effectiveDate,
                                        self.termination_date,
                                        fixedLegType,
                                        fixedCoupon,
                                        fixedFreqType,
                                        fixedDayCountType,
                                        notional,
                                        principal,
                                        paymentLag,
                                        calendarType,
                                        busDayAdjustType,
                                        dateGenRuleType)

        self._floatLeg = TuringFloatLeg(effectiveDate,
                                        self.termination_date,
                                        floatLegType,
                                        floatSpread,
                                        floatFreqType,
                                        floatDayCountType,
                                        notional,
                                        principal,
                                        paymentLag,
                                        calendarType,
                                        busDayAdjustType,
                                        dateGenRuleType)

###############################################################################

    def value(self,
              valuationDate: TuringDate,
              discountCurve: TuringDiscountCurve,
              indexCurve: TuringDiscountCurve=None,
              firstFixingRate=None):
        ''' Value the interest rate swap on a value date given a single Ibor
        discount curve. '''

        if indexCurve is None:
            indexCurve = discountCurve

        fixedLegValue = self.fixed_leg.value(valuationDate,
                                             discountCurve)

        floatLegValue = self._floatLeg.value(valuationDate,
                                             discountCurve,
                                             indexCurve,
                                             firstFixingRate)

        value = fixedLegValue + floatLegValue
        return value

###############################################################################

    def pv01(self, valuationDate, discountCurve):
        ''' Calculate the value of 1 basis point coupon on the fixed leg. '''

        pv = self.fixed_leg.value(valuationDate, discountCurve)

        # Needs to be positive even if it is a payer leg
        pv = np.abs(pv)
        pv01 = pv / self.fixed_leg._coupon / self.fixed_leg._notional
        return pv01

###############################################################################

    def swapRate(self,
                 valuationDate:TuringDate,
                 discountCurve: TuringDiscountCurve,
                 indexCurve: TuringDiscountCurve = None,
                 firstFixing: float = None):
        ''' Calculate the fixed leg coupon that makes the swap worth zero.
        If the valuation date is before the swap payments start then this
        is the forward swap rate as it starts in the future. The swap rate
        is then a forward swap rate and so we use a forward discount
        factor. If the swap fixed leg has begun then we have a spot
        starting swap. The swap rate can also be calculated in a dual curve
        approach but in this case the first fixing on the floating leg is
        needed. '''

        pv01 = self.pv01(valuationDate, discountCurve)

        if abs(pv01) < gSmall:
            raise TuringError("PV01 is zero. Cannot compute swap rate.")

        if valuationDate < self.effective_date:
            df0 = discountCurve.df(self.effective_date)
        else:
            df0 = discountCurve.df(valuationDate)

        floatLegPV = 0.0

        if indexCurve is None:
            dfT = discountCurve.df(self.maturity_date)
            floatLegPV = (df0 - dfT)
        else:
            floatLegPV = self._floatLeg.value(valuationDate,
                                              discountCurve,
                                              indexCurve,
                                              firstFixing)

            floatLegPV /= self.fixed_leg._notional

        cpn = floatLegPV / pv01
        return cpn

##########################################################################

    def cashSettledPV01(self,
                        valuationDate,
                        flatSwapRate,
                        frequencyType):
        ''' Calculate the forward value of an annuity of a forward starting
        swap using a single flat discount rate equal to the swap rate. This is
        used in the pricing of a cash-settled swaption in the TuringIborSwaption
        class. This method does not affect the standard valuation methods.'''

        m = TuringFrequency(frequencyType)

        if m == 0:
            raise TuringError("Frequency cannot be zero.")

        ''' The swap may have started in the past but we can only value
        payments that have occurred after the valuation date. '''
        startIndex = 0
        while self.fixed_leg._paymentDates[startIndex] < valuationDate:
            startIndex += 1

        ''' If the swap has yet to settle then we do not include the
        start date of the swap as a coupon payment date. '''
        if valuationDate <= self.effective_date:
            startIndex = 1

        ''' Now PV fixed leg flows. '''
        flatPV01 = 0.0
        df = 1.0
        alpha = 1.0 / m

        for _ in self.fixed_leg._paymentDates[startIndex:]:
            df = df / (1.0 + alpha * flatSwapRate)
            flatPV01 += df * alpha

        return flatPV01

###############################################################################

    def printFixedLegPV(self):
        ''' Prints the fixed leg amounts without any valuation details. Shows
        the dates and sizes of the promised fixed leg flows. '''

        self.fixed_leg.printValuation()

###############################################################################

    def printFloatLegPV(self):
        ''' Prints the fixed leg amounts without any valuation details. Shows
        the dates and sizes of the promised fixed leg flows. '''

        self._floatLeg.printValuation()

###############################################################################

    def printFlows(self):
        ''' Prints the fixed leg amounts without any valuation details. Shows
        the dates and sizes of the promised fixed leg flows. '''

        self.fixed_leg.printPayments()
        self._floatLeg.printPayments()

##########################################################################

    def __repr__(self):

        s = to_string("OBJECT TYPE", type(self).__name__)
        s += self.fixed_leg.__repr__()
        s += "\n"
        s += self._floatLeg.__repr__()
        return s

###############################################################################

    def _print(self):
        ''' Print a list of the unadjusted coupon payment dates used in
        analytic calculations for the bond. '''
        print(self)

###############################################################################
