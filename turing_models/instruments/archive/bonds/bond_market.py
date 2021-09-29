#TODO  Add Japan 


from turing_models.utilities.frequency import TuringFrequencyTypes
from turing_models.utilities.day_count import TuringDayCountTypes
from turing_models.utilities.error import TuringError
from turing_models.utilities.calendar import TuringCalendarTypes


from enum import Enum


class TuringBondMarkets(Enum):
    AUSTRIA = 1,
    BELGIUM = 2,
    CYPRUS = 3,
    ESTONIA = 4,
    FINLAND = 5,
    FRANCE = 6,
    GERMANY = 7,
    GREECE = 8,
    IRELAND = 9,
    ITALY = 10,
    LATVIA = 11,
    LITHUANIA = 12,
    LUXEMBOURG = 13,
    MALTA = 14,
    NETHERLANDS = 15,
    PORTUGAL = 16,
    SLOVAKIA = 17,
    SLOVENIA = 18,
    SPAIN = 19,
    ESM = 20,
    EFSF = 21,
    BULGARIA = 22,
    CROATIA = 23,
    CZECH_REPUBLIC = 24,
    DENMARK = 25,
    HUNGARY = 26,
    POLAND = 27,
    ROMANIA = 28,
    SWEDEN = 29,
    JAPAN = 30,
    SWITZERLAND = 31,
    UNITED_KINGDOM = 32,
    UNITED_STATES = 33,
    AUSTRALIA = 34,
    NEW_ZEALAND = 35,
    NORWAY = 36,
    SOUTH_AFRICA = 37

###############################################################################
    
def getTreasuryBondMarketConventions(country):
    ''' Returns the day count convention for accrued interest, the frequency
    and the number of days from trade date to settlement date.
    This is for Treasury markets. And for secondary bond markets. '''

    annual = TuringFrequencyTypes.ANNUAL
    semi_annual = TuringFrequencyTypes.SEMI_ANNUAL
    act_act = TuringDayCountTypes.ACT_ACT_ICMA
    thirtye360 = TuringDayCountTypes.THIRTY_E_360

    # TODO: CHECK CONVENTIONS
    
    # RETURNS
    # ACCRUAL CONVENTION
    # COUPON FREQUENCY
    # SETTLEMENT DAYS
    # NUM EX DIVIDEND DAYS AND CALENDAR TO USE

    if country == TuringBondMarkets.AUSTRIA:
        return (act_act, annual, 2, 0, None)
    elif country == TuringBondMarkets.AUSTRALIA:
        return (act_act, annual, 2, 7, TuringCalendarTypes.NONE)
    elif country == TuringBondMarkets.BELGIUM:
        return (act_act, annual, 2, 0, None)
    elif country == TuringBondMarkets.CYPRUS:
        return (act_act, semi_annual, 2, 0, None)
    elif country == TuringBondMarkets.ESTONIA:
        return (act_act, annual, 2, 0, None)
    elif country == TuringBondMarkets.FINLAND:
        return (act_act, annual, 2, 0, None)
    elif country == TuringBondMarkets.FRANCE:
        return (act_act, annual, 2, 0, None)
    elif country == TuringBondMarkets.GERMANY:
        return (act_act, annual, 2, 0, None)
    elif country == TuringBondMarkets.GREECE:
        return (act_act, annual, 3, 0, None)
    elif country == TuringBondMarkets.IRELAND:
        return (act_act, annual, 2, 0, None)
    elif country == TuringBondMarkets.ITALY:
        return (act_act, semi_annual, 2, 0, None)
    elif country == TuringBondMarkets.LATVIA:
        return (act_act, annual, 2, 0, None)
    elif country == TuringBondMarkets.LITHUANIA:
        return (act_act, annual, 1, 0, None)
    elif country == TuringBondMarkets.LUXEMBOURG:
        return (act_act, annual, 2, 0, None)
    elif country == TuringBondMarkets.MALTA:
        return (act_act, semi_annual, 2, 0, None)
    elif country == TuringBondMarkets.NETHERLANDS:
        return (act_act, annual, 2, 0, None)
    elif country == TuringBondMarkets.PORTUGAL:
        return (act_act, annual, 2, 0, None)
    elif country == TuringBondMarkets.SLOVAKIA:
        return (act_act, annual, 2, 0, None)
    elif country == TuringBondMarkets.SLOVENIA:
        return (act_act, annual, 2, 0, None)
    elif country == TuringBondMarkets.SPAIN:
        return (act_act, annual, 2, 0, None)
    elif country == TuringBondMarkets.ESM:
        return (act_act, annual, 2, 0, None)
    elif country == TuringBondMarkets.EFSF:
        return (act_act, annual, 2, 0, None)
    elif country == TuringBondMarkets.BULGARIA:
        return (act_act, semi_annual, 0, 0, None)
    elif country == TuringBondMarkets.CROATIA:
        return (act_act, semi_annual, 3, 0, None)
    elif country == TuringBondMarkets.CZECH_REPUBLIC:
        return (act_act, semi_annual, 2, 0, None)
    elif country == TuringBondMarkets.DENMARK:
        return (act_act, annual, 2, 0, None)
    elif country == TuringBondMarkets.HUNGARY:
        return (act_act, annual, 2, 0, None)
    elif country == TuringBondMarkets.POLAND:
        return (act_act, semi_annual, 2, 0, None)
    elif country == TuringBondMarkets.ROMANIA:
        return (act_act, semi_annual, 2, 0, None)
    elif country == TuringBondMarkets.SOUTH_AFRICA:
        return (act_act, annual, 2, 10, TuringCalendarTypes.NONE) # CHECK
    elif country == TuringBondMarkets.SWEDEN:
        return (thirtye360, annual, 2, 0, None)
    elif country == TuringBondMarkets.JAPAN:
        return (act_act, annual, 2, 0, None)
    elif country == TuringBondMarkets.SWITZERLAND:
        return (act_act, annual, 2, 0, None)
    elif country == TuringBondMarkets.UNITED_STATES:
        return (act_act, semi_annual, 2, 0, None)
    elif country == TuringBondMarkets.UNITED_KINGDOM:
        return (act_act, semi_annual, 1, 6, TuringCalendarTypes.UK)  # OR 7 DAYS ?
    else:
        print("Unknown Country:", country)
        return (None, None, None, None, None)