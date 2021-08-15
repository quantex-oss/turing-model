# from datetime import datetime
#
# import matplotlib.pyplot as plt
# from matplotlib.ticker import MultipleLocator
#
# from fundamental.market.constants import dates, rates
# from fundamental.market.curves.curve_generation import CurveGeneration
#
#
# curve_gen = CurveGeneration(dates, rates)
# curve_data = curve_gen.get_data_dict()
# terms, spot_rates = list(curve_data.keys()), list(curve_data.values())
# terms = [datetime.strftime(d, '%Y-%m-%d') for d in terms]
#
# plt.figure(figsize=(20, 6))
# ax = plt.gca()
# plt.xlabel('term')
# plt.ylabel('spot rate')
# plt.title('curve')
# plt.plot(terms, spot_rates)
# plt.xticks(rotation=30)
# ax.xaxis.set_major_locator(MultipleLocator(40))  # 设置40倍数
# plt.show()

from fundamental.market.data import china_money_yield_curve as curve_data
from fundamental.market.curves.curve_generation import CurveGeneration
import pandas as pd

from turing_models.instruments.core import CurveAdjust

curve_origin = curve_data.china_money_spot_curve()
# dates：年化的期限列表
# rates：和期限对应的利率列表
# parallel_shift：曲线整体平移，单位bp，正值表示向上平移，负值相反
# curve_shift：曲线旋转，单位bp，表示曲线左端和右端分别绕pivot_point旋转的绝对值之和，正值表示右侧向上旋转，负值相反
# pivot_point：旋转中心，单位是年，若不传该参数，表示旋转中心是曲线的第一个时间点
# tenor_start：旋转起始点，单位是年，若不传该参数，表示从曲线的第一个时间点开始旋转
# tenor_end：旋转结束点，单位是年，若不传该参数，表示从曲线的最后一个时间点结束旋转
# pivot_point、tenor_start和tenor_end的范围为[原曲线的第一个时间点，原曲线的最后一个时间点]
ca = CurveAdjust(dates=curve_origin.index.tolist(),
                 rates=curve_origin.tolist(),
                 parallel_shift=1000,
                 curve_shift=1000,
                 pivot_point=1,
                 tenor_start=0.5,
                 tenor_end=1.5)
curve_data_adjusted = ca.get_data_dict()
terms_adjusted, rates_adjusted = list(curve_data_adjusted.keys()), list(curve_data_adjusted.values())
curve_gen = CurveGeneration(terms_adjusted, rates_adjusted)
curve_data = curve_gen.get_data_dict()
terms, spot_rates = list(curve_data.keys()), list(curve_data.values())
curve = pd.Series(data=spot_rates, index=terms)
print(curve)
