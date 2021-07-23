from turing_models.utilities.helper_functions import to_string

###############################################################################


class TuringEquityModel(object):
    ''' This is a parent class for equity models. '''

    def __init__(self):
        pass

###############################################################################


# class TuringEquityModelBlackScholes(TuringEquityModel):
#     def __init__(self,
#                  volatility: float,
#                  implementation, parameters):
#
#         checkArgumentTypes(self.__init__, locals())
#
#         self._volatility = volatility
#         self._implementation = implementation
#         self._parameters = parameters
#
#     def __repr__(self):
#         s = label_to_string("OBJECT TYPE", type(self).__name__)
#         s += label_to_string("VOLATILITY", self._volatility)
#         s += label_to_string("IMPLEMENTATION", self._implementation)
#         s += label_to_string("PARAMETERS", self._parameters)
#         return s

###############################################################################


class TuringEquityModelHeston(TuringEquityModel):
    def __init__(self, volatility, meanReversion):
        self._parentType = TuringEquityModel
        self._volatility = volatility
        self._meanReversion = meanReversion
        self._implementation = 0

    def __repr__(self):
        s = to_string("OBJECT TYPE", type(self).__name__)
        s += to_string("VOLATILITY", self._volatility)
        s += to_string("MEAN REVERSION", self._meanReversion)
        s += to_string("IMPLEMENTATION", self._implementation)
        return s

###############################################################################
