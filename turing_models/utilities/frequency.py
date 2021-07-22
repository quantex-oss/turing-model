from .error import TuringError

###############################################################################

from enum import Enum


class TuringFrequencyTypes(Enum):
    SIMPLE = 0
    ANNUAL = 1
    SEMI_ANNUAL = 2
    TRI_ANNUAL = 3
    QUARTERLY = 4
    MONTHLY = 12
    CONTINUOUS = 99
    BIWEEKLY = 26
    WEEKLY = 52
    DAILY = 365

###############################################################################


def TuringFrequency(freqType):
    ''' This is a function that takes in a Frequency Type and returns an
    integer for the number of times a year a payment occurs.'''
    if isinstance(freqType, TuringFrequencyTypes) is False:
        print("TuringFrequency:", freqType)
        raise TuringError("Unknown frequency type")

    if freqType == TuringFrequencyTypes.CONTINUOUS:
        return -1
    elif freqType == TuringFrequencyTypes.SIMPLE:
        return 0
    elif freqType == TuringFrequencyTypes.ANNUAL:
        return 1
    elif freqType == TuringFrequencyTypes.SEMI_ANNUAL:
        return 2
    elif freqType == TuringFrequencyTypes.TRI_ANNUAL:
        return 3
    elif freqType == TuringFrequencyTypes.QUARTERLY:
        return 4
    elif freqType == TuringFrequencyTypes.MONTHLY:
        return 12
    elif freqType == TuringFrequencyTypes.BIWEEKLY:
        return 26
    elif freqType == TuringFrequencyTypes.WEEKLY:
        return 52
    elif freqType == TuringFrequencyTypes.DAILY:
        return 365


###############################################################################
