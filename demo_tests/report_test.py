from loguru import logger

from fundamental.market.constants import dates, rates
from fundamental.portfolio.portfolio import Portfolio
from fundamental.portfolio.position import Position
from fundamental.pricing_context import PricingContext
from fundamental.report.web_report import WhatIfReport, WhatIfReportContent
from turing_models.instruments.knockout_option import KnockOutOption
# from knockout_option import EqKnockOutOption
from turing_models.utilities.turing_date import TuringDate
from turing_models.instruments.common import RiskMeasure
from turing_models.utilities.global_types import TuringOptionType

portfolio = Portfolio(portfolio_name="CICC")

# What if we add a common KnockOutOption
knockout_option = KnockOutOption(# asset_id="OPTIONCN00000002",
                                 underlier="STOCKCN00000001",
                                 option_type=TuringOptionType.PUT,
                                 expiry=TuringDate(2021, 9, 3),
                                 strike_price=3.3,
                                 participation_rate=1.0,
                                 barrier=2.5,
                                 notional=16000000.0,
                                 rebate=0.2,
                                 value_date=TuringDate(2021, 7, 6),
                                 volatility=0.25,
                                 dividend_yield=0)
knockout_option.resolve()
print(knockout_option)
position_new_option = Position(tradable=knockout_option, quantity=-1)
portfolio.add(position_new_option)

scenario_extreme = PricingContext(pricing_date="latest",
                                  interest_rate=0.025,
                                  volatility=[
                                      {"asset_id": "STOCKCN00000007", "value": 0.2},
                                      {"asset_id": "STOCKCN00000002", "value": 0.3}
                                  ],
                                  spot=[
                                      {"asset_id": "STOCKCN00000007", "value": 30.5},
                                      {"asset_id": "STOCKCN00000002", "value": 5.3}
                                  ]
                                  )

with scenario_extreme:
    result = portfolio.calc(
        [RiskMeasure.Price, RiskMeasure.Delta,  RiskMeasure.Gamma, RiskMeasure.Vega,
         RiskMeasure.Theta, RiskMeasure.Rho, RiskMeasure.RhoQ, RiskMeasure.Dv01,
         RiskMeasure.DollarDuration, RiskMeasure.DollarConvexity])
    logger.info(result)

# Share the report
report = WhatIfReport(
    title="模拟组合1",
    username="eric.zuo",  # 环境变量中有,则会覆盖这个值
    email="eric.zuo@iquantex.com",  # 环境变量中有,则会覆盖这个值
    contents=[
        WhatIfReportContent(
            content_type="What-IF",
            name="卖出PUT期权",  # 默认值 可自定义
            scenario=scenario_extreme.scenario(),
            result={
                "pricing": {
                    "portfolio_name": portfolio.portfolio_name,
                    "price": result[0]

                },
                "positions": portfolio.positions_dict(),
            },
            comments="FI-RT在上述波动率变化下，如果加上新的PUT敲出期权对冲之后的表现"
        ),
    ],
    # url_domain="https://dev.turing.iquantex.com" # 默认已配置好,需要发送到其它域时传入
)
portfolio.show_table()
report.share()