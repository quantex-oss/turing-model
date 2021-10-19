# -*- coding: utf-8 -*-
"""
Created on Wed Mar 24 09:28:43 2021

@author: Dingjn
"""

import QuantLib as ql


# shibor3m
class Shibor3M:

    def __init__(self, deposit_mkt_data, swap_mkt_data, fixing_data, today):

        self.name = 'Shibor3M'
        self.deposit_mkt_data = deposit_mkt_data.copy()
        self.swap_mkt_data = swap_mkt_data.copy()
        self.fixing_data = fixing_data.copy()
        self.today = today

        self.curve, self.index = self._build(self.deposit_mkt_data, self.swap_mkt_data, self.fixing_data, self.today)

    def _build(self, deposit_mkt_data, swap_mkt_data, fixing_data, today):
        calendar = ql.China(ql.China.IB)
        convention = ql.ModifiedFollowing
        fixed_daycount = ql.Actual365Fixed()
        float_daycount = ql.Actual360()

        depo_delay = 1
        swap_delay = 1
        eom = True

        deposit_helpers = []
        for depo_tenor in deposit_mkt_data.columns:
            ix = ql.IborIndex(self.name, ql.Period(depo_tenor), depo_delay, ql.CNYCurrency(), calendar, convention, eom,
                              float_daycount)
            hp = ql.DepositRateHelper(ql.QuoteHandle(ql.SimpleQuote(deposit_mkt_data.loc[0, depo_tenor])), ix)
            deposit_helpers.append(hp)

        swap_index = ql.IborIndex(self.name, ql.Period('3M'), swap_delay, ql.CNYCurrency(), calendar, convention, eom,
                                  float_daycount)
        swap_helpers = [
            ql.SwapRateHelper(ql.QuoteHandle(ql.SimpleQuote(swap_mkt_data.loc[0, tenor])), ql.Period(tenor), calendar,
                              ql.Quarterly, convention, fixed_daycount, swap_index) for tenor in swap_mkt_data.columns]

        helpers = deposit_helpers + swap_helpers

        curve = ql.PiecewiseLinearZero(today, helpers, float_daycount)
        curve_ts = ql.YieldTermStructureHandle(curve)

        index = ql.IborIndex(self.name, ql.Period('3M'), swap_delay, ql.CNYCurrency(), calendar, convention, eom,
                             float_daycount, curve_ts)

        for i in fixing_data.index[: -1]:
            day1 = ql.DateParser.parseFormatted(fixing_data['日期'][i], '%Y-%m-%d')
            day2 = ql.DateParser.parseFormatted(fixing_data['日期'][i + 1], '%Y-%m-%d')
            f = fixing_data['Fixing'][i]
            temp_day = day1

            while temp_day < day2:
                index.addFixing(temp_day, f, True)
                temp_day = calendar.advance(temp_day, 1, ql.Days)

        temp_day = ql.DateParser.parseFormatted(fixing_data['日期'][fixing_data.index[-1]], '%Y-%m-%d')
        f = fixing_data['Fixing'][fixing_data.index[-1]]

        while temp_day <= today:
            index.addFixing(temp_day, f, True)
            temp_day = calendar.advance(temp_day, 1, ql.Days)

        return curve, index

    def tweak_keytenor(self, tenor, tenor_type, tweak):
        if tenor_type.lower() == 'deposit':
            deposit_mkt_data_tweaked = self.deposit_mkt_data.copy()
            deposit_mkt_data_tweaked.loc[0, tenor] += tweak
            curve, index = self._build(deposit_mkt_data_tweaked, self.swap_mkt_data, self.fixing_data, self.today)

            return curve, index

        elif tenor_type.lower() == 'swap':
            swap_mkt_data_tweaked = self.swap_mkt_data.copy()
            swap_mkt_data_tweaked.loc[0, tenor] += tweak

            curve, index = self._build(self.deposit_mkt_data, swap_mkt_data_tweaked, self.fixing_data, self.today)

            return curve, index

        else:
            return 'Invalid tweak type'

    def tweak_parallel(self, tweak):
        deposit_mkt_data_tweaked = self.deposit_mkt_data.copy()
        swap_mkt_data_tweaked = self.swap_mkt_data.copy()

        deposit_mkt_data_tweaked.iloc[0, :] += tweak
        swap_mkt_data_tweaked.iloc[0, :] += tweak

        curve, index = self._build(deposit_mkt_data_tweaked, swap_mkt_data_tweaked, self.fixing_data, self.today)

        return curve, index


