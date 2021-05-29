from turing_models.utilities import *
from turing_models.products.equity import TuringEquityVanillaOption
from fundamental.market.curves import TuringDiscountCurveFlat
from turing_models.models.model_black_scholes import *


class EuBSOption():
    """
    采用bs模型对普通欧式期权定价，并计算希腊值delta
    """
    def __init__(self,
                 value_date: str,
                 num_years: float,
                 strike_price: float,
                 option_type: str):
        """根据初始化变量建立期权对象"""
        # 估值日期
        self.value_date = TuringDate.fromString(value_date, "%Y-%m-%d")
        # 到期日期
        self.expiry_date = self.value_date.addYears(num_years)
        # 行权价格
        self.strike_price = strike_price
        # 期权类型
        if option_type == "call":
            self.option_type = TuringOptionTypes.EUROPEAN_CALL
        elif option_type == "put":
            self.option_type = TuringOptionTypes.EUROPEAN_PUT
        # 实例化期权对象
        self.eu_call_option = TuringEquityVanillaOption(
            self.expiry_date,
            self.strike_price,
            self.option_type)

    def value_and_delta(self,
                        stock_price,
                        volatility,
                        interest_rate,
                        dividend_yield):
        """估值计算和delta计算"""
        # 实例化曲线对象
        discount_curve = TuringDiscountCurveFlat(self.value_date, interest_rate)
        dividend_curve = TuringDiscountCurveFlat(self.value_date, dividend_yield)

        # 实例化bs模型对象
        bs_model = TuringModelBlackScholes(volatility)

        # 估值
        value_exact = self.eu_call_option.value(self.value_date,
                                                stock_price,
                                                discount_curve,
                                                dividend_curve,
                                                bs_model)

        # 计算delta
        delta_exact = self.eu_call_option.delta(self.value_date,
                                                stock_price,
                                                discount_curve,
                                                dividend_curve,
                                                bs_model)

        return value_exact, delta_exact


if __name__ == "__main__":
    # 定义相关变量
    value_date = "2021-1-1"  # 估值日期："%Y-%m-%d"格式
    num_years = 0.5          # 到期日期据估值日期的年数
    strike_price = 50        # 行权价
    option_type = "call"     # 欧式期权类型："call" or "put"
    # 实例化EuBSOption对象
    eu_bs_option = EuBSOption(value_date,
                              num_years,
                              strike_price,
                              option_type)

    stock_prices = [50.1, 50.2, 50.3, 50.4, 50.5, 50.6]         # 股票价格
    volatility = 0.20                                           # 波动率
    interest_rate = 0.05                                        # 无风险利率
    dividend_yield = 0.0                                        # 股息收益率

    for stock_price in stock_prices:
        print(eu_bs_option.value_and_delta(stock_price,
                                           volatility,
                                           interest_rate,
                                           dividend_yield))
