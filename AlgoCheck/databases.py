import pandas as pd 
import numpy as np 


def dataFrame(dfSharadar,dfTickers,sep,date):
    #-- adatbazisom tisztitasa
    if dfTickers['ticker'].duplicated().any():
        dfTickers = dfTickers.drop_duplicates(subset=['ticker'], keep='first')

    mergedDf = pd.merge(dfSharadar,dfTickers[['ticker', 'name', 'sector', 'industry', 'scalemarketcap', 'exchange','currency']],on='ticker',how='inner')  

    latestDate = mergedDf[(mergedDf['currency'] == 'USD') & (mergedDf['dimension'] == 'MRY')].groupby('ticker')['calendardate'].max()

    validTickers = latestDate[latestDate >= date].index

    filteredDf = mergedDf[(mergedDf['currency'] == 'USD') & (mergedDf['dimension'] == 'MRY') & (mergedDf['ticker'].isin(validTickers)) & (mergedDf['calendardate'] <= date)]

    tickersWithTargetDate = filteredDf[filteredDf['calendardate'] == date]['ticker'].unique()
    filteredDf = filteredDf[filteredDf['ticker'].isin(tickersWithTargetDate)]

    validTickets = []
    for ticker in filteredDf['ticker'].unique():
        years = pd.to_datetime(filteredDf[filteredDf['ticker'] == ticker]['calendardate']).dt.year.sort_values(ascending=False)
        if len(years) >= 5:
            top5 = years[:5]
            if all(np.diff(top5) == -1):
                validTickets.append(ticker)
    filteredDf = filteredDf[filteredDf['ticker'].isin(validTickets)]#csak azok lehetnek akiknek van 5 adata es az az EGYMASKOVETO elmult 5 evbol van
    columnsToRemove = [ 'reportperiod', 'fiscalperiod', 'lastupdated','price']
    filteredDf = filteredDf.drop(columns=columnsToRemove) 
    #Sector szures
    defensiveSectors = ['Consumer Defensive', 'Healthcare', 'Utilities']
    filteredDf = filteredDf[filteredDf['sector'].isin(defensiveSectors)]

    #reszveny arak lekerdezese
    sep['date'] = pd.to_datetime(sep['date'])
    year = pd.to_datetime(date).year 

    # 1 evvel kesobbi ar
    sepmaj1 = sep[(sep['date'].dt.year == year + 1) & (sep['date'].dt.month == 5)]

    #ARY
    firstMajDate = sepmaj1['date'].min() if len(sepmaj1) > 0 else None
    sharadarAry = dfSharadar[(dfSharadar['dimension'] == 'ARY') & (dfSharadar['fiscalperiod'] == f'{year}-FY') & (pd.to_datetime(dfSharadar['datekey']) < firstMajDate)]
    validTick = sharadarAry['ticker'].unique()
    filteredDf = filteredDf[filteredDf['ticker'].isin(validTick)]#csak azok lehetnek akik kiadtak a jelentest majus 1 elott

    # 2 evvel kesobbi ar
    sepmaj2 = sep[(sep['date'].dt.year == year + 2) & (sep['date'].dt.month == 5)]

    if len(sepmaj1) > 0:
        firstMajDateY1 = sepmaj1['date'].min()
        #majus elso ara
        majPrices = sep[sep['date'] == firstMajDateY1][['ticker', 'closeadj']].rename(columns={'closeadj': 'majPrice'})
        filteredDf = pd.merge(filteredDf, majPrices, on='ticker', how='left')
    else:
        #ha nincs legyen nan ertek
        filteredDf['majPrice'] = np.nan

    if len(sepmaj2) > 0:
        firstMajDateY2 = sepmaj2['date'].min()
        futurePrices = sep[sep['date'] == firstMajDateY2][['ticker', 'closeadj']].rename(columns={'closeadj': 'futurePrice'})
    else:
        futurePrices = pd.DataFrame(columns=['ticker', 'futurePrice'])


    filteredDf = filteredDf[filteredDf['majPrice'].notna()]


    filteredDf = pd.merge(filteredDf, futurePrices, on='ticker', how='left')
    missingMask = filteredDf['futurePrice'].isna()#kik tuntek el
    missingTickers = filteredDf.loc[missingMask, 'ticker'].unique()
    if len(missingTickers) > 0:
        targetDate = firstMajDateY2 if 'firstMajDateY2' in locals() else None
        if targetDate:
        
            relevantSep = sep[(sep['ticker'].isin(missingTickers)) & (sep['date'] <= targetDate)]
            lastPrices = relevantSep.sort_values('date').groupby('ticker')['closeadj'].last()
            filteredDf.loc[missingMask, 'futurePrice'] = filteredDf.loc[missingMask, 'ticker'].map(lastPrices)
    stillMissing = filteredDf[filteredDf['futurePrice'].isna()]
    if len(stillMissing) > 0:
        print(f'FIGYELEM: {len(stillMissing)} tickernél egyáltalán nincs ár adat -> Ezeket TÖRÖLJÜK.')
        filteredDf = filteredDf.dropna(subset=['futurePrice'])
    

    price = filteredDf[['ticker', 'futurePrice']].drop_duplicates()

    futureTickers = price['ticker'].unique()
    filteredDf = filteredDf[filteredDf['ticker'].isin(futureTickers)]
    filteredDf = filteredDf.drop(columns='futurePrice') 


    return filteredDf, price






