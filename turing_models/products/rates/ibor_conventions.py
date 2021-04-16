##########################################################################
# THIS IS UNFINISHED
##########################################################################

from enum import Enum

from turing_models.utilities.day_count import TuringDayCount, TuringDayCountTypes
from turing_models.utilities.frequency import TuringFrequencyTypes
from turing_models.utilities.calendar import TuringCalendarTypes,  TuringDateGenRuleTypes
from turing_models.utilities.calendar import TuringBusDayAdjustTypes

##########################################################################


class TuringIborConventions():

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
