from .helper_functions import checkArgumentTypes
from .currency import TuringCurrencyTypes
from .math import ONE_MILLION

###############################################################################


class TuringAmount(object):
    ''' A TuringAmount is a holder for an amount in a specific currency. '''

    def __init__(self,
                 notional: float = ONE_MILLION,
                 currencyType: TuringCurrencyTypes = TuringCurrencyTypes.NONE):
        ''' Create TuringAmount object. '''

        checkArgumentTypes(self.__init__, locals())

        self._notional = notional
        self._currencyType = currencyType


    def __repr__(self):
        ''' Print out the details of the schedule and the actual dates. This
        can be used for providing transparency on schedule calculations. '''

        s = ""
        if self._currencyType != TuringCurrencyTypes.NONE:
            s += self._currencyType.name
            s += " "

        s += '{:,.2f}'.format(self._notional)
        
        return s

    def amount(self):
        return self._notional

    def _print(self):
        ''' Print out the details of the schedule and the actual dates. This
        can be used for providing transparency on schedule calculations. '''
        print(self)

###############################################################################


