##############################################################################
# Copyright (C) 2018, 2019, 2020 Dominic O'Kane
##############################################################################


from financepy.turingutils.turing_error import TuringError
from financepy.turingutils.turing_frequency import TuringFrequency, TuringFrequencyTypes
from financepy.turingutils.turing_calendar import TuringCalendarTypes
from financepy.turingutils.turing_schedule import TuringSchedule
from financepy.turingutils.turing_calendar import TuringBusDayAdjustTypes
from financepy.turingutils.turing_calendar import TuringDateGenRuleTypes
from financepy.turingutils.turing_day_count import TuringDayCountTypes
from financepy.turingutils.turing_date import TuringDate
from financepy.turingutils.turing_helper_functions import labelToString, checkArgumentTypes

###############################################################################

from enum import Enum


class TuringBondMortgageTypes(Enum):
    REPAYMENT = 1
    INTEREST_ONLY = 2

###############################################################################


class TuringBondMortgage(object):
    ''' A mortgage is a vector of dates and flows generated in order to repay
    a fixed amount given a known interest rate. Payments are all the same
    amount but with a varying mixture of interest and repayment of principal.
    '''

    def __init__(self,
                 startDate: TuringDate,
                 endDate: TuringDate,
                 principal: float,
                 freqType: TuringFrequencyTypes = TuringFrequencyTypes.MONTHLY,
                 calendarType: TuringCalendarTypes = TuringCalendarTypes.WEEKEND,
                 busDayAdjustType: TuringBusDayAdjustTypes = TuringBusDayAdjustTypes.FOLLOWING,
                 dateGenRuleType: TuringDateGenRuleTypes = TuringDateGenRuleTypes.BACKWARD,
                 dayCountConventionType: TuringDayCountTypes = TuringDayCountTypes.ACT_360):
        ''' Create the mortgage using start and end dates and principal. '''

        checkArgumentTypes(self.__init__, locals())

        if startDate > endDate:
            raise TuringError("Start Date after End Date")

        self._startDate = startDate
        self._endDate = endDate
        self._principal = principal
        self._freqType = freqType
        self._calendarType = calendarType
        self._busDayAdjustType = busDayAdjustType
        self._dateGenRuleType = dateGenRuleType
        self._dayCountConventionType = dayCountConventionType

        self._schedule = TuringSchedule(startDate,
                                        endDate,
                                        self._freqType,
                                        self._calendarType,
                                        self._busDayAdjustType,
                                        self._dateGenRuleType)

###############################################################################

    def repaymentAmount(self,
                        zeroRate: float):
        ''' Determine monthly repayment amount based on current zero rate. '''

        frequency = TuringFrequency(self._freqType)

        numFlows = len(self._schedule._adjustedDates)
        p = (1.0 + zeroRate/frequency) ** (numFlows-1)
        m = zeroRate * p / (p - 1.0) / frequency
        m = m * self._principal
        return m

###############################################################################

    def generateFlows(self,
                      zeroRate: float,
                      mortgageType: TuringBondMortgageTypes):
        ''' Generate the bond flow amounts. '''

        self._mortgageType = mortgageType
        self._interestFlows = [0]
        self._principalFlows = [0]
        self._principalRemaining = [self._principal]
        self._totalFlows = [0]

        numFlows = len(self._schedule._adjustedDates)
        principal = self._principal
        frequency = TuringFrequency(self._freqType)

        if mortgageType == TuringBondMortgageTypes.REPAYMENT:
            monthlyFlow = self.repaymentAmount(zeroRate)
        elif mortgageType == TuringBondMortgageTypes.INTEREST_ONLY:
            monthlyFlow = zeroRate * self._principal / frequency
        else:
            raise TuringError("Unknown Mortgage type.")

        for i in range(1, numFlows):
            interestFlow = principal * zeroRate / frequency
            principalFlow = monthlyFlow - interestFlow
            principal = principal - principalFlow
            self._interestFlows.append(interestFlow)
            self._principalFlows.append(principalFlow)
            self._principalRemaining.append(principal)
            self._totalFlows.append(monthlyFlow)

###############################################################################

    def printLeg(self):
        print("START DATE:", self._startDate)
        print("MATURITY DATE:", self._endDate)
        print("MORTGAGE TYPE:", self._mortgageType)
        print("FREQUENCY:", self._freqType)
        print("CALENDAR:", self._calendarType)
        print("BUSDAYRULE:", self._busDayAdjustType)
        print("DATEGENRULE:", self._dateGenRuleType)

        numFlows = len(self._schedule._adjustedDates)

        print("%15s %12s %12s %12s %12s" %
              ("PAYMENT DATE", "INTEREST", "PRINCIPAL",
               "OUTSTANDING", "TOTAL"))

        print("")
        for i in range(0, numFlows):
            print("%15s %12.2f %12.2f %12.2f %12.2f" %
                  (self._schedule._adjustedDates[i],
                   self._interestFlows[i],
                   self._principalFlows[i],
                   self._principalRemaining[i],
                   self._totalFlows[i]))

###############################################################################

    def __repr__(self):
        s = labelToString("OBJECT TYPE", type(self).__name__)
        s += labelToString("START DATE", self._startDate)
        s += labelToString("MATURITY DATE", self._endDate)
        s += labelToString("MORTGAGE TYPE", self._mortgageType)
        s += labelToString("FREQUENCY", self._freqType)
        s += labelToString("CALENDAR", self._calendarType)
        s += labelToString("BUSDAYRULE", self._busDayAdjustType)
        s += labelToString("DATEGENRULE", self._dateGenRuleType)
        return s

###############################################################################

    def _print(self):
        ''' Simple print function for backward compatibility. '''
        print(self)

###############################################################################
