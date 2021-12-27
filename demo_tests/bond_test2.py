import datetime

import pandas as pd

from fundamental import PricingContext
from turing_models.instruments.common import RiskMeasure
from turing_models.instruments.rates.bond_fixed_rate import BondFixedRate
from turing_models.instruments.rates.bond_floating_rate import BondFloatingRate
from turing_models.instruments.rates.bond_adv_redemption import BondAdvRedemption
from turing_models.instruments.rates.bond_putable_adjustable import BondPutableAdjustable
from turing_models.market.data.china_money_yield_curve import dates, rates
from turing_models.utilities.bond_terms import FloatingRateTerms, EcnomicTerms, PrepaymentTerms, EmbeddedPutableOptions, \
    EmbeddedRateAdjustmentOptions

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
    pay_interest_mode="COUPON_CARRYING",
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
    pay_interest_mode="COUPON_CARRYING",
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
            "pay_rate": 0.4
        },
        {
            "pay_date": datetime.datetime(2019, 5, 4),
            "pay_rate": 0.2
        },
        {
            "pay_date": datetime.datetime(2020, 5, 4),
            "pay_rate": 0.2
        },
        {
            "pay_date": datetime.datetime(2021, 5, 4),
            "pay_rate": 0.2
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
    pay_interest_mode="COUPON_CARRYING",
    # curve_code="CBD100252",
    ecnomic_terms=ecnomic_terms
)

curve_data = pd.DataFrame(data={'tenor': dates, 'rate': rates})
bond_adv_redemption.cv.curve_data = curve_data

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

print("==============固息债（回售+调整票面利率）==============")
data_list = [
    {
        "exercise_date": datetime.datetime(2024, 4, 27),
        "exercise_price": 100.0
    }
]
data = pd.DataFrame(data=data_list)
embedded_putable_options = EmbeddedPutableOptions(data=data)
data_list = [
    {
        "exercise_date": datetime.datetime(2024, 4, 27),
        "high_rate_adjust": None,
        "low_rate_adjust": None
    }
]
data = pd.DataFrame(data=data_list)
embedded_rate_adjustment_options = EmbeddedRateAdjustmentOptions(data=data)
ecnomic_terms = EcnomicTerms(embedded_putable_options, embedded_rate_adjustment_options)

bond_putable_adjustable = BondPutableAdjustable(
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
    issue_date=datetime.datetime(2021, 5, 28),
    due_date=datetime.datetime(2026, 4, 28),
    par=100.0,
    coupon_rate=0.061,
    interest_rate_type="FIXED_RATE",
    pay_interest_cycle="ANNUAL",
    interest_rules="ACT/365",
    pay_interest_mode="COUPON_CARRYING",
    curve_code="CBD100032",
    ecnomic_terms=ecnomic_terms,
    value_date=datetime.datetime(2021, 11, 10)
)

curve_data = pd.DataFrame(data={'tenor': dates[:180], 'rate': rates[:180]})
bond_putable_adjustable.cv.curve_data = curve_data
print(bond_putable_adjustable.cv.curve_data)
# print('full price', bond_putable_adjustable.full_price())
print('clean_price', bond_putable_adjustable.calc(RiskMeasure.CleanPrice))
# print('ytm:', bond_putable_adjustable.calc(RiskMeasure.YTM))
# print('dv01:', bond_putable_adjustable.calc(RiskMeasure.Dv01))
# print('modified_duration:', bond_putable_adjustable.calc(RiskMeasure.ModifiedDuration))
# print('dollar_convexity:', bond_putable_adjustable.calc(RiskMeasure.DollarConvexity))
# print('time_to_maturity:', bond_putable_adjustable.calc(RiskMeasure.TimeToMaturity))

scenario_extreme = PricingContext(clean_price=[{"comb_symbol": "127157.SH", "value": 39.5805}])
with scenario_extreme:
    print("==========")
    # print('price', bond_putable_adjustable.calc(RiskMeasure.FullPrice))
    print('clean_price', bond_putable_adjustable.calc(RiskMeasure.CleanPrice))
    # print('dv01:', bond_putable_adjustable.calc(RiskMeasure.Dv01))
    # print('ytm:', bond_putable_adjustable.calc(RiskMeasure.YTM))
    # print('modified_duration:', bond_putable_adjustable.calc(RiskMeasure.ModifiedDuration))
    # print('dollar_convexity:', bond_putable_adjustable.calc(RiskMeasure.DollarConvexity))
print("---------------------------------------------")

scenario_extreme = PricingContext(yield_curve=[{
    "curve_code": "CBD100252",
    "type": "forward_spot_rate",
    "forward_term": bond_putable_adjustable.time_to_maturity_in_year,
    "value": [
        {
            "tenor": 0.25,
            "origin_tenor": "3M",
            "rate": 0.02489
        },
        {
            "tenor": 0.5,
            "origin_tenor": "6M",
            "rate": 0.02522
        },
        {
            "tenor": 0.75,
            "origin_tenor": "9M",
            "rate": 0.02558
        },
        {
            "tenor": 1.0,
            "origin_tenor": "12M",
            "rate": 0.02592
        },
        {
            "tenor": 2.0,
            "origin_tenor": "2Y",
            "rate": 0.02748
        },
        {
            "tenor": 3.0,
            "origin_tenor": "3Y",
            "rate": 0.02907
        },
        {
            "tenor": 4.0,
            "origin_tenor": "4Y",
            "rate": 0.03070
        },
        {
            "tenor": 5.0,
            "origin_tenor": "5Y",
            "rate": 0.03154
        },
        {
            "tenor": 7.0,
            "origin_tenor": "7Y",
            "rate": 0.03326
        },
        {
            "tenor": 10.0,
            "origin_tenor": "10Y",
            "rate": 0.03537
        }
    ]
}])
with scenario_extreme:
    print("==========")
    print('price', bond_putable_adjustable.calc(RiskMeasure.FullPrice))
    print(bond_putable_adjustable.cv.curve_data)
    print('clean_price', bond_putable_adjustable.calc(RiskMeasure.CleanPrice))
    print('dv01:', bond_putable_adjustable.calc(RiskMeasure.Dv01))
    print('ytm:', bond_putable_adjustable.calc(RiskMeasure.YTM))
    print('modified_duration:', bond_putable_adjustable.calc(RiskMeasure.ModifiedDuration))
    print('dollar_convexity:', bond_putable_adjustable.calc(RiskMeasure.DollarConvexity))