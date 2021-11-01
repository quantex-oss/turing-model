# This is an exhaustive list of all option types

from enum import Enum

###############################################################################


class TuringLongShort(Enum):
    LONG = 1
    SHORT = 2

###############################################################################


class TuringOptionTypes(Enum):
    EUROPEAN_CALL = 1
    EUROPEAN_PUT = 2
    AMERICAN_CALL = 3
    AMERICAN_PUT = 4
    DIGITAL_CALL = 5
    DIGITAL_PUT = 6
    ASIAN_CALL = 7
    ASIAN_PUT = 8
    COMPOUND_CALL = 9
    COMPOUND_PUT = 10
    SNOWBALL_CALL = 11
    SNOWBALL_PUT = 12
    KNOCKOUT_CALL = 13
    KNOCKOUT_PUT = 14
    QUANTO_DIGITAL_CALL = 15
    QUANTO_DIGITAL_PUT = 16


class TuringOptionType(Enum):

    """Option Type"""

    CALL = 'CALL'
    PUT = 'PUT'

    def __repr__(self):
        return self.value


###############################################################################


class TuringCapFloorTypes(Enum):
    CAP = 1
    FLOOR = 2

###############################################################################


class TuringSwapTypes(Enum):
    PAY = 1
    RECEIVE = 2

###############################################################################


class TuringExerciseTypes(Enum):
    EUROPEAN = 1
    BERMUDAN = 2
    AMERICAN = 3


class TuringExerciseType(Enum):
    """Exercise Type"""

    EUROPEAN = 'EUROPEAN'
    BERMUDAN = 'BERMUDAN'
    AMERICAN = 'AMERICAN'

    def __repr__(self):
        return self.value

###############################################################################


class TuringSolverTypes(Enum):
    CONJUGATE_GRADIENT = 0
    NELDER_MEAD = 1
    NELDER_MEAD_NUMBA = 2


class TuringKnockInTypes(Enum):
    RETURN = 0
    VANILLA = 1
    SPREADS = 2


class TuringKnockOutTypes(Enum):
    UP_AND_OUT_CALL = 1
    DOWN_AND_OUT_PUT = 2


class TuringAsianOptionValuationMethods(Enum):
    GEOMETRIC = 1,
    TURNBULL_WAKEMAN = 2,
    CURRAN = 3


class TuringYTMCalcType(Enum):
    UK_DMO = 1,
    US_STREET = 2,
    US_TREASURY = 3
