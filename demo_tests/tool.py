from rich import print, style
from rich.panel import Panel


def print_result(option):
    print(Panel.fit(f"price: {option.price()}\n"
                    f"delta: {option.eq_delta()}\n"
                    f"gamma: {option.eq_gamma()}\n"
                    f"vega: {option.eq_vega()}\n"
                    f"theta: {option.eq_theta()}\n"
                    f"rho: {option.eq_rho()}\n"
                    f"rho_q: {option.eq_rho_q()}", title="Result"))
