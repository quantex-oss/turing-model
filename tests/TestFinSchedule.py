###############################################################################
# Copyright (C) 2018, 2019, 2020 Dominic O'Kane
###############################################################################

import sys
sys.path.append("..")

from financepy.turingutils.turing_calendar import TuringBusDayAdjustTypes
from financepy.turingutils.turing_calendar import TuringDateGenRuleTypes
from financepy.turingutils.turing_schedule import TuringSchedule
from financepy.turingutils.turing_frequency import TuringFrequencyTypes
from financepy.turingutils.turing_calendar import TuringCalendarTypes, TuringCalendar
from financepy.turingutils.turing_date import TuringDate, setDateFormatType, TuringDateFormatTypes

from TuringTestCases import TuringTestCases, globalTestCaseMode
testCases = TuringTestCases(__file__, globalTestCaseMode)

###############################################################################

setDateFormatType(TuringDateFormatTypes.UK_LONGEST)

def dumpSchedule(desc, schedule):

    testCases.banner("=======================================================")
    testCases.banner(desc)
    testCases.banner("=======================================================")
    testCases.header("OBJ")
    testCases.print(schedule)

    testCases.header("NUM", "TYPE", "DATE", "YEAR", "DIFF")

    numFlows = len(schedule._adjustedDates)
    effDate = schedule._adjustedDates[0]
    years = 0.0
    diff = 0.0
    testCases.print(0, "EFCT DATE", str(effDate), years, diff)
    
    prevDate = schedule._adjustedDates[0]
    for iFlow in range(1, numFlows-1):
        adjustedDate = schedule._adjustedDates[iFlow]
        years = (adjustedDate - effDate) / 365.0
        diff = (adjustedDate - prevDate) / 365.0
        testCases.print(iFlow, "FLOW DATE", str(adjustedDate), years, diff)
        prevDate = adjustedDate

    termDate = schedule._adjustedDates[-1]
    years = (termDate - effDate) / 365.0
    diff = (termDate - prevDate) / 365.0

    testCases.print(numFlows-1, "TERM DATE", str(termDate), years, diff)

############################################################################### 
   
