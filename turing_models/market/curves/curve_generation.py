import datetime
from typing import List, Union

import QuantLib as ql
import numpy as np
import pandas as pd

from fundamental.turing_db.data import TuringDB
from turing_models.instruments.common import CurrencyPair, DiscountCurveType, Ctx
from turing_models.instruments.rates.irs import create_ibor_single_curve
from turing_models.market.curves.curve_ql import Shibor3M, FXImpliedAssetCurve, \
     FXForwardCurve, CNYShibor3M, USDLibor3M, FXForwardCurveFQ
from turing_models.market.curves.curve_ql_real_time import FXForwardCurve as FXForwardCurveFQRealTime, \
     CNYShibor3M as CNYShibor3MRealTime, USDLibor3M as USDLibor3MRealTime
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
                    "Shibor3M": DiscountCurveType.Shibor3M,
                    "CNYShibor3M": DiscountCurveType.CNYShibor3M,
                    "USDLibor3M": DiscountCurveType.USDLibor3M,
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

    @property
    def get_shibor_swap_fixing_data(self):
        """ 参照cicc模型确定数据日期 """
        date1 = '2019-07-05'
        date2 = '2019-07-08'
        date3 = '2019-07-09'
        original_data = TuringDB.get_global_ibor_curve(ibor_type='Shibor', currency='CNY', start=date1, end=date3)
        if not original_data.empty:
            rate1 = original_data.loc[datetime.datetime.strptime(date1, '%Y-%m-%d')].loc[4, 'rate']
            rate2 = original_data.loc[datetime.datetime.strptime(date2, '%Y-%m-%d')].loc[4, 'rate']
            rate3 = original_data.loc[datetime.datetime.strptime(date3, '%Y-%m-%d')].loc[4, 'rate']
            fixing_data = {'Date': [date1, date2, date3], 'Fixing': [rate1, rate2, rate3]}
            return fixing_data
        else:
            raise TuringError(f"Cannot find shibor data")

    def generate_discount_curve(self):
        """ 根据估值日期和曲线类型调用相关接口补全所需数据后，生成对应的曲线 """
        value_date = self._value_date
        if self.curve_type == DiscountCurveType.Shibor3M:
            discount_curve = DomDiscountCurveGen(
                value_date=value_date,
                shibor_tenors=self.get_shibor_data['tenor'].tolist(),
                shibor_origin_tenors=self.get_shibor_data['origin_tenor'].tolist(),
                shibor_rates=self.get_shibor_data['rate'].tolist(),
                shibor_swap_tenors=self.get_shibor_swap_data['tenor'].tolist(),
                shibor_swap_origin_tenors=self.get_shibor_swap_data['origin_tenor'].tolist(),
                shibor_swap_rates=self.get_shibor_swap_data['average'].tolist(),
                shibor_swap_fixing_dates=self.get_shibor_swap_fixing_data['Date'],
                shibor_swap_fixing_rates=self.get_shibor_swap_fixing_data['Fixing'],
                curve_type=DiscountCurveType.Shibor3M
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
                 dom_curve_type=DiscountCurveType.Shibor3M,
                 for_curve_type=DiscountCurveType.FX_Implied,
                 fx_forward_curve_type=DiscountCurveType.FX_Forword,
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
                                             fx_swap_origin_tenors=fx_swap_data['origin_tenor'],
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
        if self.for_curve_type == DiscountCurveType.FX_Implied:
            rates = []
            dfs = []
            for expiry in nature_days:
                expiry_ql = ql.Date(expiry._d, expiry._m, expiry._y)
                rate = foreign_discount_curve.zeroRate(expiry_ql, ql.Actual365Fixed(), ql.Annual).rate()
                df = foreign_discount_curve.discount(expiry_ql)
                rates.append(rate)
                dfs.append(df)
        elif self.for_curve_type == DiscountCurveType.FX_Implied_tr:
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
        if self.dom_curve_type == DiscountCurveType.Shibor3M:
            rates = []
            dfs = []
            for expiry in nature_days:
                expiry_ql = ql.Date(expiry._d, expiry._m, expiry._y)
                rate = domestic_discount_curve.zeroRate(expiry_ql, ql.Actual365Fixed(), ql.Annual).rate()
                df = domestic_discount_curve.discount(expiry_ql)
                rates.append(rate)
                dfs.append(df)
        elif self.dom_curve_type == DiscountCurveType.Shibor3M_tr:
            rates = domestic_discount_curve.zeroRate(nature_days, freqType=FrequencyType.ANNUAL).tolist()
            dfs = domestic_discount_curve.df(nature_days).tolist()
        else:
            raise TuringError('Unsupported domestic discount curve type')

        data_dict = {'date': days, 'rate': rates, 'df': dfs}
        return pd.DataFrame(data=data_dict)


class DomDiscountCurveGen:
    """生成本币折现曲线"""

    def __init__(self,
                 value_date: Union[TuringDate, ql.Date],
                 shibor_tenors: List[float] = None,
                 shibor_origin_tenors: List[str] = None,
                 shibor_rates: List[float] = None,
                 shibor_swap_tenors: List[float] = None,
                 shibor_swap_origin_tenors: List[str] = None,
                 shibor_swap_dates: List[str] = None,
                 shibor_swap_rates: List[float] = None,
                 shibor_swap_fixing_dates: List[str] = None,
                 shibor_swap_fixing_rates: List[float] = None,
                 libor_swap_tenors: List[float] = None,
                 libor_swap_origin_tenors: List[str] = None,
                 libor_swap_dates: List[str] = None,
                 libor_swap_rates: List[float] = None,
                 libor_swap_fixing_dates: List[str] = None,
                 libor_swap_fixing_rates: List[float] = None,
                 dom_currency_discount: float = None,
                 curve_type: DiscountCurveType = DiscountCurveType.Shibor3M):
        if isinstance(value_date, ql.Date):
            value_date_turing = TuringDate(value_date.year(), value_date.month(), value_date.dayOfMonth())
            value_date_ql = value_date
        elif isinstance(value_date, TuringDate):
            value_date_turing = value_date
            value_date_ql = ql.Date(value_date._d, value_date._m, value_date._y)
        else:
            raise TuringError('value_date: (TuringDate, ql.Date)')

        if curve_type == DiscountCurveType.Shibor3M_tr:
            shibor_deposit_tenors = shibor_tenors[:5]
            shibor_deposit_rates = shibor_rates[:5]

            self.tenors = shibor_deposit_tenors + shibor_swap_tenors
            # 转成TuringDate格式
            self.dates = value_date_turing.addYears(self.tenors)
            self.dom_curve = create_ibor_single_curve(value_date_turing,
                                                      shibor_deposit_tenors,
                                                      shibor_deposit_rates,
                                                      DayCountType.ACT_365F,
                                                      shibor_swap_tenors,
                                                      TuringSwapTypes.PAY,
                                                      shibor_swap_rates,
                                                      FrequencyType.QUARTERLY,
                                                      DayCountType.ACT_365F, 0)
        elif curve_type == DiscountCurveType.Shibor3M:
            ql.Settings.instance().evaluationDate = value_date_ql
            if len(shibor_origin_tenors) >= 5:
                shibor_origin_tenors = shibor_origin_tenors[:5]
                shibor_rates = shibor_rates[:5]
            if shibor_origin_tenors[0] == 'ON':
                shibor_origin_tenors = ['1D'] + shibor_origin_tenors[1:]
            # 与中金现在的模型代码兼容，故拼成同格式的DataFrame
            shibor_deposit_mkt_data = pd.DataFrame(data=shibor_rates, index=shibor_origin_tenors).T
            shibor_swap_mkt_data = pd.DataFrame(data=shibor_swap_rates, index=shibor_swap_origin_tenors).T
            fixing_data = pd.DataFrame(data={'Date': shibor_swap_fixing_dates, 'Fixing': shibor_swap_fixing_rates})
            self.dom_curve = Shibor3M(shibor_deposit_mkt_data, shibor_swap_mkt_data, fixing_data, value_date_ql).curve
        elif curve_type == DiscountCurveType.CNYShibor3M:
            ql.Settings.instance().evaluationDate = value_date_ql
            fixing_data = pd.DataFrame(data={'Date': shibor_swap_fixing_dates, 'Fixing': shibor_swap_fixing_rates})
            if shibor_swap_dates is not None:
                shibor_swap_mkt_data = pd.DataFrame(data={'Tenor': shibor_swap_origin_tenors,
                                                          'Date': shibor_swap_dates,
                                                          'Rate': shibor_swap_rates})
                self.dom_curve = CNYShibor3MRealTime(shibor_swap_mkt_data, fixing_data, value_date_ql).curve
            else:
                shibor_swap_mkt_data = pd.DataFrame(data={'Tenor': shibor_swap_origin_tenors,
                                                          'Rate': shibor_swap_rates})
                self.dom_curve = CNYShibor3M(shibor_swap_mkt_data, fixing_data, value_date_ql).curve
        elif curve_type == DiscountCurveType.USDLibor3M:
            ql.Settings.instance().evaluationDate = value_date_ql
            fixing_data = pd.DataFrame(data={'Date': libor_swap_fixing_dates, 'Fixing': libor_swap_fixing_rates})
            if libor_swap_dates is not None:
                libor_swap_mkt_data = pd.DataFrame(data={'Tenor': libor_swap_origin_tenors,
                                                         'Date': libor_swap_dates,
                                                         'Rate': libor_swap_rates})
                self.dom_curve = USDLibor3MRealTime(libor_swap_mkt_data, fixing_data, value_date_ql).curve
            else:
                libor_swap_mkt_data = pd.DataFrame(data={'Tenor': libor_swap_origin_tenors,
                                                         'Rate': libor_swap_rates})
                self.dom_curve = USDLibor3M(libor_swap_mkt_data, fixing_data, value_date_ql).curve

    @property
    def discount_curve(self):
        return self.dom_curve


class FXForwardCurveGen:
    def __init__(self,
                 value_date: Union[TuringDate, ql.Date],
                 exchange_rate: float,
                 fx_swap_tenors: List[float] = None,
                 fx_swap_origin_tenors: List[str] = None,
                 fx_swap_dates: List[str] = None,
                 fx_swap_quotes: List[float] = None,
                 calendar: ql.Calendar = ql.UnitedStates(),
                 day_count: ql.DayCounter = ql.Actual365Fixed(),
                 curve_type: DiscountCurveType = DiscountCurveType.FX_Forword):
        if isinstance(value_date, ql.Date):
            value_date_turing = TuringDate(value_date.year(), value_date.month(), value_date.dayOfMonth())
            value_date_ql = value_date
        elif isinstance(value_date, TuringDate):
            value_date_turing = value_date
            value_date_ql = ql.Date(value_date._d, value_date._m, value_date._y)
        else:
            raise TuringError('value_date: (TuringDate, ql.Date)')

        if curve_type == DiscountCurveType.FX_Forword_tr:
            future_dates = value_date_turing.addYears(fx_swap_tenors)
            fwd_dfs = []
            for quote in fx_swap_quotes:
                fwd_dfs.append(exchange_rate / (exchange_rate + quote))
            self.fx_forward_curve = TuringDiscountCurve(value_date_turing, future_dates, fwd_dfs)
        elif curve_type == DiscountCurveType.FX_Forword:
            ql.Settings.instance().evaluationDate = value_date_ql
            if fx_swap_origin_tenors[0: 3] == ['ON', 'TN', 'SN']:
                # 把'ON', 'TN', 'SN'转换成'1D', '2D', '3D'，ql不支持ON', 'TN', 'SN'
                fx_swap_origin_tenors = ['1D', '2D', '3D'] + fx_swap_origin_tenors[3:]
            # 与中金现在的模型代码兼容，故拼成同格式的DataFrame
            data_dict = {'Tenor': fx_swap_origin_tenors, 'Spread': fx_swap_quotes}
            fwd_data = pd.DataFrame(data=data_dict)
            self.fx_forward_curve = FXForwardCurve(exchange_rate,
                                                   fwd_data,
                                                   value_date_ql,
                                                   calendar,
                                                   day_count).curve
        elif curve_type == DiscountCurveType.FX_Forword_fq:
            ql.Settings.instance().evaluationDate = value_date_ql
            # if fx_swap_origin_tenors[0: 3] == ['ON', 'TN', 'SN']:
            #     fx_swap_origin_tenors[0: 3] = ['1D', '2D',
            #                                    '3D']  # 把'ON', 'TN', 'SN'转换成'1D', '2D', '3D'，ql不支持ON', 'TN', 'SN'
            # 与中金现在的模型代码兼容，故拼成同格式的DataFrame
            if fx_swap_dates is not None:
                fwd_data = pd.DataFrame(data={'Tenor': fx_swap_origin_tenors,
                                              'Date': fx_swap_dates,
                                              'Spread': fx_swap_quotes})
                self.fx_forward_curve = FXForwardCurveFQRealTime(exchange_rate,
                                                                 fwd_data,
                                                                 value_date_ql,
                                                                 calendar,
                                                                 day_count).curve
            else:
                fwd_data = pd.DataFrame(data={'Tenor': fx_swap_origin_tenors,
                                              'Spread': fx_swap_quotes})
                self.fx_forward_curve = FXForwardCurveFQ(exchange_rate,
                                                         fwd_data,
                                                         value_date_ql,
                                                         calendar,
                                                         day_count).curve

    @property
    def discount_curve(self):
        return self.fx_forward_curve


class ForDiscountCurveGen:
    """生成外币折现曲线"""

    def __init__(self,
                 value_date: Union[TuringDate, ql.Date],
                 domestic_discount_curve=None,  # TODO: 类型范围暂未确定
                 fx_forward_curve=None,  # TODO: 类型范围暂未确定
                 calendar: ql.Calendar = ql.UnitedStates(),
                 day_count: ql.DayCounter = ql.Actual365Fixed(),
                 curve_type: DiscountCurveType = DiscountCurveType.FX_Implied):
        if isinstance(value_date, ql.Date):
            value_date_turing = TuringDate(value_date.year(), value_date.month(), value_date.dayOfMonth())
            value_date_ql = value_date
        elif isinstance(value_date, TuringDate):
            value_date_turing = value_date
            value_date_ql = ql.Date(value_date._d, value_date._m, value_date._y)
        else:
            raise TuringError('value_date: (TuringDate, ql.Date)')

        if curve_type == DiscountCurveType.FX_Implied_tr:
            dom_discount_curve_gen = DomDiscountCurveGen(value_date_turing, curve_type=DiscountCurveType.Shibor3M_tr)
            domestic_discount_curve = dom_discount_curve_gen.discount_curve
            _tenors = dom_discount_curve_gen.tenors
            dates = value_date_turing.addYears(_tenors)
            self.for_curve = TuringDiscountCurveFXImplied(value_date_turing,
                                                          dates,
                                                          domestic_discount_curve,
                                                          fx_forward_curve)
        elif curve_type == DiscountCurveType.FX_Implied:
            ql.Settings.instance().evaluationDate = value_date_ql
            self.for_curve = FXImpliedAssetCurve(domestic_discount_curve,
                                                 fx_forward_curve,
                                                 value_date_ql,
                                                 calendar,
                                                 day_count).curve

    @property
    def discount_curve(self):
        return self.for_curve


if __name__ == '__main__':
    # fx_curve = FXIRCurve(fx_symbol=CurrencyPair.USDCNY)
    # print('CCY1 Curve\n', fx_curve.get_ccy1_curve())
    # print('CCY2 Curve\n', fx_curve.get_ccy2_curve())
    # dom = DomDiscountCurveGen()
    # day_count = ql.Actual365Fixed()
    # expiry = ql.Date(27, 12, 2021)
    # period = ql.Period(0.1, ql.Years)
    # print(expiry+period)
    # dt = TuringDate(2019, 10, 1).addYears(0.1)
    # print(dom.discount_curve.zeroRate(expiry, day_count, ql.Continuous))
    # fore = ForDiscountCurveGen(currency_pair='USD/CNY')
    # print(fore.discount_curve.zeroRate(expiry, day_count, ql.Continuous))
    # curve = CurveGeneration(value_date=datetime.datetime(2021, 12, 27), curve_type='Shibor3M')
    # print(curve.get_curve())
    from fundamental.pricing_context import PricingContext
    scenario_extreme = PricingContext(
        pricing_date="latest",
        global_ibor_curve=[{
            "ibor_type": "Shibor",
            "currency": "CNY",
            "value": [
                {
                    "tenor": 0.003,
                    "origin_tenor": "ON",
                    "rate": 0.02042,
                    "change": 0.00201
                },
                {
                    "tenor": 0.021,
                    "origin_tenor": "1W",
                    "rate": 0.02115,
                    "change": 0.00024
                },
                {
                    "tenor": 0.042,
                    "origin_tenor": "2W",
                    "rate": 0.02235,
                    "change": -0.00013
                },
                {
                    "tenor": 0.083,
                    "origin_tenor": "1M",
                    "rate": 0.023,
                    "change": 0
                },
                {
                    "tenor": 0.25,
                    "origin_tenor": "3M",
                    "rate": 0.02353,
                    "change": -0.00001
                },
                {
                    "tenor": 0.5,
                    "origin_tenor": "6M",
                    "rate": 0.02472,
                    "change": -0.00002
                },
                {
                    "tenor": 0.75,
                    "origin_tenor": "9M",
                    "rate": 0.02656,
                    "change": 0
                },
                {
                    "tenor": 1,
                    "origin_tenor": "1Y",
                    "rate": 0.027,
                    "change": 0
                }
            ]
        }],
        irs_curve=[{
            "ir_type": "Shibor3M",
            "currency": "CNY",
            "value": [{
                "tenor": 0.5,
                "origin_tenor": "6M",
                "ask": 0.02485,
                "average": 0.024825,
                "bid": 0.0248
            },
                {
                    "tenor": 0.75,
                    "origin_tenor": "9M",
                    "ask": 0.0253,
                    "average": 0.02525,
                    "bid": 0.0252
                },
                {
                    "tenor": 1,
                    "origin_tenor": "1Y",
                    "ask": 0.0258,
                    "average": 0.025775,
                    "bid": 0.02575
                },
                {
                    "tenor": 2,
                    "origin_tenor": "2Y",
                    "ask": 0.027425,
                    "average": 0.027325,
                    "bid": 0.027225
                },
                {
                    "tenor": 3,
                    "origin_tenor": "3Y",
                    "ask": 0.028725,
                    "average": 0.028625,
                    "bid": 0.028525
                },
                {
                    "tenor": 4,
                    "origin_tenor": "4Y",
                    "ask": 0.029975,
                    "average": 0.029875,
                    "bid": 0.029775
                },
                {
                    "tenor": 5,
                    "origin_tenor": "5Y",
                    "ask": 0.031103,
                    "average": 0.031027,
                    "bid": 0.03095
                },
                {
                    "tenor": 7,
                    "origin_tenor": "7Y",
                    "ask": 0.033025,
                    "average": 0.0327,
                    "bid": 0.032375
                },
                {
                    "tenor": 10,
                    "origin_tenor": "10Y",
                    "ask": 0.0348,
                    "average": 0.034363,
                    "bid": 0.033925
                }
            ]
        }]
    )
    # print(curve.generate_data())
    curve = CurveGeneration(value_date="2021-12-27T00:00:00.000+0800", curve_type='Shibor3M')
    # print(curve._value_date)
    # print(curve.get_shibor_swap_data)
    # print(curve.get_curve())
    print(curve.generate_data())
    with scenario_extreme:
        # print(curve._value_date)
        # print(curve.get_shibor_swap_data)
        # print(curve.get_curve())
        print(curve.generate_data())
    # discount_curve = curve.discount_curve()
    # print(isinstance(discount_curve, ql.YieldTermStructure))
    # print(discount_curve.zeroRate(expiry, day_count, ql.Continuous).rate())
