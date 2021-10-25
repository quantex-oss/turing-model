import datetime
from typing import List, Union

import pandas as pd
import QuantLib as ql

from fundamental.turing_db.data import TuringDB
from turing_models.instruments.common import CurrencyPair, DiscountCurveType, Currency
from turing_models.instruments.rates.irs import create_ibor_single_curve
from turing_models.market.curves.curve_ql import Shibor3M, FXImpliedAssetCurve, FXForwardCurve, USDLibor3M
from turing_models.market.curves.discount_curve import TuringDiscountCurve
from turing_models.market.curves.discount_curve_fx_implied import TuringDiscountCurveFXImplied
from turing_models.market.curves.discount_curve_zeros import TuringDiscountCurveZeros
from turing_models.utilities.day_count import TuringDayCountTypes
from turing_models.utilities.error import TuringError
from turing_models.utilities.frequency import TuringFrequencyTypes
from turing_models.utilities.global_types import TuringSwapTypes
from turing_models.utilities.turing_date import TuringDate


class CurveGeneration:
    def __init__(self,
                 annualized_term: list,
                 spot_rate: list,
                 base_date: TuringDate = TuringDate(
                     *(datetime.date.today().timetuple()[:3])),
                 frequency_type: TuringFrequencyTypes = TuringFrequencyTypes.ANNUAL,
                 number_of_days: int = 730):
        self.term = base_date.addYears(annualized_term)
        self.spot_rate = spot_rate
        self.base_date = base_date
        self.frequency_type = frequency_type  # 传入利率的frequency type，默认是年化的
        self.number_of_days = number_of_days  # 默认是两年的自然日：365*2
        self.curve = TuringDiscountCurveZeros(
            self.base_date, self.term, self.spot_rate, self.frequency_type)
        self._generate_nature_day()
        self._generate_nature_day_rate()

    def _generate_nature_day(self):
        """根据base_date和number_of_days生成TuringDate列表"""
        self.nature_days = []
        for i in range(1, self.number_of_days):
            day = self.base_date.addDays(i)
            self.nature_days.append(day)

    def _generate_nature_day_rate(self):
        """根据nature_days生成对应的即期收益率列表"""
        self.nature_days_rate = self.curve.zeroRate(self.nature_days, freqType=TuringFrequencyTypes.ANNUAL).tolist()

    def get_dates(self):
        return [day.datetime() for day in self.nature_days]

    def get_rates(self):
        return self.nature_days_rate

    def get_data_dict(self):
        nature_days = [day.datetime() for day in self.nature_days]
        return dict(zip(nature_days, self.nature_days_rate))


