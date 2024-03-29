from turing_models.utilities.error import TuringError
from turing_models.utilities.turing_date import TuringDate
from turing_models.utilities.mathematics import ONE_MILLION
from turing_models.utilities.day_count import TuringDayCount, DayCountType
from turing_models.utilities.frequency import FrequencyType
from turing_models.utilities.calendar import TuringCalendarTypes,  TuringDateGenRuleTypes
from turing_models.utilities.calendar import TuringCalendar, TuringBusDayAdjustTypes
from turing_models.utilities.schedule import TuringSchedule
from turing_models.utilities.helper_functions import to_string, checkArgumentTypes
from turing_models.utilities.global_types import TuringSwapTypes
from turing_models.market.curves.discount_curve import TuringDiscountCurve

##########################################################################

class TuringFixedLeg(object):
    """ Class for managing the fixed leg of a swap. A fixed leg is a leg with
    a sequence of flows calculated according to an ISDA schedule and with a
    coupon that is fixed over the life of the swap. """

    def __init__(self,
                 effectiveDate: TuringDate,  # Date interest starts to accrue
                 endDate: (TuringDate, str),  # Date contract ends
                 legType: TuringSwapTypes,
                 coupon: (float),
                 freqType: FrequencyType,
                 dayCountType: DayCountType,
                 notional: float = ONE_MILLION,
                 principal: float = 0.0,
                 paymentLag: int = 0,
                 calendarType: TuringCalendarTypes = TuringCalendarTypes.WEEKEND,
                 busDayAdjustType: TuringBusDayAdjustTypes = TuringBusDayAdjustTypes.FOLLOWING,
                 dateGenRuleType: TuringDateGenRuleTypes = TuringDateGenRuleTypes.BACKWARD):
        ''' Create the fixed leg of a swap contract giving the contract start
        date, its maturity, fixed coupon, fixed leg frequency, fixed leg day
        count convention and notional.  '''

        checkArgumentTypes(self.__init__, locals())

        if type(endDate) == TuringDate:
            self._terminationDate = endDate
        else:
            self._terminationDate = effectiveDate.addTenor(endDate)

        calendar = TuringCalendar(calendarType)

        self._maturityDate = calendar.adjust(self._terminationDate,
                                             busDayAdjustType)

        if effectiveDate > self._maturityDate:
            raise TuringError("Effective date after maturity date")

        self._effectiveDate = effectiveDate
        self._endDate = endDate
        self._legType = legType
        self._freqType = freqType
        self._paymentLag = paymentLag
        self._notional = notional
        self._principal = principal
        self._coupon = coupon

        self._dayCountType = dayCountType
        self._calendarType = calendarType
        self._busDayAdjustType = busDayAdjustType
        self._dateGenRuleType = dateGenRuleType

        self._startAccruedDates = []
        self._endAccruedDates = []
        self._paymentDates = []
        self._payments = []
        self._yearFracs = []
        self._accruedDays = []
        self._rates = []

        self.generatePayments()

###############################################################################

    def generatePayments(self):
        # These are generated immediately as they are for the entire
        # life of the swap. Given a valuation date we can determine
        # which cash flows are in the future and value the swap
        # The schedule allows for a specified lag in the payment date
        # Nothing is paid on the swap effective date and so the first payment
        # date is the first actual payment date

        schedule = TuringSchedule(self._effectiveDate,
                                  self._terminationDate,
                                  self._freqType,
                                  self._calendarType,
                                  self._busDayAdjustType,
                                  self._dateGenRuleType)

        scheduleDates = schedule._adjustedDates

        if len(scheduleDates) < 2:
            raise TuringError("Schedule has none or only one date")

        self._startAccruedDates = []
        self._endAccruedDates = []
        self._paymentDates = []
        self._yearFracs = []
        self._accruedDays = []
        self._rates = []

        prevDt = scheduleDates[0]

        dayCounter = TuringDayCount(self._dayCountType)
        calendar = TuringCalendar(self._calendarType)

        for nextDt in scheduleDates[1:]:

            self._startAccruedDates.append(prevDt)
            self._endAccruedDates.append(nextDt)

            if self._paymentLag == 0:
                paymentDate = nextDt
            else:
                paymentDate = calendar.addBusinessDays(nextDt,
                                                       self._paymentLag)

            self._paymentDates.append(paymentDate)

            (yearFrac, num, den) = dayCounter.yearFrac(prevDt,
                                                       nextDt)

            self._rates.append(self._coupon)

            payment = yearFrac * self._notional * self._coupon

            self._payments.append(payment)
            self._yearFracs.append(yearFrac)
            self._accruedDays.append(num)

            prevDt = nextDt

