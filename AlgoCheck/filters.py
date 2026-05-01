import numpy as np 
import pandas as pd



def stableEps(group):
    group = group.sort_values(by='calendardate')
    lastFive = group.tail(5)

    if len(lastFive) < 5:
        return False

    epsVal = lastFive['eps'].values

    if pd.isna(epsVal).any():
        return False

    if any(epsVal <= 0):
        return False

    for i in range(1, len(epsVal)):
        if epsVal[i] < epsVal[i - 1]:
            return False
    return True

def stableRevenue(group):
    group = group.sort_values(by='calendardate')
    lastFive = group.tail(5)

    if len(lastFive) < 5:
        return False

    revenueVal = lastFive['revenue'].values

    if pd.isna(revenueVal).any():
        return False

    if any(revenueVal <= 0):
        return False

    for i in range(1, len(revenueVal)):
        if revenueVal[i] < revenueVal[i - 1]:
            return False
    return True

def stablePeRatio(group):
    group = group.sort_values(by='calendardate')
    lastThree = group.tail(3)

    if len(lastThree) < 3:
        return False
    
    peVal = lastThree['pe'].values

    if pd.isna(peVal).any():
        return False
    
    if any(peVal <= 0):
        return False
    
    avgPE = peVal.mean()
    
    return avgPE < 20

def debtToEquity(group):
  
    group = group.sort_values(by='calendardate')
    lastThree = group.tail(3)
    
    if len(lastThree) < 3:
        return False
    
    equityVal = lastThree['equityusd'].values
    debtVal = lastThree['debtusd'].values
    
    if pd.isna(equityVal).any() or pd.isna(debtVal).any():
        return False
    
    if any(equityVal <= 0) or any(debtVal < 0):
        return False
    
    for i in range(len(equityVal)):
        if equityVal[i] <= debtVal[i]:
            return False
    
    return True


def avgRoeAbove(group):

    group = group.sort_values(by='calendardate')
    lastThree = group.tail(3)

    if len(lastThree) <3:
        return False
    
    roeVal = lastThree['roe'].values

    if pd.isna(roeVal).any():
        return False

    if any(roeVal <= 0):
        return False

    avgROE = roeVal.mean()

    return avgROE > 0.15


def stablePbRatio(group):

    group = group.sort_values(by='calendardate')
    lastThree = group.tail(3)

    if len(lastThree) < 3:
        return False
    
    pbVal = lastThree['pb'].values

    if pd.isna(pbVal).any():
        return False
    
    if any(pbVal <= 0):
        return False
    
    avgPB = pbVal.mean()
    
    return avgPB < 3


def stableGrossMargin(group):

    group = group.sort_values(by='calendardate')
    lastFive = group.tail(5)

    if len(lastFive) < 5:
        return False

    marginVal = lastFive['grossmargin'].values

    if pd.isna(marginVal).any():
        return False

    if any(marginVal < 0.30):
        return False

    avgMargin = marginVal.mean()
    return avgMargin >= 0.35


def stableNetMargin(group):

    group = group.sort_values(by='calendardate')
    lastFive = group.tail(5)

    if len(lastFive) < 5:
        return False

    netMarginVal = lastFive['netmargin'].values

    if pd.isna(netMarginVal).any():
        return False

    if any(netMarginVal <= 0):
        return False

    avgNetMargin = netMarginVal.mean()
    return avgNetMargin >= 0.10


def stableCurrentRatio(group):

    group = group.sort_values(by='calendardate')
    lastThree = group.tail(3)
    if len(lastThree) < 3:
        return False

    if 'currentratio' in lastThree.columns:
        cr = pd.to_numeric(lastThree['currentratio'], errors='coerce').copy()
    else:
        cr = pd.Series(np.nan, index=lastThree.index, dtype='float64')

    if 'assetsc' in lastThree.columns and 'liabilitiesc' in lastThree.columns:
        assetsC  = pd.to_numeric(lastThree['assetsc'], errors='coerce')
        liabC    = pd.to_numeric(lastThree['liabilitiesc'], errors='coerce')

        liabC = liabC.mask(liabC <= 0, np.nan)

        crFallback = assetsC / liabC
        cr = cr.fillna(crFallback)

    if cr.isna().any():
        return False
    if (cr < 1.5).any():
        return False

    return True


