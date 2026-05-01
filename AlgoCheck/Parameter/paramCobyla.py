# COBYLA konvergencia- és érzékenységvizsgálat
import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
import os
import time
from itertools import product
from core import *
from filters import *
from scipy.optimize import minimize




def runCobylaWithHistory(obj, dim, maxiter, rhobeg, tol=1e-6):

    x0 = np.zeros(dim)
    negObj = NegObjectiveWrapper(obj)
    history = []
    bestVal = -np.inf
    iterationCounter = 0
    startTime = time.time()

    def callback(xk):
        nonlocal iterationCounter, bestVal
        iterationCounter += 1
        currObj = -negObj(xk)
        if np.isfinite(currObj) and currObj > bestVal:
            bestVal = currObj
        history.append({
            'iteration': iterationCounter,
            'currObject': currObj,
            'bestObject': bestVal,
            'timestamp': time.time() - startTime,
        })

    result = minimize(
        negObj,
        x0,
        method='COBYLA',
        callback=callback,
        options={'maxiter': maxiter, 'rhobeg': rhobeg, 'tol': tol, 'disp': False},
    )

    elapsed = time.time() - startTime
    if not history:
        history.append({
            'iteration': 0,
            'currObject': -result.fun,
            'bestObject': -result.fun,
            'timestamp': elapsed,
        })

    return result, history, elapsed, history[-1]['bestObject']


if __name__ == '__main__':
    dfSharadar = pd.read_csv('../storage/new/SHARADAR.csv')
    dfTickers = pd.read_csv('../storage/new/TICKERS.csv')
    sep = pd.read_csv(
        '../storage/new/SEP.csv',
        usecols=['date', 'ticker', 'closeadj'],
        parse_dates=['date'])

    testYearList = [2007, 2008,2009,2010,2011,2012,2013,2014,2015,2016,2017,2018,2019,2020,2021,2022,2023]
    maxIterGrid = [500, 1000, 1500, 2000]
    rhobegGrid = [0.5, 1.0, 1.5, 2, 2.5, 2.75, 3.0, 3.25, 3.5, 4.0]
    tol = 1e-6
    window = 7

    minTrainStart = min(testYearList) - window
    maxTrainEnd = max(testYearList)
    allYears = list(range(minTrainStart, maxTrainEnd + 1))
    allAnchors = [f'{year}-12-31' for year in allYears]

    precomputedData = precomputeBacktestData(dfSharadar, dfTickers,sep, allAnchors)

    allSensitivityRows = []

    for testYear in testYearList:
        trainEndYear = testYear - 1
        trainStartYear = trainEndYear - window + 1
        print(f'\n Tréning ablak: {trainStartYear}-{trainEndYear}')

        trainAnchorYears = [f'{y}-12-31' for y in range(trainStartYear, trainEndYear + 1)]
        if not all(a in precomputedData for a in trainAnchorYears):
            print(' KIHAGYVA: hiányos precomputed adat')
            continue

        dateWeights = anchorWeightsFromDates(trainAnchorYears)
        objCobyla = ObjectiveCalculator(
            trainAnchorYears,
            precomputedData,
            anchorWeights=dateWeights,
            topK=100,
            lambdaStd=0.5,
            l2Pen=0.01,
        )

        sensitivityRows = []
        historyRows = []
        comboIter = list(product(maxIterGrid, rhobegGrid))

        for maxIter, rhobeg in comboIter:
            print(f'    COBYLA érzékenység maxiter={maxIter}, rhobeg={rhobeg}')
            result, history, elapsed, bestObj = runCobylaWithHistory(objCobyla, NUM_BASKETS, maxIter, rhobeg, tol=tol)
            success = int(result.status == 1)
            sensitivityRows.append({
                'testYear': testYear,
                'maxiter': maxIter,
                'rhobeg': rhobeg,
                'bestObj': bestObj,
                'finalObj': -result.fun,
                'nfev': result.nfev,
                'status': result.status,
                'message': result.message,
                'success': success,
                'elapsedSec': elapsed,
            })
            for entry in history:
                historyRows.append({
                    'testYear': testYear,
                    'maxiter': maxIter,
                    'rhobeg': rhobeg,
                    'iteration': entry['iteration'],
                    'currObject': entry['currObject'],
                    'bestObject': entry['bestObject'],
                    'timestamp': entry['timestamp'],
                })

        if not sensitivityRows:
            print('Nincs COBYLA konvergencia adat')
            continue

        os.makedirs('thesisResults', exist_ok=True)
        sensDf = pd.DataFrame(sensitivityRows)
        histDf = pd.DataFrame(historyRows)


        pivotYear = sensDf.pivot(index='rhobeg', columns='maxiter', values='bestObj')
        plt.figure(figsize=(8, 4))
        sns.heatmap(pivotYear, annot=True, fmt='.4f', cmap='viridis')
        plt.title(f'COBYLA bestObj – {testYear}')
        plt.xlabel('maxiter')
        plt.ylabel('rhobeg')
        plt.tight_layout()
        yearHeatmapPath = f'thesisResults/cobylaHeatmap-{testYear}.png'
        plt.savefig(yearHeatmapPath, dpi=150)
        plt.close()
        print(f'  -> Heatmap mentve: {yearHeatmapPath}')

        allSensitivityRows.extend(sensitivityRows)

    if allSensitivityRows:
        print('Kész. Minden évhez külön heatmap készült a thesisResults mappában.')
