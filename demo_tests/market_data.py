import sys
from loguru import logger

from fundamental.turing_db.data import TuringDB
from turing_models.instruments.common import YieldCurveCode, CurrencyPair
from turing_models.market.curves.curve_generation import FXIRCurve
from turing_models.market.volatility.vol_surface_generation import FXOptionImpliedVolatilitySurface
from turing_models.utilities.turing_date import TuringDate

logger.remove()
logger.add(sys.stderr, level="WARNING")

######################################################################################################################
# 相关变量定义

# 时间
today = TuringDate(2021, 12, 1)
start_date = TuringDate(2021, 8, 20)
end_date = TuringDate(2021, 8, 27)

# 债券收益率曲线编码
# CBD100032, 中债中短期票据收益率曲线(A)
curve_code1 = YieldCurveCode.CBD100032
# CBD100042, 中债中短期票据收益率曲线(A+)
curve_code2 = YieldCurveCode.CBD100042

# 货币对
currency_pair1 = CurrencyPair.USDCNY
currency_pair2 = CurrencyPair.JPYCNY

# 股票代码
symbol1 = '600067.SH'
symbol2 = '600277.SH'

######################################################################################################################
# 示例1：获取债券收益率曲线
# bond_yield_curve方法
# 参数：
# curve_code: (str, YieldCurveCode, List[str], List[YieldCurveCode])  曲线编码，支持四种格式
# date: TuringDate = None  指定获取哪天的债券收益率曲线，不传则返回数据库中的最新数据
# 返回值：为DataFrame格式，带有多级索引
# 补充说明：数据库数据还在完善中，暂时可能某些日期还没有数据，远期的即期和到期收益率曲线数据也在完善中

curves = TuringDB.bond_yield_curve(curve_code=[curve_code1, curve_code2], date=today)
curve_data = curves.loc[curve_code1.name]  # 从返回结果中获取其中一条曲线
print(curve_data)

######################################################################################################################
# 示例2：获取上海银行间同业拆放利率 shibor
# shibor_curve方法
# 参数：
# date: TuringDate = None  指定获取哪天的shibor曲线，不传则返回数据库中的最新数据
# 返回值：为DataFrame格式，单级索引

shibor = TuringDB.shibor_curve(date=today)
print(shibor)

######################################################################################################################
# 示例3：获取外汇掉期曲线
# fx_swap_curve方法
# 参数：
# symbol: (str, CurrencyPair, List[str], List[CurrencyPair])  货币对
# date: TuringDate = None  指定获取哪天的外汇掉期曲线，不传则返回数据库中的最新数据
# 返回值：为DataFrame格式，带有多级索引

curves = TuringDB.fx_swap_curve(symbol=[currency_pair1, currency_pair2], date=today)
curve_data = curves.loc[currency_pair1.value]  # 从返回结果中获取其中一条曲线
print(curve_data)

######################################################################################################################
# 示例4：获取利率互换曲线
# irs_curve方法
# 参数：
# curve_type: (str, List[str])  曲线类型，包括"FR007"、"FDR001"、"FDR007"、"LPR1Y"、"Shibor3M"、"ShiborON"、"LPR5Y"
# date: TuringDate = None  指定获取哪天的利率互换曲线，不传则返回数据库中的最新数据
# 返回值：为DataFrame格式，带有多级索引

curve_type1 = "Shibor3M"
curve_type2 = "ShiborON"  # 下一版本curve_type会支持枚举，暂时可传字符串
curves = TuringDB.irs_curve(curve_type=[curve_type1, curve_type2], date=today)
curve_data = curves.loc[curve_type1]  # 从返回结果中获取其中一条曲线
print(curve_data)

######################################################################################################################
# 示例5：获取外汇期权隐含波动率曲线
# fx_implied_volatility_curve方法
# 参数：
# symbol: (str, CurrencyPair, List[str], List[CurrencyPair])  货币对
# volatility_type: (str, list) = None  波动率类型，包括ATM、25D CALL、25D PUT、10D CALL、10D PUT、25D RR、25D BF、10D RR、10D BF
# date: TuringDate = None  指定获取哪天的外汇期权隐含波动率曲线，不传则返回数据库中的最新数据
# 返回值：为DataFrame格式，带有多级索引
# 补充说明：下一版本volatility_type会支持枚举，暂时可传字符串

volatility_type = ['ATM', '25D CALL', '25D PUT', '10D CALL', '10D PUT', '25D RR', '25D BF', '10D RR', '10D BF']
curves = TuringDB.fx_implied_volatility_curve(symbol=[currency_pair1, currency_pair2],
                                              volatility_type=volatility_type,
                                              date=today)
curve_data = curves.loc[currency_pair1.value]  # 从返回结果中获取其中一组曲线
print(curve_data)

