from fundamental.market.constants import dates, rates
from fundamental.market.curves.curve_generation import CurveGeneration


curve_gen = CurveGeneration(dates, rates)
print(curve_gen.get_dates())
print("--------------------------")
print(curve_gen.get_rates())
