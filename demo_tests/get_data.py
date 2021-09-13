from fundamental.portfolio.portfolio import Portfolio
from turing_models.instruments.bond_fixed_rate import BondFixedRate
from turing_models.instruments.common import RiskMeasure

# portfolio = Portfolio(portfolio_name="模型组债券测试")
#
# portfolio.calc(
#     [RiskMeasure.Dv01, RiskMeasure.DollarDuration, RiskMeasure.DollarConvexity])
#
# portfolio.show_table()
namelist = ["BONDCN00000021",
            "BONDCN00000022",
            "BONDCN00000023",
            "BONDCN00000024",
            "BONDCN00000025",
            "BONDCN00000026",
            "BONDCN00000027",
            "BONDCN00000028",
            "BONDCN00000029",
            "BONDCN00000030",
            "BONDCN00000031",
            "BONDCN00000032",
            "BONDCN00000033",
            "BONDCN00000034",
            "BONDCN00000035",
            "BONDCN00000036",
            "BONDCN00000037",
            "BONDCN00000038"
]
result = []
for i in range(len(namelist)):
    bond_fr = BondFixedRate(asset_id=namelist[i])
    bond_fr._resolve()
    full_price = bond_fr.full_price_from_discount_curve()
    clean_price = bond_fr.clean_price_from_discount_curve()
    ytm = bond_fr.yield_to_maturity()
    duration  =  bond_fr.dollar_duration()
    convexity = bond_fr.dollar_convexity()
    result.append([namelist[i], bond_fr.frequency, full_price, clean_price, ytm, duration, convexity])
print(result)