#konvergencia vizsgalata
import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
from tqdm import tqdm 
import os
from scipy.optimize import differential_evolution, minimize
from concurrent.futures import ProcessPoolExecutor
import warnings
import datetime
import time
from filters import *
from core import *
safeMax = max(1, os.cpu_count() - 2)


def differentialEvolutionOptimizeWeightsSeed(obj, dim, bounds=None, maxiter=1000, seed=42, mutation=0.7, recombination=0.85, popsize=10, strategy='best1bin', tol=0.001,polish=True,):
    if bounds is None:
        bounds = [(-10, 10)] * dim

    convHistory = [] 
    
    print(
        f'DE indítása: maxiter={maxiter}, dim={dim}, seed={seed}, '
        f'F={mutation}, CR={recombination}, pop={popsize}, strat={strategy}'
    )
    startTime = time.time()

    iterationCounter = {'count': 0}
    bestTracker = {'val': -np.inf}
    
    def callback(xk, convergence):
        iterationCounter['count'] += 1
        currObj = -obj(xk)
        if np.isfinite(currObj) and currObj > bestTracker['val']:
            bestTracker['val'] = currObj
        convHistory.append({
            'iteration': iterationCounter['count'],
            'convergence': convergence,
            'bestObject': bestTracker['val'],
            'currObject': currObj,
            'timestamp': time.time() - startTime
        })  

        # Minden 50. iternel
        if iterationCounter['count'] % 50 == 0 or convergence < 0.01:
            elapsed = time.time() - startTime
            print(f"         ├─ Iteráció {iterationCounter['count']}/{maxiter} | "
                  f"Konvergencia: {convergence:.6f} | Curr obj: {currObj:.6f} | Best obj: {bestTracker['val']:.6f} | Idő: {elapsed:.1f}s")
        return False  # False = folytatás
    
    result = differential_evolution(
        obj, bounds, 
        maxiter=maxiter, 
        polish=polish, 
        mutation=mutation,
        recombination=recombination,
        popsize=popsize,
        strategy=strategy,
        tol=tol,
        updating='deferred', 
        workers=safeMax, 
        seed=seed,
        callback=callback,
        disp=False,
    )
    
    elapsed = time.time() - startTime
    print(f'DE kész! Iterációk: {result.nit}/{maxiter} | '
          f'Best obj: {-result.fun:.6f} | Idő: {elapsed:.1f}s')
    
    bestV = result.x
    bestW = softmax(bestV)
    bestObj = -result.fun 
    return bestW, bestObj, convHistory, result.nit



