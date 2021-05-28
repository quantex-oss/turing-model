import numpy as np

from fundamental.market.curves.discount_curve import TuringDiscountCurve

from turing_models.utilities.global_variables import gDaysInYear
from turing_models.utilities.error import TuringError
from turing_models.utilities.global_types import TuringOptionTypes, TuringKnockInTypes
from turing_models.utilities.helper_functions import checkArgumentTypes
from turing_models.utilities.turing_date import TuringDate
from turing_models.models.model import TuringModel
from turing_models.models.model_black_scholes import TuringModelBlackScholes
from turing_models.models.process_simulator import TuringProcessSimulator, TuringProcessTypes, \
     TuringGBMNumericalScheme, TuringHestonNumericalScheme


bump = 1e-4


class TuringEquitySnowballOption:

    def __init__(self,
                 expiry_date: TuringDate,
                 knock_out_price: float,
                 knock_in_price: float,
                 notional: float,
                 coupon_rate: float,
                 option_type: TuringOptionTypes,
                 coupon_annualized_flag: bool = True,
                 knock_in_type: TuringKnockInTypes = TuringKnockInTypes.RETURN,
                 knock_in_strike1: float = None,
                 knock_in_strike2: float = None,
                 participation_rate: float = 1.0):
        """用到期日期、敲出价格、敲入价格、名义本金、票面利率、期权类型、
        敲入类型、敲入执行价1、敲入执行价2、敲出观察频率和参与率创建一个雪球期权对象"""

        checkArgumentTypes(self.__init__, locals())

        if not isinstance(knock_in_type, TuringKnockInTypes):
            raise TuringError("Please check inputs for argument >> knock_in_type <<")

        if ((knock_in_strike1 is not None or knock_in_strike2 is not None) and
            knock_in_type == TuringKnockInTypes.RETURN) or \
           ((knock_in_strike1 is None or knock_in_strike2 is not None) and
            knock_in_type == TuringKnockInTypes.VANILLA) or \
           ((knock_in_strike1 is None or knock_in_strike2 is None) and
               knock_in_type == TuringKnockInTypes.SPREADS):
            raise TuringError("Mismatched strike inputs and knock_in type!")

        self._expiry_date = expiry_date
        self._k1 = knock_out_price
        self._k2 = knock_in_price
        self._notional = notional
        self._coupon_rate = coupon_rate
        self._option_type = option_type
        self._flag = coupon_annualized_flag
        self._knock_in_type = knock_in_type
        self._sk1 = knock_in_strike1
        self._sk2 = knock_in_strike2
        self._participation_rate = participation_rate

    def value(self,
              value_date: TuringDate,
              stock_price: float,
              discount_curve: TuringDiscountCurve,
              dividend_curve: TuringDiscountCurve,
              model: TuringModel,
              process_type: TuringProcessTypes = TuringProcessTypes.GBM,
              scheme: (TuringGBMNumericalScheme, TuringHestonNumericalScheme) = TuringGBMNumericalScheme.ANTITHETIC,
              num_ann_obs: int = 252,
              num_paths: int = 10000,
              seed: int = 4242):
        """用蒙特卡洛方法对雪球期权进行估值计算"""

        texp = (self._expiry_date - value_date) / gDaysInYear

        df = discount_curve.df(self._expiry_date)
        r = -np.log(df)/texp

        dq = dividend_curve.df(self._expiry_date)
        q = -np.log(dq)/texp

        vol = model._volatility

        s0 = stock_price

        model_params = (s0, r-q, vol, scheme)

        process = TuringProcessSimulator()

        # Get full set of paths
        Sall = process.getProcess(process_type, texp, model_params,
                                  num_ann_obs, num_paths, seed)

        (num_paths, num_time_steps) = Sall.shape

        out_call_sign = [False] * num_paths
        out_call_index = [False] * num_paths
        in_call_sign = [False] * num_paths
        out_put_sign = [False] * num_paths
        out_put_index = [False] * num_paths
        in_put_sign = [False] * num_paths

        # 相邻敲出观察日之间的交易日数量
        num_bus_days = int(num_ann_obs / 12)

        # 生成一个标识索引的列表
        slice_length = (self._expiry_date._y - value_date._y) * 12 + \
                       (self._expiry_date._m - value_date._m) + \
                       (self._expiry_date._d > value_date._d)
        index_list = list(range(num_time_steps))[::-num_bus_days][:slice_length][::-1]

        if self._option_type == TuringOptionTypes.SNOWBALL_CALL:
            for p in range(0, num_paths):
                out_call_sign[p] = np.any(Sall[p][::-num_bus_days][:slice_length] >= self._k1)

                if out_call_sign[p]:
                    for i in index_list:
                        if Sall[p][i] >= self._k1:
                            out_call_index[p] = i
                            break

                in_call_sign[p] = np.any(Sall[p] < self._k2)

        elif self._option_type == TuringOptionTypes.SNOWBALL_PUT:
            for p in range(0, num_paths):
                out_put_sign[p] = np.any(Sall[p][::-num_bus_days][:slice_length] <= self._k1)

                if out_put_sign[p]:
                    for i in index_list:
                        if Sall[p][i] <= self._k1:
                            out_put_index[p] = i
                            break

                in_put_sign[p] = np.any(Sall[p] > self._k2)

        ones = np.ones(num_paths)
        # list转成ndarray
        out_call_sign = np.array(out_call_sign)
        not_out_call_sign = ones - out_call_sign
        out_call_index = np.array(out_call_index)
        in_call_sign = np.array(in_call_sign)
        not_in_call_sign = ones - in_call_sign
        out_put_sign = np.array(out_put_sign)
        not_out_put_sign = ones - out_put_sign
        out_put_index = np.array(out_put_index)
        in_put_sign = np.array(in_put_sign)
        not_in_put_sign = ones - in_put_sign

        if self._option_type == TuringOptionTypes.SNOWBALL_CALL:

            payoff = out_call_sign * ((self._notional * self._coupon_rate * (out_call_index / num_ann_obs)**self._flag) *
                     np.exp(-r * out_call_index / num_ann_obs)) + not_out_call_sign * not_in_call_sign * \
                     ((self._notional * self._coupon_rate * texp**self._flag) * np.exp(-r * texp))

            if self._knock_in_type == TuringKnockInTypes.RETURN:
                payoff += not_out_call_sign * in_call_sign * \
                          (-self._notional * (1 - Sall[:, -1] / s0) *
                           self._participation_rate * np.exp(-r * texp))

            elif self._knock_in_type == TuringKnockInTypes.VANILLA:
                payoff += not_out_call_sign * in_call_sign * \
                          (-self._notional * np.maximum(self._sk1 - Sall[:, -1] / s0, 0) * \
                           self._participation_rate * texp**self._flag * np.exp(-r * texp))

            elif self._knock_in_type == TuringKnockInTypes.SPREADS:
                payoff += not_out_call_sign * in_call_sign * \
                          (-self._notional * np.maximum(self._sk1 - np.maximum(Sall[:, -1] / s0, self._sk2), 0) * \
                           self._participation_rate * texp**self._flag * np.exp(-r * texp))

        elif self._option_type == TuringOptionTypes.SNOWBALL_PUT:

            payoff = out_put_sign * ((self._notional * self._coupon_rate * (out_put_index / num_ann_obs)**self._flag) *
                     np.exp(-r * out_put_index / num_ann_obs)) + not_out_put_sign * not_in_put_sign * \
                     ((self._notional * self._coupon_rate * texp**self._flag) * np.exp(-r * texp))

            if self._knock_in_type == TuringKnockInTypes.RETURN:
                payoff += not_out_put_sign * in_put_sign * \
                          (-self._notional * (Sall[:, -1] / s0 - 1) * \
                           self._participation_rate * np.exp(-r * texp))

            elif self._knock_in_type == TuringKnockInTypes.VANILLA:
                payoff += not_out_put_sign * in_put_sign * \
                          (-self._notional * np.maximum(Sall[:, -1] / s0 - self._sk1, 0) * \
                           self._participation_rate * texp**self._flag * np.exp(-r * texp))

            elif self._knock_in_type == TuringKnockInTypes.SPREADS:
                payoff += not_out_put_sign * in_put_sign * \
                          (-self._notional * np.maximum(np.minimum(Sall[:, -1] / s0, self._sk2) - self._sk1, 0) * \
                           self._participation_rate * texp**self._flag * np.exp(-r * texp))

        v = payoff.mean()

        return v

    def delta(self,
              value_date: TuringDate,
              stock_price: float,
              discount_curve: TuringDiscountCurve,
              dividend_curve: TuringDiscountCurve,
              model):
        ''' Calculation of option delta by perturbation of stock price and
        revaluation. '''
        v = self.value(value_date, stock_price, discount_curve,
                       dividend_curve, model)

        vBumped = self.value(value_date, stock_price + bump, discount_curve,
                             dividend_curve, model)

        delta = (vBumped - v) / bump
        return delta

