import datetime
import traceback
from typing import Union, List, Iterable

from loguru import logger

from fundamental import ctx
from fundamental.base import Context
from fundamental.market.curves.discount_curve_zeros import TuringDiscountCurveZeros
from turing_models.instruments.common import RiskMeasure
from turing_models.utilities import TuringFrequencyTypes
from turing_models.utilities.turing_date import TuringDate
from turing_models.utilities.error import TuringError


class PriceableImpl:
    def __init__(self):
        self.ctx: Context = ctx

    def calc(self, risk_measure: Union[RiskMeasure, List[RiskMeasure]], yr=False, option_all=None):
        result: Union[float, List] = []

        try:
            if yr:
                import yuanrong
                return yuanrong.ship()(self.yr_calc.__func__).ship(self, risk_measure=risk_measure)
            if not isinstance(risk_measure, Iterable):
                result = getattr(self, risk_measure.value)() if not option_all else getattr(self, risk_measure.value)(
                    option_all)
                result = self._calc(result)
                self.__row__(risk_measure.value, round(result, 2) if result else 0)
                return result
            for risk in risk_measure:
                res = getattr(self, risk.value)()
                res = self._calc(res)
                result.append(res)
                self.__row__(risk.value, round(res, 2) if res and not isinstance(res, Iterable) else 0)
            return result
        except Exception as e:
            logger.error(str(traceback.format_exc()))
            return ""

    def yr_calc(self, risk_measure: Union[RiskMeasure, List[RiskMeasure]], option_all=None):
        result: Union[float, List] = []
        name: list = []
        try:
            name = [getattr(self, "asset_id", None), risk_measure.value]
            result = getattr(self, risk_measure.value)() if not option_all else getattr(self, risk_measure.value)(
                option_all)
            return name, result
        except Exception as e:
            logger.error(str(traceback.format_exc()))
            return name, ""

    def _calc(self, value):
        """二次计算,默认为直接返回当前值"""
        return value

    def __row__(self, ident, _value):
        """计算后对表格数据进行填充"""
        if self.__class__.__name__ == "Position" and hasattr(self.ctx, "positions_dict"):
            for key, value in self.ctx.positions_dict.items():
                if value.get('asset_id') == self.tradable.asset_id if self.tradable else "":
                    value[ident] = _value


class Instrument(PriceableImpl):
    def __init__(self):
        super().__init__()


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
        self.pivot_rate = curve.zeroRate(point_date, freqType=TuringFrequencyTypes.ANNUAL)

        if self.tenor_start:
            start_date = self.today.addYears(self.tenor_start)
            self.start_rate = curve.zeroRate(start_date, freqType=TuringFrequencyTypes.ANNUAL)
        else:
            self.tenor_start = self.dates[0]
            self.start_rate = self.rates[0]

        if self.tenor_end:
            end_date = self.today.addYears(self.tenor_end)
            self.end_rate = curve.zeroRate(end_date, freqType=TuringFrequencyTypes.ANNUAL)
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
                self.rates[i] = (self.start_index - self.pivot_index) * dr + rates_copy[i]
            elif i > self.end_index:
                self.rates[i] = (self.end_index - self.pivot_index) * dr + rates_copy[i]

    def get_dates_result(self):
        return self.dates

    def get_rates_result(self):
        return self.rates
