from abc import ABCMeta, abstractmethod
from enum import Enum

import numpy as np
from numba import njit

from turing_models.models.model_black_scholes_analytical import bs_value, bs_delta
from turing_models.utilities.turing_date import TuringDate
from turing_models.utilities.error import TuringError


bump = 1e-4


def greek(obj, price, attr, bump=bump, order=1, cus_inc=None):
    """
    如果要传cus_inc，格式须为(函数名, 函数参数值)
    """
    cus_func = args = None
    attr_value = getattr(obj, attr)
    if cus_inc:
        cus_func, args = cus_inc

    def increment(_attr_value, count=1):
        if cus_func:
            _attr_value = cus_func(args * count)
        else:
            _attr_value += count * bump
        setattr(obj, attr, _attr_value)

    def decrement(_attr_value, count=1):
        if cus_func:
            _attr_value = cus_func(-args * count)
        else:
            _attr_value -= count * bump
        setattr(obj, attr, _attr_value)

    def clear():
        setattr(obj, attr, None)

    if order == 1:
        if isinstance(attr_value, TuringDate):
            p0 = price()
            increment(attr_value)
            p_up = price()
            clear()
            return (p_up - p0) / bump
        increment(attr_value)
        p_up = price()
        clear()
        decrement(attr_value)
        p_down = price()
        clear()
        return (p_up - p_down) / (bump * 2)
    elif order == 2:
        p0 = price()
        decrement(attr_value)
        p_down = price()
        increment(attr_value)
        p_up = price()
        clear()
        return (p_up - 2.0 * p0 + p_down) / bump / bump


@njit(fastmath=True, cache=True)
def fastDelta(s, t, k, rd, rf, vol, deltaTypeValue, optionTypeValue):
    ''' Calculation of the FX Option delta. Used in the determination of
    the volatility surface. Avoids discount curve interpolation so it
    should be slightly faster than the full calculation of delta. '''

    pips_spot_delta = bs_delta(s, t, k, rd, rf, vol, optionTypeValue, False)

    if deltaTypeValue == TuringFXDeltaMethod.SPOT_DELTA.value:
        return pips_spot_delta
    elif deltaTypeValue == TuringFXDeltaMethod.FORWARD_DELTA.value:
        pips_fwd_delta = pips_spot_delta * np.exp(rf * t)
        return pips_fwd_delta
    elif deltaTypeValue == TuringFXDeltaMethod.SPOT_DELTA_PREM_ADJ.value:
        vpctf = bs_value(s, t, k, rd, rf, vol, optionTypeValue, False) / s
        pct_spot_delta_prem_adj = pips_spot_delta - vpctf
        return pct_spot_delta_prem_adj
    elif deltaTypeValue == TuringFXDeltaMethod.FORWARD_DELTA_PREM_ADJ.value:
        vpctf = bs_value(s, t, k, rd, rf, vol, optionTypeValue, False) / s
        pct_fwd_delta_prem_adj = np.exp(rf * t) * (pips_spot_delta - vpctf)
        return pct_fwd_delta_prem_adj
    else:
        raise TuringError("Unknown TuringFXDeltaMethod")


class RiskMeasure(Enum):
    Price = "price"
    Delta = "delta"
    Gamma = "gamma"
    Vega = "vega"
    Theta = "theta"
    Rho = "rho"
    RhoQ = "rho_q"
    EqDelta = "eq_delta"
    EqGamma = "eq_gamma"
    EqVega = "eq_vega"
    EqTheta = "eq_theta"
    EqRho = "eq_rho"
    EqRhoQ = "eq_rho_q"
    Dv01 = "dv01"
    DollarDuration = "dollar_duration"
    DollarConvexity = "dollar_convexity"
    FxDelta = "fx_delta"
    FxGamma = "fx_gamma"
    FxVega = "fx_vega"
    FxTheta = "fx_theta"
    FxVanna = "fx_vanna"
    FxVolga = "fx_volga"

    def __repr__(self):
        return self.value


class BuySell(Enum):
    """Buy or Sell side of contract"""

    Buy = 'Buy'
    Sell = 'Sell'

    def __repr__(self):
        return self.value


class Exchange(Enum):
    """Exchange Name"""

    Shanghai_Stock_Exchange = 'Shanghai Stock Exchange'
    Shenzhen_Stock_Exchange = 'Shenzhen Stock Exchange'
    Zhengzhou_Commodity_Exchange = 'Zhengzhou Commodity Exchange'
    Dalian_Commodity_Exchange = 'Dalian Commodity Exchange'
    Shanghai_Futures_Exchange = 'Shanghai Futures Exchange'
    China_Financial_Futures_Exchange = 'China Financial Futures Exchange'

    def __repr__(self):
        return self.value


