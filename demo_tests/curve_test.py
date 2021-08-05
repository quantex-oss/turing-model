from datetime import datetime

import matplotlib.pyplot as plt
from matplotlib.ticker import MultipleLocator

from fundamental.market.constants import dates, rates
from fundamental.market.curves.curve_generation import CurveGeneration


curve_gen = CurveGeneration(dates, rates)
curve_data = curve_gen.get_data_dict()
terms, spot_rates = list(curve_data.keys()), list(curve_data.values())
terms = [datetime.strftime(d, '%Y-%m-%d') for d in terms]

plt.figure(figsize=(20, 6))
ax = plt.gca()
plt.xlabel('term')
plt.ylabel('spot rate')
plt.title('curve')
plt.plot(terms, spot_rates)
plt.xticks(rotation=30)
ax.xaxis.set_major_locator(MultipleLocator(40))  # 设置40倍数
plt.show()
