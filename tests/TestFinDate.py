###############################################################################
# Copyright (C) 2018, 2019, 2020 Dominic O'Kane
###############################################################################

import numpy as np
import time

import sys
sys.path.append("..")

from financepy.turingutils.turing_date import TuringDate, dateRange
from financepy.turingutils.turing_date import TuringDateFormatTypes
from financepy.turingutils.turing_date import setDateFormatType

from TuringTestCases import TuringTestCases, globalTestCaseMode
testCases = TuringTestCases(__file__, globalTestCaseMode)

###############################################################################

setDateFormatType(TuringDateFormatTypes.UK_LONGEST)

def test_FinDate():

    startDate = TuringDate(1, 1, 2018)

    assert TuringDate(1, 1, 2018) == TuringDate.fromString('1-1-2018', '%d-%m-%Y')

    testCases.header("DATE", "MONTHS", "CDS DATE")

    for numMonths in range(0, 120):
        nextCDSDate = startDate.nextCDSDate(numMonths)
        testCases.print(str(startDate), numMonths, str(nextCDSDate))

    startDate = TuringDate(1, 1, 2018)

    testCases.header("STARTDATE", "MONTHS", "CDS DATE")

    for numMonths in range(0, 365):
        startDate = startDate.addDays(1)
        nextIMMDate = startDate.nextIMMDate()
        testCases.print(numMonths, str(startDate), str(nextIMMDate))

###############################################################################


def test_FinDateTenors():

    startDate = TuringDate(23, 2, 2018)

    testCases.header("TENOR", "DATE")
    tenor = "5d"
    testCases.print(tenor, startDate.addTenor(tenor))

    tenor = "7D"
    testCases.print(tenor, startDate.addTenor(tenor))

    tenor = "1W"
    testCases.print(tenor, startDate.addTenor(tenor))

    tenor = "4W"
    testCases.print(tenor, startDate.addTenor(tenor))

    tenor = "1M"
    testCases.print(tenor, startDate.addTenor(tenor))

    tenor = "24M"
    testCases.print(tenor, startDate.addTenor(tenor))

    tenor = "2Y"
    testCases.print(tenor, startDate.addTenor(tenor))

    tenor = "10y"
    testCases.print(tenor, startDate.addTenor(tenor))

    tenor = "0m"
    testCases.print(tenor, startDate.addTenor(tenor))

    tenor = "20Y"
    testCases.print(tenor, startDate.addTenor(tenor))

###############################################################################


def test_FinDateRange():

    startDate = TuringDate(1, 1, 2010)

    testCases.header("Tenor", "Dates")

    endDate = startDate.addDays(3)
    tenor = "Default"
    testCases.print(tenor, dateRange(startDate, endDate))

    endDate = startDate.addDays(20)
    tenor = "1W"
    testCases.print(tenor, dateRange(startDate, endDate, tenor))

    tenor = "7D"
    testCases.print(tenor, dateRange(startDate, endDate, tenor))

    testCases.header("Case", "Dates")

    case = "Same startDate"
    testCases.print(case, dateRange(startDate, startDate))
    case = "startDate before endDate"
    testCases.print(case, dateRange(endDate, startDate))

###############################################################################


def test_FinDateAddMonths():

    startDate = TuringDate(1, 1, 2010)

    testCases.header("Months", "Dates")

    months = [1, 3, 6, 9, 12, 24, 36, 48, 60]

    dates = startDate.addMonths(months)

    testCases.header("DATES", "DATE")

    for dt in dates:
        testCases.print("DATE", dt)

###############################################################################


def test_FinDateAddYears():

    startDate = TuringDate(1, 1, 2010)

    testCases.header("Years", "Dates")

    years = [1, 3, 5, 7, 10]
    dates1 = startDate.addYears(years)
    for dt in dates1:
        testCases.print("DATES1", dt)

    years = np.array([1, 3, 5, 7, 10])
    dates2 = startDate.addYears(years)
    for dt in dates2:
        testCases.print("DATES2", dt)

    years = np.array([1.5, 3.25, 5.75, 7.25, 10.0])
    dates3 = startDate.addYears(years)

    for dt in dates3:
        testCases.print("DATES3", dt)

    dt = 1.0/365.0
    years = np.array([1.5+2.0*dt, 3.5-6*dt, 5.75+3*dt, 7.25+dt, 10.0+dt])
    dates4 = startDate.addYears(years)

    for dt in dates4:
        testCases.print("DATES4", dt)

