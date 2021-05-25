import sys
sys.path.append("..")

from turing_models.models.process_simulator import TuringVasicekNumericalScheme
from turing_models.models.process_simulator import TuringCIRNumericalScheme
from turing_models.models.process_simulator import TuringHestonNumericalScheme
from turing_models.models.process_simulator import TuringGBMNumericalScheme
from turing_models.models.process_simulator import TuringProcessTypes
from turing_models.models.process_simulator import TuringProcessSimulator

from TuringTestCases import TuringTestCases, globalTestCaseMode
testCases = TuringTestCases(__file__, globalTestCaseMode)

##########################################################################


def test_FinProcessSimulator():

    import time

    numPaths = 20000
    numAnnSteps = 100
    seed = 1919
    t = 1.0
    modelSim = TuringProcessSimulator()
    printPaths = False

    testCases.banner(
        "######################## GBM NORMAL ###############################")
    sigma = 0.10
    stockPrice = 100.0
    drift = 0.04
    scheme = TuringGBMNumericalScheme.NORMAL
    modelParams = (stockPrice, drift, sigma, scheme)
    start = time.time()
    paths = modelSim.getProcess(
        TuringProcessTypes.GBM,
        t,
        modelParams,
        numAnnSteps,
        numPaths,
        seed)
    end = time.time()
    elapsed = end - start
    testCases.header("PROCESS", "TIME")
    testCases.print("GBM NORMAL", elapsed)
    if printPaths:
        print(paths)

    testCases.banner(
        "######################## GBM ANTITHETIC ###########################")
    sigma = 0.10
    stockPrice = 100.0
    drift = 0.04
    scheme = TuringGBMNumericalScheme.ANTITHETIC
    modelParams = (stockPrice, drift, sigma, scheme)
    start = time.time()
    paths = modelSim.getProcess(
        TuringProcessTypes.GBM,
        t,
        modelParams,
        numAnnSteps,
        numPaths,
        seed)
    end = time.time()
    elapsed = end - start
    testCases.print("GBM ANTITHETIC", elapsed)
    if printPaths:
        print(paths)

    testCases.banner(
        "###################### HESTON EULER ###############################")
    stockPrice = 100.0
    v0 = 0.05
    kappa = 0.50
    theta = 0.05
    sigma = 0.90
    rho = -0.9
    scheme = TuringHestonNumericalScheme.EULER
    modelParams = (stockPrice, drift, v0, kappa, theta, sigma, rho, scheme)
    start = time.time()
    paths = modelSim.getProcess(
        TuringProcessTypes.HESTON,
        t,
        modelParams,
        numAnnSteps,
        numPaths,
        seed)
    end = time.time()
    elapsed = end - start
    testCases.print("HESTON EULER", elapsed)
    if printPaths:
        print(paths)

    testCases.banner(
        "###################### HESTON EULERLOG ############################")
    stockPrice = 100.0
    v0 = 0.05
    kappa = 0.50
    theta = 0.05
    sigma = 0.90
    rho = -0.9
    scheme = TuringHestonNumericalScheme.EULERLOG
    modelParams = (stockPrice, drift, v0, kappa, theta, sigma, rho, scheme)
    start = time.time()
    paths = modelSim.getProcess(
        TuringProcessTypes.HESTON,
        t,
        modelParams,
        numAnnSteps,
        numPaths,
        seed)
    end = time.time()
    elapsed = end - start
    testCases.print("HESTON EULERLOG", elapsed)
    if printPaths:
        print(paths)

    testCases.banner(
        "###################### HESTON QUADEXP #############################")
    stockPrice = 100.0
    v0 = 0.05
    kappa = 0.50
    theta = 0.05
    sigma = 0.90
    rho = -0.9
    scheme = TuringHestonNumericalScheme.QUADEXP
    modelParams = (stockPrice, drift, v0, kappa, theta, sigma, rho, scheme)
    start = time.time()
    paths = modelSim.getProcess(
        TuringProcessTypes.HESTON,
        t,
        modelParams,
        numAnnSteps,
        numPaths,
        seed)
    end = time.time()
    elapsed = end - start
    testCases.print("HESTON QUADEXP", elapsed)
    if printPaths:
        print(paths)

    testCases.banner(
        "######################## VASICEK NORMAL ###########################")
    r0 = 0.05
    kappa = 0.50
    theta = 0.05
    sigma = 0.90
    scheme = TuringVasicekNumericalScheme.NORMAL
    modelParams = (r0, kappa, theta, sigma, scheme)
    start = time.time()
    paths = modelSim.getProcess(
        TuringProcessTypes.VASICEK,
        t,
        modelParams,
        numAnnSteps,
        numPaths,
        seed)
    end = time.time()
    elapsed = end - start
    testCases.print("VASICEK_NORMAL", elapsed)
    if printPaths:
        print(paths)

    testCases.banner(
        "####################### VASICEK ANTITHETIC ########################")
    r0 = 0.05
    kappa = 0.50
    theta = 0.05
    sigma = 0.90
    scheme = TuringVasicekNumericalScheme.ANTITHETIC
    modelParams = (r0, kappa, theta, sigma, scheme)
    start = time.time()
    paths = modelSim.getProcess(
        TuringProcessTypes.VASICEK,
        t,
        modelParams,
        numAnnSteps,
        numPaths,
        seed)
    end = time.time()
    elapsed = end - start
    testCases.print("VASICEK_NORMAL ANTI", elapsed)
    if printPaths:
        print(paths)

    testCases.banner(
        "############################# CIR #################################")
    r0 = 0.05
    kappa = 0.50
    theta = 0.05
    sigma = 0.90
    scheme = TuringCIRNumericalScheme.MILSTEIN
    modelParams = (r0, kappa, theta, sigma, scheme)
    start = time.time()
    paths = modelSim.getProcess(
        TuringProcessTypes.CIR,
        t,
        modelParams,
        numAnnSteps,
        numPaths,
        seed)
    end = time.time()
    elapsed = end - start
    testCases.print("CIR", elapsed)
    if printPaths:
        print(paths)

###############################################################################


test_FinProcessSimulator()
testCases.compareTestCases()