######################################################################################################################
# 示例6：获取某一天的股票价格
# stock_price方法
# 参数：
# symbol: (str, List[str])  股票代码
# date: TuringDate = None  指定获取哪天的股票价格，不传则返回数据库中的最新数据
# 返回值：为字典格式，key为股票代码，value为股票价格

price_data = TuringDB.stock_price(symbol=[symbol1, symbol2], date=today)
stock_price = price_data[symbol1]  # 从返回结果中获取其中一只股票的价格
print(stock_price)

######################################################################################################################
# 示例7：获取一段时间的股票历史价格
# historical_stock_price方法
# 参数：
# symbol: (str, List[str])  股票代码
# start: TuringDate  开始日期
# end: TuringDate  结束日期
# 返回值：为DataFrame格式，带有多级索引
# 补充说明：日期为闭合区间[start, end]; 返回结果中的日期统一为datetime.datetime格式，便于绘图

historical_price_data = TuringDB.historical_stock_price(symbol=[symbol1, symbol2],
                                                        start=start_date,
                                                        end=end_date)
historical_stock_price = historical_price_data.loc[symbol1]  # 从返回结果中获取其中一只股票的历史价格
print(historical_stock_price)

######################################################################################################################
# 示例8：获取某一天的汇率中间价
# exchange_rate方法
# 参数：
# symbol: (str, CurrencyPair, List[str], List[CurrencyPair])  货币对
# date: TuringDate = None  指定获取哪天的汇率中间价，不传则返回数据库中的最新数据
# 返回值：为字典格式，key为货币对，value为汇率中间价
# 补充说明：部分货币对的汇率数据还在完善中，暂时可能获取不到

data = TuringDB.exchange_rate(symbol=[currency_pair1, currency_pair2],
                              date=today)
exchange_rate = data[currency_pair1.value]
print(exchange_rate)

######################################################################################################################
# 示例9：获取一段时间的汇率中间价
# historical_exchange_rate方法
# 参数：
# symbol: (str, CurrencyPair, List[str], List[CurrencyPair])  货币对
# start: TuringDate  开始日期
# end: TuringDate  结束日期
# 返回值：为DataFrame格式，带有多级索引
# 补充说明：日期为闭合区间[start, end]; 返回结果中的日期统一为datetime.datetime格式，便于绘图

data = TuringDB.historical_exchange_rate(symbol=[currency_pair1, currency_pair2],
                                         start=start_date,
                                         end=end_date)
historical_exchange_rate = data.loc[currency_pair1.value]
print(historical_exchange_rate)

######################################################################################################################
# 示例10：外汇利率期限结构
# FXIRCurve类
# 参数：
# fx_symbol: (str, CurrencyPair)  货币对
# value_date: TuringDate  估值日期，不传则默认为当日
# dom_curve_type=DiscountCurveType.Shibor3M  生成本币利率曲线的方法，不传则采用默认方法
# for_curve_type=DiscountCurveType.FX_Implied  生成外币利率曲线的方法，不传则采用默认方法
# fx_forward_curve_type=DiscountCurveType.FX_Forword  生成外汇远期曲线的方法，不传则采用默认方法
# number_of_days: int = 730  生成曲线的长度，默认为730天
# 补充说明：1、返回结果中的日期为datetime.date，下一个版本会转成带有时区的datetime.datetime格式
#         2、因目前接口数据还在完善中，暂时只支持本币为人民币

fx_curve = FXIRCurve(fx_symbol=currency_pair1)
# 获取外币利率曲线的DataFrame
foreign_curve = fx_curve.get_ccy1_curve()
domestic_curve = fx_curve.get_ccy2_curve()
print('CCY1 Curve\n', foreign_curve)
# 获取本币利率曲线的DataFrame
print('CCY2 Curve\n', domestic_curve)

######################################################################################################################
# 示例11：波动率曲面
# FXOptionImpliedVolatilitySurface类
# 参数：
# fx_symbol: (str, CurrencyPair)  货币对
# value_date: TuringDate  估值日期，不传则默认为当日
# strikes: List[float]  生成的波动率曲面的行权价 如果不传，就用exchange_rate * np.linspace(0.8, 1.2, 16)
# tenors: List[float]  生成的波动率曲面的期限（年化） 如果不传，就用[1/12, 2/12, 0.25, 0.5, 1, 2]
# volatility_function_type=TuringVolFunctionTypes.QL  生成的波动率曲面的方法，不传则采用默认方法
# 补充说明：因目前接口数据还在完善中，暂时只支持USD/CNY

fx_vol_surface = FXOptionImpliedVolatilitySurface(fx_symbol=currency_pair1)
# 获取波动率曲面的DataFrame
vol_surface_data = fx_vol_surface.get_vol_surface()
print(vol_surface_data)
