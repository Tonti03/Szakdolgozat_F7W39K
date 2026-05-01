import pandas as pd
import ast
from core import *
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import time
from datetime import datetime
import json

#Vizualizaciot atemeltem a plotbol annak erdekeben hogy a seed átlag sulyaival tudjam osszehasonlitani a teljesitmenyt


plt.style.use('seaborn-v0_8-darkgrid')
sns.set_palette('husl')


def plotAllVisualizations(results, stats, testYearList, deMaxiters, outputDir='thesisResults'):
    '''Összes vizualizáció generálása'''
    import os
    os.makedirs(outputDir, exist_ok=True)
    
    yearRangeStr = f'{min(testYearList)}-{max(testYearList)}'
    deLabel = f'DE ({deMaxiters} iter)'
    
    resultsMelted = results.melt(id_vars=['testYear'], 
                                   value_vars=['rDE', 'rCOBYLA'],
                                   var_name='Módszer', value_name='Hozam')
    resultsMelted['Módszer'] = resultsMelted['Módszer'].map({
        'rDE': deLabel,
        'rCOBYLA': 'COBYLA'
    })
    resultsMelted['Hozam'] = resultsMelted['Hozam'] * 100
    
    colors = {deLabel: '#A23B72', 'COBYLA': '#F18F01'}
    
    fig1, ax1 = plt.subplots(figsize=(12, 6))
    yearlyMean = stats['yearlyMean'] * 100
    ax1.plot(yearlyMean.index, yearlyMean['rDE'], marker='s', linewidth=2, 
             markersize=8, label=deLabel, color=colors[deLabel])
    ax1.plot(yearlyMean.index, yearlyMean['rCOBYLA'], marker='^', linewidth=2, 
             markersize=8, label='COBYLA', color=colors['COBYLA'])
    ax1.axhline(0, color='gray', linestyle='--', alpha=0.5)
    ax1.set_xlabel('Teszt év', fontsize=12)
    ax1.set_ylabel('Átlagos hozam (%)', fontsize=12)
    ax1.set_title(f'Walk-Forward Backtesting Eredmények ({yearRangeStr})', fontsize=14, fontweight='bold')
    ax1.legend(fontsize=11)
    ax1.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(f'{outputDir}/01YearlyReturns.png', dpi=300, bbox_inches='tight')
    plt.close()
    
     # Boxplot
    fig2, ax2 = plt.subplots(figsize=(14, 6))
    sns.boxplot(data=resultsMelted, x='testYear', y='Hozam', hue='Módszer', ax=ax2, palette=colors)
    ax2.axhline(0, color='gray', linestyle='--', alpha=0.5)
    ax2.set_ylabel('Hozam (%)', fontsize=12)
    ax2.set_xlabel('Teszt év', fontsize=12)
    ax2.legend(title='', fontsize=11)
    plt.tight_layout()
    plt.savefig(f'{outputDir}/02StabilityBoxplot.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    # Violin plot 
    fig3, ax3 = plt.subplots(figsize=(10, 6))
    #sns.violinplot(data=resultsMelted, x='Módszer', y='Hozam', ax=ax3, palette=colors, inner='quartile') !!!!!!!!
    sns.violinplot(data=resultsMelted, x='Módszer', y='Hozam', hue='Módszer', ax=ax3, palette=colors, inner='quartile', legend=False)
    ax3.axhline(0, color='gray', linestyle='--', alpha=0.5)
    ax3.set_title('Hozam Eloszlások Összehasonlítása', fontsize=14, fontweight='bold')
    ax3.set_ylabel('Hozam (%)', fontsize=12)
    ax3.set_xlabel('')
    plt.tight_layout()
    plt.savefig(f'{outputDir}/03DistributionViolin.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    # Kumulativ hozam 
    fig4, ax4 = plt.subplots(figsize=(12, 6))
    yearlyCumsumDe = ((1 + stats['yearlyMean']['rDE']).cumprod() - 1) * 100
    yearlyCumsumCobyla = ((1 + stats['yearlyMean']['rCOBYLA']).cumprod() - 1) * 100
    ax4.plot(yearlyCumsumDe.index, yearlyCumsumDe.values, marker='s', 
             linewidth=2, markersize=8, label=deLabel, color=colors[deLabel])
    ax4.plot(yearlyCumsumCobyla.index, yearlyCumsumCobyla.values, marker='^', 
             linewidth=2, markersize=8, label='COBYLA', color=colors['COBYLA'])
    ax4.set_xlabel('Teszt év', fontsize=12)
    ax4.set_ylabel('Kumulatív hozam (%)', fontsize=12)
    ax4.set_title('Kumulatív Hozamok Alakulása', fontsize=14, fontweight='bold')
    ax4.legend(fontsize=11)
    ax4.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(f'{outputDir}/04CumulativeReturns.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    # Bar chart
    fig5, ax5 = plt.subplots(figsize=(14, 6))
    x = np.arange(len(yearlyMean.index))
    width = 0.35
    ax5.bar(x - width/2, yearlyMean['rDE'], width, label=deLabel, color=colors[deLabel], alpha=0.8)
    ax5.bar(x + width/2, yearlyMean['rCOBYLA'], width, label='COBYLA', color=colors['COBYLA'], alpha=0.8)
    ax5.axhline(0, color='gray', linestyle='--', alpha=0.5)
    ax5.set_xlabel('Teszt év', fontsize=12)
    ax5.set_ylabel('Átlagos hozam (%)', fontsize=12)
    ax5.set_title('Évenkénti Teljesítmény Összehasonlítás', fontsize=14, fontweight='bold')
    ax5.set_xticks(x)
    ax5.set_xticklabels(yearlyMean.index)
    ax5.legend(fontsize=11)
    ax5.grid(True, alpha=0.3, axis='y')
    plt.tight_layout()
    plt.savefig(f'{outputDir}/05YearlyComparisonBars.png', dpi=300, bbox_inches='tight')
    plt.close()

    
    # Scatter plot
    fig9, ax9 = plt.subplots(figsize=(8, 8))
    
    # DE vs COBYLA
    ax9.scatter(results['rCOBYLA'] * 100, results['rDE'] * 100, alpha=0.6, s=100, 
                 edgecolors='black', color='#6A4C93')
    limsC = [min(results[['rCOBYLA', 'rDE']].min()) * 100 - 2, 
              max(results[['rCOBYLA', 'rDE']].max()) * 100 + 2]
    ax9.plot(limsC, limsC, 'k--', alpha=0.5, linewidth=2)
    ax9.set_xlim(limsC)
    ax9.set_ylim(limsC)
    ax9.set_xlabel('COBYLA hozam (%)', fontsize=11)
    ax9.set_ylabel(f'{deLabel} hozam (%)', fontsize=11)
    ax9.set_title('DE vs. COBYLA', fontsize=12, fontweight='bold')
    ax9.grid(True, alpha=0.3)
    ax9.set_aspect('equal')
    
    plt.tight_layout()
    plt.savefig(f'{outputDir}/09ScatterComparisons.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    # Ridge plot / Density plot
    fig10, ax10 = plt.subplots(figsize=(12, 6))
    for method, color in colors.items():
        data = resultsMelted[resultsMelted['Módszer'] == method]['Hozam']
        data.plot.kde(ax=ax10, label=method, linewidth=2.5, color=color)
    ax10.axvline(0, color='gray', linestyle='--', alpha=0.5)
    ax10.set_xlabel('Hozam (%)', fontsize=12)
    ax10.set_ylabel('Sűrűség', fontsize=12)
    ax10.set_title('Hozam Eloszlások (KDE)', fontsize=14, fontweight='bold')
    ax10.legend(fontsize=11)
    ax10.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(f'{outputDir}/10DensityPlot.png', dpi=300, bbox_inches='tight')
    plt.close()
    




def cumulative(returns):
    cum = [1.0]
    for r in returns:
        cum.append(cum[-1] * (1 + r))
    return cum[1:]

def CAGR(returns):
    returns = np.array(returns)
    if len(returns) == 0:
        return 0.0
    product = np.prod(1 + returns)
    return (product ** (1 / len(returns))) - 1

dfSharadar = pd.read_csv('../storage/new/SHARADAR.csv')
dfTickers = pd.read_csv('../storage/new/TICKERS.csv')
sep = pd.read_csv(
    '../storage/new/SEP.csv',
    usecols=['date', 'ticker', 'closeadj'],
    parse_dates=['date'])

df = pd.read_csv('AlgoCheck/runResult/weights.csv')
df['wDE'] = df['wDE'].apply(ast.literal_eval)
df['wCOBYLA'] = df['wCOBYLA'].apply(ast.literal_eval) 

weightsDE = pd.DataFrame(df['wDE'].tolist(), index=df.index)
weightsDE['Year'] = df['testYear']
deAvg = weightsDE.groupby('Year').mean().reset_index()

weightsCOBYLA = pd.DataFrame(df['wCOBYLA'].tolist(), index=df.index)
weightsCOBYLA['Year'] = df['testYear']
cobylaAvg = weightsCOBYLA.groupby('Year').mean().reset_index()

deDict = deAvg.set_index('Year').to_dict(orient='index')
finalDictDE = {year: list(values.values()) for year, values in deDict.items()}

cobylaDict = cobylaAvg.set_index('Year').to_dict(orient='index')
finalDictCOBYLA = {year: list(values.values()) for year, values in cobylaDict.items()}

years = [f'{y}-12-31' for y in finalDictDE.keys()]

precomputedData = precomputeBacktestData(dfSharadar, dfTickers, sep, years)

spDataRaw = ['-36.09', '39.89', '15.51', '5.56', '15.15', '21.56', '14.21', '0.9', '17.2', '13.37', '12.35', '-1.21', '50.61', '0.51', '2.04', '22.3', '13.18']
spYears = [2007, 2008, 2009, 2010, 2011, 2012, 2013, 2014, 2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023]
shvRaw = [1.4929, 0.1536, 0.1770, -0.0036, 0.0354, 0.0381, 0.0000, 0.1769, 0.3394, 0.9611, 2.1582, 2.3355, -0.0244, -0.2797, 2.5869, 5.2404, 4.8677]


spReturns = []
shvReturns=[]
for val in spDataRaw:
    spReturns.append(float(val) / 100.0)

for val in shvRaw:
    shvReturns.append(float(val)/100.0)


programReturns = []
programResultsWithTicker = []
programReturnsCOBYLA = [] 

resultsList = []

print(f"{'Year Interval':<25} {'De':<10} {'cobyla':<10}")

for year in finalDictDE.keys():
    formYear = f'{year}-12-31'
    feats, fwd = precomputedData.get(formYear, (None, None))
    
    rOptDE = portfolioReturnForW(feats, fwd, finalDictDE.get(year), topK=40)
    programReturns.append(rOptDE)
    programResultsWithTicker.append(portfolioReturnForWithTicker(feats, fwd, finalDictDE.get(year), topK=40))

    rOptCOBYLA = portfolioReturnForW(feats, fwd, finalDictCOBYLA.get(year), topK=40)
    programReturnsCOBYLA.append(rOptCOBYLA)
    
    label = f'{year+1} Máj. - {year+2} Máj.'
    print(f'{label:<25} {rOptDE*100:<9.2f}% {rOptCOBYLA*100:<9.2f}%')

    resultsList.append({
        'testYear': year,
        'rDE': rOptDE,
        'rCOBYLA': rOptCOBYLA
    })


progCum = cumulative(programReturns)
progCumCOBYLA = cumulative(programReturnsCOBYLA)
marketCum = cumulative(spReturns)

progAvg = CAGR(programReturns) 
progStd = np.std(programReturns, ddof=1)
progAvgCOBYLA = CAGR(programReturnsCOBYLA) 
progStdCOBYLA = np.std(programReturnsCOBYLA, ddof=1)
marketAvg = CAGR(spReturns) 
marketStd = np.std(spReturns, ddof=1)



resultsDf = pd.DataFrame(resultsList)
testYearList = sorted(list(finalDictDE.keys()))

statsDf = pd.DataFrame({
    'rDE': programReturns,
    'rCOBYLA': programReturnsCOBYLA
}, index=testYearList)
stats = {'yearlyMean': statsDf}

plotAllVisualizations(resultsDf, stats, testYearList, deMaxiters=1000)
print(f'COBYLA éves átlag: {progAvgCOBYLA*100:.2f}%')
print(f'COBYLA szórás: {progStdCOBYLA*100:.2f}%')
print(f'DE éves átlag: {progAvg*100:.2f}%')
print(f'DE szórás: {progStd*100:.2f}%')


statsText = (
    f'DE:\n  Avg (CAGR): {progAvg*100:.2f}%\n  Std: {progStd*100:.2f}%\n\n'
    f'S&P 500:\n  Avg (CAGR): {marketAvg*100:.2f}%\n  Std: {marketStd*100:.2f}%'
)

fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 14))

plotYears = [y + 1 for y in spYears]

ax1.plot(plotYears, progCum, label='Program (DE)', marker='o')
ax1.plot(plotYears, marketCum, label='S&P 500', marker='x')
ax1.set_title('Kumulált hozam összehasonlítsa')
ax1.text(0.02, 0.95, statsText, transform=ax1.transAxes, verticalalignment='top',
         bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
ax1.set_xlabel('Év')
ax1.set_ylabel('1 egység növekedés')
ax1.legend()
ax1.grid(True)

cellText = []
rowColors = []

for i in range(len(spYears)):
    pRet = programReturns[i]
    sRet = spReturns[i]
    
    pRetStr = f'{pRet*100:.2f}%'
    sRetStr = f'{sRet*100:.2f}%'
    diff = pRet - sRet
    
    year = spYears[i]
    label = f'{year+1} Május - {year+2} Május'
    row = [label, pRetStr, sRetStr]
    cellText.append(row)
    
    if pRet > sRet:
        rowColors.append('lightgreen')
    else:
        rowColors.append('white')

table = ax2.table(
    cellText=cellText,
    colLabels=['Évszakasz', 'DE', 'S&P 500'],
    cellColours=[[c]*3 for c in rowColors],
    loc='center'
)
table.auto_set_font_size(False)
table.set_fontsize(10)
table.scale(1, 1.5)
ax2.axis('off')

plt.tight_layout()
plt.savefig('AlgoCheck/Comp.png')

    

#sector arany
sectorSeries = []
yrs = list(finalDictDE.keys())

for i, withTicker in enumerate(programResultsWithTicker):

    merged = withTicker.merge(dfTickers[['ticker', 'sector']], on='ticker', how='left')
    counts = merged['sector'].value_counts()
    counts.name = yrs[i]
    sectorSeries.append(counts)

sectorDf = pd.DataFrame(sectorSeries).fillna(0)
sectorDfPct = sectorDf.div(sectorDf.sum(axis=1), axis=0) * 100
    
figSec, axSec = plt.subplots(figsize=(14, 8))
sectorDfPct.plot(kind='bar', stacked=True, ax=axSec, colormap='tab20', alpha=0.9, width=0.8)
    
axSec.set_ylabel('Portfólió arány (%)', fontsize=12)
axSec.set_xlabel('Teszt év', fontsize=12)
axSec.set_title(f'Szektor Allokáció az évek során (DE Top {40})', fontsize=14, fontweight='bold')
    
axSec.legend(title='Szektor', bbox_to_anchor=(1.01, 1), loc='upper left', fontsize=10)
    
axSec.grid(True, axis='y', alpha=0.3, linestyle='--')
plt.tight_layout()
    
plt.savefig('AlgoCheck/SectorDE.png')




#kosar arany
weights = deAvg.set_index('Year')
weights.columns = basketNames
weightPercent = weights * 100

figBasket, axBasket = plt.subplots(figsize=(14, 8))
weightPercent.plot(kind='bar', stacked=True, ax=axBasket, colormap='Set2', alpha=0.9, width=0.8)

axBasket.set_ylabel('Súlyozás (%)', fontsize=12)
axBasket.set_xlabel('Hozam év', fontsize=12)
axBasket.set_title(f'Átlagos kosár súlyok az évek során (DE)', fontsize=14, fontweight='bold')
axBasket.legend(title='Stratégia kosarak', bbox_to_anchor=(1.01, 1), loc='upper left', fontsize=10)

axBasket.grid(True, axis='y', alpha=0.3, linestyle='--')
plt.tight_layout()

plt.savefig('AlgoCheck/WeightsDe.png')

utility = programResultsWithTicker[-1].merge(dfTickers[['ticker', 'sector']].drop_duplicates(), on='ticker', how='left')
pd.set_option('display.max_rows', None)    
pd.set_option('display.max_columns', None) 
pd.set_option('display.width', 1000)        
print(utility)
plt.close()


#shv-de alg
lowRisk = []
mediumRisk = []
highRisk = []
plt.figure(figsize=(12, 7))

print('DE algorimus hozam : SHV etf hozam')
for i, f in zip(shvReturns,programReturns):
    print(f'{f:.2f} : {i:.2f}')
    lowRisk.append(i * 0.75 + f * 0.25)
    mediumRisk.append(i * 0.5 + f * 0.5)
    highRisk.append(i * 0.25 + f * 0.75)

textShv = (
    f'Alacsony kockázat:\n  Avg (CAGR): {CAGR(lowRisk)*100:.2f}%\n  Std: {np.std(lowRisk, ddof=1)*100:.2f}%\n\n'
    f'Közepes kockázat:\n  Avg (CAGR): {CAGR(mediumRisk)*100:.2f}%\n  Std: {np.std(mediumRisk, ddof=1)*100:.2f}%\n\n'
    f'Magas kockázat:\n  Avg (CAGR): {CAGR(highRisk)*100:.2f}%\n  Std: {np.std(highRisk, ddof=1)*100:.2f}%'
)


plt.plot(plotYears, lowRisk, marker='o',label='Alacsony kockázat - 75% SHV / 25% DE')
plt.plot(plotYears, mediumRisk, marker='x',label='Közepes kockázat - 50% SHV /50% DE')
plt.plot(plotYears, highRisk, label='Magas kockázat - 25% SHV /75% DE')
plt.title('Portfólió stratégiák teljesítménye')
plt.xlabel('Év')
plt.ylabel('Return')
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.text(
    0.02, 0.95, textShv,
    transform=plt.gca().transAxes,
    va='top',
    bbox=dict(boxstyle='round', facecolor='white', alpha=0.8)
)
plt.savefig("shvDEalg.png", dpi=200, bbox_inches="tight")

