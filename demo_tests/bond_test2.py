import datetime

import pandas as pd

from turing_models.instruments.common import RiskMeasure
from turing_models.instruments.rates.bond_fixed_rate import BondFixedRate
from turing_models.market.data.china_money_yield_curve import dates, rates

bond_fr = BondFixedRate(
    asset_id="SEC022533308",
    wind_id="",
    bbg_id="",
    cusip="",
    sedol="",
    ric="",
    isin="",
    ext_asset_id="",
    asset_name="",
    asset_type="",
    trd_curr_code="CNY",
    symbol="127157",
    comb_symbol="127157.SH",
    exchange="SH",
    issuer="",
    issue_date=datetime.datetime(2017, 5, 4),
    due_date=datetime.datetime(2022, 5, 4),
    par=100.0,
    coupon_rate=0.061,
    interest_rate_type="FIXED_RATE",
    pay_interest_cycle="ANNUAL",
    interest_rules="ACT/365",
    pay_interest_mode="ZERO_COUPON",
    # curve_code="CBD100252"
)

curve_data = pd.DataFrame(data={'tenor': dates, 'rate': rates})
bond_fr.cv.curve_data = curve_data

price = bond_fr.calc(RiskMeasure.FullPrice)
clean_price = bond_fr.calc(RiskMeasure.CleanPrice)
ytm = bond_fr.calc(RiskMeasure.YTM)
# dv01 = bond_fr.calc(RiskMeasure.Dv01)
# modified_duration = bond_fr.calc(RiskMeasure.ModifiedDuration)
# dollar_convexity = bond_fr.calc(RiskMeasure.DollarConvexity)

print("Fixed Rate Bond to be added:")
print('price', price)
print('clean_price', clean_price)
print('ytm', ytm)
# print('dv01:', dv01)
# print('modified_duration:', modified_duration)
# print('dollar_convexity:', dollar_convexity)