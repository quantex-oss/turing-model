from rich import print, style
from rich.panel import Panel


def print_result(option):
    print(Panel.fit(f"price: {option.price()}\n"
                    f"delta: {option.delta()}\n"
                    f"gamma: {option.gamma()}\n"
                    f"vega: {option.vega()}\n"
                    f"theta: {option.theta()}\n"
                    f"rho: {option.rho()}\n"
                    f"rho_q: {option.rho_q()}", title="Result"))
