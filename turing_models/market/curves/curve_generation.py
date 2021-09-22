import datetime

import pandas as pd

from fundamental.turing_db.data import Turing
from turing_models.instruments.common import CurrencyPair, RMBIRCurveType, SpotExchangeRateType
from turing_models.market.curves import TuringDiscountCurveZeros
from turing_models.utilities.error import TuringError
from turing_models.utilities.turing_date import TuringDate
from turing_models.utilities.frequency import TuringFrequencyTypes


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
        self.nature_days_rate = self.curve.zeroRate(self.nature_days).tolist()

    def get_dates(self):
        return [day.datetime() for day in self.nature_days]

    def get_rates(self):
        return self.nature_days_rate

    def get_data_dict(self):
        nature_days = [day.datetime() for day in self.nature_days]
        return dict(zip(nature_days, self.nature_days_rate))


class FXIRCurve:
    """通过外币隐含利率曲线查询接口获取期限（年）、外币隐含利率和人民币利率，
    进而采用分段三次Hermite插值（PCHIP）方式获取逐日曲线数据"""

    def __init__(self,
                 fx_symbol: (str, CurrencyPair),  # 货币对symbol，例如：'USD/CNY'
                 # 人民币利率曲线类型（'Shibor'、'Shibor3M'、'FR007'）
                 curve_type: (str, RMBIRCurveType) = RMBIRCurveType.Shibor3M,
                 # 即期汇率类型（'central'-中间价、'average'-即期询价报价均值）
                 spot_rate_type: (
                     str, SpotExchangeRateType) = SpotExchangeRateType.Central,
                 base_date: TuringDate = TuringDate(
                     *(datetime.date.today().timetuple()[:3])),
                 number_of_days: int = 730):
        if isinstance(fx_symbol, CurrencyPair):
            self.fx_symbol = fx_symbol.value
        elif isinstance(fx_symbol, str):
            self.fx_symbol = fx_symbol
        else:
            raise TuringError('Please check the input of fx_symbol')

        if isinstance(curve_type, RMBIRCurveType):
            self.curve_type = curve_type.value
        elif isinstance(curve_type, str):
            self.curve_type = curve_type
        else:
            raise TuringError('Please check the input of curve_type')

        if isinstance(spot_rate_type, SpotExchangeRateType):
            self.spot_rate_type = spot_rate_type.value
        elif isinstance(spot_rate_type, str):
            self.spot_rate_type = spot_rate_type
        else:
            raise TuringError('Please check the input of spot_rate_type')

        self.base_date = base_date
        self.number_of_days = number_of_days
        self.fx_asset_id = Turing.get_fx_symbol_to_id(_id=self.fx_symbol)[
            'asset_id']
        self.tenors = None
        self.ccy1_cc_rates = None
        self.ccy2_cc_rates = None
        self._get_iuir_curve_date()
        self._curve_generation()

    def _get_iuir_curve_date(self):
        curves_remote = Turing.get_iuir_curve(asset_ids=[self.fx_asset_id],
                                              curve_type=self.curve_type,
                                              spot_rate_type=self.spot_rate_type)[0].get('iuir_curve_data')
        if curves_remote:
            self.set_property_list(curves_remote, "tenors", "tenor")
            self.set_property_list(
                curves_remote, "ccy1_cc_rates", "implied_interest_rate")
            self.set_property_list(
                curves_remote, "ccy2_cc_rates", "cny_implied_interest_rate")

    def set_property_list(self, curves_date, _property, key):
        _list = []
        for cu in curves_date:
            _list.append(cu.get(key))
        setattr(self, _property, _list)
        return _list

    def _curve_generation(self):
        self.ccy1_curve_gen = CurveGeneration(annualized_term=self.tenors,
                                              spot_rate=self.ccy1_cc_rates,
                                              base_date=self.base_date,
                                              frequency_type=TuringFrequencyTypes.CONTINUOUS,
                                              number_of_days=self.number_of_days)
        self.ccy2_curve_gen = CurveGeneration(annualized_term=self.tenors,
                                              spot_rate=self.ccy2_cc_rates,
                                              base_date=self.base_date,
                                              frequency_type=TuringFrequencyTypes.CONTINUOUS,
                                              number_of_days=self.number_of_days)

    def get_ccy1_curve(self):
        """获取外币利率曲线的Series"""
        return pd.Series(data=self.ccy1_curve_gen.get_rates(), index=self.ccy1_curve_gen.get_dates())

    def get_ccy2_curve(self):
        """获取人民币利率曲线的Series"""
        return pd.Series(data=self.ccy2_curve_gen.get_rates(), index=self.ccy2_curve_gen.get_dates())


