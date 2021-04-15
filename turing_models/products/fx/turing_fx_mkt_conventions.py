##############################################################################
# Copyright (C) 2018, 2019, 2020 Dominic O'Kane
##############################################################################

from turing_models.turingutils.turing_error import TuringError
from enum import Enum
from turing_models.turingutils.turing_helper_functions import labelToString

# Non exhaustive list of country codes and currency names

ccyNames = {"AED": ("UNITED ARAB EMIRATES", "DIRHAM"),
            "AUD": ("AUSTRALIA", "DOLLAR"),
            "BRL": ("BRAZIL", "REAL"),
            "CAD": ("CANADA", "DOLLAR"),
            "CHF": ("SWITZERLAND", "FRANC"),
            "CLP": ("CHILE", "PESO"),
            "CNY": ("CHINA", "RENMIMBI"),
            "COP": ("COLUMBIA", "PESO"),
            "DKK": ("DENMARK", "KRONE"),
            "EUR": ("EUROZONE", "EURO"),
            "GBP": ("UK", "POUND"),
            "HKD": ("HONG KONG", "DOLLAR"),
            "HUF": ("HUNGARY", "FORINT"),
            "IDR": ("INDONESIA", "RUPIAH"),
            "INR": ("INDIA", "RUPEE"),
            "ILS": ("ISRAEL", "SHEKEL"),
            "JPY": ("JAPAN", "YEN"),
            "KRW": ("KOREAN", "WON"),
            "MYR": ("MALYSIA", "RINGIT"),
            "MXN": ("MEXICO", "PESO"),
            "NOK": ("NORWAY", "KRONE"),
            "NZD": ("NEW ZEALAND", "DOLLAR"),
            "PHP": ("PHILIPPINES", "PESO"),
            "PLN": ("POLAND", "ZLOTY"),
            "RON": ("ROMANIA", "LEU"),
            "RUB": ("RUSSIA", "RUBLE"),
            "SAR": ("SAUDI ARABIA", "RIYAL"),
            "SEK": ("SWEDEN", "KRONA"),
            "SGD": ("SINGAPORE", "DOLLAR"),
            "THB": ("THAILAND", "BHAT"),
            "TRY": ("TURKEY", "LIRA"),
            "TWD": ("TAIWAN", "DOLLAR"),
            "USD": ("US", "DOLLAR"),
            "ZAR": ("SOUTH AFRICA", "RAND")
            }

ccyQuotes = {"EURUSD": (1, 1, 1),
             "USDJPY": (1, 1, 1),
             "EURJPY": (1, 1, 1),
             "GBPUSD": (1, 1, 1),
             "EURGBP": (1, 1, 1),
             "USDCHF": (1, 1, 1),
             "AUDUSD": (1, 1, 1),
             "NZDUSD": (1, 1, 1),
             "USDCAD": (1, 1, 1),
             "EURNOK": (1, 1, 1),
             "EURSEK": (1, 1, 1),
             "EURDKK": (1, 1, 1),
             "EURHUF": (1, 1, 1),
             "EURPLN": (1, 1, 1),
             "USDTRY": (1, 1, 1),
             "USDZAR": (1, 1, 1),
             "USDMXN": (1, 1, 1),
             "USDBRL": (1, 1, 1),
             "USDSGD": (1, 1, 1)}

###############################################################################


class TuringFXATMMethod(Enum):
    SPOT = 1  # Spot FX Rate
    FWD = 2  # At the money forward
    FWD_DELTA_NEUTRAL = 3  # K = F*exp(0.5*sigma*sigma*T)
    FWD_DELTA_NEUTRAL_PREM_ADJ = 4  # K = F*exp(-0.5*sigma*sigma*T)


class TuringFXDeltaMethod(Enum):
    SPOT_DELTA = 1
    FORWARD_DELTA = 2
    SPOT_DELTA_PREM_ADJ = 3
    FORWARD_DELTA_PREM_ADJ = 4

###############################################################################


premCurrency = {'EURUSD': 'USD',
                'USDJPY': 'USD',
                'EURJPY': 'EUR',
                'USDCHF': 'USD',
                'EURCHF': 'EUR',
                'GBPUSD': 'USD',
                'EURGBP': 'EUR',
                'AUDUSD': 'USD',
                'AUDJPY': 'AUD',
                'USDCAD': 'USD',
                'USDBRL': 'USD',
                'USDMXN': 'USD'}

deltaConvention = {'EURUSD': TuringFXDeltaMethod.SPOT_DELTA,
                   'USDJPY': TuringFXDeltaMethod.SPOT_DELTA_PREM_ADJ,
                   'EURJPY': TuringFXDeltaMethod.SPOT_DELTA_PREM_ADJ,
                   'USDCHF': TuringFXDeltaMethod.SPOT_DELTA_PREM_ADJ,
                   'EURCHF': TuringFXDeltaMethod.SPOT_DELTA_PREM_ADJ,
                   'GBPUSD': TuringFXDeltaMethod.SPOT_DELTA,
                   'EURGBP': TuringFXDeltaMethod.SPOT_DELTA_PREM_ADJ,
                   'AUDUSD': TuringFXDeltaMethod.SPOT_DELTA,
                   'AUDJPY': TuringFXDeltaMethod.SPOT_DELTA_PREM_ADJ,
                   'USDCAD': TuringFXDeltaMethod.SPOT_DELTA_PREM_ADJ,
                   'USDBRL': TuringFXDeltaMethod.SPOT_DELTA_PREM_ADJ,
                   'USDMXN': TuringFXDeltaMethod.SPOT_DELTA_PREM_ADJ}

###############################################################################


class TuringFXRate():

    def __init__(self,
                 ccy1,
                 ccy2,
                 rate):

        if ccy1 in ccyNames:
            self._ccy1 = ccy1
        else:
            raise TuringError("Unknown currency code ", ccy1)

        if ccy2 in ccyNames:
            self._ccy2 = ccy2
        else:
            raise TuringError("Unknown currency code ", ccy2)

        self._ccy2 = ccy2
        self._rate

###############################################################################
