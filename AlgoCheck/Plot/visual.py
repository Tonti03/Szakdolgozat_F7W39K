import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import time
from datetime import datetime
import json

plt.style.use('seaborn-v0_8-darkgrid')
sns.set_palette('husl')

def calculateStatistics(results):
    '''Részletes statisztikák számítása'''
    stats = {}
    
    stats['yearlyMean'] = results.groupby('testYear')[['rDE', 'rCOBYLA']].mean()
    stats['yearlyStd'] = results.groupby('testYear')[['rDE', 'rCOBYLA']].std()
    stats['yearlyMedian'] = results.groupby('testYear')[['rDE', 'rCOBYLA']].median()
    
    stats['overallMean'] = results[['rDE', 'rCOBYLA']].mean()
    stats['overallStd'] = results[['rDE', 'rCOBYLA']].std()
    stats['overallMedian'] = results[['rDE', 'rCOBYLA']].median()
    stats['overallMin'] = results[['rDE', 'rCOBYLA']].min()
    stats['overallMax'] = results[['rDE', 'rCOBYLA']].max()
    
    stats['sharpeRatio'] = stats['overallMean'] / stats['overallStd']
    
    stats['winRate'] = (results[['rDE', 'rCOBYLA']] > 0).sum() / len(results)
    
    stats['cumulativeReturn'] = (1 + stats['yearlyMean'][['rDE', 'rCOBYLA']]).prod() - 1
    
    stats['diffMeanDeVsCobyla'] = stats['overallMean']['rDE'] - stats['overallMean']['rCOBYLA']
    
    stats['winsDe'] = (results['rDE'] > results['rCOBYLA']).sum()
    stats['winsCobyla'] = (results['rCOBYLA'] > results['rDE']).sum()
    
    return stats

