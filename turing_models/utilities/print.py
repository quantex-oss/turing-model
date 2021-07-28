from rich import print
from rich.panel import Panel

from turing_models.instruments.common import RiskMeasure


def print_result(option):
    print(Panel.fit(f"price: {round(option.calc(RiskMeasure.Price), 3)}\n"
                    f"delta: {round(option.calc(RiskMeasure.EqDelta), 3)}\n"
                    f"gamma: {round(option.calc(RiskMeasure.EqGamma), 3)}\n"
                    f"vega: {round(option.calc(RiskMeasure.EqVega), 3)}\n"
                    f"theta: {round(option.calc(RiskMeasure.EqTheta), 3)}\n"
                    f"rho: {round(option.calc(RiskMeasure.EqRho), 3)}\n"
                    f"rho_q: {round(option.calc(RiskMeasure.EqRhoQ), 3)}", title="Result"))