class CurveAdjust:

    def __init__(self,
                 dates: list,
                 rates: list,
                 parallel_shift=None,
                 curve_shift=None,
                 pivot_point=None,
                 tenor_start=None,
                 tenor_end=None):
        self.dates = dates
        self.rates = rates
        if parallel_shift:
            self.parallel_shift = parallel_shift * 0.0001
        if curve_shift:
            self.curve_shift = curve_shift * 0.0001
        self.pivot_point = pivot_point  # 单位：年
        self.tenor_start = tenor_start  # 单位：年
        self.tenor_end = tenor_end  # 单位：年

        self.today = TuringDate(*(datetime.date.today().timetuple()[:3]))
        self.pivot_rate = None
        self.start_rate = None
        self.end_rate = None
        self.pivot_index = None
        self.start_index = None
        self.end_index = None
        self.curve_parallel_shift()

        if curve_shift:
            if not self.pivot_point:
                self.pivot_point = self.dates[0]

            if self.pivot_point > self.dates[-1] or self.pivot_point < self.dates[0]:
                raise TuringError("Please check the input of pivot_point")

            self.confirm_center_point()
            self.modify_data()
            self.get_data_index()
            self.rotate_curve()

    def curve_parallel_shift(self):
        if hasattr(self, "parallel_shift"):
            self.rates = [x + self.parallel_shift for x in self.rates]

    def confirm_center_point(self):
        dates = self.today.addYears(self.dates)
        curve = TuringDiscountCurveZeros(self.today, dates, self.rates)
        point_date = self.today.addYears(self.pivot_point)
        self.pivot_rate = curve.zeroRate(
            point_date, freqType=TuringFrequencyTypes.ANNUAL)

        if self.tenor_start:
            start_date = self.today.addYears(self.tenor_start)
            self.start_rate = curve.zeroRate(
                start_date, freqType=TuringFrequencyTypes.ANNUAL)
        else:
            self.tenor_start = self.dates[0]
            self.start_rate = self.rates[0]

        if self.tenor_end:
            end_date = self.today.addYears(self.tenor_end)
            self.end_rate = curve.zeroRate(
                end_date, freqType=TuringFrequencyTypes.ANNUAL)
        else:
            self.tenor_end = self.dates[-1]
            self.end_rate = self.rates[-1]

    def modify_data(self):
        if self.pivot_point not in self.dates:
            dates_copy = self.dates.copy()
            for i in range(len(dates_copy)):
                if dates_copy[i] > self.pivot_point:
                    break
            self.dates.insert(i, self.pivot_point)
            self.rates.insert(i, self.pivot_rate)

        if self.tenor_start not in self.dates:
            dates_copy = self.dates.copy()
            for i in range(len(dates_copy)):
                if dates_copy[i] > self.tenor_start:
                    break
            self.dates.insert(i, self.tenor_start)
            self.rates.insert(i, self.start_rate)

        if self.tenor_end not in self.dates:
            dates_copy = self.dates.copy()
            for i in range(len(dates_copy)):
                if dates_copy[i] > self.tenor_end:
                    break
            self.dates.insert(i, self.tenor_end)
            self.rates.insert(i, self.end_rate)

    def get_data_index(self):
        self.pivot_index = self.dates.index(self.pivot_point)
        self.start_index = self.dates.index(self.tenor_start)
        self.end_index = self.dates.index(self.tenor_end)

    def rotate_curve(self):
        rates_copy = self.rates.copy()
        dr = self.curve_shift / (self.end_index - self.start_index)
        for i in range(len(rates_copy)):
            if i >= self.start_index and i <= self.end_index:
                self.rates[i] = (i - self.pivot_index) * dr + rates_copy[i]
            elif i < self.start_index:
                self.rates[i] = (self.start_index -
                                 self.pivot_index) * dr + rates_copy[i]
            elif i > self.end_index:
                self.rates[i] = (self.end_index -
                                 self.pivot_index) * dr + rates_copy[i]

    def get_dates_result(self):
        return self.dates

    def get_rates_result(self):
        return self.rates

    def get_data_dict(self):
        return dict(zip(self.dates, self.rates))


if __name__ == '__main__':
    fx_curve = FXIRCurve(fx_symbol=CurrencyPair.USDCNY,
                         curve_type=RMBIRCurveType.Shibor3M,
                         spot_rate_type=SpotExchangeRateType.Central)
    print('CCY1 Curve\n', fx_curve.get_ccy1_curve())
    print('CCY2 Curve\n', fx_curve.get_ccy2_curve())
