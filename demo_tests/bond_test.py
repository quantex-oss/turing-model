import numpy as np

from turing_models.utilities.turing_date import TuringDate
from fundamental.pricing_context import PricingContext
from turing_models.instrument.bond import Bond


dates = [0.083, 0.25, 0.5, 0.75, 1, 1.5, 2, 2.5, 3, 3.5, 4, 4.5, 5, 5.5, 6, 6.5, 7, 7.5, 8, 8.5, 9, 9.5, 10]
rates = [1.8124, 1.8848, 2.0986, 2.3175, 2.4012, 2.5515, 2.7018, 2.7638, 2.8259, 2.867, 2.9081, 2.9499, 2.9917, 3.0246,
         3.0575, 3.091, 3.1244, 3.1235, 3.1226, 3.122, 3.1213, 3.1209, 3.1204]
# zero_rates = np.array(rates)
bond = Bond(bond_type='BOND',
            issue_date=TuringDate(2021, 1, 1),
            maturity_date=TuringDate(2026, 1, 1),
            coupon=0.03,
            freq_type='每年付息',
            accrual_type='30/360',
            face_amount=100,
            ytm=0.05,
            zero_dates=dates,
            zero_rates=rates,
            clean_price=98)

print('dv01:', bond.dv01())
print('full_price_from_ytm:', bond.full_price_from_ytm())
print('principal:', bond.principal())
print('dollar_duration:', bond.dollar_duration())
print('macauley_duration:', bond.macauley_duration())
print('modified_duration:', bond.duration())
print('convexity_from_ytm:', bond.convexity())
print('clean_price_from_ytm:', bond.clean_price_from_ytm())
print('clean_price_from_discount_curve:', bond.clean_price_from_discount_curve())
print('full_price_from_discount_curve:', bond.full_price_from_discount_curve())
print('current_yield:', bond.current_yield())
print('yield_to_maturity:', bond.yield_to_maturity())
print('calc_accrued_interest:', bond.calc_accrued_interest())
