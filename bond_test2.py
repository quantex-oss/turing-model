import datetime

import pandas as pd

from fundamental.pricing_context import PricingContext, CurveScenario
from turing_models.instruments.common import RiskMeasure
from turing_models.instruments.rates.bond_adv_redemption import \
     BondAdvRedemption
from turing_models.instruments.rates.bond_fixed_rate import BondFixedRate
from turing_models.instruments.rates.bond_floating_rate import BondFloatingRate
from turing_models.market.data.china_money_yield_curve import dates, rates
from turing_models.instruments.rates.bond_putable_adjustable import BondPutableAdjustable
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
    symbol="200004",
    comb_symbol="200004.IB",
    exchange="IB",
    issuer="",
    issue_date=datetime.datetime(2020, 3, 16),
    due_date=datetime.datetime(2050, 3, 16),
    par=100.0,
    coupon_rate=0.0339,
    interest_rate_type="FIXED_RATE",
    pay_interest_cycle="SEMI_ANNUAL",
    interest_rules="ACT/ACT",
    pay_interest_mode="COUPON_CARRYING",
    curve_code="CBD100311"
)

scenario_extreme = PricingContext(clean_price=[{"comb_symbol": "200004.IB", "value": 99.1455}],
                                  pricing_date=datetime.datetime(2021, 12, 27))
with scenario_extreme:
    print(bond_fixed_rate._market_clean_price)
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
floating_rate_terms = FloatingRateTerms(floating_rate_benchmark="LPR1Y",
                                        floating_spread=-0.01,
                                        floating_adjust_mode="",
                                        base_interest_rate=0.0385)
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
    symbol="200217",
    comb_symbol="200217.IB",
    exchange="IB",
    issuer="",
    issue_date=datetime.datetime(2020, 6, 9),
    due_date=datetime.datetime(2023, 6, 9),
    par=100.0,
    coupon_rate=0.0285,
    interest_rate_type="FLOATING_RATE",
    pay_interest_cycle="QUARTERLY",
    interest_rules="ACT/ACT",
    pay_interest_mode="COUPON_CARRYING",
    curve_code="CBD100332",
    ecnomic_terms=ecnomic_terms
)

scenario_extreme = PricingContext(clean_price=[{"comb_symbol": "200217.IB", "value": 100.1974}],
                                  pricing_date=datetime.datetime(2021, 12, 27))
with scenario_extreme:

    full_price = bond_floating_rate.calc(RiskMeasure.FullPrice)
    clean_price = bond_floating_rate.calc(RiskMeasure.CleanPrice)
    dv01 = bond_floating_rate.calc(RiskMeasure.Dv01)
    ytm = bond_floating_rate.calc(RiskMeasure.YTM)
    modified_duration = bond_floating_rate.calc(RiskMeasure.ModifiedDuration)
    dollar_convexity = bond_floating_rate.calc(RiskMeasure.DollarConvexity)
    time_to_maturity = bond_floating_rate.calc(RiskMeasure.TimeToMaturity)

    print('full price', full_price)
    print('clean_price', clean_price)
    print('dv01:', dv01)
    print('ytm:', ytm)
    print('modified_duration:', modified_duration)
    print('dollar_convexity:', dollar_convexity)
    print('time_to_maturity:', time_to_maturity)

print("==============固息债（含提前偿还条款）==============")
data_list = [
        {
            "pay_date": datetime.datetime(2024, 10, 29),
            "pay_rate": 0.2
        },
        {
            "pay_date": datetime.datetime(2025, 10, 29),
            "pay_rate": 0.2
        },
        {
            "pay_date": datetime.datetime(2026, 10, 29),
            "pay_rate": 0.2
        },
        {
            "pay_date": datetime.datetime(2027, 10, 29),
            "pay_rate": 0.2
        },
        {
            "pay_date": datetime.datetime(2028, 10, 29),
            "pay_rate": 0.2
        },

    ]
data = pd.DataFrame(data=data_list)
prepayment_terms = PrepaymentTerms(data=data)
ecnomic_terms = EcnomicTerms(prepayment_terms)

bond_adv_redemption = BondAdvRedemption(
    asset_id="SEC045926019",
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
    symbol="2180432",
    comb_symbol="2180432.IB",
    exchange="IB",
    issuer="",
    issue_date=datetime.datetime(2021, 10, 29),
    due_date=datetime.datetime(2028, 10, 29),
    par=100.0,
    coupon_rate=0.0477,
    interest_rate_type="FIXED_RATE",
    pay_interest_cycle="ANNUAL",
    interest_rules="ACT/365F",
    pay_interest_mode="COUPON_CARRYING",
    curve_code="CBD100461",
    ecnomic_terms=ecnomic_terms
)

curve_data = pd.DataFrame(data={'tenor': dates, 'rate': rates})
bond_adv_redemption.cv.curve_data = curve_data

scenario_extreme = PricingContext(clean_price=[{"comb_symbol": "2180432.IB", "value": 101.0978}],
                                  pricing_date=datetime.datetime(2021, 12, 27))
with scenario_extreme:
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
        "exercise_date": datetime.datetime(2023, 4, 28),
        "exercise_price": 100.0
    }
]
data = pd.DataFrame(data=data_list)
embedded_putable_options = EmbeddedPutableOptions(data=data)
data_list = [
    {
        "exercise_date": datetime.datetime(2023, 4, 28),
        "high_rate_adjust": 0.03,
        "low_rate_adjust": -0.03
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
    symbol="1880106",
    comb_symbol="1880106.IB",
    exchange="IB",
    issuer="",
    issue_date=datetime.datetime(2018, 4, 28),
    due_date=datetime.datetime(2025, 4, 28),
    par=100.0,
    coupon_rate=0.0508,
    interest_rate_type="FIXED_RATE",
    pay_interest_cycle="ANNUAL",
    interest_rules="ACT/ACT",
    pay_interest_mode="COUPON_CARRYING",
    curve_code="CBD100541",
    ecnomic_terms=ecnomic_terms,
    value_date=datetime.datetime(2021, 12, 27)
)

print("==========")
print(bond_putable_adjustable.recommend_dir)
print(bond_putable_adjustable.adjust_fix)
print('price', bond_putable_adjustable.calc(RiskMeasure.FullPrice))
print('clean_price', bond_putable_adjustable.calc(RiskMeasure.CleanPrice))
print('dv01:', bond_putable_adjustable.calc(RiskMeasure.Dv01))
print('ytm:', bond_putable_adjustable.calc(RiskMeasure.YTM))
print('modified_duration:', bond_putable_adjustable.calc(RiskMeasure.ModifiedDuration))
print('dollar_convexity:', bond_putable_adjustable.calc(RiskMeasure.DollarConvexity))
print("---------------------------------------------")
