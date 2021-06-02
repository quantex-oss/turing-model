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
    KNOCKOUT = 13

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

###############################################################################


class TuringSolverTypes(Enum):
    CONJUGATE_GRADIENT = 0
    NELDER_MEAD = 1
    NELDER_MEAD_NUMBA = 2


class TuringKnockInTypes(Enum):
    RETURN = 0
    VANILLA = 1
    SPREADS = 2

class TuringEquityKnockoutTypes(Enum):
    DOWN_AND_OUT_CALL = 1
    UP_AND_OUT_CALL = 2
    UP_AND_OUT_PUT = 3
    DOWN_AND_OUT_PUT = 4


option_type_dict = {
        'call_European': {'type': TuringOptionTypes.EUROPEAN_CALL, 'option_name': ["european", "generic"]},
        'call_American': {'type': TuringOptionTypes.AMERICAN_CALL, 'option_name': ["american", "generic"]},
        'call_Asian': {'type': TuringOptionTypes.ASIAN_CALL, 'option_name': ["asian", "asian"]},
        'call_Snowball': {'type': TuringOptionTypes.SNOWBALL_CALL, 'option_name': []},
        'call_Snowball_Return': {'type': TuringKnockInTypes.RETURN, 'option_name': []},
        'call_Snowball_Vanilla': {'type': TuringKnockInTypes.VANILLA, 'option_name': []},
        'call_Snowball_Spreads': {'type': TuringKnockInTypes.SPREADS, 'option_name': []},
        'call_Knockout': {'type': TuringOptionTypes.KNOCKOUT, 'option_name': []},
        'call_Knockout_down_and_out': {'type': TuringEquityKnockoutTypes.DOWN_AND_OUT_CALL, 'option_name': []},
        'call_Knockout_up_and_out': {'type': TuringEquityKnockoutTypes.UP_AND_OUT_PUT, 'option_name': []},

        'put_European': {'type': TuringOptionTypes.EUROPEAN_PUT, 'option_name': ["european", "generic"]},
        'put_American': {'type': TuringOptionTypes.AMERICAN_PUT, 'option_name': ["american", "generic"]},
        'put_Asian': {'type': TuringOptionTypes.ASIAN_PUT, 'option_name': ["asian", "asian"]},
        'put_Snowball': {'type': TuringOptionTypes.SNOWBALL_PUT, 'option_name': []},
        'put_Snowball_Return': {'type': TuringKnockInTypes.RETURN, 'option_name': []},
        'put_Snowball_Vanilla': {'type': TuringKnockInTypes.VANILLA, 'option_name': []},
        'put_Snowball_Spreads': {'type': TuringKnockInTypes.SPREADS, 'option_name': []},
        'put_Knockout': {'type': TuringOptionTypes.KNOCKOUT, 'option_name': []},
        'put_Knockout_down_and_out': {'type': TuringEquityKnockoutTypes.DOWN_AND_OUT_PUT, 'option_name': []},
        'put_Knockout_up_and_out': {'type': TuringEquityKnockoutTypes.UP_AND_OUT_PUT, 'option_name': []},
    }