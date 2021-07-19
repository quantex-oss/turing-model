from turing_models.utilities.error import TuringError
from turing_models.utilities.turing_date import TuringDate
from turing_models.utilities.day_count import TuringDayCountTypes
from turing_models.utilities.frequency import TuringFrequencyTypes
from turing_models.utilities.calendar import TuringCalendarTypes, TuringDateGenRuleTypes
from turing_models.utilities.calendar import TuringCalendar, TuringBusDayAdjustTypes
from turing_models.utilities.helper_functions import checkArgumentTypes, label_to_string
from turing_models.utilities.mathematics import ONE_MILLION
from turing_models.utilities.global_types import TuringSwapTypes
from fundamental.market.curves.discount_curve import TuringDiscountCurve

from .float_leg import TuringFloatLeg

###############################################################################


class TuringIborOIS(object):
    ''' Class for managing an Ibor-OIS basis swap contract. This is a
    contract in which a floating leg with one LIBOR tenor is exchanged for a 
    floating leg payment of an overnight index swap. There is no exchange of
    par. The contract is entered into at zero initial cost. The contract lasts
    from a start date to a specified maturity date.
    
    The value of the contract is the NPV of the two coupon streams. Discounting
    is done on a supplied discount curve which is separate from the curves from
    which the implied index rates are extracted. '''
    
    def __init__(self,
                 effectiveDate: TuringDate,  # Date interest starts to accrue
                 terminationDateOrTenor: (TuringDate, str),  # Date contract ends
                 iborType: TuringSwapTypes,
                 iborFreqType: TuringFrequencyTypes = TuringFrequencyTypes.QUARTERLY,
                 iborDayCountType: TuringDayCountTypes  = TuringDayCountTypes.THIRTY_E_360,
                 iborSpread: float = 0.0,
                 oisFreqType: TuringFrequencyTypes = TuringFrequencyTypes.QUARTERLY,
                 oisDayCountType: TuringDayCountTypes = TuringDayCountTypes.THIRTY_E_360,
                 oisSpread: float = 0.0,
                 oisPaymentLag: int = 0,
                 notional: float = ONE_MILLION,
                 calendarType: TuringCalendarTypes = TuringCalendarTypes.WEEKEND,
                 busDayAdjustType: TuringBusDayAdjustTypes = TuringBusDayAdjustTypes.FOLLOWING,
                 dateGenRuleType: TuringDateGenRuleTypes = TuringDateGenRuleTypes.BACKWARD):
        ''' Create a Ibor basis swap contract giving the contract start
        date, its maturity, frequency and day counts on the two floating 
        legs and notional. The floating leg parameters have default
        values that can be overwritten if needed. The start date is contractual
        and is the same as the settlement date for a new swap. It is the date
        on which interest starts to accrue. The end of the contract is the
        termination date. This is not adjusted for business days. The adjusted
        termination date is called the maturity date. This is calculated. '''

        checkArgumentTypes(self.__init__, locals())

        if type(terminationDateOrTenor) == TuringDate:
            self._terminationDate = terminationDateOrTenor
        else:
            self._terminationDate = effectiveDate.addTenor(terminationDateOrTenor)

        calendar = TuringCalendar(calendarType)
        self._maturityDate = calendar.adjust(self._terminationDate,
                                             busDayAdjustType)

        if effectiveDate > self._maturityDate:
            raise TuringError("Start date after maturity date")

        oisType = TuringSwapTypes.PAY
        if iborType == TuringSwapTypes.PAY:
            oisType = TuringSwapTypes.RECEIVE
        
        principal = 0.0

        self._floatIborLeg = TuringFloatLeg(effectiveDate,
                                            self._terminationDate,
                                            iborType,
                                            iborSpread,
                                            iborFreqType,
                                            iborDayCountType,
                                            notional,
                                            principal,
                                            0,
                                            calendarType,
                                            busDayAdjustType,
                                            dateGenRuleType)

        self._floatOISLeg = TuringFloatLeg(effectiveDate,
                                           self._terminationDate,
                                           oisType,
                                           oisSpread,
                                           oisFreqType,
                                           oisDayCountType,
                                           notional,
                                           principal,
                                           oisPaymentLag,
                                           calendarType,
                                           busDayAdjustType,
                                           dateGenRuleType)

###############################################################################

    def value(self,
              valuationDate: TuringDate,
              discountCurve: TuringDiscountCurve,
              indexIborCurve: TuringDiscountCurve = None,
              indexOISCurve: TuringDiscountCurve = None,
              firstFixingRateLeg1=None,
              firstFixingRateLeg2=None):
        ''' Value the interest rate swap on a value date given a single Ibor
        discount curve and an index curve for the Ibors on each swap leg. '''

        if indexIborCurve is None:
            indexIborCurve = discountCurve

        if indexOISCurve is None:
            indexOISCurve = discountCurve

        floatIborLegValue = self._floatIborLeg.value(valuationDate,
                                                     discountCurve, 
                                                     indexIborCurve, 
                                                     firstFixingRateLeg1)

        floatOISLegValue = self._floatOISLeg.value(valuationDate,
                                                   discountCurve,
                                                   indexOISCurve,
                                                   firstFixingRateLeg2)

        value = floatIborLegValue + floatOISLegValue
        return value

###############################################################################

    def printFlows(self):
        ''' Prints the fixed leg amounts without any valuation details. Shows
        the dates and sizes of the promised fixed leg flows. '''

        self._floatIborLeg.printPayments()
        self._floatOISLeg.printPayments()

##########################################################################

    def __repr__(self):
        s = label_to_string("OBJECT TYPE", type(self).__name__)
        s += self._floatIborLeg.__repr__()
        s += "\n"
        s += self._floatOISLeg.__repr__()
        return s

###############################################################################

    def _print(self):
        ''' Print a list of the unadjusted coupon payment dates used in
        analytic calculations for the bond. '''
        print(self)

###############################################################################
