##############################################################################
# Copyright (C) 2018, 2019, 2020 Dominic O'Kane
##############################################################################

##########################################################################
# THIS IS UNFINISHED
##########################################################################

from enum import Enum

from financepy.finutils.turing_day_count import TuringDayCount, TuringDayCountTypes
from financepy.finutils.turing_frequency import TuringFrequencyTypes
from financepy.finutils.turing_calendar import TuringCalendarTypes,  TuringDateGenRuleTypes
from financepy.finutils.turing_calendar import TuringBusDayAdjustTypes

##########################################################################


class FinIborConventions():

    def __init__(self,
                 currencyName: str,
                 indexName: str = "LIBOR"):

        if currencyName == "USD" and indexName == "LIBOR":
            self._spotLag = 2
            self._dayCountType=TuringDayCountTypes.THIRTY_E_360_ISDA
            self._calendarType=TuringCalendarTypes.TARGET
        elif currencyName == "EUR"and indexName == "EURIBOR":
            self._spotLag = 2
            self._dayCountType=TuringDayCountTypes.THIRTY_E_360_ISDA
            self._calendarType=TuringCalendarTypes.TARGET
        else:
            pass

###############################################################################
