##############################################################################
# Copyright (C) 2018, 2019, 2020 Dominic O'Kane
##############################################################################

from turing_models.turingutils.turing_date import TuringDate
from turing_models.turingutils.turing_frequency import TuringFrequency, TuringFrequencyTypes
from turing_models.turingutils.turing_calendar import TuringCalendarTypes
from turing_models.turingutils.turing_schedule import TuringSchedule
from turing_models.turingutils.turing_calendar import TuringBusDayAdjustTypes
from turing_models.turingutils.turing_calendar import TuringDateGenRuleTypes
from turing_models.turingutils.turing_day_count import TuringDayCount, TuringDayCountTypes
from turing_models.turingutils.turing_error import TuringError
from turing_models.turingutils.turing_helper_functions import checkArgumentTypes, labelToString
from turing_models.market.curves.turing_discount_curve import TuringDiscountCurve

###############################################################################


class TuringBondAnnuity(object):
    ''' An annuity is a vector of dates and flows generated according to ISDA
    standard rules which starts on the next date after the start date
    (effective date) and runs up to an end date with no principal repayment.
    Dates are then adjusted according to a specified calendar. '''

    def __init__(self,
                 maturityDate: TuringDate,
                 coupon: float,
                 freqType: TuringFrequencyTypes,
                 calendarType: TuringCalendarTypes = TuringCalendarTypes.WEEKEND,
                 busDayAdjustType: TuringBusDayAdjustTypes = TuringBusDayAdjustTypes.FOLLOWING,
                 dateGenRuleType: TuringDateGenRuleTypes = TuringDateGenRuleTypes.BACKWARD,
                 dayCountConventionType: TuringDayCountTypes = TuringDayCountTypes.ACT_360,
                 face: float = 100.0):

        checkArgumentTypes(self.__init__, locals())

        self._maturityDate = maturityDate
        self._coupon = coupon
        self._freqType = freqType
        self._frequency = TuringFrequency(freqType)

        # ISDA Style conventions
        self._calendarType = calendarType
        self._busDayAdjustType = busDayAdjustType
        self._dateGenRuleType = dateGenRuleType
        self._dayCountConventionType = dayCountConventionType

        self._face = face
        self._par = 100.0

        self._flowDates = []
        self._settlementDate = TuringDate(1, 1, 1900)
        self._accruedInterest = None
        self._accruedDays = 0.0
        self._alpha = 0.0

###############################################################################

    def cleanPriceFromDiscountCurve(self,
                                    settlementDate: TuringDate,
                                    discountCurve: TuringDiscountCurve):
        ''' Calculate the bond price using some discount curve to present-value
        the bond's cashflows. '''

        fullPrice = self.fullPriceFromDiscountCurve(settlementDate,
                                                    discountCurve)
        accrued = self._accruedInterest * self._par / self._face
        cleanPrice = fullPrice - accrued
        return cleanPrice

###############################################################################

    def fullPriceFromDiscountCurve(self,
                                   settlementDate: TuringDate,
                                   discountCurve: TuringDiscountCurve):
        ''' Calculate the bond price using some discount curve to present-value
        the bond's cashflows. '''

        self.calculateFlowDatesPayments(settlementDate)
        pv = 0.0

        numFlows = len(self._flowDates)

        for i in range(1, numFlows):
            dt = self._flowDates[i]
            df = discountCurve.df(dt)
            flow = self._flowAmounts[i]
            pv = pv + flow * df

        return pv * self._par / self._face

###############################################################################

    def calculateFlowDatesPayments(self,
                                   settlementDate: TuringDate):

        # No need to generate flows if settlement date has not changed
        if settlementDate == self._settlementDate:
            return

        if settlementDate == self._maturityDate:
            raise TuringError("Settlement date is maturity date.")

        self._settlementDate = settlementDate
        calendarType = TuringCalendarTypes.NONE
        busDayRuleType = TuringBusDayAdjustTypes.NONE
        dateGenRuleType = TuringDateGenRuleTypes.BACKWARD

        self._flowDates = TuringSchedule(settlementDate,
                                         self._maturityDate,
                                         self._freqType,
                                         calendarType,
                                         busDayRuleType,
                                         dateGenRuleType)._generate()

        self._pcd = self._flowDates[0]
        self._ncd = self._flowDates[1]
        self.calcAccruedInterest(settlementDate)

        self._flowAmounts = [0.0]
        basis = TuringDayCount(self._dayCountConventionType)

        prevDt = self._pcd

        for nextDt in self._flowDates[1:]:
            alpha = basis.yearFrac(prevDt, nextDt)[0]
            flow = self._coupon * alpha * self._face
            self._flowAmounts.append(flow)
            prevDt = nextDt

###############################################################################

    def calcAccruedInterest(self,
                            settlementDate: TuringDate):
        ''' Calculate the amount of coupon that has accrued between the
        previous coupon date and the settlement date. '''

        if settlementDate != self._settlementDate:
            self.calculateFlowDatesPayments(settlementDate)

        if len(self._flowDates) == 0:
            raise TuringError("Accrued interest - not enough flow dates.")

        dc = TuringDayCount(self._dayCountConventionType)

        (accFactor, num, _) = dc.yearFrac(self._pcd,
                                          settlementDate,
                                          self._ncd, 
                                          self._frequency)

        self._alpha = 1.0 - accFactor * self._frequency

        self._accruedInterest = accFactor * self._face * self._coupon
        self._accruedDays = num
        return self._accruedInterest

###############################################################################

    def printFlows(self,
                   settlementDate: TuringDate):
        ''' Print a list of the unadjusted coupon payment dates used in
        analytic calculations for the bond. '''

        self.calculateFlowDatesPayments(settlementDate)

        numFlows = len(self._flowDates)
        for i in range(1, numFlows):
            dt = self._flowDates[i]
            flow = self._flowAmounts[i]
            print(dt, ",", flow)

###############################################################################

    def __repr__(self):
        ''' Print a list of the unadjusted coupon payment dates used in
        analytic calculations for the bond. '''

        s = labelToString("OBJECT TYPE", type(self).__name__)
        s += labelToString("MATURITY DATE", self._maturityDate)
        s += labelToString("FREQUENCY", self._freqType)
        s += labelToString("CALENDAR", self._calendarType)
        s += labelToString("BUS_DAY_RULE", self._busDayAdjustType)
        s += labelToString("DATE_GEN_RULE", self._dateGenRuleType)

        return s

###############################################################################

    def _print(self):
        ''' Simple print function for backward compatibility. '''
        print(self)


###############################################################################
