import os
from unittest import result
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import time
from datetime import datetime
import json
from scipy.optimize import differential_evolution, minimize
from core import *
from concurrent.futures import ProcessPoolExecutor
from tqdm import tqdm
from Plot.visual import summary

sTime = time.time()

def deOpt(negObjDe, dim=None, maxiter=None, seed=None, workers=None):
    deStart = time.time()

    resultDe = differential_evolution(
            negObjDe, 
            bounds = [(-10, 10)] * dim, 
            maxiter=maxiter, 
            polish=True, 
            updating='deferred', 
            workers=workers, 
            seed=seed,
            disp=False,
            strategy='rand1bin',   
            mutation=(0.7, 1.0),  
            recombination=0.7
        )
    elapsed = time.time() - deStart
    print(f'DE kész! Iterációk: {resultDe.nit}/{maxiter} | '
            f'Best obj: {-resultDe.fun:.6f} | Idő: {elapsed:.1f}s')   
    
    return resultDe.x

def cobylaOpt(negObj, dim):
    startTime = time.time()
    x0 = np.zeros(dim)
    
    result = minimize(
        negObj,
        x0,
        method='COBYLA',
        options={'maxiter': 1000, 'rhobeg': 3.5, 'tol': 1e-6}
    )
    
    elapsed = time.time() - startTime
    print(f'COBYLA kész! Iterációk: {result.nfev} | '
          f'Best obj: {-result.fun:.6f} | Idő: {elapsed:.1f}s')
    
    return result.x


#evolucios algoritmus
if __name__ == '__main__':
    print('Adatok betöltése...')
    dfSharadar = pd.read_csv('../storage/new/SHARADAR.csv')
    dfTickers = pd.read_csv('../storage/new/TICKERS.csv')
    sep = pd.read_csv(
    '../storage/new/SEP.csv',
    usecols=['date', 'ticker', 'closeadj'],
    parse_dates=['date'])

    # Beallitasok a Walk-Forward Analysis-hoz
    numRuns = 50
    testYearList = [2007, 2008,2009,2010,2011,2012,2013,2014,2015,2016,2017,2018,2019,2020,2021,2022,2023]
    topK = 40
    lambdaStd = 0.3
    l2Pen = 0.1
    maxiter=1000
    safeMax = max(1, os.cpu_count() - 2)
    #

    yearRangeStr = f'{min(testYearList)}-{max(testYearList)}'
    numYears = len(testYearList)
    
    print(f'\n Walk-Forward Analysis indítása...')
    print(f'   • Ismétlések: {numRuns}')
    print(f'   • Teszt évek: {yearRangeStr} ({numYears} év)')

    window = 7

    minTrainStart = min(testYearList) - window
    maxTrainEnd = max(testYearList) 
    allYears = list(range(minTrainStart, maxTrainEnd + 1))
    allAnchors = [f'{year}-12-31' for year in allYears]

    precomputedData = precomputeBacktestData(dfSharadar, dfTickers, sep, allAnchors)

    allWeights = []
    allResults = []
    cobylaCache = {}

    baseSeeds = np.random.default_rng(42).integers(0, 2**32 - 1, size=numRuns)

    for seed in baseSeeds:
        for testYear in testYearList:

            trainEndYear = testYear - 1
            trainStartYear = trainEndYear - window + 1
            print(f'-------------------------------')
            print(f'Teszt év: {testYear} | Seed: {seed}')
            print(f'Tréning ablak: {trainStartYear}-{trainEndYear}')

            trainAnchorYears = [f'{y}-12-31' for y in range(trainStartYear, trainEndYear + 1)]
            if not all(a in precomputedData for a in trainAnchorYears):
                    print(f'KIHAGYVA: hiányos precomputed adat')
                    continue
        
            dateWeights = anchorWeightsFromDates(trainAnchorYears)

            obj = ObjectiveCalculator(trainAnchorYears, precomputedData, anchorWeights=dateWeights, topK=topK, lambdaStd=lambdaStd, l2Pen=l2Pen)
            dim = NUM_BASKETS

            RStart = time.time()

            #--------------------------------------DE opt--------------------------------------
            print(f'DE optimalizáció indítása...')
            negObjDe = NegObjectiveWrapper(obj)
            bestVDE = deOpt(negObjDe, dim=NUM_BASKETS, maxiter=maxiter, seed=seed, workers=safeMax)
            bestWDE = softmax(bestVDE)
            #---------------------------------------------------------------------------------------------

            print('--')

            #--------------------------------------Cobyla opt--------------------------------------
            cacheKey = testYear
            if cacheKey not in cobylaCache:
                print(f'COBYLA optimalizáció indítása...')
                negObjCobyla = NegObjectiveWrapper(obj)
                bestVCobyla = cobylaOpt(negObjCobyla, dim=NUM_BASKETS)
                bestWCobyla = softmax(bestVCobyla)
                cobylaCache[cacheKey] = bestWCobyla
            else:
                print(f'COBYLA cache találat (már futott erre az évre)')
                bestWCobyla = cobylaCache[cacheKey]
            #---------------------------------------------------------------------------------------------


            print(f'Hozamok számítása teszt évre ({testYear})...')
            print(f'-------------------------------')
            testAnchor = f'{testYear}-12-31'
            feats, fwd = precomputedData.get(testAnchor, (None, None))

            if feats is None or fwd is None or feats.empty or fwd.empty:
                print(f'FIGYELEM: Nincs teszt adat {testAnchor}-ra!')
                rOpt = np.nan
                rOptDE = np.nan
                rOptCOBYLA = np.nan
            else:
                rOptDE = portfolioReturnForW(feats, fwd, bestWDE, topK=topK)
                rOptCOBYLA = portfolioReturnForW(feats, fwd, bestWCobyla, topK=topK)
                print(f'Teszt év hozama (DE): {rOptDE:.6f}')
                print(f'Teszt év hozama (COBYLA): {rOptCOBYLA:.6f}')

            allResults.append({
                'runSeed': seed,
                'testYear': testYear,
                'rDE': rOptDE,
                'rCOBYLA': rOptCOBYLA,
            })
            allWeights.append({
                'runSeed': seed,
                'testYear': testYear,
                'wDE': bestWDE,
                'wCOBYLA': bestWCobyla,
            })

    elapsedTime = time.time() - sTime

    allResultsDf = pd.DataFrame(allResults)
    allWeightsDf = pd.DataFrame(allWeights)

    summary(allResultsDf, allWeightsDf, testYearList, maxiter, elapsedTime, numRuns)