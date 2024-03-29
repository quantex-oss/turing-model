import datetime

from fundamental import PricingContext
from turing_models.instruments.common import RiskMeasure
from turing_models.instruments.rates.bond_fixed_rate import BondFixedRate
from turing_models.instruments.rates.bond_floating_rate import BondFloatingRate
from turing_models.instruments.rates.bond_adv_redemption import BondAdvRedemption
from turing_models.instruments.rates.bond_putable_adjustable import BondPutableAdjustable


value_date = datetime.datetime(2021, 12, 27)
print("==============固息债示例==============")
bond_fixed_rate = BondFixedRate(
    comb_symbol="200004.IB",
    value_date=value_date
)
bond_fixed_rate.resolve()
# print(bond_fixed_rate)
print('===============')
full_price = bond_fixed_rate.calc(RiskMeasure.FullPrice)
clean_price = bond_fixed_rate.calc(RiskMeasure.CleanPrice)
ytm = bond_fixed_rate.calc(RiskMeasure.YTM)
dv01 = bond_fixed_rate.calc(RiskMeasure.Dv01)
modified_duration = bond_fixed_rate.calc(RiskMeasure.ModifiedDuration)
dollar_convexity = bond_fixed_rate.calc(RiskMeasure.DollarConvexity)
time_to_maturity = bond_fixed_rate.calc(RiskMeasure.TimeToMaturity)
print(bond_fixed_rate._spread_adjustment)
print(bond_fixed_rate.cv.curve_data)
print('full price', full_price)
print('clean_price', clean_price)
print('ytm', ytm)
print('dv01:', dv01)
print('modified_duration:', modified_duration)
print('dollar_convexity:', dollar_convexity)
print('time_to_maturity:', time_to_maturity)

