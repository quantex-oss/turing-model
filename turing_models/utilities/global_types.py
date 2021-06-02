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

class TuringKnockOutTypes(Enum):
    DOWN_AND_OUT_CALL = 1
    UP_AND_OUT_CALL = 2
    UP_AND_OUT_PUT = 3
    DOWN_AND_OUT_PUT = 4


option_type_dict = {
        'call_European': {'type': TuringOptionTypes.EUROPEAN_CALL, 'knock_out_type': None, 'knock_in_type': None, 'option_name': ["european", "generic"]},
        'call_American': {'type': TuringOptionTypes.AMERICAN_CALL, 'knock_out_type': None, 'knock_in_type': None, 'option_name': ["american", "generic"]},
        'call_Asian': {'type': TuringOptionTypes.ASIAN_CALL, 'knock_out_type': None, 'knock_in_type': None, 'option_name': ["asian", "asian"]},
        'call_Snowball_Return': {'type': TuringOptionTypes.SNOWBALL_CALL, 'knock_out_type': None, 'knock_in_type': TuringKnockInTypes.RETURN, 'option_name': ["snowball", "generic"]},
        'call_Snowball_Vanilla': {'type': TuringOptionTypes.SNOWBALL_CALL, 'knock_out_type': None, 'knock_in_type': TuringKnockInTypes.VANILLA, 'option_name': ["snowball", "generic"]},
        'call_Snowball_Spreads': {'type': TuringOptionTypes.SNOWBALL_CALL, 'knock_out_type': None, 'knock_in_type': TuringKnockInTypes.SPREADS, 'option_name': ["snowball", "generic"]},
        'call_Knockout_down_and_out': {'type': TuringOptionTypes.KNOCKOUT, 'knock_out_type': TuringKnockOutTypes.DOWN_AND_OUT_CALL, 'knock_in_type': None, 'option_name': ["knockout", "generic"]},
        'call_Knockout_up_and_out': {'type': TuringOptionTypes.KNOCKOUT, 'knock_out_type': TuringKnockOutTypes.UP_AND_OUT_CALL, 'knock_in_type': None, 'option_name': ["knockout", "generic"]},

        'put_European': {'type': TuringOptionTypes.EUROPEAN_PUT, 'knock_out_type': None, 'knock_in_type': None, 'option_name': ["european", "generic"]},
        'put_American': {'type': TuringOptionTypes.AMERICAN_PUT, 'knock_out_type': None, 'knock_in_type': None, 'option_name': ["american", "generic"]},
        'put_Asian': {'type': TuringOptionTypes.ASIAN_PUT, 'knock_out_type': None, 'knock_in_type': None, 'option_name': ["asian", "asian"]},
        'put_Snowball_Return': {'type': TuringOptionTypes.SNOWBALL_PUT, 'knock_out_type': None, 'knock_in_type': TuringKnockInTypes.RETURN, 'option_name': ["snowball", "generic"]},
        'put_Snowball_Vanilla': {'type': TuringOptionTypes.SNOWBALL_PUT, 'knock_out_type': None, 'knock_in_type': TuringKnockInTypes.VANILLA, 'option_name': ["snowball", "generic"]},
        'put_Snowball_Spreads': {'type': TuringOptionTypes.SNOWBALL_PUT, 'knock_out_type': None, 'knock_in_type': TuringKnockInTypes.SPREADS, 'option_name': ["snowball", "generic"]},
        'put_Knockout_down_and_out': {'type': TuringOptionTypes.KNOCKOUT, 'knock_out_type': TuringKnockOutTypes.DOWN_AND_OUT_PUT, 'knock_in_type': None, 'option_name': ["knockout", "generic"]},
        'put_Knockout_up_and_out': {'type': TuringOptionTypes.KNOCKOUT, 'knock_out_type': TuringKnockOutTypes.UP_AND_OUT_PUT, 'knock_in_type': None, 'option_name': ["knockout", "generic"]},
    }
