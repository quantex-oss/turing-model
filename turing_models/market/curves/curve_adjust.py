import datetime

import pandas as pd

from turing_models.market.curves.discount_curve_zeros import TuringDiscountCurveZeros
from turing_models.utilities.frequency import FrequencyType
from turing_models.utilities.error import TuringError
from turing_models.utilities.turing_date import TuringDate


class CurveAdjustmentImpl:

    def __init__(self,
                 curve_data: pd.DataFrame = None,
                 parallel_shift=None,
                 curve_shift=None,
                 pivot_point=None,
                 tenor_start=None,
                 tenor_end=None,
                 value_date=TuringDate(*(datetime.date.today().timetuple()[:3]))):
        self.tenors = curve_data['tenor'].tolist()
        self.rates = curve_data['rate'].tolist()
        if parallel_shift:
            self.parallel_shift = parallel_shift * 0.0001
        if curve_shift:
            self.curve_shift = curve_shift * 0.0001
        self.pivot_point = pivot_point  # 单位：年
        self.tenor_start = tenor_start  # 单位：年
        self.tenor_end = tenor_end  # 单位：年

        self.today = value_date
        self.pivot_rate = None
        self.start_rate = None
        self.end_rate = None
        self.pivot_index = None
        self.start_index = None
        self.end_index = None
        self.curve_parallel_shift()

        if curve_shift:
            if not self.pivot_point:
                self.pivot_point = self.tenors[0]

            if self.pivot_point > self.tenors[-1] or self.pivot_point < self.tenors[0]:
                raise TuringError("Please check the input of pivot_point")

            self.confirm_center_point()
            self.modify_data()
            self.get_data_index()
            self.rotate_curve()

    def curve_parallel_shift(self):
        if hasattr(self, "parallel_shift"):
            self.rates = [x + self.parallel_shift for x in self.rates]

    def confirm_center_point(self):
        dates = self.today.addYears(self.tenors)
        curve = TuringDiscountCurveZeros(self.today, dates, self.rates)
        point_date = self.today.addYears(self.pivot_point)
        self.pivot_rate = curve.zeroRate(
            point_date, freqType=FrequencyType.ANNUAL)

        if self.tenor_start:
            start_date = self.today.addYears(self.tenor_start)
            self.start_rate = curve.zeroRate(
                start_date, freqType=FrequencyType.ANNUAL)
        else:
            self.tenor_start = self.tenors[0]
            self.start_rate = self.rates[0]

        if self.tenor_end:
            end_date = self.today.addYears(self.tenor_end)
            self.end_rate = curve.zeroRate(
                end_date, freqType=FrequencyType.ANNUAL)
        else:
            self.tenor_end = self.tenors[-1]
            self.end_rate = self.rates[-1]

    def modify_data(self):
        if self.pivot_point not in self.tenors:
            dates_copy = self.tenors.copy()
            for i in range(len(dates_copy)):
                if dates_copy[i] > self.pivot_point:
                    break
            self.tenors.insert(i, self.pivot_point)
            self.rates.insert(i, self.pivot_rate)

        if self.tenor_start not in self.tenors:
            dates_copy = self.tenors.copy()
            for i in range(len(dates_copy)):
                if dates_copy[i] > self.tenor_start:
                    break
            self.tenors.insert(i, self.tenor_start)
            self.rates.insert(i, self.start_rate)

        if self.tenor_end not in self.tenors:
            dates_copy = self.tenors.copy()
            for i in range(len(dates_copy)):
                if dates_copy[i] > self.tenor_end:
                    self.tenors.insert(i, self.tenor_end)
                    self.rates.insert(i, self.end_rate)
                    return
            self.tenors.append(self.tenor_end)
            self.rates.append(self.end_rate)


    def get_data_index(self):
        self.pivot_index = self.tenors.index(self.pivot_point)
        self.start_index = self.tenors.index(self.tenor_start)
        self.end_index = self.tenors.index(self.tenor_end)

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
        return self.tenors

    def get_rates_result(self):
        return self.rates

    def get_curve_data(self):
        return pd.DataFrame(data={'tenor': self.tenors, 'rate': self.rates})

    def get_curve_result(self):
        dates = self.today.addYears(self.tenors)
        return TuringDiscountCurveZeros(self.today, dates, self.rates)
