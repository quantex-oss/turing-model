import datetime
from typing import List, Union

import QuantLib as ql
import numpy as np
import pandas as pd

from fundamental.turing_db.data import TuringDB
from turing_models.instruments.common import CurrencyPair, DiscountCurveType, Ctx
from turing_models.instruments.rates.irs import create_ibor_single_curve
from turing_models.market.curves.discount_curve import TuringDiscountCurve
from turing_models.market.curves.discount_curve_fx_implied import TuringDiscountCurveFXImplied
from turing_models.utilities.day_count import DayCountType
from turing_models.utilities.error import TuringError
from turing_models.utilities.frequency import FrequencyType
from turing_models.utilities.global_types import TuringSwapTypes
from turing_models.utilities.helper_classes import Base
from turing_models.utilities.helper_functions import turingdate_to_qldate, to_datetime, \
     to_turing_date
from turing_models.utilities.turing_date import TuringDate


class CurveGeneration(Base, Ctx):
    value_date: Union[str, datetime.datetime, datetime.date] = datetime.datetime.today()
    curve_type: Union[str, DiscountCurveType] = DiscountCurveType.Shibor3M
    interval = 0.1  # 表示每隔0.1年计算一个rate

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.check_param()

    def check_param(self):
        """ 将字符串转换为枚举类型、时间转换为datetime.datetime格式 """
        if self.value_date is not None:
            self.value_date = to_datetime(self.value_date)
        if self.curve_type is not None:
            if not isinstance(self.curve_type, DiscountCurveType):
                rules = {
                    "Shibor3M": DiscountCurveType.Shibor3M_tr
                }
                self.curve_type = rules.get(self.curve_type,
                                            TuringError('Please check the input of curve_type'))
                if isinstance(self.curve_type, TuringError):
                    raise self.curve_type

    @property
    def _original_value_date(self):
        if self.ctx_pricing_date is not None:
            # 目前ctx_pricing_date有两个格式：TuringDate和latest
            if isinstance(self.ctx_pricing_date, TuringDate):
                # 接口支持用datetime.datetime格式请求数据
                return to_datetime(self.ctx_pricing_date)
            else:
                # 如果是latest，则保持
                return self.ctx_pricing_date
        return self.value_date

    @property
    def _value_date(self):
        # 将latest转成TuringDate
        return to_turing_date(self._original_value_date)

    @property
    def get_shibor_data(self):
        """ 从接口获取shibor """
        shibor_data = self.ctx_global_ibor_curve(ibor_type='Shibor', currency='CNY')
        if shibor_data is not None:
            return pd.DataFrame(shibor_data)
        date = self._original_value_date
        original_data = TuringDB.get_global_ibor_curve(ibor_type='Shibor', currency='CNY', start=date, end=date)
        if not original_data.empty:
            return original_data
        else:
            raise TuringError(f"Cannot find shibor data")

    @property
    def get_shibor_swap_data(self):
        """ 从接口获取利率互换曲线 """
        irs_curve = self.ctx_irs_curve(ir_type="Shibor3M", currency='CNY')
        if irs_curve is not None:
            return pd.DataFrame(irs_curve)
        date = self._original_value_date
        original_data = TuringDB.get_irs_curve(ir_type="Shibor3M", currency='CNY', start=date, end=date)
        if not original_data.empty:
            return original_data.loc["Shibor3M"]
        else:
            raise TuringError("Cannot find shibor swap curve data for 'CNY'")

    def generate_discount_curve(self):
        """ 根据估值日期和曲线类型调用相关接口补全所需数据后，生成对应的曲线 """
        value_date = self._value_date
        if self.curve_type == DiscountCurveType.Shibor3M_tr:
            discount_curve = DomDiscountCurveGen(
                value_date=value_date,
                shibor_tenors=self.get_shibor_data['tenor'].tolist(),
                shibor_rates=self.get_shibor_data['rate'].tolist(),
                shibor_swap_tenors=self.get_shibor_swap_data['tenor'].tolist(),
                shibor_swap_rates=self.get_shibor_swap_data['average'].tolist(),
                curve_type=DiscountCurveType.Shibor3M_tr
            ).discount_curve
        else:
            raise TuringError('Unsupported curve type')
        return discount_curve

    def pair_discount_curve_and_term(self):
        """ 根据曲线类型，将生成的曲线与期限对应 """
        discount_curve = self.generate_discount_curve()
        if self.curve_type == DiscountCurveType.Shibor3M:
            term = self.get_shibor_swap_data['tenor'].iloc[-1]
        else:
            raise TuringError('Unsupported curve type')
        return discount_curve, term

    def generate_date_list(
            self,
            term,
            date_type: (datetime.datetime, ql.Date, TuringDate) = datetime.datetime
    ):
        """ 根据估值日期和传入的期限生成等间隔的时间表 """
        value_date = self._value_date
        tenors = np.around(np.arange(0, term + self.interval, self.interval), 2)
        if date_type == datetime.datetime:
            nature_days = [value_date.addYears(tenor).datetime() for tenor in tenors]
        elif date_type == ql.Date:
            nature_days = [turingdate_to_qldate(value_date.addYears(tenor)) for tenor in tenors]
        elif date_type == TuringDate:
            nature_days = [value_date.addYears(tenor) for tenor in tenors]
        else:
            raise TuringError('Unsupported date type')
        return tenors, nature_days

    def get_curve(self):
        """ 生成dataframe """
        discount_curve, term = self.pair_discount_curve_and_term()
        if isinstance(discount_curve, ql.YieldTermStructure):
            tenors, nature_days = self.generate_date_list(term, ql.Date)
            day_count = ql.Actual365Fixed()
            compounding = ql.Continuous
            rates = np.around([discount_curve.zeroRate(day, day_count, compounding).rate() for day in nature_days], 6)
            result = pd.DataFrame(data={'tenor': tenors, 'rate': rates})
            return result
        else:
            raise TuringError('Unsupported curve type')

    def generate_data(self):
        """ 提供给定价服务调用 """
        original_data = self.get_curve()
        curve_data = []
        tenors = original_data['tenor'].tolist()
        rates = original_data['rate'].tolist()
        length = len(tenors)
        for i in range(length):
            curve_data.append({"tenor": tenors[i], 'rate': rates[i]})
        return curve_data