scenario_extreme = PricingContext(
    pricing_date='latest',
    spread_adjustment=[{"symbol": "200004.IB", "value": 0.01}],
    yield_curve=[{
        "curve_code": "CBD100311",
        "type": "spot_rate",
        "value":
            [
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
    }]
)
with scenario_extreme:
    print('===============')
    full_price = bond_fixed_rate.calc(RiskMeasure.FullPrice)
    print(bond_fixed_rate.value_date)
    print(bond_fixed_rate._spread_adjustment)
    print(bond_fixed_rate.cv.curve_data)
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

print('===============')
full_price = bond_fixed_rate.calc(RiskMeasure.FullPrice)
print(bond_fixed_rate.value_date)
print(bond_fixed_rate._spread_adjustment)
print(bond_fixed_rate.cv.curve_data)
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
bond_floating_rate = BondFloatingRate(
    comb_symbol="200217.IB",
    value_date=value_date
)
bond_floating_rate.resolve()
full_price = bond_floating_rate.calc(RiskMeasure.FullPrice)
clean_price = bond_floating_rate.calc(RiskMeasure.CleanPrice)
dv01 = bond_floating_rate.calc(RiskMeasure.Dv01)
modified_duration = bond_floating_rate.calc(RiskMeasure.ModifiedDuration)
dollar_convexity = bond_floating_rate.calc(RiskMeasure.DollarConvexity)
time_to_maturity = bond_floating_rate.calc(RiskMeasure.TimeToMaturity)
ytm = bond_floating_rate.calc(RiskMeasure.YTM)
print('full price', full_price)
print('clean_price', clean_price)
print('dv01:', dv01)
print('modified_duration:', modified_duration)
print('dollar_convexity:', dollar_convexity)
print('time_to_maturity:', time_to_maturity)
print('ytm', ytm)
scenario_extreme = PricingContext(
    pricing_date='latest',
    next_base_interest_rate=[{"floating_rate_benchmark": "IR00000001", "value": 0.04}],
    ytm=[{"symbol": "200217.IB", "value": 0.04}],
    clean_price=[{"symbol": "200217.IB", "value": 0.04}],
)
with scenario_extreme:
    full_price = bond_floating_rate.calc(RiskMeasure.FullPrice)
    clean_price = bond_floating_rate.calc(RiskMeasure.CleanPrice)
    dv01 = bond_floating_rate.calc(RiskMeasure.Dv01)
    modified_duration = bond_floating_rate.calc(RiskMeasure.ModifiedDuration)
    dollar_convexity = bond_floating_rate.calc(RiskMeasure.DollarConvexity)
    time_to_maturity = bond_floating_rate.calc(RiskMeasure.TimeToMaturity)
    ytm = bond_floating_rate.calc(RiskMeasure.YTM)

    print('full price', full_price)
    print('clean_price', clean_price)
    print('dv01:', dv01)
    print('modified_duration:', modified_duration)
    print('dollar_convexity:', dollar_convexity)
    print('time_to_maturity:', time_to_maturity)
    print('ytm', ytm)

full_price = bond_floating_rate.calc(RiskMeasure.FullPrice)
clean_price = bond_floating_rate.calc(RiskMeasure.CleanPrice)
dv01 = bond_floating_rate.calc(RiskMeasure.Dv01)
modified_duration = bond_floating_rate.calc(RiskMeasure.ModifiedDuration)
dollar_convexity = bond_floating_rate.calc(RiskMeasure.DollarConvexity)
time_to_maturity = bond_floating_rate.calc(RiskMeasure.TimeToMaturity)
ytm = bond_floating_rate.calc(RiskMeasure.YTM)

print('full price', full_price)
print('clean_price', clean_price)
print('dv01:', dv01)
print('modified_duration:', modified_duration)
print('dollar_convexity:', dollar_convexity)
print('time_to_maturity:', time_to_maturity)
print('ytm', ytm)

print("==============固息债（含提前偿还条款）==============")
bond_adv_redemption = BondAdvRedemption(
    comb_symbol="2180432.IB",
    value_date=value_date
)
bond_adv_redemption.resolve()
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
#
print("==============固息债（回售+调整票面利率）==============")
bond_putable_adjustable = BondPutableAdjustable(
    comb_symbol="1880106.IB",
    value_date=value_date
)
bond_putable_adjustable.resolve()
full_price = bond_putable_adjustable.calc(RiskMeasure.FullPrice)
clean_price = bond_putable_adjustable.calc(RiskMeasure.CleanPrice)
dv01 = bond_putable_adjustable.calc(RiskMeasure.Dv01)
modified_duration = bond_putable_adjustable.calc(RiskMeasure.ModifiedDuration)
dollar_convexity = bond_putable_adjustable.calc(RiskMeasure.DollarConvexity)
time_to_maturity = bond_putable_adjustable.calc(RiskMeasure.TimeToMaturity)
ytm = bond_putable_adjustable.calc(RiskMeasure.YTM)
print('full price', full_price)
print('clean_price', clean_price)
print('ytm:', ytm)
print('dv01:', dv01)
print('modified_duration:', modified_duration)
print('dollar_convexity:', dollar_convexity)
print('time_to_maturity:', time_to_maturity)

curve_data = [
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

scenario_extreme = PricingContext(
    # pricing_date='2021-12-28T00:00:00.000+0800',
    ytm=[{"symbol": "1880106.IB", "value": 0.04}],
    clean_price=[{"symbol": "1880106.IB", "value": 0.04}],
    yield_curve=[{
    "curve_code": "CBD100541",                             # 比如和债券的曲线编码对应
    "type": "forward_spot_rate",
    "forward_term": bond_putable_adjustable.forward_term,  # 必须显式传入匹配的forward_term
    "value": curve_data
}])
with scenario_extreme:
    print("修改远期的即期收益率曲线后")
    print('price', bond_putable_adjustable.calc(RiskMeasure.FullPrice))
    print(bond_putable_adjustable.forward_cv.curve_data)
    print('clean_price', bond_putable_adjustable.calc(RiskMeasure.CleanPrice))
    print('dv01:', bond_putable_adjustable.calc(RiskMeasure.Dv01))
    print('ytm:', bond_putable_adjustable.calc(RiskMeasure.YTM))
    print('modified_duration:', bond_putable_adjustable.calc(RiskMeasure.ModifiedDuration))
    print('dollar_convexity:', bond_putable_adjustable.calc(RiskMeasure.DollarConvexity))
    print('time_to_maturity:', bond_putable_adjustable.calc(RiskMeasure.TimeToMaturity))

print('price', bond_putable_adjustable.calc(RiskMeasure.FullPrice))
print(bond_putable_adjustable.forward_cv.curve_data)
print('clean_price', bond_putable_adjustable.calc(RiskMeasure.CleanPrice))
print('dv01:', bond_putable_adjustable.calc(RiskMeasure.Dv01))
print('ytm:', bond_putable_adjustable.calc(RiskMeasure.YTM))
print('modified_duration:', bond_putable_adjustable.calc(RiskMeasure.ModifiedDuration))
print('dollar_convexity:', bond_putable_adjustable.calc(RiskMeasure.DollarConvexity))
print('time_to_maturity:', bond_putable_adjustable.calc(RiskMeasure.TimeToMaturity))
