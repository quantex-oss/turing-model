import numpy as np

import sys
sys.path.append("..")

from TuringTestCases import TuringTestCases, globalTestCaseMode
testCases = TuringTestCases(__file__, globalTestCaseMode)

##########################################################################
#
#def test_FinPieceCurve():
#
#    times = np.linspace(0.0, 1.0, 5)
#    values = np.ones(5) * 0.05
#
#    flatCurve = FinPieceCurve(times,values)
#
#    dfs = flatCurve.df(times, 0)
#    testCases.print(dfs)
#    dfs = flatCurve.df(times, 1)
#    testCases.print(dfs)
#    dfs = flatCurve.df(times, 2)
#    testCases.print(dfs)
#    dfs = flatCurve.df(times, -1)
#    testCases.print(dfs)

##########################################################################


#test_FinPieceCurve()
testCases.compareTestCases()
