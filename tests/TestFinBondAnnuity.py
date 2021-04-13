###############################################################################
# Copyright (C) 2018, 2019, 2020 Dominic O'Kane
###############################################################################

# TODO Set up test cases correctly

import sys
sys.path.append("..")

from financepy.finutils.turing_calendar import TuringDateGenRuleTypes
from financepy.finutils.turing_calendar import TuringBusDayAdjustTypes
from financepy.finutils.turing_day_count import TuringDayCountTypes
from financepy.finutils.turing_calendar import TuringCalendarTypes
from financepy.finutils.turing_frequency import TuringFrequencyTypes
from financepy.finutils.turing_date import TuringDate, setDateFormatType, TuringDateFormatTypes
from financepy.products.bonds.turing_bond_annuity import TuringBondAnnuity

from TuringTestCases import TuringTestCases, globalTestCaseMode
testCases = TuringTestCases(__file__, globalTestCaseMode)

###############################################################################


def test_FinBondAnnuity():

    settlementDate = TuringDate(20, 6, 2018)

    #   print("==============================================================")
    #   print("SEMI-ANNUAL FREQUENCY")
    #   print("==============================================================")

    maturityDate = TuringDate(20, 6, 2019)
    coupon = 0.05
    freqType = TuringFrequencyTypes.SEMI_ANNUAL
    calendarType = TuringCalendarTypes.WEEKEND
    busDayAdjustType = TuringBusDayAdjustTypes.FOLLOWING
    dateGenRuleType = TuringDateGenRuleTypes.BACKWARD
    basisType = TuringDayCountTypes.ACT_360
    face = 1000000

    annuity = TuringBondAnnuity(
        maturityDate,
        coupon,
        freqType,
        calendarType,
        busDayAdjustType,
        dateGenRuleType,
        basisType,
        face)

    annuity.calculateFlowDatesPayments(settlementDate)

    testCases.header("Date", "Flow")
    numFlows = len(annuity._flowDates)
    for i in range(1, numFlows):
        dt = annuity._flowDates[i]
        flow = annuity._flowAmounts[i]
        testCases.print(dt, flow)

#    print("===============================================================")
#    print("QUARTERLY FREQUENCY")
#    print("===============================================================")

    maturityDate = TuringDate(20, 6, 2028)
    coupon = 0.05
    freqType = TuringFrequencyTypes.SEMI_ANNUAL
    calendarType = TuringCalendarTypes.WEEKEND
    busDayAdjustType = TuringBusDayAdjustTypes.FOLLOWING
    dateGenRuleType = TuringDateGenRuleTypes.BACKWARD
    basisType = TuringDayCountTypes.ACT_360

    annuity = TuringBondAnnuity(
        maturityDate,
        coupon,
        freqType,
        calendarType,
        busDayAdjustType,
        dateGenRuleType,
        basisType,
        face)

    annuity.calculateFlowDatesPayments(settlementDate)

    testCases.header("Date", "Flow")
    numFlows = len(annuity._flowDates)
    for i in range(1, numFlows):
        dt = annuity._flowDates[i]
        flow = annuity._flowAmounts[i]
        testCases.print(dt, flow)

#    print("==================================================================")
#    print("MONTHLY FREQUENCY")
#    print("==================================================================")

    maturityDate = TuringDate(20, 6, 2028)
    coupon = 0.05
    freqType = TuringFrequencyTypes.MONTHLY
    calendarType = TuringCalendarTypes.WEEKEND
    busDayAdjustType = TuringBusDayAdjustTypes.FOLLOWING
    dateGenRuleType = TuringDateGenRuleTypes.BACKWARD
    basisType = TuringDayCountTypes.ACT_360

    annuity = TuringBondAnnuity(
        maturityDate,
        coupon,
        freqType,
        calendarType,
        busDayAdjustType,
        dateGenRuleType,
        basisType,
        face)

    annuity.calculateFlowDatesPayments(settlementDate)

    testCases.header("Date", "Flow")
    numFlows = len(annuity._flowDates)
    for i in range(1, numFlows):
        dt = annuity._flowDates[i]
        flow = annuity._flowAmounts[i]
        testCases.print(dt, flow)

#    print("==================================================================")
#    print("FORWARD GEN")
#    print("==================================================================")

    maturityDate = TuringDate(20, 6, 2028)
    coupon = 0.05
    freqType = TuringFrequencyTypes.ANNUAL
    calendarType = TuringCalendarTypes.WEEKEND
    busDayAdjustType = TuringBusDayAdjustTypes.FOLLOWING
    dateGenRuleType = TuringDateGenRuleTypes.FORWARD
    basisType = TuringDayCountTypes.ACT_360

    annuity = TuringBondAnnuity(
        maturityDate,
        coupon,
        freqType,
        calendarType,
        busDayAdjustType,
        dateGenRuleType,
        basisType,
        face)

    annuity.calculateFlowDatesPayments(settlementDate)

    testCases.header("Date", "Flow")
    numFlows = len(annuity._flowDates)
    for i in range(1, numFlows):
        dt = annuity._flowDates[i]
        flow = annuity._flowAmounts[i]
        testCases.print(dt, flow)

#    print("==================================================================")
#    print("BACKWARD GEN WITH SHORT END STUB")
#    print("==================================================================")

    maturityDate = TuringDate(20, 6, 2028)
    coupon = 0.05
    freqType = TuringFrequencyTypes.ANNUAL
    calendarType = TuringCalendarTypes.WEEKEND
    busDayAdjustType = TuringBusDayAdjustTypes.FOLLOWING
    dateGenRuleType = TuringDateGenRuleTypes.FORWARD
    basisType = TuringDayCountTypes.ACT_360

    annuity = TuringBondAnnuity(
        maturityDate,
        coupon,
        freqType,
        calendarType,
        busDayAdjustType,
        dateGenRuleType,
        basisType,
        face)

    annuity.calculateFlowDatesPayments(settlementDate)

    testCases.header("Date", "Flow")
    numFlows = len(annuity._flowDates)
    for i in range(1, numFlows):
        dt = annuity._flowDates[i]
        flow = annuity._flowAmounts[i]
        testCases.print(dt, flow)

#    print("==================================================================")
#    print("FORWARD GEN WITH LONG END STUB")
#    print("==================================================================")

    maturityDate = TuringDate(20, 6, 2028)
    coupon = 0.05
    freqType = TuringFrequencyTypes.SEMI_ANNUAL
    calendarType = TuringCalendarTypes.WEEKEND
    busDayAdjustType = TuringBusDayAdjustTypes.FOLLOWING
    dateGenRuleType = TuringDateGenRuleTypes.FORWARD
    basisType = TuringDayCountTypes.ACT_360

    annuity = TuringBondAnnuity(
        maturityDate,
        coupon,
        freqType,
        calendarType,
        busDayAdjustType,
        dateGenRuleType,
        basisType,
        face)

    annuity.calculateFlowDatesPayments(settlementDate)

    testCases.header("Date", "Flow")
    numFlows = len(annuity._flowDates)
    for i in range(1, numFlows):
        dt = annuity._flowDates[i]
        flow = annuity._flowAmounts[i]
        testCases.print(dt, flow)

##########################################################################


test_FinBondAnnuity()
testCases.compareTestCases()
