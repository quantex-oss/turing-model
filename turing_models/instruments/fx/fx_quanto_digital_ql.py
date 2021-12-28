# -*- coding: utf-8 -*-
"""
Created on Tue Sep 14 14:12:19 2021

@author: Dingjn
"""

import math
from scipy.stats import norm

from turing_models.utilities.error import TuringError


class FXQuantoDigitalQL:
    def __init__(self, f_ccy, d_ccy, q_ccy, strike, accrualStart, accrualEnd, obs_start, obs_end, flavor, notional,
                 coupon_rate, tradeDirection):
        self.f_ccy = f_ccy
        self.d_ccy = d_ccy
        self.q_ccy = q_ccy
        self.strike = strike
        self.accrualStart = accrualStart
        self.accrualEnd = accrualEnd
        self.obs_start = obs_start
        self.obs_end = obs_end
        self.flavor = flavor
        self.notional = notional
        self.coupon_rate = coupon_rate
        self.tradeDirection = tradeDirection.lower()

    # quanto-adjusted ATM
    def __getATM__(self, today, spot_f_d, fwd_crv_fd,
                   sigma_f_d, sigma_d_q, rho_fd_dq, daycount):

        dcf = daycount.yearFraction(today, self.obs_end)
        quanto_adj = math.exp(-rho_fd_dq * sigma_f_d * sigma_d_q * dcf)

        atm_adj = spot_f_d / fwd_crv_fd.discount(self.obs_end) * quanto_adj

        return atm_adj

    # NPV
    def NPV(self, today, spot_f_d, spot_d_q, fwd_crv_fd, fwd_crv_dq, q_crv,
            sigma_f_d, sigma_d_q, rho_fd_dq, calendar, daycount, convention, vtk_f_d=0.0, vtk_d_q=0.0):

        # sigma_f_d is the volatility surface of f/d, given an expiry date and strike price, we can get a volatility, then add a tweak
        sigma_f_d = sigma_f_d.interp_vol(self.obs_end, self.strike) + vtk_f_d

        atm_d_q = spot_d_q / fwd_crv_dq.discount(self.obs_end)

        sigma_d_q = sigma_d_q.interp_vol(self.obs_end, atm_d_q) + vtk_d_q

        dcf = daycount.yearFraction(today, self.obs_end)
        atm = self.__getATM__(today, spot_f_d, fwd_crv_fd,
                              sigma_f_d, sigma_d_q, rho_fd_dq, daycount)

        d2 = (math.log(atm / self.strike) - 0.5 * sigma_f_d ** 2 * dcf) / (sigma_f_d * math.sqrt(dcf))
        df = q_crv.discount(self.accrualEnd) / q_crv.discount(today)

        coupon_dcf = daycount.yearFraction(self.accrualStart, self.accrualEnd)

        if self.flavor == 'call':
            npv = df * (norm.cdf(d2)) * self.notional * self.coupon_rate * coupon_dcf

        elif self.flavor == 'put':
            npv = df * (norm.cdf(-d2)) * self.notional * self.coupon_rate * coupon_dcf

        else:
            raise TuringError('Please check the input of flavor')

        if self.tradeDirection == 'long':
            return npv
        elif self.tradeDirection == 'short':
            return -npv
        else:
            raise TuringError('Please check the input of tradeDirection')

    def Exercise_Prob(self, today, spot_f_d, spot_d_q, fwd_crv_fd, fwd_crv_dq, q_crv,
                      sigma_f_d, sigma_d_q, rho_fd_dq, calendar, daycount, convention, vtk_f_d=0.0, vtk_d_q=0.0):
        # sigma_f_d is the volatility surface of f/d, given an expiry date and strike price, we can get a volatility, then add a tweak
        sigma_f_d = sigma_f_d.interp_vol(self.obs_end, self.strike) + vtk_f_d

        atm_d_q = spot_d_q / fwd_crv_dq.discount(self.obs_end)

        sigma_d_q = sigma_d_q.interp_vol(self.obs_end, atm_d_q) + vtk_d_q

        dcf = daycount.yearFraction(today, self.obs_end)
        atm = self.__getATM__(today, spot_f_d, fwd_crv_fd,
                              sigma_f_d, sigma_d_q, rho_fd_dq, daycount)

        d2 = (math.log(atm / self.strike) - 0.5 * sigma_f_d ** 2 * dcf) / (sigma_f_d * math.sqrt(dcf))

        if self.flavor == 'call':
            return norm.cdf(d2)

        elif self.flavor == 'put':
            return norm.cdf(-d2)

        else:
            raise TuringError('Please check the input of flavor')

    # Delta wrt Foreign/Domestic FX spot
    def Delta(self, today, spot_f_d, spot_d_q, fwd_crv_fd, fwd_crv_dq, q_crv,
              sigma_f_d, sigma_d_q, rho_fd_dq, calendar, daycount, convention, tweak=1):

        npv_up = self.NPV(today, spot_f_d + tweak / 10000, spot_d_q, fwd_crv_fd, fwd_crv_dq, q_crv,
                          sigma_f_d, sigma_d_q, rho_fd_dq, calendar, daycount, convention)

        npv_down = self.NPV(today, spot_f_d - tweak / 10000, spot_d_q, fwd_crv_fd, fwd_crv_dq, q_crv,
                            sigma_f_d, sigma_d_q, rho_fd_dq, calendar, daycount, convention)

        delta = (npv_up - npv_down) / (2 * tweak)

        res_delta = delta * 10000 / spot_d_q

        return res_delta

    # Gamma wrt Foreign/Domestic FX spot
    def Gamma(self, today, spot_f_d, spot_d_q, fwd_crv_fd, fwd_crv_dq, q_crv,
              sigma_f_d, sigma_d_q, rho_fd_dq, calendar, daycount, convention, tweak=1):

        delta_up = self.Delta(today, spot_f_d + tweak / 10000, spot_d_q, fwd_crv_fd, fwd_crv_dq, q_crv,
                              sigma_f_d, sigma_d_q, rho_fd_dq, calendar, daycount, convention, tweak)

        delta_down = self.Delta(today, spot_f_d - tweak / 10000, spot_d_q, fwd_crv_fd, fwd_crv_dq, q_crv,
                                sigma_f_d, sigma_d_q, rho_fd_dq, calendar, daycount, convention, tweak)

        gamma = (delta_up - delta_down) / (2 * tweak)

        return gamma

    # Vega wrt Foreign/Domestic FX Vol
    def Vega(self, today, spot_f_d, spot_d_q, fwd_crv_fd, fwd_crv_dq, q_crv,
             sigma_f_d, sigma_d_q, rho_fd_dq, calendar, daycount, convention, tweak=1):

        npv_up = self.NPV(today, spot_f_d, spot_d_q, fwd_crv_fd, fwd_crv_dq, q_crv,
                          sigma_f_d, sigma_d_q, rho_fd_dq, calendar, daycount, convention, tweak / 100)

        npv_down = self.NPV(today, spot_f_d, spot_d_q, fwd_crv_fd, fwd_crv_dq, q_crv,
                            sigma_f_d, sigma_d_q, rho_fd_dq, calendar, daycount, convention, -tweak / 100)

        vega = (npv_up - npv_down) / (2 * tweak)

        return vega

    # Vega wrt Domestic/Quanto FX Vol

    def QuantoVega(self, today, spot_f_d, spot_d_q, fwd_crv_fd, fwd_crv_dq, q_crv,
                   sigma_f_d, sigma_d_q, rho_fd_dq, calendar, daycount, convention, tweak=1):

        npv_up = self.NPV(today, spot_f_d, spot_d_q, fwd_crv_fd, fwd_crv_dq, q_crv,
                          sigma_f_d, sigma_d_q, rho_fd_dq, calendar, daycount, convention, 0, tweak / 100)

        npv_down = self.NPV(today, spot_f_d, spot_d_q, fwd_crv_fd, fwd_crv_dq, q_crv,
                            sigma_f_d, sigma_d_q, rho_fd_dq, calendar, daycount, convention, 0, -tweak / 100)

        quantovega = (npv_up - npv_down) / (2 * tweak)

        return quantovega

    # sensitivity wrt to corr input
    def Corr_sens(self, today, spot_f_d, spot_d_q, fwd_crv_fd, fwd_crv_dq, q_crv,
                  sigma_f_d, sigma_d_q, rho_fd_dq, calendar, daycount, convention, tweak=1):

        npv_up = self.NPV(today, spot_f_d, spot_d_q, fwd_crv_fd, fwd_crv_dq, q_crv,
                          sigma_f_d, sigma_d_q, rho_fd_dq + tweak / 100, calendar, daycount, convention)

        npv_down = self.NPV(today, spot_f_d, spot_d_q, fwd_crv_fd, fwd_crv_dq, q_crv,
                            sigma_f_d, sigma_d_q, rho_fd_dq - tweak / 100, calendar, daycount, convention)

        corr_sens = (npv_up - npv_down) / (2 * tweak)

        return corr_sens