def elesDataFrame(dfSharadar,dfTickers,sep,date):
    #-- adatbazisom tisztitasa
    if dfTickers['ticker'].duplicated().any():
        dfTickers = dfTickers.drop_duplicates(subset=['ticker'], keep='first')

    mergedDf = pd.merge(dfSharadar,dfTickers[['ticker', 'name', 'sector', 'industry', 'scalemarketcap', 'exchange','currency']],on='ticker',how='inner')  

    latestDate = mergedDf[(mergedDf['currency'] == 'USD') & (mergedDf['dimension'] == 'MRY')].groupby('ticker')['calendardate'].max()

    validTickers = latestDate[latestDate >= date].index

    filteredDf = mergedDf[(mergedDf['currency'] == 'USD') & (mergedDf['dimension'] == 'MRY') & (mergedDf['ticker'].isin(validTickers)) & (mergedDf['calendardate'] <= date)]

    tickersWithTargetDate = filteredDf[filteredDf['calendardate'] == date]['ticker'].unique()
    filteredDf = filteredDf[filteredDf['ticker'].isin(tickersWithTargetDate)]

    validTickets = []
    for ticker in filteredDf['ticker'].unique():
        years = pd.to_datetime(filteredDf[filteredDf['ticker'] == ticker]['calendardate']).dt.year.sort_values(ascending=False)
        if len(years) >= 5:
            top5 = years[:5]
            if all(np.diff(top5) == -1):
                validTickets.append(ticker)
    filteredDf = filteredDf[filteredDf['ticker'].isin(validTickets)]#csak azok lehetnek akiknek van 5 adata es az az EGYMASKOVETO elmult 5 evbol van
    columnsToRemove = [ 'reportperiod', 'fiscalperiod', 'lastupdated','price']
    filteredDf = filteredDf.drop(columns=columnsToRemove) 
    #Sector szures
    defensiveSectors = ['Consumer Defensive', 'Healthcare', 'Utilities']
    filteredDf = filteredDf[filteredDf['sector'].isin(defensiveSectors)]

    #reszveny arak lekerdezese
    sep['date'] = pd.to_datetime(sep['date'])
    year = pd.to_datetime(date).year 

    # 1 evvel kesobbi ar
    sepmaj1 = sep[(sep['date'].dt.year == year + 1) & (sep['date'].dt.month == 5)]

    #ARY
    firstMajDate = sepmaj1['date'].min() if len(sepmaj1) > 0 else None
    sharadarAry = dfSharadar[(dfSharadar['dimension'] == 'ARY') & (dfSharadar['fiscalperiod'] == f'{year}-FY') & (pd.to_datetime(dfSharadar['datekey']) < firstMajDate)]
    validTick = sharadarAry['ticker'].unique()
    filteredDf = filteredDf[filteredDf['ticker'].isin(validTick)]#csak azok lehetnek akik kiadtak a jelentest majus 1 elott

    if len(sepmaj1) > 0:
        firstMajDateY1 = sepmaj1['date'].min()
        #majus elso ara
        majPrices = sep[sep['date'] == firstMajDateY1][['ticker', 'closeadj']].rename(columns={'closeadj': 'majPrice'})
        filteredDf = pd.merge(filteredDf, majPrices, on='ticker', how='left')
    else:
        #ha nincs legyen nan ertek
        filteredDf['majPrice'] = np.nan

    filteredDf = filteredDf[filteredDf['majPrice'].notna()]

    return filteredDf