class FXIRCurve:
    def __init__(self,
                 fx_symbol: (str, CurrencyPair),  # 货币对symbol，例如：'USD/CNY'
                 value_date: TuringDate = TuringDate(*(datetime.date.today().timetuple()[:3])),
                 dom_curve_type=DiscountCurveType.Shibor3M,
                 for_curve_type = DiscountCurveType.FX_Implied,
                 number_of_days: int = 730):

        if isinstance(fx_symbol, CurrencyPair):
            fx_symbol = fx_symbol.value
        elif isinstance(fx_symbol, str):
            fx_symbol = fx_symbol
        else:
            raise TuringError('fx_symbol: (str, CurrencyPair)')

        self.dom_curve_type = dom_curve_type
        self.for_curve_type = for_curve_type

        exchange_rate = TuringDB.exchange_rate(symbol=fx_symbol, date=value_date)[fx_symbol]

        shibor_data = TuringDB.shibor_curve(date=value_date)
        shibor_swap_data = TuringDB.irs_curve(curve_type='Shibor3M', date=value_date)['Shibor3M']
        fx_swap_data = TuringDB.swap_curve(symbol=fx_symbol, date=value_date)[fx_symbol]

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
                                             fx_swap_quotes=fx_swap_data['swap_point']).discount_curve

        self.foreign_discount_curve = ForDiscountCurveGen(value_date=value_date,
                                                          exchange_rate=exchange_rate,
                                                          fx_swap_tenors=fx_swap_data['tenor'],
                                                          fx_swap_quotes=fx_swap_data['swap_point'],
                                                          domestic_discount_curve=self.domestic_discount_curve,
                                                          fx_forward_curve=fx_forward_curve,
                                                          curve_type=for_curve_type).discount_curve

        self.nature_days = []
        for i in range(1, number_of_days+1):
            day = value_date.addDays(i)
            self.nature_days.append(day)

    def get_ccy1_curve(self):
        """获取外币利率曲线的DataFrame"""
        nature_days = self.nature_days
        days = [day.datetime() for day in nature_days]
        foreign_discount_curve = self.foreign_discount_curve
        if self.for_curve_type == DiscountCurveType.FX_Implied:
            rates = []
            for expiry in nature_days:
                expiry_ql = ql.Date(expiry._d, expiry._m, expiry._y)
                rate = foreign_discount_curve.zeroRate(expiry_ql, ql.Actual365Fixed(), ql.Annual).rate()
                rates.append(rate)
        elif self.for_curve_type == DiscountCurveType.FX_Implied_tr:
            rates = foreign_discount_curve.zeroRate(nature_days, freqType=TuringFrequencyTypes.ANNUAL).tolist()
        else:
            raise TuringError('Unsupported foreign discount curve type')

        data_dict = {'date': days, 'rate': rates}
        return pd.DataFrame(data=data_dict)

    def get_ccy2_curve(self):
        """获取人民币利率曲线的DataFrame"""
        nature_days = self.nature_days
        days = [day.datetime() for day in nature_days]
        domestic_discount_curve = self.domestic_discount_curve
        if self.dom_curve_type == DiscountCurveType.Shibor3M:
            rates = []
            for expiry in nature_days:
                expiry_ql = ql.Date(expiry._d, expiry._m, expiry._y)
                rate = domestic_discount_curve.zeroRate(expiry_ql, ql.Actual365Fixed(), ql.Annual).rate()
                rates.append(rate)
        elif self.dom_curve_type == DiscountCurveType.Shibor3M_tr:
            rates = domestic_discount_curve.zeroRate(nature_days, freqType=TuringFrequencyTypes.ANNUAL).tolist()
        else:
            raise TuringError('Unsupported domestic discount curve type')

        data_dict = {'date': days, 'rate': rates}
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
                 shibor_swap_rates: List[float] = None,
                 libor_swap_tenors: List[float] = None,
                 libor_swap_origin_tenors: List[str] = None,
                 libor_swap_rates: List[float] = None,
                 d_ccy_discount: float = None,
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
                                                      TuringDayCountTypes.ACT_365F,
                                                      shibor_swap_tenors,
                                                      TuringSwapTypes.PAY,
                                                      shibor_swap_rates,
                                                      TuringFrequencyTypes.QUARTERLY,
                                                      TuringDayCountTypes.ACT_365F, 0)
        elif curve_type == DiscountCurveType.Shibor3M:
            ql.Settings.instance().evaluationDate = value_date_ql
            shibor_deposit_origin_tenors = shibor_origin_tenors[:5]
            shibor_deposit_origin_tenors[0] = '1D'  # 把'O/N'转换成'1D'，ql不支持'O/N'
            shibor_deposit_rates = shibor_rates[:5]
            # 与中金现在的模型代码兼容，故拼成同格式的DataFrame
            shibor_deposit_mkt_data = pd.DataFrame(data=shibor_deposit_rates, index=shibor_deposit_origin_tenors).T

            shibor_swap_mkt_data = pd.DataFrame(data=shibor_swap_rates, index=shibor_swap_origin_tenors).T

            # TODO: 待与中金同事确认后改为从外部传入的格式
            date1 = '2019-07-05'
            date2 = '2019-07-08'
            date3 = '2019-07-09'
            rate1 = TuringDB.shibor_curve(date=TuringDate.fromString(date1, '%Y-%m-%d'))['rate'][4]
            rate2 = TuringDB.shibor_curve(date=TuringDate.fromString(date2, '%Y-%m-%d'))['rate'][4]
            rate3 = TuringDB.shibor_curve(date=TuringDate.fromString(date3, '%Y-%m-%d'))['rate'][4]
            fixing_data = pd.DataFrame(data={'日期': [date1, date2, date3], 'Fixing': [rate1, rate2, rate3]})

            self.dom_curve = Shibor3M(shibor_deposit_mkt_data, shibor_swap_mkt_data, fixing_data, value_date_ql).curve
        elif curve_type == DiscountCurveType.FlatForward:
            ql.Settings.instance().evaluationDate = value_date_ql
            calendar = ql.China()
            daycount = ql.Actual365Fixed()
            self.dom_curve = ql.FlatForward(0, calendar, d_ccy_discount, daycount)
        elif curve_type == DiscountCurveType.USDLibor3M:
            ql.Settings.instance().evaluationDate = value_date_ql
            data_dict = {'Tenor': libor_swap_origin_tenors, 'ZeroRate': libor_swap_rates}
            libor_swap_mkt_data = pd.DataFrame(data=data_dict)
            date1 = '2021-07-28'
            date2 = '2021-07-29'
            date3 = '2021-07-30'
            date4 = '2021-08-02'
            date5 = '2021-08-03'
            date6 = '2021-08-04'
            date7 = '2021-08-05'
            date8 = '2021-08-06'
            date9 = '2021-08-09'
            date10 = '2021-08-10'
            date11 = '2021-08-11'
            date12 = '2021-08-12'
            date13 = '2021-08-13'
            date14 = '2021-08-16'
            date15 = '2021-08-17'
            date16 = '2021-08-18'
            date17 = '2021-08-19'
            date18 = '2021-08-20'
            date_list = [date1, date2, date3, date4, date5,
                         date6, date7, date8, date9, date10,
                         date11, date12, date13, date14,
                         date15, date16, date17, date18]
            rate1 = 0.001285
            rate2 = 0.0012575
            rate3 = 0.0011775
            rate4 = 0.0012375
            rate5 = 0.0012138
            rate6 = 0.0012175
            rate7 = 0.0012538
            rate8 = 0.0012838
            rate9 = 0.0012725
            rate10 = 0.0012275
            rate11 = 0.0012125
            rate12 = 0.0012475
            rate13 = 0.0012425
            rate14 = 0.001245
            rate15 = 0.0012725
            rate16 = 0.0013088
            rate17 = 0.0013075
            rate18 = 0.0012838
            rate_list = [rate1, rate2, rate3, rate4, rate5,
                         rate6, rate7, rate8, rate9, rate10,
                         rate11, rate12, rate13, rate14,
                         rate15, rate16, rate17, rate18]

            fixing_data = pd.DataFrame(data={'Date': date_list, 'Fixing': rate_list})
            self.dom_curve = USDLibor3M(libor_swap_mkt_data, fixing_data, value_date_ql)

    @property
    def discount_curve(self):
        return self.dom_curve


