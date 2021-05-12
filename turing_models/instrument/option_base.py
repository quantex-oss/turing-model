import datetime
from typing import Union

from tunny.models import model

from fundamental import ctx
from turing_models.instrument.common import OptionType, OptionStyle, Currency, \
    OptionSettlementMethod, BuySell, AssetClass, AssetType, Exchange, KnockType
from turing_models.market.curves import TuringDiscountCurveFlat
from turing_models.models.model_black_scholes import TuringModelBlackScholes
from turing_models.products.equity import TuringOptionTypes, \
    TuringEquityVanillaOption, TuringEquityAsianOption, \
    TuringAsianOptionValuationMethods
from turing_models.utilities.error import TuringError
from turing_models.utilities.turing_date import TuringDate

class OptionBase:
    def __init__(self,
                 option_style=None,
                 start_averaging_date=None,
                 expiration_date=None,
                 strike_price=None,
                 option_type=None
                 ):
        self.option_style = option_style
        self.start_averaging_date = start_averaging_date
        self.expiration_date = expiration_date
        self.strike_price = strike_price
        self.option_type = option_type

    def get_option(self):
        option = None
        # 欧式期权
        if self.option_style == OptionStyle.European or self.option_style == 'European':
            option = TuringEquityVanillaOption(
                self.expiration_date,
                self.strike_price,
                self.option_type)

        # 美式期权
        # 亚式期权
        if self.option_style == OptionStyle.Asian or self.option_style == 'Asian':
            option = TuringEquityAsianOption(
                self.start_averaging_date,
                self.expiration_date,
                self.strike_price,
                self.option_type)

        # 雪球期权
        return option

