from .error import TuringError
from .turing_date import TuringDate
from .calendar import (TuringCalendar, TuringCalendarTypes)
from .calendar import (TuringBusDayAdjustTypes, TuringDateGenRuleTypes)
from .frequency import (TuringFrequency, TuringFrequencyTypes)
from .helper_functions import to_string
from .helper_functions import checkArgumentTypes

###############################################################################
# TODO: Start and end date to allow for long stubs
###############################################################################


class TuringSchedule(object):
    ''' A schedule is a set of dates generated according to ISDA standard
    rules which starts on the next date after the effective date and runs up to
    a termination date. Dates are adjusted to a provided calendar. The zeroth
    element is the previous coupon date (PCD) and the first element is the
    Next Coupon Date (NCD). We reference ISDA 2006.'''

    def __init__(self,
                 effectiveDate: TuringDate,  # Also known as the start date
                 terminationDate: TuringDate,  # This is UNADJUSTED (set flag to adjust it)
                 freqType: TuringFrequencyTypes = TuringFrequencyTypes.ANNUAL,
                 calendarType: TuringCalendarTypes = TuringCalendarTypes.WEEKEND,
                 busDayAdjustType: TuringBusDayAdjustTypes = TuringBusDayAdjustTypes.FOLLOWING,
                 dateGenRuleType: TuringDateGenRuleTypes = TuringDateGenRuleTypes.BACKWARD,
                 adjustTerminationDate:bool = True,  # Default is to adjust
                 endOfMonthFlag:bool = False,  # All flow dates are EOM if True
                 firstDate = None,  # First coupon date
                 nextToLastDate = None): # Penultimate coupon date
        ''' Create TuringSchedule object which calculates a sequence of dates
        following the ISDA convention for fixed income products, mainly swaps.

        If the date gen rule type is FORWARD we get the unadjusted dates by stepping
        forward from the effective date in steps of months determined by the period
        tenor - i.e. the number of months between payments. We stop before we go past the
        termination date.

        If the date gen rule type is BACKWARD we get the unadjusted dates by
        stepping backward from the termination date in steps of months determined by
        the period tenor - i.e. the number of months between payments. We stop
        before we go past the effective date.

        - If the EOM flag is false, and the start date is on the 31st then the
        the unadjusted dates will fall on the 30 if a 30 is a previous date.
        - If the EOM flag is false and the start date is 28 Feb then all
        unadjusted dates will fall on the 28th.
        - If the EOM flag is false and the start date is 28 Feb then all
        unadjusted dates will fall on their respective EOM.

        We then adjust all of the flow dates if they fall on a weekend or holiday
        according to the calendar specified. These dates are adjusted in
        accordance with the business date adjustment.

        The effective date is never adjusted as it is not a payment date.
        The termination date is not automatically business day adjusted in a
        swap - assuming it is a holiday date. This must be explicitly stated in
        the trade confirm. However, it is adjusted in a CDS contract as standard.

        Inputs firstDate and nextToLastDate are for managing long payment stubs
        at the start and end of the swap but *have not yet been implemented*. All
        stubs are currently short, either at the start or end of swap. '''

        checkArgumentTypes(self.__init__, locals())

        if effectiveDate >= terminationDate:
            raise TuringError("Effective date must be before termination date.")

        self._effectiveDate = effectiveDate
        self._terminationDate = terminationDate

        if firstDate is None:
            self._firstDate  = effectiveDate
        else:
            if firstDate > effectiveDate and firstDate < terminationDate:
                self._firstDate = firstDate
                print("FIRST DATE NOT IMPLEMENTED") # TODO
            else:
                raise TuringError("First date must be after effective date and" +
                               " before termination date")

        if nextToLastDate is None:
            self._nextToLastDate = terminationDate
        else:
            if nextToLastDate > effectiveDate and nextToLastDate < terminationDate:
                self._nextToLastDate = nextToLastDate
                print("NEXT TO LAST DATE NOT IMPLEMENTED") # TODO
            else:
                raise TuringError("Next to last date must be after effective date and" +
                               " before termination date")

        self._freqType = freqType
        self._calendarType = calendarType
        self._busDayAdjustType = busDayAdjustType
        self._dateGenRuleType = dateGenRuleType

        self._adjustTerminationDate = adjustTerminationDate

        if endOfMonthFlag is True:
            self._endOfMonthFlag = True
        else:
            self._endOfMonthFlag = False

        self._adjustedDates = None

        self._generate()

###############################################################################

    def scheduleDates(self):
        ''' Returns a list of the schedule of FinDates. '''

        if self._adjustedDates is None:
            self._generate()

        return self._adjustedDates

