import datetime

import pandas as pd

from turing_models.instruments.common import RiskMeasure
from turing_models.instruments.rates.bond_fixed_rate import BondFixedRate
from turing_models.instruments.rates.bond_floating_rate import BondFloatingRate
from turing_models.instruments.rates.bond_adv_redemption import BondAdvRedemption
from turing_models.market.data.china_money_yield_curve import dates, rates
from turing_models.utilities.bond_terms import FloatingRateTerms, EcnomicTerms, PrepaymentTerms

print("==============固息债示例==============")
bond_fixed_rate = BondFixedRate(
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
bond_fixed_rate.cv.curve_data = curve_data

full_price = bond_fixed_rate.calc(RiskMeasure.FullPrice)
clean_price = bond_fixed_rate.calc(RiskMeasure.CleanPrice)
ytm = bond_fixed_rate.calc(RiskMeasure.YTM)
dv01 = bond_fixed_rate.calc(RiskMeasure.Dv01)
modified_duration = bond_fixed_rate.calc(RiskMeasure.ModifiedDuration)
dollar_convexity = bond_fixed_rate.calc(RiskMeasure.DollarConvexity)
time_to_maturity = bond_fixed_rate.calc(RiskMeasure.TimeToMaturity)

print('full price', full_price)
print('clean_price', clean_price)
print('ytm', ytm)
print('dv01:', dv01)
print('modified_duration:', modified_duration)
print('dollar_convexity:', dollar_convexity)
print('time_to_maturity:', time_to_maturity)

print("==============浮息债示例==============")
floating_rate_terms = FloatingRateTerms(floating_rate_benchmark="Shibor3M",
                                        floating_spread=0.005,
                                        floating_adjust_mode="",
                                        base_interest_rate=0.02)
ecnomic_terms = EcnomicTerms(floating_rate_terms)

bond_floating_rate = BondFloatingRate(
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
    # curve_code="CBD100252",
    ecnomic_terms=ecnomic_terms
)

full_price = bond_floating_rate.calc(RiskMeasure.FullPrice)
clean_price = bond_floating_rate.calc(RiskMeasure.CleanPrice)
dv01 = bond_floating_rate.calc(RiskMeasure.Dv01)
modified_duration = bond_floating_rate.calc(RiskMeasure.ModifiedDuration)
dollar_convexity = bond_floating_rate.calc(RiskMeasure.DollarConvexity)
time_to_maturity = bond_floating_rate.calc(RiskMeasure.TimeToMaturity)

print('full price', full_price)
print('clean_price', clean_price)
print('dv01:', dv01)
print('modified_duration:', modified_duration)
print('dollar_convexity:', dollar_convexity)
print('time_to_maturity:', time_to_maturity)

print("==============固息债（含提前偿还条款）==============")
data_list = [
        {
            "pay_date": datetime.datetime(2018, 5, 4),
            "pay_rate": 0.04
        },
        {
            "pay_date": datetime.datetime(2019, 5, 4),
            "pay_rate": 0.041
        },
        {
            "pay_date": datetime.datetime(2020, 5, 4),
            "pay_rate": 0.042
        },
        {
            "pay_date": datetime.datetime(2021, 5, 4),
            "pay_rate": 0.043
        }
    ]
data = pd.DataFrame(data=data_list)
prepayment_terms = PrepaymentTerms(data=data)
ecnomic_terms = EcnomicTerms(prepayment_terms)

bond_adv_redemption = BondAdvRedemption(
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
    # curve_code="CBD100252",
    ecnomic_terms=ecnomic_terms
)

full_price = bond_adv_redemption.calc(RiskMeasure.FullPrice)
clean_price = bond_adv_redemption.calc(RiskMeasure.CleanPrice)
ytm = bond_adv_redemption.calc(RiskMeasure.YTM)
dv01 = bond_adv_redemption.calc(RiskMeasure.Dv01)
modified_duration = bond_adv_redemption.calc(RiskMeasure.ModifiedDuration)
dollar_convexity = bond_adv_redemption.calc(RiskMeasure.DollarConvexity)
time_to_maturity = bond_adv_redemption.calc(RiskMeasure.TimeToMaturity)

print('full price', full_price)
print('clean_price', clean_price)
print('ytm:', ytm)
print('dv01:', dv01)
print('modified_duration:', modified_duration)
print('dollar_convexity:', dollar_convexity)
print('time_to_maturity:', time_to_maturity)