class OptionType(Enum):
    """Option Type"""

    Call = 'Call'
    Put = 'Put'
    Binary_Call = 'Binary Call'
    Binary_Put = 'Binary Put'

    def __repr__(self):
        return self.value


class OptionStyle(Enum):
    """Option Exercise Style"""

    European = 'European'
    American = 'American'
    Asian = 'Asian'
    Bermudan = 'Bermudan'
    Snowball = 'Snowball'

    def __repr__(self):
        return self.value


class Currency(Enum):
    """Currency, ISO 4217 currency code or exchange quote modifier (e.g. GBP vs GBp)"""

    _ = ''
    ACU = 'ACU'
    ADP = 'ADP'
    AED = 'AED'
    AFA = 'AFA'
    ALL = 'ALL'
    AMD = 'AMD'
    ANG = 'ANG'
    AOA = 'AOA'
    AOK = 'AOK'
    AON = 'AON'
    ARA = 'ARA'
    ARS = 'ARS'
    ARZ = 'ARZ'
    ATS = 'ATS'
    AUD = 'AUD'
    AUZ = 'AUZ'
    AZM = 'AZM'
    B03 = 'B03'
    BAD = 'BAD'
    BAK = 'BAK'
    BAM = 'BAM'
    BBD = 'BBD'
    BDN = 'BDN'
    BDT = 'BDT'
    BEF = 'BEF'
    BGL = 'BGL'
    BGN = 'BGN'
    BHD = 'BHD'
    BIF = 'BIF'
    BMD = 'BMD'
    BND = 'BND'
    BR6 = 'BR6'
    BRE = 'BRE'
    BRF = 'BRF'
    BRL = 'BRL'
    BRR = 'BRR'
    BSD = 'BSD'
    BTC = 'BTC'
    BTN = 'BTN'
    BTR = 'BTR'
    BWP = 'BWP'
    BYR = 'BYR'
    BZD = 'BZD'
    C23 = 'C23'
    CAC = 'CAC'
    CAD = 'CAD'
    CAZ = 'CAZ'
    CCI = 'CCI'
    CDF = 'CDF'
    CFA = 'CFA'
    CHF = 'CHF'
    CHZ = 'CHZ'
    CLF = 'CLF'
    CLP = 'CLP'
    CLZ = 'CLZ'
    CNH = 'CNH'
    CNO = 'CNO'
    CNY = 'CNY'
    CNZ = 'CNZ'
    COP = 'COP'
    COZ = 'COZ'
    CPB = 'CPB'
    CPI = 'CPI'
    CRC = 'CRC'
    CUP = 'CUP'
    CVE = 'CVE'
    CYP = 'CYP'
    CZH = 'CZH'
    CZK = 'CZK'
    DAX = 'DAX'
    DEM = 'DEM'
    DIJ = 'DIJ'
    DJF = 'DJF'
    DKK = 'DKK'
    DOP = 'DOP'
    DZD = 'DZD'
    E51 = 'E51'
    E52 = 'E52'
    E53 = 'E53'
    E54 = 'E54'
    ECI = 'ECI'
    ECS = 'ECS'
    ECU = 'ECU'
    EEK = 'EEK'
    EF0 = 'EF0'
    EGP = 'EGP'
    ESP = 'ESP'
    ETB = 'ETB'
    EUR = 'EUR'
    EUZ = 'EUZ'
    F06 = 'F06'
    FED = 'FED'
    FIM = 'FIM'
    FJD = 'FJD'
    FKP = 'FKP'
    FRF = 'FRF'
    FT1 = 'FT1'
    GBP = 'GBP'
    GBZ = 'GBZ'
    GEK = 'GEK'
    GHC = 'GHC'
    GHS = 'GHS'
    GHY = 'GHY'
    GIP = 'GIP'
    GLR = 'GLR'
    GMD = 'GMD'
    GNF = 'GNF'
    GQE = 'GQE'
    GRD = 'GRD'
    GTQ = 'GTQ'
    GWP = 'GWP'
    GYD = 'GYD'
    HKB = 'HKB'
    HKD = 'HKD'
    HNL = 'HNL'
    HRK = 'HRK'
    HSI = 'HSI'
    HTG = 'HTG'
    HUF = 'HUF'
    IDB = 'IDB'
    IDO = 'IDO'
    IDR = 'IDR'
    IEP = 'IEP'
    IGP = 'IGP'
    ILS = 'ILS'
    INO = 'INO'
    INP = 'INP'
    INR = 'INR'
    IPA = 'IPA'
    IPX = 'IPX'
    IQD = 'IQD'
    IRR = 'IRR'
    IRS = 'IRS'
    ISI = 'ISI'
    ISK = 'ISK'
    ISO = 'ISO'
    ITL = 'ITL'
    J05 = 'J05'
    JMD = 'JMD'
    JNI = 'JNI'
    JOD = 'JOD'
    JPY = 'JPY'
    JPZ = 'JPZ'
    JZ9 = 'JZ9'
    KES = 'KES'
    KGS = 'KGS'
    KHR = 'KHR'
    KMF = 'KMF'
    KOR = 'KOR'
    KPW = 'KPW'
    KRW = 'KRW'
    KWD = 'KWD'
    KYD = 'KYD'
    KZT = 'KZT'
    LAK = 'LAK'
    LBA = 'LBA'
    LBP = 'LBP'
    LHY = 'LHY'
    LKR = 'LKR'
    LRD = 'LRD'
    LSL = 'LSL'
    LSM = 'LSM'
    LTL = 'LTL'
    LUF = 'LUF'
    LVL = 'LVL'
    LYD = 'LYD'
    MAD = 'MAD'
    MDL = 'MDL'
    MGF = 'MGF'
    MKD = 'MKD'
    MMK = 'MMK'
    MNT = 'MNT'
    MOP = 'MOP'
    MRO = 'MRO'
    MTP = 'MTP'
    MUR = 'MUR'
    MVR = 'MVR'
    MWK = 'MWK'
    MXB = 'MXB'
    MXN = 'MXN'
    MXP = 'MXP'
    MXW = 'MXW'
    MXZ = 'MXZ'
    MYO = 'MYO'
    MYR = 'MYR'
    MZM = 'MZM'
    MZN = 'MZN'
    NAD = 'NAD'
    ND3 = 'ND3'
    NGF = 'NGF'
    NGI = 'NGI'
    NGN = 'NGN'
    NIC = 'NIC'
    NLG = 'NLG'
    NOK = 'NOK'
    NOZ = 'NOZ'
    NPR = 'NPR'
    NZD = 'NZD'
    NZZ = 'NZZ'
    O08 = 'O08'
    OMR = 'OMR'
    PAB = 'PAB'
    PEI = 'PEI'
    PEN = 'PEN'
    PEZ = 'PEZ'
    PGK = 'PGK'
    PHP = 'PHP'
    PKR = 'PKR'
    PLN = 'PLN'
    PLZ = 'PLZ'
    PSI = 'PSI'
    PTE = 'PTE'
    PYG = 'PYG'
    QAR = 'QAR'
    R2K = 'R2K'
    ROL = 'ROL'
    RON = 'RON'
    RSD = 'RSD'
    RUB = 'RUB'
    RUF = 'RUF'
    RUR = 'RUR'
    RWF = 'RWF'
    SAR = 'SAR'
    SBD = 'SBD'
    SCR = 'SCR'
    SDP = 'SDP'
    SDR = 'SDR'
    SEK = 'SEK'
    SET = 'SET'
    SGD = 'SGD'
    SGS = 'SGS'
    SHP = 'SHP'
    SKK = 'SKK'
    SLL = 'SLL'
    SRG = 'SRG'
    SSI = 'SSI'
    STD = 'STD'
    SUR = 'SUR'
    SVC = 'SVC'
    SVT = 'SVT'
    SYP = 'SYP'
    SZL = 'SZL'
    T21 = 'T21'
    T51 = 'T51'
    T52 = 'T52'
    T53 = 'T53'
    T54 = 'T54'
    T55 = 'T55'
    T71 = 'T71'
    TE0 = 'TE0'
    TED = 'TED'
    TF9 = 'TF9'
    THB = 'THB'
    THO = 'THO'
    TMM = 'TMM'
    TND = 'TND'
    TNT = 'TNT'
    TOP = 'TOP'
    TPE = 'TPE'
    TPX = 'TPX'
    TRB = 'TRB'
    TRL = 'TRL'
    TRY = 'TRY'
    TRZ = 'TRZ'
    TTD = 'TTD'
    TWD = 'TWD'
    TZS = 'TZS'
    UAH = 'UAH'
    UCB = 'UCB'
    UDI = 'UDI'
    UFC = 'UFC'
    UFZ = 'UFZ'
    UGS = 'UGS'
    UGX = 'UGX'
    USB = 'USB'
    USD = 'USD'
    UVR = 'UVR'
    UYP = 'UYP'
    UYU = 'UYU'
    VAC = 'VAC'
    VEB = 'VEB'
    VEF = 'VEF'
    VES = 'VES'
    VND = 'VND'
    VUV = 'VUV'
    WST = 'WST'
    XAF = 'XAF'
    XAG = 'XAG'
    XAU = 'XAU'
    XPD = 'XPD'
    XPT = 'XPT'
    XCD = 'XCD'
    XDR = 'XDR'
    XEU = 'XEU'
    XOF = 'XOF'
    XPF = 'XPF'
    YDD = 'YDD'
    YER = 'YER'
    YUD = 'YUD'
    YUN = 'YUN'
    ZAL = 'ZAL'
    ZAR = 'ZAR'
    ZAZ = 'ZAZ'
    ZMK = 'ZMK'
    ZMW = 'ZMW'
    ZRN = 'ZRN'
    ZRZ = 'ZRZ'
    ZWD = 'ZWD'
    AUd = 'AUd'
    BWp = 'BWp'
    EUr = 'EUr'
    GBp = 'GBp'
    ILs = 'ILs'
    KWd = 'KWd'
    MWk = 'MWk'
    SGd = 'SGd'
    SZl = 'SZl'
    USd = 'USd'
    ZAr = 'ZAr'

    def __repr__(self):
        return self.value


