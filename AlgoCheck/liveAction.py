
import time
from scipy.optimize import differential_evolution
import core as core
import databases as databases
from datetime import datetime
import pandas as pd
import pandas_market_calendars as mcal
import numpy as np
import os
import sys
import json
sys.path.append('.')
from dotenv import load_dotenv
load_dotenv()


def Opt(negObjDe, dim=None, maxiter=None, seed=None, workers=None):
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


if __name__ == "__main__":
    todayDate = datetime.now().strftime('%Y-%m-%d')
    dfSharadar = pd.read_csv('../storage/new/SHARADAR.csv')
    dfTickers = pd.read_csv('../storage/new/TICKERS.csv')
    sep = pd.read_csv(
        '../storage/new/SEP.csv',
        usecols=['date', 'ticker', 'closeadj'],
        parse_dates=['date'])
        
    now = datetime.now()     #datetime(2025, 1, 1)
    nyse = mcal.get_calendar('NYSE')
    startDate = f'{now.year}-05-01'
    endDate = f'{now.year}-05-07'

    schedule = nyse.schedule(start_date=startDate, end_date=endDate)

    firstTradingDay = schedule.index[0]

    if now < firstTradingDay:
        testYear = now.year - 2
    else:
        testYear = now.year - 1

    window = 7

    minTrainStart = testYear - window
    maxTrainEnd = testYear-1
    allYears = list(range(minTrainStart, maxTrainEnd + 1))
    allAnchors = [f'{year}-12-31' for year in allYears]
    precomputedData = core.precomputeBacktestData(dfSharadar, dfTickers, sep, allAnchors)
    baseSeeds = np.random.default_rng(42).integers(0, 2**32 - 1, size=50)
    topK = 40
    lambdaStd = 0.3
    l2Pen = 0.1
    maxiter=1000
    safeMax = max(1, os.cpu_count() - 2)
    allWeights = []
    for seed in baseSeeds:
        print(f'Teszt év: {testYear} | Seed: {seed}')
        print(f'Tréning ablak: {minTrainStart}-{maxTrainEnd}')

        dateWeights = core.anchorWeightsFromDates(allAnchors)
        obj = core.ObjectiveCalculator(allAnchors, precomputedData, anchorWeights=dateWeights, topK=topK, lambdaStd=lambdaStd, l2Pen=l2Pen)
        dim = core.NUM_BASKETS
        
        #--------------------------------------DE opt--------------------------------------
        print(f'DE optimalizáció indítása...')
        negObjDe = core.NegObjectiveWrapper(obj)
        bestVDE = Opt(negObjDe, dim=dim, maxiter=maxiter, seed=seed, workers=safeMax)
        bestWDE = core.softmax(bestVDE)
        #---------------------------------------------------------------------------------------------

        allWeights.append({
            'year': testYear,
            'runSeed': seed,
            'wDE': bestWDE,
        })

    print('vége---------')

    dfWeights = pd.DataFrame(allWeights)
    deAvg = dfWeights.groupby('year')['wDE'].apply(lambda x: np.mean(np.vstack(x), axis=0))




    programResultsWithTicker = []
    formattedTestYear = f'{testYear}-12-31'
    filteredDf = databases.elesDataFrame(dfSharadar, dfTickers, sep, formattedTestYear) 
    feats = core.buildFeaturedFrame(filteredDf)
        
    programResults= core.ReturnPortfolioTickers(feats, deAvg.loc[testYear], topK=topK)

    if isinstance(programResults, pd.DataFrame):
        tickers = programResults['ticker'].tolist()
    else:
        tickers = []


    print('---EredmenyKezd---')
    print(json.dumps(tickers))
    print('---EredmenyVeg---')


#autopep8 --in-place --recursive --select=E225,E303,W391 .