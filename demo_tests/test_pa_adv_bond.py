import datetime

import pandas as pd

from fundamental import PricingContext
from turing_models.instruments.common import RiskMeasure
from turing_models.instruments.rates.bond_fixed_rate import BondFixedRate
from turing_models.instruments.rates.bond_floating_rate import BondFloatingRate
from turing_models.instruments.rates.bond_pa_wiz_adv_rdp import BondPAwizAdvRep
from turing_models.instruments.rates.bond_putable_adjustable import BondPutableAdjustable
from turing_models.utilities.bond_terms import FloatingRateTerms, EcnomicTerms, PrepaymentTerms, EmbeddedPutableOptions, \
    EmbeddedRateAdjustmentOptions

value_date = datetime.datetime(2021, 12, 27)
print("==============固息债（含提前偿还+回售+调整票面利率条款）==============")
data_list = [
        
        
        {
            "pay_date": datetime.datetime(2020, 5, 4),
            "pay_rate": 0.2
        },
        {
            "pay_date": datetime.datetime(2021, 5, 4),
            "pay_rate": 0.2
        },
        {
            "pay_date": datetime.datetime(2022, 5, 4),
            "pay_rate": 0.2
        },
        {
            "pay_date": datetime.datetime(2023, 5, 4),
            "pay_rate": 0.2
        },
        {
            "pay_date": datetime.datetime(2024, 5, 4),
            "pay_rate": 0.2
        },
    ]
data = pd.DataFrame(data=data_list)
prepayment_terms = PrepaymentTerms(data=data)

data_list = [
    {
        "exercise_date": datetime.datetime(2022, 5, 4),
        "exercise_price": 100.0
    }
]
data = pd.DataFrame(data=data_list)
embedded_putable_options = EmbeddedPutableOptions(data=data)
data_list = [
    {
        "exercise_date": datetime.datetime(2022, 5, 4),
        "high_rate_adjust": None,
        "low_rate_adjust": None
    }
]
data = pd.DataFrame(data=data_list)
embedded_rate_adjustment_options = EmbeddedRateAdjustmentOptions(data=data)
ecnomic_terms = EcnomicTerms(embedded_putable_options, embedded_rate_adjustment_options, prepayment_terms)

bond_adv_redemption = BondPAwizAdvRep(
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
    due_date=datetime.datetime(2024, 5, 4),
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