###############################################################################

    def _generate(self):
        ''' Generate schedule of dates according to specified date generation
        rules and also adjust these dates for holidays according to the
        specified business day convention and the specified calendar. '''

        calendar = TuringCalendar(self._calendarType)
        frequency = TuringFrequency(self._freqType)
        if frequency > 52:
            numDays = int(365 / frequency)
        elif frequency > 12:
            numWeeks = int(52 / frequency)
        else:
            numMonths = int(12 / frequency)

        unadjustedScheduleDates = []
        self._adjustedDates = []

        if self._dateGenRuleType == TuringDateGenRuleTypes.BACKWARD:

            nextDate = self._terminationDate
            flowNum = 0

            ordinal = 1
            while nextDate > self._effectiveDate:

                unadjustedScheduleDates.append(nextDate)

                if frequency > 52:
                    nextDate = self._terminationDate.addDays(-numDays * ordinal)
                elif frequency > 12:
                    nextDate = self._terminationDate.addWeeks(-numWeeks * ordinal)
                else:
                    nextDate = self._terminationDate.addMonths(-numMonths * ordinal)

                ordinal += 1

                if self._endOfMonthFlag is True:
                    nextDate = nextDate.EOM()

                flowNum += 1

            # Add on the Previous Coupon Date
            unadjustedScheduleDates.append(nextDate)
            flowNum += 1

            # reverse order and holiday adjust dates
            # the first date is not adjusted as this was provided
            dt = unadjustedScheduleDates[flowNum - 1]
            self._adjustedDates.append(dt)

            # We adjust all flows after the effective date and before the
            # termination date to fall on business days according to their cal
            for i in range(1, flowNum-1):

                dt = calendar.adjust(unadjustedScheduleDates[flowNum - i - 1],
                                     self._busDayAdjustType)

                if dt not in self._adjustedDates:
                    self._adjustedDates.append(dt)

            self._adjustedDates.append(self._terminationDate)

        elif self._dateGenRuleType == TuringDateGenRuleTypes.FORWARD:

            # This needs checking
            nextDate = self._effectiveDate

            ordinal = 1
            while nextDate < self._terminationDate:
                unadjustedScheduleDates.append(nextDate)
                if frequency > 52:
                    nextDate = self._effectiveDate.addDays(numDays * ordinal)
                elif frequency > 12:
                    nextDate = self._effectiveDate.addWeeks(numWeeks * ordinal)
                else:
                    nextDate = self._effectiveDate.addMonths(numMonths * ordinal)
                ordinal += 1

            unadjustedScheduleDates.append(nextDate)
            self._adjustedDates.append(unadjustedScheduleDates[0])

            # The effective date is not adjusted as it is given
            for i in range(1, ordinal):

                dt = calendar.adjust(unadjustedScheduleDates[i],
                                     self._busDayAdjustType)

                if dt not in self._adjustedDates:
                    self._adjustedDates.append(dt)

            # self._adjustedDates.append(self._terminationDate)

        if self._adjustedDates[0] < self._effectiveDate:
            self._adjustedDates[0] = self._effectiveDate

        # The market standard for swaps is not to adjust the termination date
        # unless it is specified in the contract. It is standard for CDS.
        # We change it if the adjustTerminationDate flag is True.
        if self._adjustTerminationDate is True:

            self._terminationDate = calendar.adjust(self._terminationDate,
                                                    self._busDayAdjustType)

            self._adjustedDates[-1] = self._terminationDate

        #######################################################################
        # Check the resulting schedule to ensure that no two dates are the
        # same and that they are monotonic - this should never happen but ...
        #######################################################################

        if len(self._adjustedDates) < 2:
            raise TuringError("Schedule has two dates only.")

        prevDt = self._adjustedDates[0]
        for dt in self._adjustedDates[1:]:

            if dt == prevDt:
                raise TuringError("Two matching dates in schedule")

            if dt < prevDt: # Dates must be ordered
                raise TuringError("Dates are not monotonic")

            prevDt = dt

        #######################################################################

        return self._adjustedDates

##############################################################################

    def __repr__(self):
        ''' Print out the details of the schedule and the actual dates. This
        can be used for providing transparency on schedule calculations. '''

        s = to_string("OBJECT TYPE", type(self).__name__)
        s += to_string("EFFECTIVE DATE", self._effectiveDate)
        s += to_string("END DATE", self._terminationDate)
        s += to_string("FREQUENCY", self._freqType)
        s += to_string("CALENDAR", self._calendarType)
        s += to_string("BUSDAYRULE", self._busDayAdjustType)
        s += to_string("DATEGENRULE", self._dateGenRuleType)
        s += to_string("ADJUST TERM DATE", self._adjustTerminationDate)
        s += to_string("END OF MONTH", self._endOfMonthFlag, "")

        if 1==0:
            if len(self._adjustedDates) > 0:
                s += "\n\n"
                s += to_string("EFF", self._adjustedDates[0], "")

            if len(self._adjustedDates) > 1:
                s += "\n"
                s += to_string("FLW", self._adjustedDates[1:], "",
                               listFormat=True)

        return s

###############################################################################

    def _print(self):
        ''' Print out the details of the schedule and the actual dates. This
        can be used for providing transparency on schedule calculations. '''
        print(self)

###############################################################################