class FXForwardCurveGen:
    def __init__(self,
                 value_date: Union[TuringDate, ql.Date],
                 exchange_rate: float,
                 fx_swap_tenors: List[float] = None,
                 fx_swap_origin_tenors: List[str] = None,
                 fx_swap_quotes: List[float] = None):
        if isinstance(value_date, ql.Date):
            value_date_turing = TuringDate(value_date.year(), value_date.month(), value_date.dayOfMonth())
            value_date_ql = value_date
        elif isinstance(value_date, TuringDate):
            value_date_turing = value_date
            value_date_ql = ql.Date(value_date._d, value_date._m, value_date._y)
        else:
            raise TuringError('value_date: (TuringDate, ql.Date)')

        ql.Settings.instance().evaluationDate = value_date_ql
        fx_swap_origin_tenors[0: 3] = ['1D', '2D', '3D']  # 把ON', 'TN', 'SN'转换成'1D', '2D', '3D'，ql不支持ON', 'TN', 'SN'
        # 与中金现在的模型代码兼容，故拼成同格式的DataFrame
        data_dict = {'Tenor': fx_swap_origin_tenors, 'Spread': fx_swap_quotes}
        fwd_data = pd.DataFrame(data=data_dict)

        self.fx_forward_curve = FXForwardCurve(exchange_rate,
                                               fwd_data,
                                               value_date_ql,
                                               ql.UnitedStates(),
                                               ql.Actual365Fixed()).curve

    @property
    def discount_curve(self):
        return self.fx_forward_curve


class ForDiscountCurveGen:
    """生成外币折现曲线"""

    def __init__(self,
                 value_date: Union[TuringDate, ql.Date],
                 exchange_rate: float,
                 fx_swap_tenors: List[float] = None,
                 fx_swap_quotes: List[float] = None,
                 domestic_discount_curve=None,  # TODO: 类型范围暂未确定
                 fx_forward_curve=None,  # TODO: 类型范围暂未确定
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
            future_dates = value_date_turing.addYears(fx_swap_tenors)
            fwd_dfs = []
            for quote in fx_swap_quotes:
                fwd_dfs.append(exchange_rate / (exchange_rate + quote))
            fx_forward_curve = TuringDiscountCurve(value_date_turing, future_dates, fwd_dfs)
            self.for_curve = TuringDiscountCurveFXImplied(value_date_turing,
                                                          dates,
                                                          domestic_discount_curve,
                                                          fx_forward_curve)
        elif curve_type == DiscountCurveType.FX_Implied:
            ql.Settings.instance().evaluationDate = value_date_ql
            self.for_curve = FXImpliedAssetCurve(domestic_discount_curve,
                                                 fx_forward_curve,
                                                 value_date_ql,
                                                 ql.UnitedStates(),
                                                 ql.Actual365Fixed()).curve

    @property
    def discount_curve(self):
        return self.for_curve


if __name__ == '__main__':
    fx_curve = FXIRCurve(fx_symbol=CurrencyPair.USDCNY)
    print('CCY1 Curve\n', fx_curve.get_ccy1_curve())
    print('CCY2 Curve\n', fx_curve.get_ccy2_curve())
    # dom = DomDiscountCurveGen()
    # daycount = ql.Actual365Fixed()
    # expiry = ql.Date(16, 10, 2021)
    # print(dom.discount_curve.zeroRate(expiry, daycount, ql.Continuous))
    # fore = ForDiscountCurveGen(currency_pair='USD/CNY')
    # print(fore.discount_curve.zeroRate(expiry, daycount, ql.Continuous))