###############################################################################

    def value(self,
              valuationDate: TuringDate,
              discountCurve: TuringDiscountCurve):

        self._paymentDfs = []
        self._paymentPVs = []
        self._cumulativePVs = []

        notional = self._notional
        dfValue = discountCurve.df(valuationDate)
        legPV = 0.0
        numPayments = len(self._paymentDates)

        dfPmnt = 0.0

        for iPmnt in range(0, numPayments):

            pmntDate = self._paymentDates[iPmnt]
            pmntAmount= self._payments[iPmnt]

            if pmntDate > valuationDate:

                dfPmnt = discountCurve.df(pmntDate) / dfValue
                pmntPV = pmntAmount * dfPmnt
                legPV += pmntPV

                self._paymentDfs.append(dfPmnt)
                self._paymentPVs.append(pmntAmount*dfPmnt)
                self._cumulativePVs.append(legPV)

            else:

                self._paymentDfs.append(0.0)
                self._paymentPVs.append(0.0)
                self._cumulativePVs.append(0.0)

        if pmntDate > valuationDate:
            paymentPV = self._principal * dfPmnt * notional
            self._paymentPVs[-1] += paymentPV
            legPV += paymentPV
            self._cumulativePVs[-1] = legPV

        if self._legType == TuringSwapTypes.PAY:
            legPV = legPV * (-1.0)

        return legPV

##########################################################################

    def printPayments(self):
        ''' Prints the fixed leg dates, accrual factors, discount factors,
        cash amounts, their present value and their cumulative PV using the
        last valuation performed. '''

        print("START DATE:", self._effectiveDate)
        print("MATURITY DATE:", self._maturityDate)
        print("COUPON (%):", self._coupon * 100)
        print("FREQUENCY:", str(self._freqType))
        print("DAY COUNT:", str(self._dayCountType))

        if len(self._payments) == 0:
            print("Payments not calculated.")
            return

        header = "PAY_DATE     ACCR_START   ACCR_END      DAYS  YEARFRAC"
        header += "    RATE      PAYMENT "
        print(header)

        numFlows = len(self._paymentDates)

        for iFlow in range(0, numFlows):
            print("%11s  %11s  %11s  %4d  %8.6f  %8.6f  %11.2f" %
                  (self._paymentDates[iFlow],
                   self._startAccruedDates[iFlow],
                   self._endAccruedDates[iFlow],
                   self._accruedDays[iFlow],
                   self._yearFracs[iFlow],
                   self._rates[iFlow] * 100.0,
                   self._payments[iFlow]))

###############################################################################

    def printValuation(self):
        ''' Prints the fixed leg dates, accrual factors, discount factors,
        cash amounts, their present value and their cumulative PV using the
        last valuation performed. '''

        print("START DATE:", self._effectiveDate)
        print("MATURITY DATE:", self._maturityDate)
        print("COUPON (%):", self._coupon * 100)
        print("FREQUENCY:", str(self._freqType))
        print("DAY COUNT:", str(self._dayCountType))

        if len(self._payments) == 0:
            print("Payments not calculated.")
            return

        header = "PAY_DATE     ACCR_START   ACCR_END     DAYS  YEARFRAC"
        header += "    RATE      PAYMENT       DF          PV        CUM PV"
        print(header)

        numFlows = len(self._paymentDates)

        for iFlow in range(0, numFlows):
            print("%11s  %11s  %11s  %4d  %8.6f  %8.5f  % 11.2f  %10.8f  % 11.2f  % 11.2f" %
                  (self._paymentDates[iFlow],
                   self._startAccruedDates[iFlow],
                   self._endAccruedDates[iFlow],
                   self._accruedDays[iFlow],
                   self._yearFracs[iFlow],
                   self._rates[iFlow] * 100.0,
                   self._payments[iFlow],
                   self._paymentDfs[iFlow],
                   self._paymentPVs[iFlow],
                   self._cumulativePVs[iFlow]))

##########################################################################

    def __repr__(self):
        s = to_string("OBJECT TYPE", type(self).__name__)
        s += to_string("START DATE", self._effectiveDate)
        s += to_string("TERMINATION DATE", self._terminationDate)
        s += to_string("MATURITY DATE", self._maturityDate)
        s += to_string("NOTIONAL", self._notional)
        s += to_string("PRINCIPAL", self._principal)
        s += to_string("LEG TYPE", self._legType)
        s += to_string("COUPON", self._coupon)
        s += to_string("FREQUENCY", self._freqType)
        s += to_string("DAY COUNT", self._dayCountType)
        s += to_string("CALENDAR", self._calendarType)
        s += to_string("BUS DAY ADJUST", self._busDayAdjustType)
        s += to_string("DATE GEN TYPE", self._dateGenRuleType)
        return s

###############################################################################

    def _print(self):
        ''' Print a list of the unadjusted coupon payment dates used in
        analytic calculations for the bond. '''
        print(self)

###############################################################################