def positiveFreeCashFlow(group):

    group = group.sort_values(by='calendardate')
    lastFive = group.tail(5)

    if len(lastFive) < 5:
        return False

    fcfVal = lastFive['fcf'].values

    if pd.isna(fcfVal).any():
        return False

    if any(fcfVal <= 0):
        return False

    return True


def growingFreeCashFlow(group):

    group = group.sort_values(by='calendardate')
    lastFive = group.tail(5)

    if len(lastFive) < 5:
        return False

    fcfVal = lastFive['fcf'].values

    if pd.isna(fcfVal).any():
        return False

    if any(fcfVal <= 0):
        return False

    for i in range(1, len(fcfVal)):
        if fcfVal[i] < fcfVal[i - 1]:
            return False

    return True


def stableRoic(group):

    group = group.sort_values(by='calendardate')
    lastFive = group.tail(5)

    if len(lastFive) < 5:
        return False

    roicVal = lastFive['roic'].values

    if pd.isna(roicVal).any():
        return False

    if any(roicVal <= 0):
        return False

    avgRoic = roicVal.mean()
    return avgRoic >= 0.15


def consistentDividends(group):

    group = group.sort_values(by='calendardate')
    lastFive = group.tail(5)

    if len(lastFive) < 5:
        return False

    dpsVal = lastFive['dps'].values

    if pd.isna(dpsVal).any():
        return False

    if any(dpsVal <= 0):
        return False

    for i in range(1, len(dpsVal)):
        if dpsVal[i] < dpsVal[i - 1]:
            return False

    return True


def sustainablePayout(group):

    group = group.sort_values(by='calendardate')
    lastThree = group.tail(3)

    if len(lastThree) < 3:
        return False

    payoutVal = lastThree['payoutratio'].values

    if pd.isna(payoutVal).any():
        return False

    if any(payoutVal <= 0):
        return False

    avgPayout = payoutVal.mean()
    return avgPayout < 0.70


def efficientAssetTurnover(group):

    group = group.sort_values(by='calendardate')
    lastThree = group.tail(3)

    if len(lastThree) < 3:
        return False

    turnoverVal = lastThree['assetturnover'].values

    if pd.isna(turnoverVal).any():
        return False

    if any(turnoverVal <= 0):
        return False

    avgTurnover = turnoverVal.mean()
    return avgTurnover >= 0.5


def lowCapexToRevenue(group):

    group = group.sort_values(by='calendardate')
    lastThree = group.tail(3)

    if len(lastThree) < 3:
        return False

    capexVal = lastThree['capex'].values
    revenueVal = lastThree['revenue'].values

    if pd.isna(capexVal).any() or pd.isna(revenueVal).any():
        return False

    if any(revenueVal <= 0):
        return False

    capexRatios = np.abs(capexVal) / revenueVal

    avgCapexRatio = capexRatios.mean()
    return avgCapexRatio < 0.10


def positiveRetainedEarnings(group):

    group = group.sort_values(by='calendardate')
    lastThree = group.tail(3)

    if len(lastThree) < 3:
        return False

    retearnVal = lastThree['retearn'].values

    if pd.isna(retearnVal).any():
        return False

    if any(retearnVal <= 0):
        return False

    return True


def growingBookValue(group):

    group = group.sort_values(by='calendardate')
    lastFive = group.tail(5)

    if len(lastFive) < 5:
        return False

    bvpsVal = lastFive['bvps'].values

    if pd.isna(bvpsVal).any():
        return False

    if any(bvpsVal <= 0):
        return False

    for i in range(1, len(bvpsVal)):
        if bvpsVal[i] < bvpsVal[i - 1]:
            return False

    return True


def lowPriceToSales(group):

    group = group.sort_values(by='calendardate')
    lastThree = group.tail(3)

    if len(lastThree) < 3:
        return False

    psVal = lastThree['ps'].values

    if pd.isna(psVal).any():
        return False

    if any(psVal <= 0):
        return False

    avgPS = psVal.mean()
    return avgPS < 2.5