class CurrencyPair(Enum):
    USDCNY = 'USD/CNY'
    JPYCNY = 'JPY/CNY'
    GBPCNY = 'GBP/CNY'
    NZDCNY = 'NZD/CNY'
    CHFCNY = 'CHF/CNY'
    CNYMYR = 'CNY/MYR'
    CNYZAR = 'CNY/ZAR'
    CNYAED = 'CNY/AED'
    CNYHUF = 'CNY/HUF'
    CNYDKK = 'CNY/DKK'
    CNYNOK = 'CNY/NOK'
    CNYMXN = 'CNY/MXN'
    EURCNY = 'EUR/CNY'
    HKDCNY = 'HKD/CNY'
    AUDCNY = 'AUD/CNY'
    SGDCNY = 'SGD/CNY'
    CADCNY = 'CAD/CNY'
    CNYRUB = 'CNY/RUB'
    CNYKRW = 'CNY/KRW'
    CNYSAR = 'CNY/SAR'
    CNYPLN = 'CNY/PLN'
    CNYSEK = 'CNY/SEK'
    CNYTRY = 'CNY/TRY'
    CNYTHB = 'CNY/THB'
    EURUSD = 'EUR/USD'

    def __repr__(self):
        return self.value


class RMBIRCurveType(Enum):
    Shibor = 'Shibor'
    Shibor3M = 'Shibor3M'
    FR007 = 'FR007'

    def __repr__(self):
        return self.value


