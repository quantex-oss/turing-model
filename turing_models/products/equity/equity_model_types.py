


from turing_models.utilities.helper_functions import labelToString

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
#         s = labelToString("OBJECT TYPE", type(self).__name__)
#         s += labelToString("VOLATILITY", self._volatility)
#         s += labelToString("IMPLEMENTATION", self._implementation)
#         s += labelToString("PARAMETERS", self._parameters)
#         return s

###############################################################################


class TuringEquityModelHeston(TuringEquityModel):
    def __init__(self, volatility, meanReversion):
        self._parentType = TuringEquityModel
        self._volatility = volatility
        self._meanReversion = meanReversion
        self._implementation = 0

    def __repr__(self):
        s = labelToString("OBJECT TYPE", type(self).__name__)
        s += labelToString("VOLATILITY", self._volatility)
        s += labelToString("MEAN REVERSION", self._meanReversion)
        s += labelToString("IMPLEMENTATION", self._implementation)
        return s

###############################################################################