class FXIRCurve:
    def __init__(self,
                 fx_symbol: (str, CurrencyPair),  # 货币对symbol，例如：'USD/CNY'
                 value_date: TuringDate = TuringDate(*(datetime.date.today().timetuple()[:3])),
                 dom_curve_type=DiscountCurveType.Shibor3M_tr,
                 for_curve_type=DiscountCurveType.FX_Implied_tr,
                 fx_forward_curve_type=DiscountCurveType.FX_Forword_tr,
                 number_of_days: int = 730):

        if isinstance(fx_symbol, CurrencyPair):
            fx_symbol = fx_symbol.value
        elif isinstance(fx_symbol, str):
            pass
        else:
            raise TuringError('fx_symbol: (str, CurrencyPair)')

        self.dom_curve_type = dom_curve_type
        self.for_curve_type = for_curve_type

        exchange_rate = TuringDB.exchange_rate(symbol=fx_symbol, date=value_date)[fx_symbol]

        shibor_data = TuringDB.shibor_curve(date=value_date, df=False)
        shibor_swap_data = TuringDB.irs_curve(curve_type='Shibor3M', date=value_date, df=False)['Shibor3M']
        fx_swap_data = TuringDB.fx_swap_curve(symbol=fx_symbol, date=value_date, df=False)[fx_symbol]

        self.domestic_discount_curve = DomDiscountCurveGen(value_date=value_date,
                                                           shibor_tenors=shibor_data['tenor'],
                                                           shibor_origin_tenors=shibor_data['origin_tenor'],
                                                           shibor_rates=shibor_data['rate'],
                                                           shibor_swap_tenors=shibor_swap_data['tenor'],
                                                           shibor_swap_origin_tenors=shibor_swap_data['origin_tenor'],
                                                           shibor_swap_rates=shibor_swap_data['average'],
                                                           curve_type=dom_curve_type).discount_curve

        fx_forward_curve = FXForwardCurveGen(value_date=value_date,
                                             exchange_rate=exchange_rate,
                                             fx_swap_tenors=fx_swap_data['tenor'],
                                             fx_swap_quotes=fx_swap_data['swap_point'],
                                             curve_type=fx_forward_curve_type).discount_curve

        self.foreign_discount_curve = ForDiscountCurveGen(value_date=value_date,
                                                          domestic_discount_curve=self.domestic_discount_curve,
                                                          fx_forward_curve=fx_forward_curve,
                                                          curve_type=for_curve_type).discount_curve

        self.nature_days = []
        for i in range(1, number_of_days + 1):
            day = value_date.addDays(i)
            self.nature_days.append(day)

    def get_ccy1_curve(self):
        """获取外币利率曲线的DataFrame"""
        nature_days = self.nature_days
        days = [day.datetime() for day in nature_days]
        foreign_discount_curve = self.foreign_discount_curve
        if self.for_curve_type == DiscountCurveType.FX_Implied_tr:
            rates = foreign_discount_curve.zeroRate(nature_days, freqType=FrequencyType.ANNUAL).tolist()
            dfs = foreign_discount_curve.df(nature_days).tolist()
        else:
            raise TuringError('Unsupported foreign discount curve type')

        data_dict = {'date': days, 'rate': rates, 'df': dfs}
        return pd.DataFrame(data=data_dict)

    def get_ccy2_curve(self):
        """获取人民币利率曲线的DataFrame"""
        nature_days = self.nature_days
        days = [day.datetime() for day in nature_days]
        domestic_discount_curve = self.domestic_discount_curve
        if self.dom_curve_type == DiscountCurveType.Shibor3M_tr:
            rates = domestic_discount_curve.zeroRate(nature_days, freqType=FrequencyType.ANNUAL).tolist()
            dfs = domestic_discount_curve.df(nature_days).tolist()
        else:
            raise TuringError('Unsupported domestic discount curve type')

        data_dict = {'date': days, 'rate': rates, 'df': dfs}
        return pd.DataFrame(data=data_dict)


