from turing_models.utilities import *
from turing_models.products.equity import TuringEquityVanillaOption
from turing_models.market.curves import TuringDiscountCurveFlat
from turing_models.models.model_black_scholes import *
# from dgc import observables, computed
# from loguru import logger
# import sys
# logger.remove()
# handler_id = logger.add(sys.stderr, level="INFO")


# @observables
class EuBSOption:
    """
    采用bs模型对普通欧式期权定价，并计算希腊值delta
    """
    def __init__(self,
                 value_date: str,
                 num_years: float,
                 strike_price: float,
                 option_type: str,
                 stock_price: float,
                 volatility: float,
                 interest_rate: float,
                 dividend_yield: float,
                 num_options: float = 1.0):
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
        # 期权数量
        self.num_options = num_options
        # 实例化期权对象
        self.eu_call_option = TuringEquityVanillaOption(
            self.expiry_date,
            self.strike_price,
            self.option_type,
            self.num_options)
        # 股票价格
        self.stock_price = stock_price
        # 波动率
        self.volatility = volatility
        # 无风险利率
        self.interest_rate = interest_rate
        # 股息收益率
        self.dividend_yield = dividend_yield
        # 实例化bs模型对象
        self.bs_model = TuringModelBlackScholes(self.volatility)

    # @computed
    def value(self):
        """估值计算"""
        print("Calculate the value of the option")
        # 实例化曲线对象
        discount_curve = TuringDiscountCurveFlat(self.value_date,
                                                 self.interest_rate)
        dividend_curve = TuringDiscountCurveFlat(self.value_date,
                                                 self.dividend_yield)

        # 估值
        value_exact = self.eu_call_option.value(self.value_date,
                                                self.stock_price,
                                                discount_curve,
                                                dividend_curve,
                                                self.bs_model)

        return value_exact

    # @computed
    def delta(self):
        """delta计算"""
        print("Calculate the delta of the option")
        # 实例化曲线对象
        discount_curve = TuringDiscountCurveFlat(self.value_date,
                                                 self.interest_rate)
        dividend_curve = TuringDiscountCurveFlat(self.value_date,
                                                 self.dividend_yield)

        # 计算delta
        delta_exact = self.eu_call_option.delta(self.value_date,
                                                self.stock_price,
                                                discount_curve,
                                                dividend_curve,
                                                self.bs_model)

        return delta_exact


# @observables
class StockObject:
    """
    返回股票的value和delta
    """
    def __init__(self,
                 stock_price: float,
                 num_shares: int):
        """根据初始化变量建立股票对象"""
        self.stock_price = stock_price
        self.num_shares = num_shares

    # @computed
    def value(self):
        """value计算"""
        print("Calculate the value of the stock")
        value_exact = self.stock_price * self.num_shares

        return value_exact

    # @computed
    def delta(self):
        """delta计算"""
        print("Calculate the delta of the stock")
        delta_exact = 1 * self.num_shares

        return delta_exact


if __name__ == "__main__":
    # 定义期权1相关变量
    value_date1 = "2021-1-1"                              # 估值日期："%Y-%m-%d"格式
    num_years1 = 0.5                                      # 到期日期据估值日期的年数
    strike_price1 = 50                                    # 行权价
    option_type1 = "call"                                 # 欧式期权类型："call" or "put"
    stock_prices1 = [50.1, 50.2, 50.3, 50.4, 50.5, 50.6]  # 股票价格
    volatility1 = 0.20                                    # 波动率
    interest_rate1 = 0.05                                 # 无风险利率
    dividend_yield1 = 0.0                                 # 股息收益率
    # 实例化EuBSOption对象
    eu_bs_option1 = EuBSOption(value_date1,
                               num_years1,
                               strike_price1,
                               option_type1,
                               stock_price=50.0,
                               volatility=volatility1,
                               interest_rate=interest_rate1,
                               dividend_yield=dividend_yield1,
                               num_options=1)

    # 定义股票1相关变量
    stock_price2 = 10.0                                   # 股票价格
    num_shares = 1000                                     # 股票数量：股
    # 实例化StockObject对象
    stock_one = StockObject(stock_price2, num_shares)

    for stock_price in stock_prices1:
    #     eu_bs_option1.stock_price = stock_price
    #     # for _ in range(100):
    #     print('value: ', eu_bs_option1.value() + stock_one.value())
    #     print('delta: ', eu_bs_option1.delta() + stock_one.delta())

        print(eu_bs_option1.delta())
