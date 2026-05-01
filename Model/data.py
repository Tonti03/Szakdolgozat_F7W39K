import os 
import json
from datetime import datetime
import pandas_market_calendars as mcal

DATA='UserData.json'
TEST=[]

class DataManager:

    data = None
    def __init__(self):
        self.data=self.loadData()
        self.validDate()
    def loadData(self):
        if os.path.exists(DATA):
            with open(DATA,'r') as d:
                try:
                    return json.load(d)
                except json.JSONDecodeError:
                    return None
        else:
            return None
    
    def saveData(self, portfolio, riskLevel):
        nowStr =datetime.now().strftime('%Y-%m-%d')
        dataTemplate={'portfolio':portfolio if portfolio else TEST,'userInfo':{'riskLevel':riskLevel},'IsGenerated':False,'lastDate':nowStr}
        with open(DATA,'w') as d:
            json.dump(dataTemplate,d)
        self.data = dataTemplate
            
    def getPortfolio(self):
        return self.data['portfolio'] if self.data else []
    
    def getUserInfo(self):
        return self.data['userInfo'] if self.data else None
    
    def getIsGenerated(self):
        return self.data['IsGenerated'] if self.data else None
    
    def isRegistered(self):
        return self.data is not None


    def validDate(self):

        if self.data is None:
            return
            
        lastDateStr=self.data.get('lastDate')
        lastDate=datetime.strptime(lastDateStr, "%Y-%m-%d")
        now = datetime.now()
        startDate = f'{now.year}-05-01'
        endDate = f'{now.year}-05-07'
        nyse = mcal.get_calendar('NYSE')

        schedule = nyse.schedule(start_date=startDate, end_date=endDate)

        if schedule.empty:
            firstTradingDay = datetime(now.year, 5, 1)
        else:
            firstTradingDay = schedule.index[0]


        if now >= firstTradingDay and lastDate < firstTradingDay:
            self.data['IsGenerated'] = False
            with open(DATA, 'w') as d:
                    json.dump(self.data, d)

    def generatedSave(self,gen):
        nowStr =datetime.now().strftime('%Y-%m-%d')
        self.data['portfolio'] = gen 
        self.data['lastDate'] = nowStr
        self.data['IsGenerated'] = True
        with open(DATA, 'w') as d:
                    json.dump(self.data, d)

    def deleteTicker(self,deletableTickers):
        chosen=[]
        for i,y in deletableTickers:
            if y.get()==True:
                chosen.append(i)

        updatedPortfolio = [item for item in self.data['portfolio'] if item not in chosen]
        self.data['portfolio'] = updatedPortfolio
        
        with open(DATA, 'w') as d:
            json.dump(self.data, d)
        

    
        