# NDCNYDiscount

class NDCNYDiscount:

    def __init__(self, zero_data, today):
        self.name = 'NDCNYDiscount'
        self.zero_data = zero_data
        self.today = today
        self.curve = self._build(self.zero_data, self.today)

    def _build(self, zero_data, today):
        calendar = ql.China(ql.China.IB)
        convention = ql.ModifiedFollowing
        daycount = ql.Actual365Fixed()

        dates = [calendar.advance(today, ql.Period(tn)) for tn in zero_data.columns]
        zeros = [r for r in zero_data.loc[0, :]]

        return ql.ZeroCurve(dates, zeros, daycount, calendar,
                            ql.Linear(), ql.Compounded, ql.Quarterly)

    # USD Libor


class USDLibor3M:

    def __init__(self, curve_data, fixing_data, today):
        self.name = 'USDLibor3M'
        self.curve_data = curve_data.copy()
        self.fixing_data = fixing_data.copy()
        self.today = today

        self.curve, self.index = self._build(self.curve_data, self.fixing_data, self.today)

    def _build(self, curve_data, fixing_data, today):
        calendar = ql.UnitedStates()
        convention = ql.ModifiedFollowing
        daycount = ql.Thirty360()

        dates = [today] + [calendar.advance(today, ql.Period(tenor)) for tenor in curve_data['Tenor']]
        zeros = [0] + [zero for zero in curve_data['Rate']]

        curve = ql.ZeroCurve(dates, zeros, daycount, calendar)
        curve_ts = ql.YieldTermStructureHandle(curve)

        index = ql.USDLibor(ql.Period('3M'), curve_ts)

        for i in fixing_data.index[: -1]:
            date = fixing_data.loc[i, 'Date']
            fixing = fixing_data.loc[i, 'Fixing']
            index.addFixing(ql.Date(date.day, date.month, date.year), fixing)

        return curve, index

    def tweak_parallel(self, tweak):
        curve_data_tweaked = self.curve_data.copy()

        curve_data_tweaked['ZeroRate'] += tweak

        curve, index = self._build(curve_data_tweaked, self.fixing_data, self.today)

        return curve, index


# FX fwd curve
class FXForwardCurve:

    def __init__(self, spot, fwd_data, today, calendar, daycount):
        self.spot = spot
        self.fwd_data = fwd_data.copy()
        self.today = today
        self.calendar = calendar
        self.daycount = daycount
        self.curve = self._build(self.spot, self.fwd_data, self.today,
                                 self.calendar, self.daycount)

    def _build(self, spot, fwd_data, today, calendar, daycount):
        fwd_dates = [today] + [calendar.advance(today, ql.Period(fwd_data.loc[ix, ['Tenor']][0])) for
                               ix in fwd_data.index]

        fwd_points = [fwd_data.loc[ix, ['Spread']][0] for ix in fwd_data.index]
        fwd_dfs = [1] + [spot / (spot + s) for s in fwd_points]

        fwd_crv = ql.DiscountCurve(fwd_dates, fwd_dfs, daycount, calendar)
        fwd_crv.enableExtrapolation()

        return fwd_crv

    # FX implied curve


class FXImpliedAssetCurve:

    def __init__(self, denominated_crv, fx_fwd_crv, today, calendar, daycount):
        self.denominated_crv = denominated_crv
        self.fx_fwd_crv = fx_fwd_crv
        self.today = today
        self.calendar = calendar
        self.daycount = daycount

        self.curve = self._build(self.denominated_crv, self.fx_fwd_crv, self.today,
                                 self.calendar, self.daycount)

    def _build(self, denominated_crv, fx_fwd_crv, today, calendar, daycount):
        asset_dates = list(denominated_crv.dates())
        asset_dfs = [denominated_crv.discount(d) / fx_fwd_crv.discount(d) for d in asset_dates]
        asset_crv = ql.DiscountCurve(asset_dates, asset_dfs, daycount, calendar)
        asset_crv.enableExtrapolation()

        return asset_crv