###############################################################################

    def gamma(self,
              value_date: TuringDate,
              stock_price: float,
              discount_curve: TuringDiscountCurve,
              dividend_curve: TuringDiscountCurve,
              model):
        ''' Calculation of option gamma by perturbation of stock price and
        revaluation. '''

        v = self.value(value_date, stock_price, discount_curve,
                       dividend_curve, model)

        vBumpedDn = self.value(value_date, stock_price - bump, discount_curve,
                               dividend_curve, model)

        vBumpedUp = self.value(value_date, stock_price + bump, discount_curve,
                               dividend_curve, model)

        gamma = (vBumpedUp - 2.0 * v + vBumpedDn) / bump / bump
        return gamma

###############################################################################

    def vega(self,
             value_date: TuringDate,
             stock_price: float,
             discount_curve: TuringDiscountCurve,
             dividend_curve: TuringDiscountCurve,
             model):
        ''' Calculation of option vega by perturbing vol and revaluation. '''

        v = self.value(value_date, stock_price, discount_curve,
                       dividend_curve, model)

        model = TuringModelBlackScholes(model._volatility + bump)

        vBumped = self.value(value_date, stock_price, discount_curve,
                             dividend_curve, model)

        vega = (vBumped - v) / bump
        return vega

###############################################################################

    def theta(self,
              value_date: TuringDate,
              stock_price: float,
              discount_curve: TuringDiscountCurve,
              dividend_curve: TuringDiscountCurve,
              model):
        ''' Calculation of option theta by perturbing value date by one
        calendar date (not a business date) and then doing revaluation and
        calculating the difference divided by dt = 1 / gDaysInYear. '''

        v = self.value(value_date, stock_price,
                       discount_curve,
                       dividend_curve, model)

        nextDate = value_date.addDays(1)

        # Need to do this carefully.

        discount_curve._valuationDate = nextDate
        bump = (nextDate - value_date) / gDaysInYear

        vBumped = self.value(nextDate, stock_price,
                             discount_curve,
                             dividend_curve, model)

        discount_curve._valuationDate = value_date
        theta = (vBumped - v) / bump
        return theta

###############################################################################

    def rho(self,
            value_date: TuringDate,
            stock_price: float,
            discount_curve: TuringDiscountCurve,
            dividend_curve: TuringDiscountCurve,
            model):
        ''' Calculation of option rho by perturbing interest rate and
        revaluation. '''

        v = self.value(value_date, stock_price, discount_curve,
                       dividend_curve, model)

        vBumped = self.value(value_date, stock_price,
                             discount_curve.bump(bump),
                             dividend_curve, model)

        rho = (vBumped - v) / bump
        return rho

    def rho_q(self,
              value_date: TuringDate,
              stock_price: float,
              discount_curve: TuringDiscountCurve,
              dividend_curve: TuringDiscountCurve,
              model):
        ''' Calculation of option rho_q by perturbing interest rate and
        revaluation. '''

        v = self.value(value_date, stock_price, discount_curve,
                       dividend_curve, model)

        vBumped = self.value(value_date, stock_price, discount_curve,
                             dividend_curve.bump(bump), model)

        rho_q = (vBumped - v) / bump
        return rho_q