def test_FinSchedule():

    ###########################################################################
    # BACKWARD SCHEDULES TESTING DIFFERENT FREQUENCIES
    ###########################################################################
    
    d1 = TuringDate(20, 6, 2018)
    d2 = TuringDate(20, 6, 2020)
    freqType = TuringFrequencyTypes.SEMI_ANNUAL
    calendarType = TuringCalendarTypes.WEEKEND
    busDayAdjustType = TuringBusDayAdjustTypes.FOLLOWING
    dateGenRuleType = TuringDateGenRuleTypes.BACKWARD
    terminationDateAdjust = True

    schedule = TuringSchedule(d1,
                              d2,
                              freqType,
                              calendarType,
                              busDayAdjustType,
                              dateGenRuleType,
                              terminationDateAdjust)

    dumpSchedule("BACKWARD SEMI-ANNUAL FREQUENCY", schedule)

    d1 = TuringDate(20, 6, 2018)
    d2 = TuringDate(20, 6, 2020)
    freqType = TuringFrequencyTypes.QUARTERLY
    calendarType = TuringCalendarTypes.WEEKEND
    busDayAdjustType = TuringBusDayAdjustTypes.FOLLOWING
    dateGenRuleType = TuringDateGenRuleTypes.BACKWARD

    schedule = TuringSchedule(d1,
                              d2,
                              freqType,
                              calendarType,
                              busDayAdjustType,
                              dateGenRuleType,
                              terminationDateAdjust)

    dumpSchedule("BACKWARD QUARTERLY FREQUENCY", schedule)

    d1 = TuringDate(20, 6, 2018)
    d2 = TuringDate(20, 6, 2020)
    freqType = TuringFrequencyTypes.MONTHLY
    calendarType = TuringCalendarTypes.WEEKEND
    busDayAdjustType = TuringBusDayAdjustTypes.FOLLOWING
    dateGenRuleType = TuringDateGenRuleTypes.BACKWARD

    schedule = TuringSchedule(d1,
                              d2,
                              freqType,
                              calendarType,
                              busDayAdjustType,
                              dateGenRuleType,
                              terminationDateAdjust)

    dumpSchedule("BACKWARD MONTHLY FREQUENCY", schedule)

    ###########################################################################
    # FORWARD SCHEDULES TESTING DIFFERENT FREQUENCIES
    ###########################################################################

    d1 = TuringDate(20, 6, 2018)
    d2 = TuringDate(20, 6, 2020)
    freqType = TuringFrequencyTypes.ANNUAL
    calendarType = TuringCalendarTypes.WEEKEND
    busDayAdjustType = TuringBusDayAdjustTypes.FOLLOWING
    dateGenRuleType = TuringDateGenRuleTypes.FORWARD

    schedule = TuringSchedule(d1,
                              d2,
                              freqType,
                              calendarType,
                              busDayAdjustType,
                              dateGenRuleType,
                              terminationDateAdjust)
    
    dumpSchedule("FORWARD ANNUAL", schedule)

    d1 = TuringDate(20, 6, 2018)
    d2 = TuringDate(20, 6, 2020)
    freqType = TuringFrequencyTypes.SEMI_ANNUAL
    calendarType = TuringCalendarTypes.WEEKEND
    busDayAdjustType = TuringBusDayAdjustTypes.FOLLOWING
    dateGenRuleType = TuringDateGenRuleTypes.BACKWARD

    schedule = TuringSchedule(d1,
                              d2,
                              freqType,
                              calendarType,
                              busDayAdjustType,
                              dateGenRuleType)
    
    dumpSchedule("FORWARD SEMI-ANNUAL", schedule)

    d1 = TuringDate(20, 6, 2018)
    d2 = TuringDate(20, 6, 2020)
    freqType = TuringFrequencyTypes.MONTHLY
    calendarType = TuringCalendarTypes.WEEKEND
    busDayAdjustType = TuringBusDayAdjustTypes.FOLLOWING
    dateGenRuleType = TuringDateGenRuleTypes.BACKWARD

    schedule = TuringSchedule(d1,
                              d2,
                              freqType,
                              calendarType,
                              busDayAdjustType,
                              dateGenRuleType,
                              terminationDateAdjust)
    
    dumpSchedule("FORWARD MONTHLY", schedule)

    ###########################################################################
    # BACKWARD SHORT STUB AT FRONT
    ###########################################################################

    d1 = TuringDate(20, 8, 2018)
    d2 = TuringDate(20, 6, 2020)
    freqType = TuringFrequencyTypes.QUARTERLY
    calendarType = TuringCalendarTypes.WEEKEND
    busDayAdjustType = TuringBusDayAdjustTypes.FOLLOWING
    dateGenRuleType = TuringDateGenRuleTypes.BACKWARD

    schedule = TuringSchedule(d1,
                              d2,
                              freqType,
                              calendarType,
                              busDayAdjustType,
                              dateGenRuleType,
                              terminationDateAdjust)
    dumpSchedule("BACKWARD GEN WITH SHORT END STUB", schedule)

    ###########################################################################
    # BACKWARD SUPER SHORT STUB AT FRONT
    ###########################################################################

    d1 = TuringDate(19, 9, 2018)
    d2 = TuringDate(20, 6, 2020)
    freqType = TuringFrequencyTypes.QUARTERLY
    calendarType = TuringCalendarTypes.WEEKEND
    busDayAdjustType = TuringBusDayAdjustTypes.FOLLOWING
    dateGenRuleType = TuringDateGenRuleTypes.BACKWARD

    schedule = TuringSchedule(d1,
                              d2,
                              freqType,
                              calendarType,
                              busDayAdjustType,
                              dateGenRuleType,
                              terminationDateAdjust)

    dumpSchedule("BACKWARD GEN WITH VERY SHORT END STUB", schedule)

    ###########################################################################
    # FORWARD SHORT STUB AT END
    ###########################################################################

    d1 = TuringDate(20, 8, 2018)
    d2 = TuringDate(20, 6, 2020)
    freqType = TuringFrequencyTypes.SEMI_ANNUAL
    calendarType = TuringCalendarTypes.WEEKEND
    busDayAdjustType = TuringBusDayAdjustTypes.FOLLOWING
    dateGenRuleType = TuringDateGenRuleTypes.FORWARD

    schedule = TuringSchedule(d1,
                              d2,
                              freqType,
                              calendarType,
                              busDayAdjustType,
                              dateGenRuleType,
                              terminationDateAdjust)

    dumpSchedule("FORWARD GEN WITH END STUB", schedule)

    d1 = TuringDate(19, 9, 2018)
    d2 = TuringDate(20, 6, 2020)
    freqType = TuringFrequencyTypes.QUARTERLY
    calendarType = TuringCalendarTypes.TARGET
    busDayAdjustType = TuringBusDayAdjustTypes.FOLLOWING
    dateGenRuleType = TuringDateGenRuleTypes.FORWARD

    schedule = TuringSchedule(d1,
                              d2,
                              freqType,
                              calendarType,
                              busDayAdjustType,
                              dateGenRuleType)

    dumpSchedule("FORWARD GEN WITH VERY SHORT END STUB", schedule)

    d1 = TuringDate(20, 6, 2018)
    d2 = TuringDate(20, 6, 2020)
    freqType = TuringFrequencyTypes.SEMI_ANNUAL
    calendarType = TuringCalendarTypes.WEEKEND
    busDayAdjustType = TuringBusDayAdjustTypes.FOLLOWING
    dateGenRuleType = TuringDateGenRuleTypes.BACKWARD
    terminationDateAdjust = True
    
    schedule = TuringSchedule(d1,
                              d2,
                              freqType,
                              calendarType,
                              busDayAdjustType,
                              dateGenRuleType,
                              terminationDateAdjust)

    dumpSchedule("TERMINATION DATE ADJUSTED", schedule)

    d1 = TuringDate(20, 6, 2018)
    d2 = TuringDate(20, 6, 2020)
    freqType = TuringFrequencyTypes.SEMI_ANNUAL
    calendarType = TuringCalendarTypes.WEEKEND
    busDayAdjustType = TuringBusDayAdjustTypes.MODIFIED_FOLLOWING
    dateGenRuleType = TuringDateGenRuleTypes.BACKWARD
    terminationDateAdjust = True
    eomFlag = True

    schedule = TuringSchedule(d1,
                              d2,
                              freqType,
                              calendarType,
                              busDayAdjustType,
                              dateGenRuleType,
                              terminationDateAdjust,
                              eomFlag)

    dumpSchedule("END OF MONTH - NOT EOM TERM DATE - USING MOD FOLL", schedule)

    d1 = TuringDate(30, 6, 2018)
    d2 = TuringDate(30, 6, 2020)
    freqType = TuringFrequencyTypes.SEMI_ANNUAL
    calendarType = TuringCalendarTypes.WEEKEND
    busDayAdjustType = TuringBusDayAdjustTypes.MODIFIED_FOLLOWING
    dateGenRuleType = TuringDateGenRuleTypes.BACKWARD
    terminationDateAdjust = True
    eomFlag = True

    schedule = TuringSchedule(d1,
                              d2,
                              freqType,
                              calendarType,
                              busDayAdjustType,
                              dateGenRuleType,
                              terminationDateAdjust,
                              eomFlag)

    dumpSchedule("END OF MONTH - EOM TERM DATE - USING MOD FOLL", schedule)
    