###############################################################################


def test_FinDateSpeed():

    numSteps = 100
    start = time.time()
    dateList = []
    for _ in range(0, numSteps):
        startDate = TuringDate(1, 1, 2010)
        dateList.append(startDate)
    end = time.time()
    elapsed = end - start

    testCases.header("LABEL", "TIME")
    testCases.print("TIMING", elapsed)

    mem = sys.getsizeof(dateList)
    testCases.print("Mem:", mem)


###############################################################################


def test_FinDateFormat():

    dt = TuringDate(20, 10, 2019)
    testCases.header("FORMAT", "DATE")

    for formatType in TuringDateFormatTypes:
        setDateFormatType(formatType) 
        testCases.print(formatType.name, dt)

###############################################################################


def test_IntraDay():

    testCases.header("Date1", "Date2", "Diff")
    d1 = TuringDate(20, 10, 2019, 0, 0, 0)
    d2 = TuringDate(25, 10, 2019, 0, 0, 0)
    diff = d2 - d1
    testCases.print(d1, d2, diff)
    testCases.print(d1._excelDate, d2._excelDate, diff)

    ###########################################################################

    d1 = TuringDate(20, 10, 2019, 10, 0, 0)
    d2 = TuringDate(25, 10, 2019, 10, 25, 0)
    diff = d2 - d1
    testCases.print(d1, d2, diff)
    testCases.print(d1._excelDate, d2._excelDate, diff)

    ###########################################################################

    d1 = TuringDate(20, 10, 2019, 10, 0, 0)
    d2 = TuringDate(20, 10, 2019, 10, 25, 30)
    diff = d2 - d1
    testCases.print(d1, d2, diff)
    testCases.print(d1._excelDate, d2._excelDate, diff)

    ###########################################################################

    d1 = TuringDate(19, 10, 2019, 10, 0, 0)
    d2 = TuringDate(20, 10, 2019, 10, 25, 40)
    diff = d2 - d1
    testCases.print(d1, d2, diff)
    testCases.print(d1._excelDate, d2._excelDate, diff)

###############################################################################

def test_FinDateEOM():

    dt = TuringDate(29, 2, 2000)
    assert(dt.isEOM() == True)

    dt = TuringDate(28, 2, 2001)
    assert(dt.isEOM() == True)

    dt = TuringDate(29, 2, 2004)
    assert(dt.isEOM() == True)

    dt = TuringDate(28, 2, 2005)
    assert(dt.isEOM() == True)

    dt = TuringDate(31, 3, 2003)
    assert(dt.isEOM() == True)

    dt = TuringDate(30, 4, 2004)
    assert(dt.isEOM() == True)

    dt = TuringDate(31, 5, 2004)
    assert(dt.isEOM() == True)

    dt = TuringDate(31, 12, 2010)
    assert(dt.isEOM() == True)

    dt = TuringDate(2, 2, 2000)
    assert(dt.EOM().isEOM() == True)

    dt = TuringDate(24, 2, 2001)
    assert(dt.EOM().isEOM() == True)

    dt = TuringDate(22, 2, 2004)
    assert(dt.EOM().isEOM() == True)

    dt = TuringDate(1, 2, 2005)
    assert(dt.EOM().isEOM() == True)

    dt = TuringDate(1, 3, 2003)
    assert(dt.EOM().isEOM() == True)

    dt = TuringDate(3, 4, 2004)
    assert(dt.EOM().isEOM() == True)

    dt = TuringDate(5, 5, 2004)
    assert(dt.EOM().isEOM() == True)

    dt = TuringDate(7, 12, 2010)
    assert(dt.EOM().isEOM() == True)

###############################################################################
    
start = time.time()

test_FinDate()
test_FinDateTenors()
test_FinDateRange()
test_FinDateAddMonths()
test_FinDateAddYears()
test_FinDateSpeed()
test_FinDateFormat()
test_IntraDay()
test_FinDateEOM()

end = time.time()
elapsed = end - start
# print("Elapsed time:", elapsed)

testCases.compareTestCases()

setDateFormatType(TuringDateFormatTypes.UK_LONG)
