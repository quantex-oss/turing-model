##############################################################################
# Copyright (C) 2018, 2019, 2020 Dominic O'Kane
##############################################################################

##########################################################################
# THIS IS UNFINISHED
##########################################################################

from enum import Enum

from ...finutils.turing_day_count import FinDayCount, FinDayCountTypes
from ...finutils.turing_frequency import FinFrequencyTypes
from ...finutils.turing_calendar import FinCalendarTypes,  FinDateGenRuleTypes
from ...finutils.turing_calendar import FinBusDayAdjustTypes

##########################################################################


class FinIborConventions():

    def __init__(self,
                 currencyName: str,
                 indexName: str = "LIBOR"):

        if currencyName == "USD" and indexName == "LIBOR":
            self._spotLag = 2
            self._dayCountType=FinDayCountTypes.THIRTY_E_360_ISDA
            self._calendarType=FinCalendarTypes.TARGET
        elif currencyName == "EUR"and indexName == "EURIBOR":
            self._spotLag = 2
            self._dayCountType=FinDayCountTypes.THIRTY_E_360_ISDA
            self._calendarType=FinCalendarTypes.TARGET
        else:
            pass

###############################################################################
