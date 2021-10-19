# -*- coding: utf-8 -*-
"""
Created on Mon Nov 16 15:53:19 2020

@author: Dingjn
"""

import math
import numpy as np
import QuantLib as ql
from scipy.interpolate import CubicSpline
from scipy.stats import norm


class FXVolSurface:
    
    def __init__(self, vol_data, d_ccy, f_ccy, spot, fwd_crv, d_crv, f_crv, today, calendar, convention, daycount, excludePremium):

        self.vol_data = vol_data
        self.d_ccy = d_ccy
        self.f_ccy = f_ccy
        self.spot = spot
        self.fwd_crv = fwd_crv
        self.d_crv = d_crv
        self.f_crv = f_crv
        self.today = today
        self.calendar = calendar 
        self.convention = convention
        self.daycount = daycount
        self.excludePremium = excludePremium
    
        self.vol_data['25DC'] = (self.vol_data['25DRR'] + 2 * self.vol_data['25DBF'] + 2 * 
                                 self.vol_data['ATM']) / 2
        self.vol_data['25DP'] = self.vol_data['25DC'] - self.vol_data['25DRR']
        self.vol_data['10DC'] = (self.vol_data['10DRR'] + 2 * self.vol_data['10DBF'] + 2 * 
                                 self.vol_data['ATM']) / 2
        self.vol_data['10DP'] = self.vol_data['10DC'] - self.vol_data['10DRR'] 
    
    def __DeltaToStrike__(self):
        strike_25DC_list = []
        strike_25DP_list = []
        strike_10DC_list = []
        strike_10DP_list = []
        expiry_list = []
        strike_ATM_list = []
        
        for ix, row in self.vol_data.iterrows():
            tenor = row['Tenor']
            expiry = self.calendar.advance(self.today, ql.Period(tenor))
            expiry_list.append(expiry)
            T = self.daycount.yearFraction(self.today, expiry)
            F = self.spot / self.fwd_crv.discount(T)
            strike_ATM_list.append(F)
            df_f = self.f_crv.discount(T)
            sigma_25DC = row['25DC']
            sigma_25DP = row['25DP']
            sigma_10DC = row['10DC']
            sigma_10DP = row['10DP']
            
            if self.excludePremium:
                strike_25DC = F / math.exp(norm.ppf(0.25 / df_f) * sigma_25DC * math.sqrt(T) - 0.5 * sigma_25DC ** 2 * T) 
                strike_25DP = F / math.exp( - norm.ppf(0.25 / df_f) * sigma_25DP * math.sqrt(T) - 0.5 * sigma_25DP ** 2 * T)
                strike_10DC = F / math.exp(norm.ppf(0.10 / df_f) * sigma_10DC * math.sqrt(T) - 0.5 * sigma_10DC ** 2 * T)
                strike_10DP = F / math.exp( - norm.ppf(0.10 / df_f) * sigma_10DP * math.sqrt(T) - 0.5 * sigma_10DP ** 2 * T)
                
                strike_25DC_list.append(strike_25DC)
                strike_25DP_list.append(strike_25DP)
                strike_10DC_list.append(strike_10DC)
                strike_10DP_list.append(strike_10DP)
                
            else:
                strike_25DC = F / math.exp(norm.ppf(0.25) * sigma_25DC * math.sqrt(T) - 0.5 * sigma_25DC ** 2 * T) 
                strike_25DP = F / math.exp( - norm.ppf(0.25) * sigma_25DP * math.sqrt(T) - 0.5 * sigma_25DP ** 2 * T)
                strike_10DC = F / math.exp(norm.ppf(0.10) * sigma_10DC * math.sqrt(T) - 0.5 * sigma_10DC ** 2 * T)
                strike_10DP = F / math.exp( - norm.ppf(0.10) * sigma_10DP * math.sqrt(T) - 0.5 * sigma_10DP ** 2 * T)
                
                strike_25DC_list.append(strike_25DC)
                strike_25DP_list.append(strike_25DP)
                strike_10DC_list.append(strike_10DC)
                strike_10DP_list.append(strike_10DP)
        
        self.vol_data['expiry'] = expiry_list
        self.vol_data['Strike_10DP'] = strike_10DP_list
        self.vol_data['Strike_25DP'] = strike_25DP_list
        self.vol_data['Strike_ATM'] = strike_ATM_list
        self.vol_data['Strike_25DC'] = strike_25DC_list
        self.vol_data['Strike_10DC'] = strike_10DC_list
        
           
    
    def interp_vol(self, expiry, strike):
        
        self.__DeltaToStrike__()
        
        if expiry <= self.vol_data.loc[0, 'expiry']:
            smile = self.vol_data.loc[0, ['10DP', '25DP', 'ATM', '25DC', '10DC']]
            strikes = self.vol_data.loc[0, ['Strike_10DP', 'Strike_25DP', 'Strike_ATM', 'Strike_25DC', 'Strike_10DC']]
            interp = CubicSpline(strikes, smile, True)
            if strike <= strikes[0]:
                interp_vol = smile[0]
            elif strike >= strikes[-1]:
                interp_vol = smile[-1]
            else:
                interp_vol = interp(strike)

        elif expiry >= self.vol_data.loc[len(self.vol_data)-1, 'expiry']:
            smile = self.vol_data.loc[len(self.vol_data)-1, ['10DP', '25DP', 'ATM', '25DC', '10DC']]
            strikes = self.vol_data.loc[len(self.vol_data)-1, ['Strike_10DP', 'Strike_25DP', 'Strike_ATM', 'Strike_25DC', 'Strike_10DC']]
            interp = CubicSpline(strikes, smile, True)
            if strike <= strikes[0]:
                interp_vol = smile[0]
            elif strike >= strikes[-1]:
                interp_vol = smile[-1]
            else:
                interp_vol = interp(strike)
            
        else:
            pos_right = np.argmax(self.vol_data['expiry'] > expiry)
            pos_left = pos_right - 1
            

            smile_left = self.vol_data.loc[pos_left, ['10DP', '25DP', 'ATM', '25DC', '10DC']]
            strikes_left = self.vol_data.loc[pos_left, ['Strike_10DP', 'Strike_25DP', 'Strike_ATM', 'Strike_25DC', 'Strike_10DC']]
            interp_left = CubicSpline(strikes_left, smile_left, True)
            if strike <= strikes_left[0]:
                interp_vol_left = smile_left[0]
            elif strike >= strikes_left[-1]:
                interp_vol_left = smile_left[-1]
            else:
                interp_vol_left = interp_left(strike)
            
            dcf_left = self.daycount.yearFraction(self.today, self.vol_data.loc[pos_left, 'expiry'])
            var_left = interp_vol_left ** 2 * dcf_left
            
            
            smile_right = self.vol_data.loc[pos_right, ['10DP', '25DP', 'ATM', '25DC', '10DC']]
            strikes_right = self.vol_data.loc[pos_right, ['Strike_10DP', 'Strike_25DP', 'Strike_ATM', 'Strike_25DC', 'Strike_10DC']]
            interp_right = CubicSpline(strikes_right, smile_right, True)
            
            if strike <= strikes_right[0]:
                interp_vol_right = smile_right[0]
            elif strike >= strikes_right[-1]:
                interp_vol_right = smile_right[-1]
            else:
                interp_vol_right = interp_right(strike)
            
            dcf_right = self.daycount.yearFraction(self.today, self.vol_data.loc[pos_right, 'expiry'])
            var_right = interp_vol_right ** 2 * dcf_right
            
            dcf = self.daycount.yearFraction(self.today, expiry)

            interp_vol = math.sqrt((var_left * (dcf_right - dcf) + var_right * (dcf - dcf_left)) / (dcf_right - dcf_left) / dcf)
            
        return interp_vol
            
            