def moderateEVToEBITDA(group):

    group = group.sort_values(by='calendardate')
    lastThree = group.tail(3)

    if len(lastThree) < 3:
        return False

    evEbitdaVal = lastThree['evebitda'].values

    if pd.isna(evEbitdaVal).any():
        return False

    if any(evEbitdaVal <= 0):
        return False

    avgEVEbitda = evEbitdaVal.mean()
    return avgEVEbitda < 12


def lowIntangibles(group):

    group = group.sort_values(by='calendardate')
    lastThree = group.tail(3)

    if len(lastThree) < 3:
        return False

    intangiblesVal = lastThree['intangibles'].values
    assetsVal = lastThree['assets'].values

    if pd.isna(intangiblesVal).any() or pd.isna(assetsVal).any():
        return False

    if any(assetsVal <= 0):
        return False

    intangiblesRatios = intangiblesVal / assetsVal
    avgIntangiblesRatio = intangiblesRatios.mean()

    return avgIntangiblesRatio < 0.20


def efficientWorkingCapital(group):
    group = group.sort_values(by='calendardate')
    lastThree = group.tail(3)

    if len(lastThree) < 3:
        return False

    wcVal = lastThree['workingcapital'].values

    if pd.isna(wcVal).any():
        return False

    if any(wcVal <= 0):
        return False

    return True


def largeMarketCap(group):

    group = group.sort_values(by='calendardate')
    latest = group.tail(1)
    
    if len(latest) < 1:
        return False
    
    marketcapVal = latest['marketcap'].values[0]
    
    if pd.isna(marketcapVal):
        return False
    
    return marketcapVal >= 1_000_000_000


def noShareDilution(group):

    group = group.sort_values(by='calendardate')
    lastFive = group.tail(5)
    
    if len(lastFive) < 5:
        return False
    
    sharesVal = lastFive['sharesbas'].values
    
    if pd.isna(sharesVal).any():
        return False
    
    if any(sharesVal <= 0):
        return False
    
    firstShares = sharesVal[0]
    lastShares = sharesVal[-1]
    
    dilutionRatio = (lastShares - firstShares) / firstShares
    
    return dilutionRatio <= 0.10


def strongInterestCoverage(group):
    minCov=5.0
    eps=1e-9
    group = group.sort_values(by='calendardate')
    lastThree = group.tail(3)
    if len(lastThree) < 3:
        return False
    if 'ebit' not in lastThree.columns or 'intexp' not in lastThree.columns:
        return False

    ebitVal   = pd.to_numeric(lastThree['ebit'],   errors='coerce').values
    intexpVal = pd.to_numeric(lastThree['intexp'], errors='coerce').values
    if np.isnan(ebitVal).any() or np.isnan(intexpVal).any():
        return False

    if np.all(np.abs(intexpVal) < eps):
        return True

    for ebit, iexp in zip(ebitVal, intexpVal):
        if abs(iexp) < eps:
            continue
        if ebit <= 0:
            return False
        coverage = ebit / abs(iexp)
        if coverage < minCov:
            return False

    return True  


def highEarningsQuality(group):

    group = group.sort_values(by='calendardate')
    lastThree = group.tail(3)
    
    if len(lastThree) < 3:
        return False
    
    ncfoVal = lastThree['ncfo'].values  # Operating Cash Flow
    netincVal = lastThree['netinccmn'].values  # Net Income
    
    if pd.isna(ncfoVal).any() or pd.isna(netincVal).any():
        return False
    
    for i in range(len(ncfoVal)):
        if ncfoVal[i] < netincVal[i]:
            return False
    
    return True


def consistentCashConversion(group):

    group = group.sort_values(by='calendardate')
    lastFive = group.tail(5)
    
    if len(lastFive) < 5:
        return False
    
    fcfVal = lastFive['fcf'].values
    netincVal = lastFive['netinccmn'].values
    
    if pd.isna(fcfVal).any() or pd.isna(netincVal).any():
        return False
    
    totalFcf = fcfVal.sum()
    totalNetinc = netincVal.sum()
    
    if totalNetinc <= 0:
        return False
    
    cashConversionRatio = totalFcf / totalNetinc
    
    return cashConversionRatio >= 0.70