class DiscountCurveType(Enum):
    Shibor3M_CICC = 'Shibor3M_CICC'
    Shibor3M = 'Shibor3M'
    FX_Implied_CICC = 'FX_Implied_CICC'
    FX_Implied = 'FX_Implied'


class SpotExchangeRateType(Enum):
    Central = 'central'
    Average = 'average'

    def __repr__(self):
        return self.value


class OptionSettlementMethod(Enum):
    """How the option is settled (e.g. Cash, Physical)"""

    Cash = 'Cash'
    Physical = 'Physical'

    def __repr__(self):
        return self.value


class AssetClass(Enum):
    """Asset classification of security. Assets are classified into broad groups
       which exhibit similar characteristics and behave in a consistent way
       under different market conditions"""

    Cash = 'Cash'
    Commod = 'Commod'
    Credit = 'Credit'
    Cross_Asset = 'Cross Asset'
    Econ = 'Econ'
    Equity = 'Equity'
    Fund = 'Fund'
    FX = 'FX'
    Mortgage = 'Mortgage'
    Rates = 'Rates'
    Loan = 'Loan'
    Social = 'Social'
    Cryptocurrency = 'Cryptocurrency'

    def __repr__(self):
        return self.value


class AssetType(Enum):
    """Asset type differentiates the product categorization or contract type"""

    Access = 'Access'
    AssetSwapFxdFlt = 'AssetSwapFxdFlt'
    Any = 'Any'
    AveragePriceOption = 'AveragePriceOption'
    Basis = 'Basis'
    BasisSwap = 'BasisSwap'
    Benchmark = 'Benchmark'
    Benchmark_Rate = 'Benchmark Rate'
    Binary = 'Binary'
    Bond = 'Bond'
    BondFuture = 'BondFuture'
    BondFutureOption = 'BondFutureOption'
    BondOption = 'BondOption'
    Calendar_Spread = 'Calendar Spread'
    Cap = 'Cap'
    Cash = 'Cash'
    Certificate = 'Certificate'
    CD = 'CD'
    Cliquet = 'Cliquet'
    CMSOption = 'CMSOption'
    CMSOptionStrip = 'CMSOptionStrip'
    CMSSpreadOption = 'CMSSpreadOption'
    CMSSpreadOptionStrip = 'CMSSpreadOptionStrip'
    Commodity = 'Commodity'
    CommodityReferencePrice = 'CommodityReferencePrice'
    CommodVarianceSwap = 'CommodVarianceSwap'
    CommodityPowerNode = 'CommodityPowerNode'
    CommodityPowerAggregatedNodes = 'CommodityPowerAggregatedNodes'
    CommodityEUNaturalGasHub = 'CommodityEUNaturalGasHub'
    CommodityNaturalGasHub = 'CommodityNaturalGasHub'
    Company = 'Company'
    Convertible = 'Convertible'
    Credit_Basket = 'Credit Basket'
    Cross = 'Cross'
    CSL = 'CSL'
    Currency = 'Currency'
    Custom_Basket = 'Custom Basket'
    Cryptocurrency = 'Cryptocurrency'
    Default_Swap = 'Default Swap'
    Economic = 'Economic'
    Endowment = 'Endowment'
    Equity_Basket = 'Equity Basket'
    ETF = 'ETF'
    ETN = 'ETN'
    Event = 'Event'
    FRA = 'FRA'
    FixedLeg = 'FixedLeg'
    Fixing = 'Fixing'
    FloatLeg = 'FloatLeg'
    Floor = 'Floor'
    Forward = 'Forward'
    Fund = 'Fund'
    Future = 'Future'
    FutureContract = 'FutureContract'
    FutureMarket = 'FutureMarket'
    FutureOption = 'FutureOption'
    FutureStrategy = 'FutureStrategy'
    Hedge_Fund = 'Hedge Fund'
    Index = 'Index'
    InflationSwap = 'InflationSwap'
    Inter_Commodity_Spread = 'Inter-Commodity Spread'
    InvoiceSpread = 'InvoiceSpread'
    Market_Location = 'Market Location'
    MLF = 'MLF'
    Multi_Asset_Allocation = 'Multi-Asset Allocation'
    MultiCrossBinary = 'MultiCrossBinary'
    MultiCrossBinaryLeg = 'MultiCrossBinaryLeg'
    Mutual_Fund = 'Mutual Fund'
    Note = 'Note'
    Option = 'Option'
    OptionLeg = 'OptionLeg'
    OptionStrategy = 'OptionStrategy'
    Pension_Fund = 'Pension Fund'
    Preferred_Stock = 'Preferred Stock'
    Physical = 'Physical'
    Precious_Metal = 'Precious Metal'
    Precious_Metal_Swap = 'Precious Metal Swap'
    Precious_Metal_RFQ = 'Precious Metal RFQ'
    Reference_Entity = 'Reference Entity'
    Research_Basket = 'Research Basket'
    Rate = 'Rate'
    Risk_Premia = 'Risk Premia'
    Roll = 'Roll'
    Securities_Lending_Loan = 'Securities Lending Loan'
    Share_Class = 'Share Class'
    Single_Stock = 'Single Stock'
    Swap = 'Swap'
    SwapLeg = 'SwapLeg'
    SwapStrategy = 'SwapStrategy'
    Swaption = 'Swaption'
    Synthetic = 'Synthetic'
    Systematic_Hedging = 'Systematic Hedging'
    VarianceSwap = 'VarianceSwap'
    VolatilitySwap = 'VolatilitySwap'
    WeatherIndex = 'WeatherIndex'
    XccySwap = 'XccySwap'
    XccySwapFixFix = 'XccySwapFixFix'
    XccySwapFixFlt = 'XccySwapFixFlt'
    XccySwapMTM = 'XccySwapMTM'

    def __repr__(self):
        return self.value


