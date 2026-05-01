from tqdm import tqdm
from databases import dataFrame
from filters import *




def featuredVectorForGroup(group):
    res = []
    for _, func in Funcs:
        try:
            res.append(1 if func(group) else 0)
        except:
            res.append(0)
    return np.array(res, dtype=int)

def buildFeaturedFrame(filteredDf):
    feats, tickers = [], []

    for t, g in filteredDf.groupby('ticker', sort=False):
        g = g.sort_values(by='calendardate')
        tickers.append(t)
        feats.append(featuredVectorForGroup(g))
    X = np.vstack(feats) if feats else np.zeros((0, NUM_FACTORS), dtype=int)

    if X.size == 0:
        return pd.DataFrame(columns=['ticker'] + basketNames)

    data = {'ticker': tickers}
    for basket, names in BASKETS.items():
        idxs = [funcIndex[name] for name in names]
        data[basket] = X[:, idxs].mean(axis=1)

    return pd.DataFrame(data, columns=['ticker'] + basketNames)

def forwardReturnsForDate(filteredDf, price):
    anchor = filteredDf['calendardate'].max()
    p0 = (filteredDf[filteredDf['calendardate'] == anchor][['ticker','majPrice']].dropna().rename(columns={'majPrice': 'price0'}).set_index('ticker'))
    p1 = price[['ticker', 'futurePrice']].dropna().set_index('ticker').rename(columns={'futurePrice': 'price1'})

    joined = p0.join(p1, how='inner').dropna()
    if joined.empty:
        return pd.DataFrame(columns=['ticker', 'fwd_ret'])#hozam

    joined['fwd_ret'] = (joined['price1'] - joined['price0']) / joined['price0']
    return joined.reset_index()[['ticker', 'fwd_ret']]

def precomputeBacktestData(dfSharadar, dfTickers, sep, anchors):


    print(f'Adatok előkészítése {len(anchors)} db dátumra')
    precomputedData = {}
    
    for date in tqdm(anchors, desc='Adatok előszámítása'):
        filteredDf, price = dataFrame(dfSharadar, dfTickers, sep, date) 
        feats = buildFeaturedFrame(filteredDf)
        fwd   = forwardReturnsForDate(filteredDf, price)
        if not fwd.empty:
            feats = feats[feats['ticker'].isin(fwd['ticker'])].reset_index(drop=True)
        else:
            feats = feats.iloc[0:0]
        precomputedData[date] = (feats, fwd)

        

    print('Előkészítés vége')
    return precomputedData

def anchorWeightsFromDates(anchors, recencyHalflifeYears=6):
    years = np.array([int(a[:4]) for a in anchors])
    baseYear = years.max()
    age = baseYear - years
    recencyW = 0.5 ** (age / float(recencyHalflifeYears))


    s = recencyW.sum()
    return (recencyW / s) if s > 0 else np.ones_like(recencyW) / len(recencyW)

def weightedMeanStd(x, w):
    x = np.asarray(x, float)
    w = np.asarray(w, float)
    w = w / w.sum()
    weightedAvg = np.sum(w * x)
    volatility = np.sqrt(np.sum(w * (x - weightedAvg) ** 2))
    return float(weightedAvg), float(volatility)

def softmax(v):
    v = np.asarray(v, float)
    v = v - v.max()
    e = np.exp(v)
    return e / e.sum()

def portfolioReturnForW(featureDf, fwdDf, w, topK=10):
    if featureDf.empty or fwdDf.empty:
        return np.nan
    scores = featureDf[basketNames].values.dot(w)
    tmp = featureDf[['ticker']].copy()
    tmp['score'] = scores
    tmp = tmp.merge(fwdDf, on='ticker', how='inner')
    if tmp.empty:
        return np.nan
    top = tmp.nlargest(topK, 'score')
    return float(top['fwd_ret'].mean())

class ObjectiveCalculator:

    def __init__(self, anchors, precomputedData, anchorWeights=None, topK=None, lambdaStd=None, l2Pen=None):

        if topK is None:
            raise ValueError('topK paraméter kötelező!')
        if lambdaStd is None:
            raise ValueError('lambdaStd paraméter kötelező!')
        if l2Pen is None:
            raise ValueError('l2Pen paraméter kötelező!')

        self.anchors = anchors
        self.anchorWeights = anchorWeights

        self.precomputedData = precomputedData
        self.topK = topK
        self.lambdaStd = lambdaStd
        self.l2Pen = l2Pen
        
        

    def __call__(self, v):

        w = softmax(v)
        rets, ws = [], []


        for date, aw in zip(self.anchors, self.anchorWeights):
            
            feats, fwd = self.precomputedData.get(date, (None, None))
            
            if feats is None or fwd is None:
                continue

            r = portfolioReturnForW(feats, fwd, w, topK=self.topK)
            
            if not np.isnan(r):
                rets.append(r); ws.append(aw)

        if len(rets) < 3:  
            return -1e6

        weightedAvg, volatility = weightedMeanStd(rets, ws) #sulyozott atlag es szoras

        return float(weightedAvg - self.lambdaStd * volatility - self.l2Pen * np.sum(w * w))        #atlagos hozam- buntetes a volatilitasert - sulyok negyzeteinek osszege buntet ha egy kosar tul nagy sulyt kap


class NegObjectiveWrapper:
    def __init__(self, obj):
        self.obj = obj
    def __call__(self, v):
        return -self.obj(v)



def portfolioReturnForWithTicker(featureDf, fwdDf, w, topK=10):
    if featureDf.empty or fwdDf.empty:
        return np.nan
    scores = featureDf[basketNames].values.dot(w)
    tmp = featureDf[['ticker']].copy()
    tmp['score'] = scores
    tmp = tmp.merge(fwdDf, on='ticker', how='inner')
    if tmp.empty:
        return np.nan
    top = tmp.nlargest(topK, 'score')
    return top


def ReturnPortfolioTickers(featureDf, w, topK=10):
    if featureDf.empty:
        return np.nan
    scores = featureDf[basketNames].values.dot(w)
    tmp = featureDf[['ticker']].copy()
    tmp['score'] = scores
    top = tmp.nlargest(topK, 'score')
    return top