def stableRevenueLargeCap(group):

    group = group.sort_values(by='calendardate')
    lastFive = group.tail(5)
    
    if len(lastFive) < 5:
        return False
    
    revenueVal = lastFive['revenue'].values
    
    if pd.isna(revenueVal).any():
        return False
    
    if any(revenueVal <= 0):
        return False
    
    avgRevenue = revenueVal.mean()
    if avgRevenue < 500_000_000:
        return False
    
    for i in range(1, len(revenueVal)):
        if revenueVal[i] < revenueVal[i - 1]: 
            return False
    
    return True


def lowDebtToAssets(group):

    group = group.sort_values(by='calendardate')
    lastThree = group.tail(3)
    
    if len(lastThree) < 3:
        return False
    
    debtVal = lastThree['debt'].values
    assetsVal = lastThree['assets'].values
    
    if pd.isna(debtVal).any() or pd.isna(assetsVal).any():
        return False
    
    if any(assetsVal <= 0):
        return False
    
    for i in range(len(debtVal)):
        debtToAssets = debtVal[i] / assetsVal[i]
        
        if debtToAssets > 0.50:
            return False
    
    return True











Funcs = [
    ('stableEps', stableEps),
    ('stableRevenue', stableRevenue),
    ('positiveFreeCashFlow', positiveFreeCashFlow),
    ('growingFreeCashFlow', growingFreeCashFlow),
    ('stableRoic', stableRoic),
    ('stablePeRatio', stablePeRatio),
    ('stablePbRatio', stablePbRatio),
    ('lowPriceToSales', lowPriceToSales),
    ('moderateEVToEBITDA', moderateEVToEBITDA),
    ('debtToEquity', debtToEquity),
    ('strongInterestCoverage', strongInterestCoverage),
    ('lowDebtToAssets', lowDebtToAssets),
    ('stableCurrentRatio', stableCurrentRatio),
    ('avgRoeAbove', avgRoeAbove),
    ('stableGrossMargin', stableGrossMargin),
    ('stableNetMargin', stableNetMargin),
    ('highEarningsQuality', highEarningsQuality),
    ('consistentCashConversion', consistentCashConversion),
    ('positiveRetainedEarnings', positiveRetainedEarnings),
    ('growingBookValue', growingBookValue),
    ('efficientAssetTurnover', efficientAssetTurnover),
    ('efficientWorkingCapital', efficientWorkingCapital),
    ('lowIntangibles', lowIntangibles),
    ('noShareDilution', noShareDilution),
    ('lowCapexToRevenue', lowCapexToRevenue),
    ('consistentDividends', consistentDividends),
    ('sustainablePayout', sustainablePayout),
    ('largeMarketCap', largeMarketCap),
    ('stableRevenueLargeCap', stableRevenueLargeCap)
]
funcNames = [n for n, _ in Funcs]

# kosarak
BASKETS = {
    'Value': [
        'positiveFreeCashFlow',
        'growingFreeCashFlow',
        'lowPriceToSales',
        'moderateEVToEBITDA',
        'stablePbRatio',
        'lowCapexToRevenue',
        'lowIntangibles',
    ],
    'Quality': [
        'stableEps',
        'stableRevenue',
        'stableRoic',
        'stablePeRatio',
        'avgRoeAbove',
        'stableGrossMargin',
        'stableNetMargin',
        'highEarningsQuality',
        'consistentCashConversion',
        'positiveRetainedEarnings',
        'growingBookValue',
        'efficientAssetTurnover',
    ],
    'Stability': [
        'debtToEquity',
        'strongInterestCoverage',
        'lowDebtToAssets',
        'stableCurrentRatio',
        'efficientWorkingCapital',
        'largeMarketCap',
        'stableRevenueLargeCap',
    ],
    'Shareholder': [
        'noShareDilution',
        'consistentDividends',
        'sustainablePayout',
    ],
}

basketNames = list(BASKETS.keys())
NUM_FACTORS = len(funcNames)
NUM_BASKETS = len(basketNames)
funcIndex = {name: idx for idx, name in enumerate(funcNames)}