class DomDiscountCurveGen:
    """生成本币折现曲线"""

    def __init__(self,
                 value_date: TuringDate,
                 shibor_tenors: List[float] = None,
                 shibor_rates: List[float] = None,
                 shibor_swap_tenors: List[float] = None,
                 shibor_swap_rates: List[float] = None,
                 curve_type: DiscountCurveType = DiscountCurveType.Shibor3M_tr):

        if curve_type == DiscountCurveType.Shibor3M_tr:
            shibor_deposit_tenors = shibor_tenors[:5]
            shibor_deposit_rates = shibor_rates[:5]

            self.tenors = shibor_deposit_tenors + shibor_swap_tenors
            # 转成TuringDate格式
            self.dates = value_date.addYears(self.tenors)
            self.dom_curve = create_ibor_single_curve(value_date,
                                                      shibor_deposit_tenors,
                                                      shibor_deposit_rates,
                                                      DayCountType.ACT_365F,
                                                      shibor_swap_tenors,
                                                      TuringSwapTypes.PAY,
                                                      shibor_swap_rates,
                                                      FrequencyType.QUARTERLY,
                                                      DayCountType.ACT_365F, 0)

    @property
    def discount_curve(self):
        return self.dom_curve


class FXForwardCurveGen:
    def __init__(self,
                 value_date: TuringDate,
                 exchange_rate: float,
                 fx_swap_tenors: List[float] = None,
                 fx_swap_quotes: List[float] = None,
                 curve_type: DiscountCurveType = DiscountCurveType.FX_Forword_tr):

        if curve_type == DiscountCurveType.FX_Forword_tr:
            future_dates = value_date.addYears(fx_swap_tenors)
            fwd_dfs = []
            for quote in fx_swap_quotes:
                fwd_dfs.append(exchange_rate / (exchange_rate + quote))
            self.fx_forward_curve = TuringDiscountCurve(value_date, future_dates, fwd_dfs)

    @property
    def discount_curve(self):
        return self.fx_forward_curve


class ForDiscountCurveGen:
    """生成外币折现曲线"""

    def __init__(self,
                 value_date: TuringDate,
                 domestic_discount_curve=None,  # TODO: 类型范围暂未确定
                 fx_forward_curve=None,  # TODO: 类型范围暂未确定
                 curve_type: DiscountCurveType = DiscountCurveType.FX_Implied_tr):

        if curve_type == DiscountCurveType.FX_Implied_tr:
            dates = list(domestic_discount_curve._dfDates)
            self.for_curve = TuringDiscountCurveFXImplied(value_date,
                                                          dates,
                                                          domestic_discount_curve,
                                                          fx_forward_curve)

    @property
    def discount_curve(self):
        return self.for_curve