class TuringFXATMMethod(Enum):
    SPOT = 1  # Spot FX Rate
    FWD = 2  # At the money forward
    FWD_DELTA_NEUTRAL = 3  # K = F*exp(0.5*sigma*sigma*T)
    FWD_DELTA_NEUTRAL_PREM_ADJ = 4  # K = F*exp(-0.5*sigma*sigma*T)


class TuringFXDeltaMethod(Enum):
    SPOT_DELTA = 1
    FORWARD_DELTA = 2
    SPOT_DELTA_PREM_ADJ = 3
    FORWARD_DELTA_PREM_ADJ = 4


class Ctx:
    @property
    def ctx_spot(self):
        asset_id = getattr(self, 'underlier', None) or getattr(
            self, 'asset_id', None)
        return getattr(self.ctx, f"spot_{asset_id}")

    @property
    def ctx_volatility(self):
        asset_id = getattr(self, 'underlier', None) or getattr(
            self, 'asset_id', None)
        return getattr(self.ctx, f"volatility_{asset_id}")

    @property
    def ctx_fx_implied_volatility_curve(self):
        asset_id = getattr(self, 'underlier', None) or getattr(
            self, 'asset_id', None)
        return getattr(self.ctx, f"fx_implied_volatility_curve_{asset_id}")

    @property
    def ctx_irs_curve(self):
        asset_id = getattr(self, 'underlier', None) or getattr(
            self, 'asset_id', None)
        return getattr(self.ctx, f"irs_curve_{asset_id}")

    @property
    def ctx_shibor_curve(self):
        asset_id = getattr(self, 'underlier', None) or getattr(
            self, 'asset_id', None)
        return getattr(self.ctx, f"shibor_curve_{asset_id}")

    @property
    def ctx_swap_curve(self):
        asset_id = getattr(self, 'underlier', None) or getattr(
            self, 'asset_id', None)
        return getattr(self.ctx, f"swap_curve_{asset_id}")

    @property
    def ctx_interest_rate(self):
        return self.ctx.interest_rate

    @property
    def ctx_dividend_yield(self):
        return self.ctx.dividend_yield

    @property
    def ctx_pricing_date(self):
        return self.ctx.pricing_date

    @property
    def ctx_ytm(self):
        return self.ctx.ytm

    @property
    def ctx_parallel_shift(self):
        return getattr(self.ctx, f"parallel_shift_{self.curve_code}")

    @property
    def ctx_curve_shift(self):
        return getattr(self.ctx, f"curve_shift_{self.curve_code}")

    @property
    def ctx_pivot_point(self):
        return getattr(self.ctx, f"pivot_point_{self.curve_code}")

    @property
    def ctx_tenor_start(self):
        return getattr(self.ctx, f"tenor_start_{self.curve_code}")

    @property
    def ctx_tenor_end(self):
        return getattr(self.ctx, f"tenor_end_{self.curve_code}")