def createComparisonTable(stats, deMaxiters):
    '''Összehasonlító táblázat létrehozása'''
    comparison = pd.DataFrame({

        f'DE ({deMaxiters} iter)': [
            f"{stats['overallMean']['rDE']*100:.2f}%",
            f"{stats['overallStd']['rDE']*100:.2f}%",
            f"{stats['overallMedian']['rDE']*100:.2f}%",
            f"{stats['overallMin']['rDE']*100:.2f}%",
            f"{stats['overallMax']['rDE']*100:.2f}%",
            f"{stats['sharpeRatio']['rDE']:.3f}",
            f"{stats['winRate']['rDE']*100:.1f}%",
            f"{stats['cumulativeReturn']['rDE']*100:.2f}%"
        ],
        'COBYLA': [
            f"{stats['overallMean']['rCOBYLA']*100:.2f}%",
            f"{stats['overallStd']['rCOBYLA']*100:.2f}%",
            f"{stats['overallMedian']['rCOBYLA']*100:.2f}%",
            f"{stats['overallMin']['rCOBYLA']*100:.2f}%",
            f"{stats['overallMax']['rCOBYLA']*100:.2f}%",
            f"{stats['sharpeRatio']['rCOBYLA']:.3f}",
            f"{stats['winRate']['rCOBYLA']*100:.1f}%",
            f"{stats['cumulativeReturn']['rCOBYLA']*100:.2f}%"
        ]
    }, index=[
        'Átlagos hozam',
        'Szórás',
        'Medián hozam',
        'Min hozam',
        'Max hozam',
        'Sharpe ratio',
        'Nyerési arány',
        'Kumulatív hozam'
    ])
    
    return comparison

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
    
    # Evenkenti hozamok
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
    ax2.set_title('Optimalizációs Módszerek Stabilitása (több seed átlaga)', fontsize=14, fontweight='bold')
    ax2.set_ylabel('Hozam (%)', fontsize=12)
    ax2.set_xlabel('Teszt év', fontsize=12)
    ax2.legend(title='', fontsize=11)
    plt.tight_layout()
    plt.savefig(f'{outputDir}/02StabilityBoxplot.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    # Violin plot
    fig3, ax3 = plt.subplots(figsize=(10, 6))
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
    

    
    # Heatmap DE
    fig7, ax7 = plt.subplots(figsize=(10, 8))
    pivotDe = results.pivot_table(values='rDE', index='runSeed', columns='testYear')
    sns.heatmap(pivotDe * 100, annot=True, fmt='.2f', cmap='RdYlGn', center=0, 
                ax=ax7, cbar_kws={'label': 'Hozam (%)'})
    ax7.set_title(f'{deLabel} Hozamok - Seed × Év Heatmap', fontsize=14, fontweight='bold')
    ax7.set_xlabel('Teszt év', fontsize=12)
    ax7.set_ylabel('Seed ID', fontsize=12)
    plt.tight_layout()
    plt.savefig(f'{outputDir}/07HeatmapDe.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    # Heatmap COBYLA
    fig8, ax8 = plt.subplots(figsize=(10, 8))
    pivotCobyla = results.pivot_table(values='rCOBYLA', index='runSeed', columns='testYear')
    sns.heatmap(pivotCobyla * 100, annot=True, fmt='.2f', cmap='RdYlGn', center=0, 
                ax=ax8, cbar_kws={'label': 'Hozam (%)'})
    ax8.set_title('COBYLA Hozamok - Seed × Év Heatmap', fontsize=14, fontweight='bold')
    ax8.set_xlabel('Teszt év', fontsize=12)
    ax8.set_ylabel('Seed ID', fontsize=12)
    plt.tight_layout()
    plt.savefig(f'{outputDir}/08HeatmapCobyla.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    # Scatter plot DE vs COBYLA
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
    

def generateLatexTable(comparisonDf, outputDir='thesisResults'):
    '''LaTeX táblázat generálása szakdolgozathoz'''
    latexCode = comparisonDf.to_latex(
        caption='Optimalizációs módszerek teljesítmény-összehasonlítása (DE vs COBYLA)',
        label='tab:optimizationComparison',
        column_format='lcc',
        escape=False
    )
    
    with open(f'{outputDir}/ComparisonTable.tex', 'w', encoding='utf-8') as f:
        f.write(latexCode)
    

def printThesisSummary(stats, elapsedTime, numRuns, testYearList, deMaxiters):
    '''Szakdolgozat összefoglaló kiíratása'''
    yearRangeStr = f'{min(testYearList)}-{max(testYearList)}'
    numYears = len(testYearList)
    deLabel = f'DE ({deMaxiters} iter)'
    
    print(f"\n{'-'*80}")
    print(f'SZAKDOLGOZAT - OPTIMALIZÁCIÓS MÓDSZEREK ÖSSZEHASONLÍTÁSA (DE vs COBYLA)')
    print(f"{'-'*80}")
    print(f"Futás időpontja: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f'Teljes futási idő: {elapsedTime/60:.1f} perc ({elapsedTime/3600:.2f} óra)')
    print(f'Ismétlések száma: {numRuns}')
    print(f'Teszt évek: {yearRangeStr} ({numYears} év)')

    print(f"\n{'-'*80}")
    print(f'ÖSSZESÍTETT EREDMÉNYEK')
    print(f"{'-'*80}")
    print(f"\n{'Metrika':<25} {deLabel:<18} {'COBYLA':<18}")
    print(f"{'-'*80}")
    print(f"{'Átlagos hozam':<25} {stats['overallMean']['rDE']*100:>18.2f}% {stats['overallMean']['rCOBYLA']*100:>18.2f}%")
    print(f"{'Szórás':<25} {stats['overallStd']['rDE']*100:>18.2f}% {stats['overallStd']['rCOBYLA']*100:>18.2f}%")
    print(f"{'Sharpe ratio':<25} {stats['sharpeRatio']['rDE']:>25.3f} {stats['sharpeRatio']['rCOBYLA']:>25.3f}")
    print(f"{'Nyerési arány':<25} {stats['winRate']['rDE']*100:>18.1f}% {stats['winRate']['rCOBYLA']*100:>18.1f}%")
    print(f"{'Kumulatív hozam':<25} {stats['cumulativeReturn']['rDE']*100:>18.2f}% {stats['cumulativeReturn']['rCOBYLA']*100:>18.2f}%")
    
    print(f"\n{'-'*80}")
    print(f'HEAD-TO-HEAD ÖSSZEHASONLÍTÁS')
    print(f"{'-'*80}")
    print(f'\nKülönbségek:')
    print(f"  DE - COBYLA:   {stats['diffMeanDeVsCobyla']*100:+.2f}%")
    
    print(f"\n{'-'*80}")
    print(f'ÉVENKÉNTI ÁTLAGOS HOZAMOK')
    print(f"{'-'*80}")
    yearlyComparison = pd.DataFrame({
        'DE (%)': (stats['yearlyMean']['rDE'] * 100).round(2),
        'COBYLA (%)': (stats['yearlyMean']['rCOBYLA'] * 100).round(2),
    })
    print(yearlyComparison.to_string())
    
    print(f"\n{'='*80}\n")




def summary(results, allWeights, testYearList, deMaxiters, elapsedTime, numRuns):

    print('\nStat számítása...')
    stats = calculateStatistics(results)
    

    comparisonTable = createComparisonTable(stats, deMaxiters)
    
    printThesisSummary(stats, elapsedTime, numRuns, testYearList, deMaxiters)
    
    import os
    os.makedirs('thesisResults', exist_ok=True)
    results.to_csv('thesisResults/WalkforwardResultsDetailed.csv', index=False)
    comparisonTable.to_csv('thesisResults/ComparisonSummary.csv')
    stats['yearlyMean'].to_csv('thesisResults/YearlyMean.csv')
    stats['yearlyStd'].to_csv('thesisResults/YearlyStd.csv')
    
    
    generateLatexTable(comparisonTable)
    
    plotAllVisualizations(results, stats, testYearList, deMaxiters)
    
    with pd.ExcelWriter('thesisResults/ThesisCompleteResults.xlsx', engine='openpyxl') as writer:
        results.to_excel(writer, sheet_name='Részletes eredmények', index=False)
        comparisonTable.to_excel(writer, sheet_name='Összehasonlítás')
        stats['yearlyMean'].to_excel(writer, sheet_name='Évenkénti átlagok')
        stats['yearlyStd'].to_excel(writer, sheet_name='Évenkénti szórások')
    
    weightsDetailDf = pd.DataFrame(allWeights)
    for col in ['wDE', 'wCOBYLA']:
        weightsDetailDf[col] = weightsDetailDf[col].apply(lambda arr: json.dumps(arr.tolist()) if arr is not None else json.dumps([]))
    weightsPath = os.path.join('thesisResults', 'weights.csv')
    weightsDetailDf.to_csv(weightsPath, index=False)