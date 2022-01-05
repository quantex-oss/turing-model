import datetime
from typing import List, Union

import QuantLib as ql
import numpy as np
import pandas as pd
from pydantic import BaseModel

from fundamental import PricingContext, ctx
from fundamental.turing_db.data import TuringDB
from turing_models.instruments.common import CurrencyPair, DiscountCurveType, Ctx
from turing_models.instruments.rates.irs import create_ibor_single_curve
from turing_models.market.curves.curve_ql import Shibor3M, FXImpliedAssetCurve, \
    FXForwardCurve, CNYShibor3M, USDLibor3M, FXForwardCurveFQ
from turing_models.market.curves.curve_ql_real_time import FXForwardCurve as FXForwardCurveFQRealTime, \
    CNYShibor3M as CNYShibor3MRealTime, \
    USDLibor3M as USDLibor3MRealTime
from turing_models.market.curves.discount_curve import TuringDiscountCurve
from turing_models.market.curves.discount_curve_fx_implied import TuringDiscountCurveFXImplied
from turing_models.utilities.day_count import DayCountType
from turing_models.utilities.error import TuringError
from turing_models.utilities.frequency import FrequencyType
from turing_models.utilities.global_types import TuringSwapTypes
from turing_models.utilities.helper_functions import datetime_to_turingdate, turingdate_to_qldate
from turing_models.utilities.turing_date import TuringDate


class Base(BaseModel):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def api_data(self, **kw):
        ...

    def evaluation(self, *args, **kw):
        context = kw.pop('context', '')
        try:
            if context:
                ctx.context = context
        except Exception:
            pass
        scenario = PricingContext()
        request_id = kw.pop('request_id', '')
        if request_id:
            ctx.request_id = request_id

        pricing_context = kw.pop('pricing_context', '')
        self.api_data(**kw)
        if pricing_context:
            scenario.resolve(pricing_context)
            with scenario:
                return self._generate()
        else:
            return self._generate()

    def _generate(self):
        return getattr(self, "generate_data")()


class CurveGeneration(Base, Ctx):
    value_date: Union[str, datetime.datetime] = None
    curve_type: str = None
    interval = 0.1  # 表示每隔0.1年计算一个rate

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not self.value_date:
            self.value_date = datetime.datetime.today()
        self.check_param()

    def check_param(self):
        """ 将字符串转换为枚举类型 """
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
    def _value_date(self):
        if self.ctx_pricing_date is not None:
            if isinstance(self.ctx_pricing_date, TuringDate):
                return self.ctx_pricing_date.datetime()
        return self.value_date

    @property
    def get_shibor_data(self):
        """ 从接口获取shibor """
        date = self._value_date
        original_data = TuringDB.get_global_ibor_curve(ibor_type='Shibor', currency='CNY', start=date, end=date)
        if original_data is not None:
            data = original_data.loc[date]
            return data
        else:
            raise TuringError(f"Cannot find shibor data")

    @property
    def get_shibor_swap_data(self):
        """ 从接口获取利率互换曲线 """
        date = self._value_date
        original_data = TuringDB.get_irs_curve(ir_type="Shibor3M", currency='CNY', start=date, end=date)
        if original_data is not None:
            data = original_data.loc["Shibor3M"].loc[date]
            return data
        else:
            raise TuringError("Cannot find shibor swap curve data for 'CNY'")

    @property
    def get_shibor_swap_fixing_data(self):
        """ 参照cicc模型确定数据日期 """
        date1 = '2019-07-05'
        date2 = '2019-07-08'
        date3 = '2019-07-09'
        original_data = TuringDB.get_global_ibor_curve(ibor_type='Shibor', currency='CNY', start=date1, end=date3)
        if original_data is not None:
            rate1 = original_data.loc[datetime.datetime.strptime(date1, '%Y-%m-%d')].loc[4, 'rate']
            rate2 = original_data.loc[datetime.datetime.strptime(date2, '%Y-%m-%d')].loc[4, 'rate']
            rate3 = original_data.loc[datetime.datetime.strptime(date3, '%Y-%m-%d')].loc[4, 'rate']
            fixing_data = {'Date': [date1, date2, date3], 'Fixing': [rate1, rate2, rate3]}
            return fixing_data
        else:
            raise TuringError(f"Cannot find shibor data")

    def generate_discount_curve_and_term(self):
        """ 根据估值日期和曲线类型调用相关接口补全所需数据后，生成对应的曲线 """
        value_date = self._value_date
        if self.curve_type == DiscountCurveType.Shibor3M:
            discount_curve = DomDiscountCurveGen(
                value_date=datetime_to_turingdate(value_date),
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
            term = self.get_shibor_swap_data['tenor'].iloc[-1]
            return discount_curve, term
        else:
            raise TuringError('Unsupported curve type')

    def generate_date_list(
            self,
            term,
            date_type: (datetime.datetime, ql.Date, TuringDate) = datetime.datetime
    ):
        """ 根据估值日期和传入的期限生成等间隔的时间表 """
        value_date = self._value_date
        value_date_tr = datetime_to_turingdate(value_date)
        tenors = np.arange(0, term + self.interval, self.interval)
        if date_type == datetime.datetime:
            nature_days = [value_date_tr.addYears(tenor).datetime() for tenor in tenors]
        elif date_type == ql.Date:
            nature_days = [turingdate_to_qldate(value_date_tr.addYears(tenor)) for tenor in tenors]
        elif date_type == TuringDate:
            nature_days = [value_date_tr.addYears(tenor) for tenor in tenors]
        else:
            raise TuringError('Unsupported date type')
        return tenors, nature_days

    def generate_data(self):
        """ 生成dataframe """
        discount_curve, term = self.generate_discount_curve_and_term()
        if isinstance(discount_curve, ql.YieldTermStructure):
            tenors, nature_days = self.generate_date_list(term, ql.Date)
            day_count = ql.Actual365Fixed()
            compounding = ql.Continuous
            rates = [discount_curve.zeroRate(day, day_count, compounding).rate() for day in nature_days]
            result = pd.DataFrame(data={'tenor': tenors, 'rate': rates})
            return result
        else:
            raise TuringError('Unsupported curve type')


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
    curve = CurveGeneration(value_date=datetime.datetime(2021, 12, 27), curve_type='Shibor3M')
    print(curve.generate_data())
    # discount_curve = curve.discount_curve()
    # print(isinstance(discount_curve, ql.YieldTermStructure))
    # print(discount_curve.zeroRate(expiry, day_count, ql.Continuous).rate())
