from fundamental.market.constants import dates, rates
from turing_models.instruments.common import Currency
from turing_models.instruments.knockout_option import KnockOutOption
from turing_models.utilities.global_types import TuringOptionType, TuringKnockOutTypes
from turing_models.utilities.turing_date import TuringDate


def test_knockout_option_knock_out_type_():
    knockout_option = KnockOutOption(asset_id='OPTIONCN00000001',
                                     underlier='STOCKCN00000001',
                                     option_type=TuringOptionType.CALL,
                                     expiry=TuringDate(2021, 9, 3),
                                     strike_price=5.3,
                                     participation_rate=1.0,
                                     barrier=5.5,
                                     notional=1000000,
                                     rebate=0.2,
                                     value_date=TuringDate(2021, 7, 6),
                                     currency=Currency.CNY,
                                     stock_price=5.262,
                                     volatility=0.1,
                                     zero_dates=dates,
                                     zero_rates=rates,
                                     dividend_yield=0)
    assert knockout_option.knock_out_type_ == TuringKnockOutTypes.UP_AND_OUT_CALL


def test_knockout_option_price():
    knockout_option = KnockOutOption(asset_id='OPTIONCN00000001',
                                     underlier='STOCKCN00000001',
                                     option_type=TuringOptionType.CALL,
                                     expiry=TuringDate(2021, 9, 3),
                                     strike_price=5.3,
                                     participation_rate=1.0,
                                     barrier=5.5,
                                     notional=1000000,
                                     rebate=0.2,
                                     value_date=TuringDate(2021, 7, 6),
                                     currency=Currency.CNY,
                                     stock_price=5.262,
                                     volatility=0.1,
                                     zero_dates=dates,
                                     zero_rates=rates,
                                     dividend_yield=0)
    assert knockout_option.price() == 27872.77897054046
