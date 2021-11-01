# -*- coding: utf-8 -*-
"""
Created on Fri Nov 13 15:28:22 2020

@author: Dingjn
"""

import xlrd
import math
import numpy as np
import pandas as pd
import QuantLib as ql
import matplotlib as mpl
import matplotlib.pyplot as plt
from scipy.stats import norm




class FXVanilla:
    def __init__(self, d_ccy, f_ccy, strike, start, expiry, flavor, notional):

        self.d_ccy = d_ccy
        self.d_ccy = f_ccy

        self.strike = strike
        self.start = start
        self.expiry = expiry
        self.flavor = flavor
        self.notional = notional

 # ATM
    def __getATM__(self, today, spot_f_d, fwd_crv_fd, daycount):

        dcf = daycount.yearFraction(today, self.expiry)
        atm = spot_f_d / fwd_crv_fd.discount(self.expiry)

        return atm



# NPV
    def NPV(self, today, spot_f_d, fwd_crv_fd, disc_crv, sigma_f_d, calendar, daycount, convention, vol_tweak = 0.0):

        if self.expiry <= today:
            return 0

        sigma_f_d = sigma_f_d.interp_vol(self.expiry, self.strike) + vol_tweak

        dcf = daycount.yearFraction(today, self.expiry)
        atm = self.__getATM__(today, spot_f_d, fwd_crv_fd, daycount)

        d1 = (math.log(atm / self.strike) + 0.5 * sigma_f_d ** 2 * dcf) / (sigma_f_d * math.sqrt(dcf))
        d2 = (math.log(atm / self.strike) - 0.5 * sigma_f_d ** 2 * dcf) / (sigma_f_d * math.sqrt(dcf))
        df = disc_crv.discount(self.expiry) / disc_crv.discount(today)


        if self.flavor == 'call':
            npv = df * (atm*norm.cdf(d1) - self.strike*norm.cdf(d2)) * self.notional

        else:
            npv = df * (self.strike*norm.cdf(-d2) - atm*norm.cdf(-d1)) * self.notional

        return npv



    def Delta(self, today, spot_f_d, fwd_crv_fd, disc_crv, sigma_f_d, calendar, daycount, convention, tweak = 1e-4):

        npv_up = self.NPV(today, spot_f_d + tweak, fwd_crv_fd, disc_crv, sigma_f_d, calendar, daycount, convention)

        npv_down = self.NPV(today, spot_f_d - tweak, fwd_crv_fd, disc_crv, sigma_f_d, calendar, daycount, convention)

        delta = (npv_up - npv_down) / (2 * tweak*10000)

        return delta


    def Gamma(self, today, spot_f_d, fwd_crv_fd, disc_crv, sigma_f_d, calendar, daycount, convention, tweak = 1e-4):

        delta_up = self.Delta(today, spot_f_d + tweak, fwd_crv_fd, disc_crv, sigma_f_d, calendar, daycount, convention)

        delta_down = self.Delta(today, spot_f_d - tweak, fwd_crv_fd, disc_crv, sigma_f_d, calendar, daycount, convention)

        gamma = (delta_up - delta_down) / (2 * tweak*10000)

        return gamma


    def Vega(self, today, spot_f_d, fwd_crv_fd, disc_crv, sigma_f_d, calendar, daycount, convention, tweak = 0.01):

        npv_up = self.NPV(today, spot_f_d, fwd_crv_fd, disc_crv, sigma_f_d, calendar, daycount, convention, tweak)


        npv_down = self.NPV(today, spot_f_d, fwd_crv_fd, disc_crv, sigma_f_d, calendar, daycount, convention, -tweak)

        vega = (npv_up - npv_down) / (2 * tweak * 100)

        return vega


    def Theta(self, today, spot_f_d, fwd_crv_fd, disc_crv, sigma_f_d, calendar, daycount, convention):

        npv_today = self.NPV(today, spot_f_d, fwd_crv_fd, disc_crv, sigma_f_d, calendar, daycount, convention)

        tmr = calendar.advance(today, ql.Period('1D'))

        npv_tmr = self.NPV(tmr, spot_f_d, fwd_crv_fd, disc_crv, sigma_f_d, calendar, daycount, convention)

        theta = npv_tmr - npv_today

        return theta