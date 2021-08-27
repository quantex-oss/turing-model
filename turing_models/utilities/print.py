from rich import print
from rich.panel import Panel

from turing_models.instruments.common import RiskMeasure


def print_result(option):
    print(Panel.fit(f"price: {round(option.run(RiskMeasure.Price), 3)}\n"
                    f"delta: {round(option.run(RiskMeasure.EqDelta), 3)}\n"
                    f"gamma: {round(option.run(RiskMeasure.EqGamma), 3)}\n"
                    f"vega: {round(option.run(RiskMeasure.EqVega), 3)}\n"
                    f"theta: {round(option.run(RiskMeasure.EqTheta), 3)}\n"
                    f"rho: {round(option.run(RiskMeasure.EqRho), 3)}\n"
                    f"rho_q: {round(option.run(RiskMeasure.EqRhoQ), 3)}", title="Result"))