###############################################################################

def test_FinScheduleAlignment(eomFlag):
        
    valuationDate = TuringDate(29, 3, 2005)
    effDate = valuationDate.addTenor("2d")
    freqType = TuringFrequencyTypes.SEMI_ANNUAL
    busDayAdjustType = TuringBusDayAdjustTypes.MODIFIED_FOLLOWING
    dateGenRuleType = TuringDateGenRuleTypes.BACKWARD
    calendarType = TuringCalendarTypes.UNITED_STATES
    adjustTerminationDate = False

    matDate1 = effDate.addTenor("4Y")
    matDate2 = effDate.addTenor("50Y")

#    print(matDate1)
#    print(matDate2)

    myCal = TuringCalendar(calendarType)

    adjustedMatDate1 = myCal.adjust(matDate1, busDayAdjustType)
    adjustedMatDate2 = myCal.adjust(matDate2, busDayAdjustType)

#    print(adjustedMatDate1)
#    print(adjustedMatDate2)
    
    sched1 = TuringSchedule(effDate,
                            adjustedMatDate1,
                            freqType,
                            calendarType,
                            busDayAdjustType,
                            dateGenRuleType,
                            adjustTerminationDate,
                            eomFlag)
    
#    print(sched1)
    
    sched2 = TuringSchedule(effDate,
                            adjustedMatDate2,
                            freqType,
                            calendarType,
                            busDayAdjustType,
                            dateGenRuleType,
                            adjustTerminationDate,
                            eomFlag)

    compare = (sched1._adjustedDates[-1] == sched2._adjustedDates[len(sched1._adjustedDates)-1])
    assert(compare == eomFlag)

###############################################################################

