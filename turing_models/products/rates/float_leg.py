from turing_models.utilities.error import TuringError
from turing_models.utilities.turing_date import TuringDate
from turing_models.utilities.mathematics import ONE_MILLION
from turing_models.utilities.day_count import TuringDayCount, TuringDayCountTypes
from turing_models.utilities.frequency import TuringFrequencyTypes
from turing_models.utilities.calendar import TuringCalendarTypes,  TuringDateGenRuleTypes
from turing_models.utilities.calendar import TuringCalendar, TuringBusDayAdjustTypes
from turing_models.utilities.schedule import TuringSchedule
from turing_models.utilities.helper_functions import label_to_string, checkArgumentTypes
from turing_models.utilities.global_types import TuringSwapTypes
from fundamental.market.curves.discount_curve import TuringDiscountCurve

##########################################################################

class TuringFloatLeg(object):
    ''' Class for managing the floating leg of a swap. A float leg consists of
    a sequence of flows calculated according to an ISDA schedule and with a 
    coupon determined by an index curve which changes over life of the swap.'''
    
    def __init__(self,
                 effectiveDate: TuringDate,  # Date interest starts to accrue
                 endDate: (TuringDate, str),  # Date contract ends
                 legType: TuringSwapTypes,
                 spread: (float),
                 freqType: TuringFrequencyTypes,
                 dayCountType: TuringDayCountTypes,
                 notional: float = ONE_MILLION,
                 principal: float = 0.0,
                 paymentLag: int= 0,
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
            raise TuringError("Start date after maturity date")

        self._effectiveDate = effectiveDate
        self._endDate = endDate
        self._legType = legType
        self._freqType = freqType
        self._paymentLag = paymentLag
        self._notional = notional
        self._principal = principal
        self._spread = spread

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

        self.generatePaymentDates()

###############################################################################

    def generatePaymentDates(self):
        ''' Generate the floating leg payment dates and accrual factors. The
        coupons cannot be generated yet as we do not have the index curve. '''

        scheduleDates = TuringSchedule(self._effectiveDate,
                                       self._terminationDate,
                                       self._freqType,
                                       self._calendarType,
                                       self._busDayAdjustType,
                                       self._dateGenRuleType)._generate()

        if len(scheduleDates) < 2:
            raise TuringError("Schedule has none or only one date")

        self._startAccruedDates = []
        self._endAccruedDates = []
        self._paymentDates = []
        self._yearFracs = []
        self._accruedDays = []

        prevDt = scheduleDates[0]

        dayCounter = TuringDayCount(self._dayCountType)
        calendar = TuringCalendar(self._calendarType)

        # All of the lists end up with the same length
        for nextDt in scheduleDates[1:]:

            self._startAccruedDates.append(prevDt)
            self._endAccruedDates.append(nextDt)

            if self._paymentLag == 0:
                paymentDate = nextDt
            else:
                paymentDate = calendar.addBusinessDays(nextDt, 
                                                       self._paymentLag)

            self._paymentDates.append(paymentDate)

            (yearFrac, num, _) = dayCounter.yearFrac(prevDt, 
                                                     nextDt)        
            
            self._yearFracs.append(yearFrac)
            self._accruedDays.append(num)

            prevDt = nextDt

###############################################################################

    def value(self,
              valuationDate: TuringDate,  # This should be the settlement date
              discountCurve: TuringDiscountCurve,
              indexCurve: TuringDiscountCurve,
              firstFixingRate: float=None):
        ''' Value the floating leg with payments from an index curve and
        discounting based on a supplied discount curve as of the valuation date
        supplied. For an existing swap, the user must enter the next fixing
        coupon. '''

        if discountCurve is None:
            raise TuringError("Discount curve is None")

        if indexCurve is None:
            indexCurve = discountCurve

        self._rates = []
        self._payments = []        
        self._paymentDfs = []
        self._paymentPVs = []
        self._cumulativePVs = []

        notional = self._notional
        dfValue = discountCurve.df(valuationDate)
        legPV = 0.0
        numPayments = len(self._paymentDates)
        firstPayment = False

        for iPmnt in range(0, numPayments):

            pmntDate = self._paymentDates[iPmnt]
            
            if pmntDate > valuationDate:

                startAccruedDt = self._startAccruedDates[iPmnt]
                endAccruedDt = self._endAccruedDates[iPmnt]
                alpha = self._yearFracs[iPmnt]

                if firstPayment is False and firstFixingRate is not None:

                    fwdRate = firstFixingRate
                    firstPayment = True

                else:
                    
                    dfStart = indexCurve.df(startAccruedDt)
                    dfEnd = indexCurve.df(endAccruedDt)
                    fwdRate = (dfStart / dfEnd - 1.0) / alpha

                pmntAmount = (fwdRate + self._spread) * alpha * notional

                dfPmnt = discountCurve.df(pmntDate) / dfValue
                pmntPV = pmntAmount * dfPmnt
                legPV += pmntPV

                self._rates.append(fwdRate)
                self._payments.append(pmntAmount)
                self._paymentDfs.append(dfPmnt)
                self._paymentPVs.append(pmntPV)
                self._cumulativePVs.append(legPV)

            else:

                self._rates.append(0.0)
                self._payments.append(0.0)
                self._paymentDfs.append(0.0)
                self._paymentPVs.append(0.0)
                self._cumulativePVs.append(legPV)

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
        print("SPREAD (bp):", self._spread * 10000)
        print("FREQUENCY:", str(self._freqType))
        print("DAY COUNT:", str(self._dayCountType))

        if len(self._paymentDates) == 0:
            print("Payments Dates not calculated.")
            return

        header = "PAY_DATE     ACCR_START   ACCR_END      DAYS  YEARFRAC"
        print(header)

        numFlows = len(self._paymentDates) 
        
        for iFlow in range(0, numFlows):
            print("%11s  %11s  %11s  %4d  %8.6f  " %
                  (self._paymentDates[iFlow],
                   self._startAccruedDates[iFlow],
                   self._endAccruedDates[iFlow],
                   self._accruedDays[iFlow],
                   self._yearFracs[iFlow]))
            
###############################################################################

    def printValuation(self):
        ''' Prints the fixed leg dates, accrual factors, discount factors,
        cash amounts, their present value and their cumulative PV using the
        last valuation performed. '''

        print("START DATE:", self._effectiveDate)
        print("MATURITY DATE:", self._maturityDate)
        print("SPREAD (BPS):", self._spread * 10000)
        print("FREQUENCY:", str(self._freqType))
        print("DAY COUNT:", str(self._dayCountType))

        if len(self._payments) == 0:
            print("Payments not calculated.")
            return

        header = "PAY_DATE     ACCR_START   ACCR_END     DAYS  YEARFRAC"
        header += "    IBOR      PAYMENT       DF          PV        CUM PV"
        print(header)

        numFlows = len(self._paymentDates) 
        
        for iFlow in range(0, numFlows):
            print("%11s  %11s  %11s  %4d  %8.6f  %9.5f  % 11.2f  %10.8f  % 11.2f  % 11.2f" %
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

###############################################################################

    def __repr__(self):
        s = label_to_string("OBJECT TYPE", type(self).__name__)
        s += label_to_string("START DATE", self._effectiveDate)
        s += label_to_string("TERMINATION DATE", self._terminationDate)
        s += label_to_string("MATURITY DATE", self._maturityDate)
        s += label_to_string("NOTIONAL", self._notional)
        s += label_to_string("SWAP TYPE", self._legType)
        s += label_to_string("SPREAD (BPS)", self._spread * 10000)
        s += label_to_string("FREQUENCY", self._freqType)
        s += label_to_string("DAY COUNT", self._dayCountType)
        s += label_to_string("CALENDAR", self._calendarType)
        s += label_to_string("BUS DAY ADJUST", self._busDayAdjustType)
        s += label_to_string("DATE GEN TYPE", self._dateGenRuleType)
        return s

###############################################################################

    def _print(self):
        ''' Print a list of the unadjusted coupon payment dates used in
        analytic calculations for the bond. '''
        print(self)

###############################################################################
