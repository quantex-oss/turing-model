from loguru import logger

from fundamental.market.constants import dates, rates
from fundamental.portfolio.portfolio import Portfolio
from fundamental.portfolio.position import Position
from fundamental.pricing_context import PricingContext
from fundamental.report.web_report import WhatIfReport, WhatIfReportContent
from turing_models.instruments.knockout_option import KnockOutOption
from volatility.knockout_option import EqKnockOutOption
from turing_models.utilities.turing_date import TuringDate
from turing_models.instruments.common import RiskMeasure
from turing_models.utilities.global_types import TuringKnockOutTypes

portfolio = Portfolio(portfolio_name="FI-RT")

# Define Scenario
scenario_extreme = PricingContext(pricing_date="latest",
                                  interest_rate=0.02,
                                  volatility=[
                                      {"asset_id": "STOCKCN00000007", "value": 0.2},
                                      {"asset_id": "STOCKCN00000002", "value": 0.3}
                                  ],
                                  spot=[
                                      {"asset_id": "STOCKCN00000007", "value": 30.5},
                                      {"asset_id": "STOCKCN00000002", "value": 5.3}
                                  ]
                                  )

# Calc Portfolio Risk Measures with Scenario
with scenario_extreme:
    result = portfolio.calc(
        [
            RiskMeasure.Price, RiskMeasure.Delta, RiskMeasure.DeltaSum, RiskMeasure.GammaSum, RiskMeasure.VegaSum,
            RiskMeasure.ThetaSum, RiskMeasure.RhoSum, RiskMeasure.RhoQSum, RiskMeasure.Gamma, RiskMeasure.Vega, RiskMeasure.Theta, RiskMeasure.Rho,
            RiskMeasure.RhoQ, RiskMeasure.Dv01, RiskMeasure.DollarConvexity, RiskMeasure.DollarDuration
        ]
    )
    what_if_content = WhatIfReportContent(
        content_type="What-IF",
        name="FI-RT的极端情况",  # 默认值 可自定义
        scenario=scenario_extreme.scenario(),
        result={
            "pricing": {
                "portfolio_name": portfolio.portfolio_name,
                "price": result[0]

            },
            "positions": portfolio.positions_dict(),
        },
        comments="FI-RT在利率不变，但相关股票的波动率变化较大的情况下的表现"
    )
    logger.info(result[0])

# What if we add a common KnockOutOption
knockout_option = KnockOutOption(asset_id="OPTIONCN00000002",
                                 underlier="STOCKCN00000002",
                                 knock_out_type=TuringKnockOutTypes.UP_AND_OUT_CALL,
                                 expiry=TuringDate(2021, 9, 3),
                                 strike_price=11.3,
                                 participation_rate=1.0,
                                 barrier=13,
                                 notional=1000000,
                                 rebate=0.2,
                                 value_date=TuringDate(2021, 7, 6),
                                 volatility=0.1,
                                 dividend_yield=0)
knockout_option.resolve()

position_new_option = Position(tradable=knockout_option, quantity=-1)
portfolio.add(position_new_option)

with scenario_extreme:
    result_new_option = portfolio.calc(
        [
            RiskMeasure.Price, RiskMeasure.Delta, RiskMeasure.DeltaSum, RiskMeasure.GammaSum, RiskMeasure.VegaSum,
            RiskMeasure.ThetaSum, RiskMeasure.RhoSum, RiskMeasure.RhoQSum, RiskMeasure.Gamma, RiskMeasure.Vega, RiskMeasure.Theta, RiskMeasure.Rho,
            RiskMeasure.RhoQ, RiskMeasure.Dv01, RiskMeasure.DollarConvexity, RiskMeasure.DollarDuration
        ]
    )
    what_if_content_new_option = WhatIfReportContent(
        content_type="What-IF",
        name="",  # 默认值 可自定义
        scenario=scenario_extreme.scenario(),
        result={
            "pricing": {
                "portfolio_name": portfolio.portfolio_name,
                "price": result[0]

            },
            "positions": portfolio.positions_dict(),
        },
        comments="FI-RT在上述波动率变化下，如果加上新的敲出期权对冲之后的表现"
    )
    logger.info(result_new_option[0])

# What if we add an new Option with customized pricing method
knockout_option_eq = EqKnockOutOption(asset_id="OPTIONCN00000002",
                                      underlier="STOCKCN00000002",
                                      knock_out_type=TuringKnockOutTypes.UP_AND_OUT_CALL,
                                      expiry=TuringDate(2021, 9, 3),
                                      strike_price=11.3,
                                      participation_rate=1.0,
                                      barrier=13,
                                      notional=1000000,
                                      rebate=0.2,
                                      value_date=TuringDate(2021, 7, 6),
                                      volatility=0.1,
                                      dividend_yield=0)
knockout_option_eq.resolve()
position_new_option_new_pricing = Position(
    tradable=knockout_option_eq, quantity=-1)
portfolio.add(position_new_option_new_pricing)

with scenario_extreme:
    result_new_option_new_pricing = portfolio.calc(
        [
            RiskMeasure.Price, RiskMeasure.Delta, RiskMeasure.DeltaSum, RiskMeasure.GammaSum, RiskMeasure.VegaSum,
            RiskMeasure.ThetaSum, RiskMeasure.RhoSum, RiskMeasure.RhoQSum, RiskMeasure.Gamma, RiskMeasure.Vega, RiskMeasure.Theta, RiskMeasure.Rho,
            RiskMeasure.RhoQ, RiskMeasure.Dv01, RiskMeasure.DollarConvexity, RiskMeasure.DollarDuration
        ]
    )
    what_if_content_new_option_new_pricing = WhatIfReportContent(
        content_type="What-IF",
        name=portfolio.portfolio_name,  # 默认值 可自定义
        scenario=scenario_extreme.scenario(),
        result={
            "pricing": {
                "portfolio_name": portfolio.portfolio_name,
                "price": result[0]

            },
            "positions": portfolio.positions_dict(),
        },
        comments="I have some comments to make in relation to this matter."
    )
    logger.info(result_new_option_new_pricing[0])

# Share the report
report = WhatIfReport(
    title="Test report",
    username="eric.zuo",  # 环境变量中有,则会覆盖这个值
    email="eric.zuo@iquantex.com",  # 环境变量中有,则会覆盖这个值
    contents=[
        what_if_content,
        what_if_content_new_option,
        what_if_content_new_option_new_pricing
    ],
    # url_domain="https://dev.turing.iquantex.com" # 默认已配置好,需要发送到其它域时传入
)
portfolio.show_table()
# report.share()