if __name__ == '__main__':
    dfSharadar = pd.read_csv('../storage/new/SHARADAR.csv')
    dfTickers = pd.read_csv('../storage/new/TICKERS.csv')
    sep = pd.read_csv(
    '../storage/new/SEP.csv',
    usecols=['date', 'ticker', 'closeadj'],
    parse_dates=['date'])
    testYearList = [2023]  
    maxIter = 800
    mutationGrid = [0.5, 0.6, 0.8,0.9,1.0]
    recombinationGrid = [0.5, 0.6, 0.7, 0.85]
    popsizeGrid = [15]
    strategyGrid = ['best1bin', 'rand1bin']
    seedsPerCombo = 4
    seedRng = np.random.default_rng(2024)
    
    window = 10

    minTrainStart = min(testYearList) - window
    maxTrainEnd = max(testYearList) 
    allYears = list(range(minTrainStart, maxTrainEnd + 1))
    allAnchors = [f'{year}-12-31' for year in allYears]

    precomputedData = precomputeBacktestData(dfSharadar, dfTickers, sep, allAnchors)

    gridResults = []
    convRecords = []

    for testYear in testYearList:

        trainEndYear = testYear - 1
        trainStartYear = trainEndYear - window + 1
        print(f'Tréning ablak: {trainStartYear}-{trainEndYear}')

        trainAnchorYears = [f'{y}-12-31' for y in range(trainStartYear, trainEndYear + 1)]
        if not all(a in precomputedData for a in trainAnchorYears):
            print(f'KIHAGYVA: hiányos precomputed adat')
            continue

        dateWeights = anchorWeightsFromDates(trainAnchorYears)
        objDe = ObjectiveCalculator(trainAnchorYears, precomputedData, anchorWeights=dateWeights, topK=50, lambdaStd=0.5, l2Pen=0.01,)
        negObjDe = NegObjectiveWrapper(objDe)

        for mutation in mutationGrid:
            for recombination in recombinationGrid:
                for popsize in popsizeGrid:
                    for strategy in strategyGrid:
                        for _ in range(seedsPerCombo):
                            seedVal = int(seedRng.integers(0, 2**32 - 1))
                            print(f'DE: F={mutation}, CR={recombination}, pop={popsize}, strat={strategy}, seed={seedVal} ...')
                            deStart = time.time()
                            _, deObj, convHistory, nit = differentialEvolutionOptimizeWeightsSeed(
                                negObjDe,
                                dim=NUM_BASKETS,
                                maxiter=maxIter,
                                seed=seedVal,
                                mutation=mutation,
                                recombination=recombination,
                                popsize=popsize,
                                strategy=strategy,
                                tol=0.001,
                                polish=True,
                            )
                            deTime = time.time() - deStart
                            print(f'seed={seedVal} | Obj: {deObj:.6f} | Idő: {deTime:.1f}s | Iteráció: {nit}')

                            gridResults.append({
                                'testYear': testYear,
                                'mutation': mutation,
                                'recombination': recombination,
                                'popsize': popsize,
                                'strategy': strategy,
                                'maxiter': maxIter,
                                'seed': seedVal,
                                'bestObj': deObj,
                                'runtimeSec': deTime,
                                'nit': nit,
                            })

                            for entry in convHistory:
                                convRecords.append({
                                    'testYear': testYear,
                                    'mutation': mutation,
                                    'recombination': recombination,
                                    'popsize': popsize,
                                    'strategy': strategy,
                                    'seed': seedVal,
                                    'iteration': entry['iteration'],
                                    'convergence': entry['convergence'],
                                    'currObject': entry.get('currObject', np.nan),
                                    'bestObject': entry.get('bestObject', np.nan),
                                    'timestamp': entry['timestamp'],
                                })

    os.makedirs('thesisResults', exist_ok=True)

    resultsDf = pd.DataFrame(gridResults)
    if not resultsDf.empty:
        resultsPath = 'thesisResults/deHypergridResults.csv'
        resultsDf.to_csv(resultsPath, index=False)
        print(f'DE rács eredmények mentve: {resultsPath}')

        agg = (
            resultsDf
            .groupby(['mutation', 'recombination', 'popsize', 'strategy', 'maxiter'])
            .agg(
                meanObj=('bestObj', 'mean'),
                stdObj=('bestObj', 'std'),
                count=('bestObj', 'count'),
                meanRuntimeSec=('runtimeSec', 'mean'),
            )
            .reset_index()
        )
        agg['stdObj'] = agg['stdObj'].fillna(0.0)
        agg['sem'] = agg['stdObj'] / np.sqrt(agg['count'].clip(lower=1))
        agg['lowerCi'] = agg['meanObj'] - 1.96 * agg['sem']
        agg['upperCi'] = agg['meanObj'] + 1.96 * agg['sem']
        agg = agg.sort_values('meanObj', ascending=False)

        statsPath = 'thesisResults/deComboStats.csv'
        agg.to_csv(statsPath, index=False)
        print(f'Kombó statisztikák mentve: {statsPath}')

        if not agg.empty:
            bestMean = agg.iloc[0]
            bestLower = agg.sort_values('lowerCi', ascending=False).iloc[0]
            print(
                f"Legjobb (átlag): F={bestMean['mutation']}, CR={bestMean['recombination']}, "
                f"pop={int(bestMean['popsize'])}, strat={bestMean['strategy']} | "
                f"meanObj={bestMean['meanObj']:.6f} | n={int(bestMean['count'])}"
            )
            print(
                f"Legjobb (lower CI): F={bestLower['mutation']}, CR={bestLower['recombination']}, "
                f"pop={int(bestLower['popsize'])}, strat={bestLower['strategy']} | "
                f"lowerCi={bestLower['lowerCi']:.6f} | n={int(bestLower['count'])}"
            )

            for (popsize, strategy), sub in agg.groupby(['popsize', 'strategy']):
                pivot = sub.pivot(index='mutation', columns='recombination', values='meanObj')
                plt.figure(figsize=(7, 4))
                sns.heatmap(pivot, annot=True, fmt='.5f', cmap='viridis')
                plt.title(f'DE mean obj – pop={int(popsize)}, strat={strategy}')
                plt.tight_layout()
                heatmapPath = f'thesisResults/deMeanobjHeatmap-pop{int(popsize)}-strat{strategy}.png'
                plt.savefig(heatmapPath, dpi=150)
                plt.close()
                print(f'Heatmap mentve: {heatmapPath}')

    else:
        print('Üres eredményhalmaz, nincs mit menteni.')

    convDf = pd.DataFrame(convRecords)
    if not convDf.empty:
        convPath = 'thesisResults/deConvHistory.csv'
        convDf.to_csv(convPath, index=False)
        print(f'Konvergencia-adatok mentve: {convPath}')
    else:
        print(' Üres konvergencia-halmaz, nincs mit ábrázolni.')
