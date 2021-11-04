from dataclasses import dataclass

import QuantLib as ql

from fundamental.turing_db.option_data import FxOptionApi
from turing_models.instruments.fx.fx_option import FXOption
from turing_models.products.fx.fx_vanilla_option_ql import FXVanilla
from turing_models.utilities.error import TuringError
from turing_models.utilities.global_types import TuringOptionType


@dataclass(repr=False, eq=False, order=False, unsafe_hash=True)
class FXVanillaOption(FXOption):

    calendar = ql.China(ql.China.IB)
    daycount = ql.Actual365Fixed()
    convention = ql.Following

    def __post_init__(self):
        super().__post_init__()
        if self.domestic_name and self.foreign_name \
           and self.strike and self.start_date and self.expiry_ql \
           and self.option_type and self.notional:
            self.option = FXVanilla(d_ccy=self.domestic_name,
                                    f_ccy=self.foreign_name,
                                    strike=self.strike,
                                    start=self.start_date,
                                    expiry=self.expiry_ql,
                                    flavor=self.option_type_,
                                    notional=self.notional)

    @property
    def option_type_(self):
        if self.option_type == "CALL" or self.option_type == "call" or self.option_type == TuringOptionType.CALL:
            return "call"
        elif self.option_type == "PUT" or self.option_type == "put" or self.option_type == TuringOptionType.PUT:
            return "put"
        else:
            raise TuringError('Please check the input of option_type')

    @property
    def value_date_ql(self):
        return ql.Date(self.value_date_._d, self.value_date_._m, self.value_date_._y)

    def params(self) -> list:
        return [
            self.value_date_ql,
            self.exchange_rate,
            self.fx_forward_curve,
            self.domestic_discount_curve,
            self.volatility_surface,
            self.calendar,
            self.daycount,
            self.convention
        ]

    def price(self):
        return self.option.NPV(*self.params())

    def atm(self):
        return self.option.__getATM__(self.value_date_ql,
                                      self.exchange_rate,
                                      self.fx_forward_curve,
                                      self.daycount)

    def fx_delta(self):
        return self.option.Delta(*self.params())

    def fx_gamma(self):
        return self.option.Gamma(*self.params())

    def fx_vega(self):
        return self.option.Vega(*self.params())

    def fx_theta(self):
        return self.option.Theta(*self.params())

    def fx_vanna(self):
        return self.vanna(*self.params())

    def fx_volga(self):
        return self.volga(*self.params())

    def vanna(self, today, spot_f_d, fwd_crv_fd, disc_crv, sigma_f_d, calendar, daycount, convention, tweak1=1e-4,
              tweak2=0.01):

        npv_upup = self.option.NPV(today, spot_f_d + tweak1, fwd_crv_fd, disc_crv, sigma_f_d, calendar, daycount,
                                   convention, tweak2)

        npv_updown = self.option.NPV(today, spot_f_d + tweak1, fwd_crv_fd, disc_crv, sigma_f_d, calendar, daycount,
                                     convention, - tweak2)

        vega_up = (npv_upup - npv_updown) / (2 * tweak2 * 100)

        npv_downup = self.option.NPV(today, spot_f_d - tweak1, fwd_crv_fd, disc_crv, sigma_f_d, calendar, daycount,
                                     convention, tweak2)

        npv_downdown = self.option.NPV(today, spot_f_d - tweak1, fwd_crv_fd, disc_crv, sigma_f_d, calendar, daycount,
                                       convention, - tweak2)

        vega_down = (npv_downup - npv_downdown) / (2 * tweak2 * 100)

        vanna = (vega_up - vega_down) / (2 * tweak1 * 10000)

        return vanna

    def volga(self, today, spot_f_d, fwd_crv_fd, disc_crv, sigma_f_d, calendar, daycount, convention, vol_tweak=0.01):

        npv_upup = self.option.NPV(today, spot_f_d, fwd_crv_fd, disc_crv, sigma_f_d, calendar, daycount, convention,
                                   vol_tweak + vol_tweak)

        npv_updown = self.option.NPV(today, spot_f_d, fwd_crv_fd, disc_crv, sigma_f_d, calendar, daycount, convention,
                                     vol_tweak - vol_tweak)

        vega_up = (npv_upup - npv_updown) / (2 * vol_tweak * 100)

        npv_downup = self.option.NPV(today, spot_f_d, fwd_crv_fd, disc_crv, sigma_f_d, calendar, daycount, convention,
                                     - vol_tweak + vol_tweak)

        npv_downdown = self.option.NPV(today, spot_f_d, fwd_crv_fd, disc_crv, sigma_f_d, calendar, daycount, convention,
                                       - vol_tweak - vol_tweak)

        vega_down = (npv_downup - npv_downdown) / (2 * vol_tweak * 100)

        volga = (vega_up - vega_down) / (2 * vol_tweak * 100)

        return volga

    def set_property_list(self, curve, underlier, _property, key):
        _list = []
        for k, v in curve.items():
            if k == underlier:
                for cu in v.get('iuir_curve_data'):
                    _list.append(cu.get(key))
        setattr(self, _property, _list)
        return _list

    def spot_path(self):
        return 'turing_models.instruments.fx.fx.ForeignExchange'

    def _resolve(self):
        if self.asset_id and not self.asset_id.startswith("OPTION_"):
            temp_dict = FxOptionApi.fetch_fx_option(
                gurl=None, asset_id=self.asset_id)
            for k, v in temp_dict.items():
                if not getattr(self, k, None) and v:
                    setattr(self, k, v)
        self.resolve_param()

    def resolve_param(self):
        self.check_underlier()
        if not self.product_type:
            setattr(self, 'product_type', 'VANILLA')
        self.__post_init__()
