import datetime

from fundamental import PricingContext
from turing_models.instruments.common import RiskMeasure
from turing_models.instruments.rates.bond_vanilla_option import BondVanillaOption
from turing_models.utilities.turing_date import TuringDate

print("==============固息债示例==============")
bond_eur_opt = BondVanillaOption(
    asset_id="SEC022533308",
    underlying_wind_id="",
    underlying_bbg_id="",
    underlying_cusip="",
    underlying_sedol="",
    underlying_ric="",
    underlying_isin="",
    underlying_ext_asset_id="",
    underlying_asset_name="",
    underlying_asset_type="",
    underlying_trd_curr_code="CNY",
    underlying_symbol="200016",
    underlying_comb_symbol="200016.IB",
    underlying_exchange="SH",
    underlying_issuer="",
    underlying_issue_date=datetime.datetime(2020, 11, 19),
    underlying_due_date=datetime.datetime(2030, 11, 19),
    underlying_par=100.0,
    underlying_coupon_rate=0.0327,
    underlying_interest_rate_type="FIXED_RATE",
    underlying_pay_interest_cycle="SEMI_ANNUAL",
    underlying_interest_rules="ACT/365",
    underlying_pay_interest_mode="COUPON_CARRYING",
    underlying_curve_code="CBD100222",
    value_date=datetime.datetime(2021, 8, 20),
    # number_of_options=968388.8817,
    notional=100000000,
    strike=103.2643,
    expiry=TuringDate(2021, 12, 20),
    option_type="put",
    start_date=TuringDate(2021, 8, 20),
    volatility=0.05,
    interest_rate=0.03
)

# full_price = bond_eur_opt.price()
# delta = bond_eur_opt.bond_delta()
# gamma = bond_eur_opt.bond_gamma()
vega = bond_eur_opt.bond_vega()
# theta = bond_eur_opt.bond_theta()
# print('full price', full_price)
# print(delta)
# print(gamma)
print(vega)
# print(theta)