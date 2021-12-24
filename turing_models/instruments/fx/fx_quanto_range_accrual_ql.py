#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jun  2 13:50:26 2021

@author: Dingjn
"""

from turing_models.instruments.fx.fx_quanto_digital_ql import *


class FXQuantoRangeAccrualQL:
    def __init__(self, f_ccy, d_ccy, q_ccy, obsStart, obsEnd, accrualStart, accrualEnd, rangeUp, rangeDown, inCoupon,
                 outCoupon, notional, tradeDirection):
        self.d_ccy = d_ccy
        self.f_ccy = f_ccy
        self.q_ccy = q_ccy
        self.obsStart = obsStart
        self.obsEnd = obsEnd
        self.accrualStart = accrualStart
        self.accrualEnd = accrualEnd
        self.rangeUp = rangeUp
        self.rangeDown = rangeDown
        self.inCoupon = inCoupon
        self.outCoupon = outCoupon
        self.notional = notional
        self.tradeDirection = tradeDirection.lower()

    def NPV(self, today, spot_f_d, spot_d_q, fwd_crv_fd, fwd_crv_dq, q_crv,
            sigma_f_d, sigma_d_q, rho_fd_dq, fx_fixings, calendar, daycount, convention, vtk_f_d=0.0, vtk_d_q=0.0):

        DCF = daycount.yearFraction(self.accrualStart, self.accrualEnd)

        sch = list(ql.Schedule(self.obsStart, self.obsEnd, ql.Period('1D'), calendar, convention, convention,
                               ql.DateGeneration.Forward, False))

        numIn = 0
        numOut = 0

        if self.accrualEnd < today:
            return 0

        for date in sch:

            if date <= today:
                if date in fx_fixings.index:
                    if fx_fixings.loc[date, 'Fixing'] < self.rangeDown or fx_fixings.loc[date, 'Fixing'] > self.rangeUp:
                        numOut += 1
                    else:
                        numIn += 1

            else:

                digiStart = today
                digiEnd = date

                digi1 = FXQuantoDigitalQL(self.f_ccy, self.d_ccy, self.q_ccy, self.rangeDown, digiStart, digiEnd,
                                        digiStart, digiEnd, 'call', 1, 1, 'long')
                pv1 = digi1.NPV(today, spot_f_d, spot_d_q, fwd_crv_fd, fwd_crv_dq, q_crv, sigma_f_d, sigma_d_q,
                                rho_fd_dq,
                                calendar, daycount, convention, vtk_f_d, vtk_d_q) / daycount.yearFraction(digiStart,
                                                                                                          digiEnd)

                digi2 = FXQuantoDigitalQL(self.f_ccy, self.d_ccy, self.q_ccy, self.rangeUp, digiStart, digiEnd, digiStart,
                                        digiEnd, 'call', 1, 1, 'long')
                pv2 = digi2.NPV(today, spot_f_d, spot_d_q, fwd_crv_fd, fwd_crv_dq, q_crv, sigma_f_d, sigma_d_q,
                                rho_fd_dq,
                                calendar, daycount, convention, vtk_f_d, vtk_d_q) / daycount.yearFraction(digiStart,
                                                                                                          digiEnd)

                pv = (pv1 - pv2) / (q_crv.discount(digiEnd) / q_crv.discount(today))

                numIn += pv
                numOut += (1 - pv)

        bds = calendar.businessDaysBetween(self.obsStart, self.obsEnd) + 1

        npv = (self.inCoupon * numIn / bds + self.outCoupon * numOut / bds) * DCF * q_crv.discount(
            self.accrualEnd) / q_crv.discount(today)

        npv *= self.notional

        return npv if self.tradeDirection == 'long' else -npv

    # Delta wrt Foreign/Domestic FX spot
    def Delta(self, today, spot_f_d, spot_d_q, fwd_crv_fd, fwd_crv_dq, q_crv,
              sigma_f_d, sigma_d_q, rho_fd_dq, fx_fixings, calendar, daycount, convention, tweak=1):

        npv_up = self.NPV(today, spot_f_d + tweak / 10000, spot_d_q, fwd_crv_fd, fwd_crv_dq, q_crv,
                          sigma_f_d, sigma_d_q, rho_fd_dq, fx_fixings, calendar, daycount, convention)

        npv_down = self.NPV(today, spot_f_d - tweak / 10000, spot_d_q, fwd_crv_fd, fwd_crv_dq, q_crv,
                            sigma_f_d, sigma_d_q, rho_fd_dq, fx_fixings, calendar, daycount, convention)

        delta = (npv_up - npv_down) / (2 * tweak)

        res_delta = delta * 10000 / spot_d_q

        return res_delta

    # Gamma wrt Foreign/Domestic FX spot
    def Gamma(self, today, spot_f_d, spot_d_q, fwd_crv_fd, fwd_crv_dq, q_crv,
              sigma_f_d, sigma_d_q, rho_fd_dq, fx_fixings, calendar, daycount, convention, tweak=1):

        delta_up = self.Delta(today, spot_f_d + tweak / 10000, spot_d_q, fwd_crv_fd, fwd_crv_dq, q_crv,
                              sigma_f_d, sigma_d_q, rho_fd_dq, fx_fixings, calendar, daycount, convention)

        delta_down = self.Delta(today, spot_f_d - tweak / 10000, spot_d_q, fwd_crv_fd, fwd_crv_dq, q_crv,
                                sigma_f_d, sigma_d_q, rho_fd_dq, fx_fixings, calendar, daycount, convention)

        gamma = (delta_up - delta_down) / (2 * tweak)

        return gamma

    # Vega wrt Foreign/Domestic FX Vol
    def Vega(self, today, spot_f_d, spot_d_q, fwd_crv_fd, fwd_crv_dq, q_crv,
             sigma_f_d, sigma_d_q, rho_fd_dq, fx_fixings, calendar, daycount, convention, tweak=1):

        npv_up = self.NPV(today, spot_f_d, spot_d_q, fwd_crv_fd, fwd_crv_dq, q_crv,
                          sigma_f_d, sigma_d_q, rho_fd_dq, fx_fixings, calendar, daycount, convention, tweak / 100)

        npv_down = self.NPV(today, spot_f_d, spot_d_q, fwd_crv_fd, fwd_crv_dq, q_crv,
                            sigma_f_d, sigma_d_q, rho_fd_dq, fx_fixings, calendar, daycount, convention, - tweak / 100)

        vega = (npv_up - npv_down) / (2 * tweak)

        return vega

    # Vega wrt Domestic/Quanto FX Vol
    def QuantoVega(self, today, spot_f_d, spot_d_q, fwd_crv_fd, fwd_crv_dq, q_crv,
                   sigma_f_d, sigma_d_q, rho_fd_dq, fx_fixings, calendar, daycount, convention, tweak=1):

        npv_up = self.NPV(today, spot_f_d, spot_d_q, fwd_crv_fd, fwd_crv_dq, q_crv,
                          sigma_f_d, sigma_d_q, rho_fd_dq, fx_fixings, calendar, daycount, convention, 0, tweak / 100)

        npv_down = self.NPV(today, spot_f_d, spot_d_q, fwd_crv_fd, fwd_crv_dq, q_crv,
                            sigma_f_d, sigma_d_q, rho_fd_dq, fx_fixings, calendar, daycount, convention, 0,
                            -tweak / 100)

        quantovega = (npv_up - npv_down) / (2 * tweak)

        return quantovega

    # sensitivity wrt to corr input
    def Corr_sens(self, today, spot_f_d, spot_d_q, fwd_crv_fd, fwd_crv_dq, q_crv,
                  sigma_f_d, sigma_d_q, rho_fd_dq, fx_fixings, calendar, daycount, convention, tweak=1):

        npv_up = self.NPV(today, spot_f_d, spot_d_q, fwd_crv_fd, fwd_crv_dq, q_crv,
                          sigma_f_d, sigma_d_q, rho_fd_dq + tweak / 100, fx_fixings, calendar, daycount, convention)

        npv_down = self.NPV(today, spot_f_d, spot_d_q, fwd_crv_fd, fwd_crv_dq, q_crv,
                            sigma_f_d, sigma_d_q, rho_fd_dq - tweak / 100, fx_fixings, calendar, daycount, convention)

        corr_sens = (npv_up - npv_down) / (2 * tweak)

        return corr_sens
