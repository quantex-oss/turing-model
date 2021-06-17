from rich import print, style
from rich.panel import Panel


def print_result(option):
    print(Panel.fit(f"price: {round(option.price(), 3)}\n"
                    f"delta: {round(option.eq_delta(), 3)}\n"
                    f"gamma: {round(option.eq_gamma(), 3)}\n"
                    f"vega: {round(option.eq_vega(), 3)}\n"
                    f"theta: {round(option.eq_theta(), 3)}\n"
                    f"rho: {round(option.eq_rho(), 3)}\n"
                    f"rho_q: {round(option.eq_rho_q(), 3)}", title="Result"))
