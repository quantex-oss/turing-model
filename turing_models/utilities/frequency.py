from turing_models.utilities.error import TuringError

###############################################################################

from enum import Enum


class FrequencyType(Enum):
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
    if isinstance(freqType, FrequencyType) is False:
        print("TuringFrequency:", freqType)
        raise TuringError("Unknown frequency type")

    if freqType == FrequencyType.CONTINUOUS:
        return -1
    elif freqType == FrequencyType.SIMPLE:
        return 0
    elif freqType == FrequencyType.ANNUAL:
        return 1
    elif freqType == FrequencyType.SEMI_ANNUAL:
        return 2
    elif freqType == FrequencyType.TRI_ANNUAL:
        return 3
    elif freqType == FrequencyType.QUARTERLY:
        return 4
    elif freqType == FrequencyType.MONTHLY:
        return 12
    elif freqType == FrequencyType.BIWEEKLY:
        return 26
    elif freqType == FrequencyType.WEEKLY:
        return 52
    elif freqType == FrequencyType.DAILY:
        return 365


###############################################################################