def test_FinScheduleAlignmentLeapYearEOM():
    ''' Effective date on leap year.'''
    
    valuationDate = TuringDate(26, 2, 2006)
    effDate = valuationDate.addTenor("2D")
    freqType = TuringFrequencyTypes.SEMI_ANNUAL
    busDayAdjustType = TuringBusDayAdjustTypes.MODIFIED_FOLLOWING
    dateGenRuleType = TuringDateGenRuleTypes.BACKWARD
    calendarType = TuringCalendarTypes.UNITED_STATES
    adjustTerminationDate = True

    matDate1 = effDate.addTenor("4Y")
    matDate2 = effDate.addTenor("50Y")
    eomFlag = True
    
    sched1 = TuringSchedule(effDate,
                            matDate1,
                            freqType,
                            calendarType,
                            busDayAdjustType,
                            dateGenRuleType,
                            adjustTerminationDate,
                            eomFlag)
        
    sched2 = TuringSchedule(effDate,
                            matDate2,
                            freqType,
                            calendarType,
                            busDayAdjustType,
                            dateGenRuleType,
                            adjustTerminationDate,
                            eomFlag)

#    print(sched1._adjustedDates)
#    print(sched2._adjustedDates[:len(sched1._adjustedDates)])

    compare = (sched1._adjustedDates[-1] == sched2._adjustedDates[len(sched1._adjustedDates)-1])
    assert(compare == eomFlag)

###############################################################################

def test_FinScheduleAlignmentLeapYearNotEOM():
    ''' Effective date on leap year. Not EOM. '''
    
    eomFlag = False

    valuationDate = TuringDate(26, 2, 2006)
    effDate = valuationDate.addTenor("2D")
    freqType = TuringFrequencyTypes.SEMI_ANNUAL
    busDayAdjustType = TuringBusDayAdjustTypes.MODIFIED_FOLLOWING
    dateGenRuleType = TuringDateGenRuleTypes.BACKWARD
    calendarType = TuringCalendarTypes.UNITED_STATES
    adjustTerminationDate = True

    matDate1 = effDate.addTenor("4Y")
    matDate2 = effDate.addTenor("50Y")

#    print(matDate1, matDate2) 

    sched1 = TuringSchedule(effDate,
                            matDate1,
                            freqType,
                            calendarType,
                            busDayAdjustType,
                            dateGenRuleType,
                            adjustTerminationDate,
                            eomFlag)
        
    sched2 = TuringSchedule(effDate,
                            matDate2,
                            freqType,
                            calendarType,
                            busDayAdjustType,
                            dateGenRuleType,
                            adjustTerminationDate,
                            eomFlag)

#    print(sched1._adjustedDates)
#    print(sched2._adjustedDates[:len(sched1._adjustedDates)])

    compare = (sched1._adjustedDates[-1] == sched2._adjustedDates[len(sched1._adjustedDates)-1])
    assert(compare == True)

###############################################################################

def test_FinScheduleAlignmentEff31():
    ''' EOM schedule so all unadjusted dates fall on month end.'''
    
    eomFlag = True
    valuationDate = TuringDate(29, 7, 2006)
    effDate = valuationDate.addTenor("2D")
    freqType = TuringFrequencyTypes.SEMI_ANNUAL
    busDayAdjustType = TuringBusDayAdjustTypes.MODIFIED_FOLLOWING
    dateGenRuleType = TuringDateGenRuleTypes.BACKWARD
    calendarType = TuringCalendarTypes.UNITED_STATES
    adjustTerminationDate = True

    matDate1 = effDate.addTenor("4Y")
    matDate2 = effDate.addTenor("50Y")
    
#    print(matDate1, matDate2)

    sched1 = TuringSchedule(effDate,
                            matDate1,
                            freqType,
                            calendarType,
                            busDayAdjustType,
                            dateGenRuleType,
                            adjustTerminationDate,
                            eomFlag)
        
    sched2 = TuringSchedule(effDate,
                            matDate2,
                            freqType,
                            calendarType,
                            busDayAdjustType,
                            dateGenRuleType,
                            adjustTerminationDate,
                            eomFlag)

#    print(sched1._adjustedDates)
#    print(sched2._adjustedDates[:len(sched1._adjustedDates)])

    compare = (sched1._adjustedDates[-1] == sched2._adjustedDates[len(sched1._adjustedDates)-1])
    assert(compare == True)

###############################################################################

test_FinSchedule()
test_FinScheduleAlignment(True)
test_FinScheduleAlignment(False)

test_FinScheduleAlignmentLeapYearEOM()
test_FinScheduleAlignmentLeapYearNotEOM()

test_FinScheduleAlignmentEff31()

testCases.compareTestCases()

setDateFormatType(TuringDateFormatTypes.UK_LONGEST)