class Priceable(Ctx):
    pass


class Eq(Priceable, metaclass=ABCMeta):

    @abstractmethod
    def price(self):
        pass

    @abstractmethod
    def eq_delta(self):
        pass

    @abstractmethod
    def eq_gamma(self):
        pass

    @abstractmethod
    def eq_vega(self):
        pass

    @abstractmethod
    def eq_theta(self):
        pass

    @abstractmethod
    def eq_rho(self):
        pass

    @abstractmethod
    def eq_rho_q(self):
        pass


class FX(Priceable, metaclass=ABCMeta):

    @abstractmethod
    def price(self):
        pass

    @abstractmethod
    def fx_delta(self):
        pass

    @abstractmethod
    def fx_gamma(self):
        pass

    @abstractmethod
    def fx_vega(self):
        pass

    @abstractmethod
    def fx_theta(self):
        pass

    @abstractmethod
    def fx_vanna(self):
        pass

    @abstractmethod
    def fx_volga(self):
        pass


class IR(Priceable, metaclass=ABCMeta):

    @abstractmethod
    def dv01(self):
        pass

    @abstractmethod
    def dollar_duration(self):
        pass

    @abstractmethod
    def dollar_convexity(self):
        pass


class CD(Priceable, metaclass=ABCMeta):

    @abstractmethod
    def dv01(self):
        pass

    @abstractmethod
    def dollar_duration(self):
        pass

    @abstractmethod
    def dollar_convexity(self):
        pass
