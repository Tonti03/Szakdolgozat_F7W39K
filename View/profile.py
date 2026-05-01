import subprocess
import customtkinter as ctk
import yfinance as yf
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import pandas_market_calendars as mcal
from datetime import datetime, timedelta
import pandas as pd
import matplotlib.ticker as ticker
import threading 
import subprocess 
import sys 
import os
import json


class PortfolioSelection(ctk.CTkToplevel):
    def __init__(self,master,callback,currPortfolio,generatedPortfolio):
        super().__init__(master)
        self.callback= callback
        self.portfolio = currPortfolio
        self.generatedPortfolio = generatedPortfolio
        self.grid_rowconfigure(0,weight=0)
        self.grid_rowconfigure(1,weight=1)
        self.grid_rowconfigure(2,weight=0)
        self.grid_columnconfigure(0,weight=1)
        self.title('Portfólió Bővítése')
        self.geometry('400x500')
        self.attributes('-topmost',True)

        self.top = ctk.CTkFrame(self, fg_color='transparent')
        self.top.grid(column=0, row=0, sticky='nsew',pady=(20, 10))

        ctk.CTkLabel(self.top, text='Portfólió Bővítése', font=('Roboto', 24, 'bold')).pack()
        ctk.CTkLabel(self.top, text='Válassza ki a hozzáadni kívánt elemeket', font=('Roboto', 13), text_color='gray').pack(pady=(5, 0))

        self.restPlace = ctk.CTkScrollableFrame(self, fg_color='transparent')
        self.restPlace.grid(column=0, row=1, sticky='nsew',padx=20)
        self.checkboxes = []

        itemsAdded = False
        for i in self.generatedPortfolio:
            if i not in self.portfolio:
                itemsAdded = True
                var = ctk.BooleanVar(value=True)
                chk = ctk.CTkCheckBox(self.restPlace, text=f'{i}', variable=var, font=('Roboto', 14), corner_radius=50) 
                chk.pack(pady=8, anchor='w', padx=10)
                self.checkboxes.append((i,var))
        
        if not itemsAdded:
            ctk.CTkLabel(self.restPlace, text='Minden ajánlott részvény már a portfólió része.', font=('Roboto', 14), text_color='gray').pack(pady=20)
        

        self.bottomPlace = ctk.CTkFrame(self,fg_color='#242424')
        self.bottomPlace.grid(column=0, row= 2, sticky='nsew')
        self.bottomPlace.grid_columnconfigure(0,weight=1)
        self.bottomPlace.grid_columnconfigure(1,weight=1)

        ctk.CTkButton(self.bottomPlace,text='Mentés',font=('Arial', 15, 'bold'), command = lambda:self.saveSelection(self.checkboxes)).grid(column=1, row=0, sticky='e',padx=10,pady=20)
        ctk.CTkButton(self.bottomPlace,text='Mégsem',font=('Arial', 15, 'bold'), command = lambda: self.master.master.restartApplication()).grid(column=0, row=0, sticky='w',padx=10,pady=20)
        self.protocol('WM_DELETE_WINDOW', lambda:self.master.master.restartApplication())

    def saveSelection(self, resourceStocks):
        chosen=[]
        for i,y in resourceStocks:
            if y.get()==True:
                chosen.append(i)
        chosen += self.portfolio
        self.callback(chosen)









class ProfileDisplay(ctk.CTkFrame):
    def __init__(self,master,dataManager):
        super().__init__(master)
        self.dataManager = dataManager
        self.riskLevel = self.dataManager.getUserInfo()['riskLevel']
        self.portfolio = self.dataManager.getPortfolio()
        self.isGenerated = self.dataManager.getIsGenerated()
        self.riskDict = {1:'🟢 Alacsony',2:'🟡 Közepes',3:'🔴 Magas'}
        self.currChart = None
        self.timeRemain = timedelta(0)
        self.grid_rowconfigure(0, weight=0)
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=9)

        self.sideBar = ctk.CTkFrame(self,fg_color = '#1B1B1B')
        self.sideBar.grid(row=0, column = 0, rowspan=2, sticky='nsew')

        self.topBar = ctk.CTkFrame(self, fg_color='#242424')
        self.topBar.grid(row=0,column=1,sticky='nsew')

        self.rest = ctk.CTkFrame(self)
        self.rest.grid(row=1,column=1,sticky='nsew')

        if self.portfolio == []:
            self.topBar.grid_columnconfigure(1,weight=1)
            error=ctk.CTkLabel(self.topBar,text='Nincsen rendelkezésre álló portfólió', text_color='red')
            error.grid(row=0,column=0)
        else:
            self.top()
        self.side()
        



    def top(self):

        self.topBar.grid_columnconfigure(1, weight=1)
        self.topBar.grid_columnconfigure(2, weight=2)
        left = ctk.CTkFrame(self.topBar,fg_color='#242424' )
        left.grid(row=0,column = 1, sticky='nsew')
        midRight = ctk.CTkFrame(self.topBar,fg_color='#242424' )
        midRight.grid(row=0,column = 2, sticky='nsew')


        ctk.CTkLabel(left, text='Stock portfólió hozam:', font=('Arial', 20, 'bold')).pack(pady=(20,10),padx=20)
        now = datetime.now()
        startDate = f'{now.year}-05-01'
        endDate = f'{now.year}-05-07'
        nyse = mcal.get_calendar('NYSE')

        schedule = nyse.schedule(start_date=startDate, end_date=endDate)

        firstTradingDay = schedule.index[0]
        origiFirstTradingDay = firstTradingDay
        shvReturn = 0
        avgStockReturn =0

        if len(self.portfolio) > 0:
            if now < firstTradingDay:
                startDate = f'{now.year-1}-05-01'
                endDate = f'{now.year-1}-05-07'
                schedule = nyse.schedule(start_date=startDate, end_date=endDate)
                firstTradingDay = schedule.index[0]

            totalReturn= 0
            stockNum = 0

            try:
                tick= self.portfolio + ['SHV']
                data = yf.download(tick, start=firstTradingDay, progress=False, auto_adjust=True)['Close']
                if 'SHV' in data.columns:
                    etfData = data['SHV']
                    data = data.drop(columns=['SHV'])

                    shvClean=etfData.dropna()
                    if len(shvClean)>0:
                        shvStart = shvClean.iloc[0]
                        shvEnd = shvClean.iloc[-1]
                        shvReturn = (shvEnd - shvStart) / shvStart
                        print(shvReturn)
                    else:
                        shvReturn=0
                else:
                    shvReturn=0
                
                
                
                
                
                
                if isinstance(data, pd.Series):
                    data = data.to_frame(name=self.portfolio[0])
                validData = data.dropna(axis=1, how ='all')

                if len(validData.columns) == len(self.portfolio) and len(validData)>0:
                    validData = validData.bfill().ffill()
                    startP = validData.iloc[0]
                    endP = validData.iloc[-1]
                    returns = (endP-startP)/startP
                    avgStockReturn = returns.mean()

                    shvWeight = {1: 0.75, 2: 0.50, 3: 0.25}.get(self.riskLevel, 0)
                    stockWeight = 1 - shvWeight

                    finalReturn = (avgStockReturn * stockWeight) + (shvReturn * shvWeight)
                    finalReturnPercent = finalReturn * 100


                    if finalReturnPercent >= 0:
                        ctk.CTkLabel(left,text= f'{finalReturnPercent:.2f}%', font=('Roboto', 20, 'bold'), text_color='#00FF00').pack(padx=20)
                    else:
                        ctk.CTkLabel(left,text= f'{finalReturnPercent:.2f}%', font=('Roboto', 20, 'bold'), text_color='#FF4444').pack(padx=20)

                else:
                    missing = [i for i in self.portfolio if i not in validData.columns]
                    print(f'Hiányzó árfolyam:{missing}')
                    ctk.CTkLabel(left,text= 'Adathiba, így nem mutatható ki a teljes részvénycsomag hozama!', font=('Arial', 10), text_color='red').pack(padx=20)
            except Exception as excep:
                print(f'Fatal error: {excep}')
                ctk.CTkLabel(left,text= 'Adathiba, így nem mutatható ki a teljes részvénycsomag hozama!', font=('Arial', 10), text_color='red').pack(padx=20)

        ctk.CTkLabel(left,text= f'Ref. date: {firstTradingDay}', font=('Arial', 8, 'bold'), text_color='white').pack(padx=20)

        ctk.CTkOptionMenu(left, values=self.portfolio, fg_color='#1A1A1A', text_color='white', command = self.stockDetails).pack(pady=(10,10),padx=20)
        if len(self.portfolio) > 0:
            self.stockDetails(self.portfolio[0])
        else:
            ctk.CTkLabel(left,text= 'Nincsen részvény a portfoliódban', font=('Arial', 10), text_color='red').pack(pady=10,padx=20)


        ctk.CTkLabel(midRight, text='Portfolió Felosztása:', font=('Arial', 20, 'bold')).pack(pady=(20, 10), padx=20, anchor='w')

        shvWeight = {1: 0.75, 2: 0.50, 3: 0.25}.get(self.riskLevel, 0)
        stockWeight = 1 - shvWeight
        bar = ctk.CTkFrame(midRight,height=45, fg_color='transparent') 
        bar.pack(fill='x', padx=20,pady=10)

        stockBar =ctk.CTkFrame(bar, fg_color='#3B8ED0', height=45,corner_radius=2)
        
        etfBar = ctk.CTkFrame(bar, fg_color='#2CC985',height=45, corner_radius=2)
        stockBar.grid(row=0,column=0, sticky='nsew')
        etfBar.grid(row=0, column=1, sticky='nsew')
        bar.grid_columnconfigure(0,weight=int(stockWeight * 100))
        bar.grid_columnconfigure(1, weight=int(shvWeight * 100))

        stockText = f'{int(stockWeight * 100)}%\n({avgStockReturn * 100:+.2f}%)'
        etfText = f'{int(shvWeight * 100)}%\n({shvReturn * 100:+.2f}%)'
        ctk.CTkLabel(stockBar,text=stockText,text_color='white',font=('Arial', 12, 'bold')).place(relx=0.5, rely=0.5, anchor='center')
        ctk.CTkLabel(etfBar, text=etfText, text_color='white', font=('Arial', 12,'bold')).place(relx=0.5,rely=0.5, anchor='center')
        
        label = ctk.CTkFrame(midRight, fg_color='transparent')
        label.pack(fill='x', padx=20, pady=5)

        l1 = ctk.CTkFrame(label, fg_color='transparent')
        l2 = ctk.CTkFrame(label, fg_color='transparent')
        l1.pack(side='left', padx=(0, 20))
        l2.pack(side='left')
        ctk.CTkFrame(l1, width=15, height=15, fg_color='#3B8ED0').pack(side='left', padx=(0, 5))
        ctk.CTkLabel(l1, text='Részvénycsomag', font=('Arial', 12)).pack(side='left')
        ctk.CTkFrame(l2, width=15, height=15, fg_color='#2CC985').pack(side='left', padx=(0, 5))
        ctk.CTkLabel(l2, text='iShares Short Treasury Bond (SHV)', font=('Arial', 12)).pack(side='left')

        
        if now > origiFirstTradingDay:
            
            if self.isGenerated:
                nextYearStart= f'{now.year+1}-05-01'
                nextYearEnd =f'{now.year+1}-05-07'
                try:
                    nextSchedule =nyse.schedule(start_date=nextYearStart, end_date=nextYearEnd)
                    origiFirstTradingDay = nextSchedule.index[0]
                except:
                    origiFirstTradingDay = origiFirstTradingDay.replace(year=now.year + 1)

                self.timeRemain = origiFirstTradingDay - now       
            else:
                self.timeRemain = origiFirstTradingDay - now 
                
        else:
            self.timeRemain = origiFirstTradingDay - now



        





    def side(self):
        ctk.CTkLabel(self.sideBar, text='Üdvözöljük!', font=('Arial', 20, 'bold')).pack(pady=20,padx=20)
        ctk.CTkLabel(self.sideBar, text='Kockázati szint:', font=('Arial', 16, 'bold')).pack(pady=(20,5),padx=20)
        ctk.CTkLabel(self.sideBar, text=self.riskDict[self.riskLevel], font=('Arial', 14, 'bold')).pack(pady=(5,20),padx=10)
        line = ctk.CTkFrame(self.sideBar,height=5, fg_color='#555555')
        line.pack(fill='x', padx=20,pady=10)
        ctk.CTkLabel(self.sideBar,text=f'Új portfólió:',font=('Arial', 16, 'bold')).pack(pady=(10,0))
        
        showButton=False

        if self.isGenerated == False or self.timeRemain.total_seconds() <=0:
            showButton = True

        if showButton:
            ctk.CTkLabel(self.sideBar, text='Esedékes a generálás',text_color='orange', font=('Arial', 14, 'bold')).pack(pady=5)
            self.runAlg=ctk.CTkButton(self.sideBar,text='Generálás',command=lambda:self.startAlg())
            self.runAlg.pack(pady=5)
            self.status = ctk.CTkLabel(self.sideBar, text='', font=('Arial', 10))
            self.status.pack(pady=0)
        else:
            ctk.CTkLabel(self.sideBar, text=f'{self.timeRemain.days} nap', font=('Arial', 13, 'bold')).pack(pady=10)

        line = ctk.CTkFrame(self.sideBar,height=5, fg_color='#555555')
        line.pack(fill='x', padx=20,pady=10)

        if self.portfolio != []:
            self.stockList = ctk.CTkScrollableFrame(self.sideBar,label_text='Részvényeim')
            self.stockList.pack(pady=10,padx=20)
            selectedTick=[]
            for i in self.portfolio:
                var = ctk.BooleanVar(value=False)
                chk = ctk.CTkCheckBox(self.stockList, text=f'{i}', variable = var,font=('Roboto', 14), corner_radius=30)
                chk.pack(pady=5)
                selectedTick.append((i,var))
            removeButton=ctk.CTkButton(self.sideBar,text='Törlés', fg_color='darkred', hover_color='#8B0000',command=lambda:self.deleteSelection(selectedTick),font=('Arial', 14, 'bold'))
            removeButton.pack(pady=10,padx=20)
            removeButton.configure(state='disabled')
            def checkSelection(*args):
                selected = False
                for ticker, var in selectedTick:
                    if var.get() == True:
                        selected = True
                
                if selected:
                    removeButton.configure(state='normal')
                else:
                    removeButton.configure(state='disabled')

            for ticker, var in selectedTick:
                var.trace('w', checkSelection)

        

        ctk.CTkButton(self.sideBar,text='Kilépés', font=('Arial', 14, 'bold'), fg_color='darkred', hover_color='#8B0000', command=lambda: self.master.quit()).pack(pady=(5,20), padx=20, fill='x',side='bottom')
        ctk.CTkButton(self.sideBar, text='Oldal Frissítése', font=('Arial', 14, 'bold'),command=lambda: self.master.restartApplication(), fg_color='grey', hover_color='darkgrey').pack(pady=(10,5), padx=20, fill='x',side='bottom')
        line = ctk.CTkFrame(self.sideBar,height=5, fg_color='#555555')
        line.pack(fill='x', padx=20,pady=10,side='bottom')   
               
    def deleteSelection(self, selectedTick):
        self.dataManager.deleteTicker(selectedTick)
        self.master.restartApplication()


    
             
        
    def startAlg(self):
        self.runAlg.configure(state='disabled',text='Futtatás...')
        self.status.configure(text='Algoritmus fut...', text_color='orange')
        threading.Thread(target=lambda:self.runAlgInMultipleThread(), daemon=True).start()

    def runAlgInMultipleThread(self):
        projectRoot= os.getcwd()
        dePath =os.path.join(projectRoot, 'AlgoCheck', 'liveAction.py')

        env = os.environ.copy()
        algDir = os.path.join(dePath, 'AlgoCheck')
        env['PYTHONPATH'] = f'{dePath}{os.pathsep}{algDir}{os.pathsep}{env.get('PYTHONPATH', '')}'

        try:#cwd=projectRoot ugy futtatja mintha a liveAction itt. állna ebben a mappaban
            cmd = [sys.executable, '-u', dePath]
            process= subprocess.Popen(cmd,cwd=projectRoot,env=env,stdout=subprocess.PIPE, stderr=subprocess.STDOUT,text=True,  bufsize=1)

            getText= False
            generatedPortfolio = None

            while True:
                line = process.stdout.readline()
                if not line and process.poll() is not None:
                    break
                
                if line:
                    print(f'[LiveAction]: {line.strip()}') 
                    if '---EredmenyKezd---' in line:
                        getText = True
                        continue

                    if getText == True and '---EredmenyVeg---' not in line:
                        try:
                            generatedPortfolio = json.loads(line.strip())
                            getText = False
                        except Exception as err:
                            print(f'{err}')
                            getText = False

            returnCode = process.poll()

            if returnCode == 0:
                
                if generatedPortfolio == None:
                    self.after(0, lambda: self.algoFinished(False, msg='Futási hiba'))
                else:
                #proba = ['NVDA', 'AMD', 'TSLA'] 
                    self.after(0, lambda: self.algoFinished(True,proba=generatedPortfolio))
            else:
                print(f'Hiba kód: {returnCode}')
                self.after(0, lambda: self.algoFinished(False, msg='Futási hiba'))#amit lehet futtassa
        except Exception as e:
            print(f'Hiba:{e}')
            self.after(0, lambda: self.algoFinished(False, msg=str(e)))

    def algoFinished(self,success,msg=None,proba=None):
        if success == True:
            PortfolioSelection(self,self.retrn,self.portfolio,proba)
        else:
            print(f'Hiba:{msg}')
            ctk.CTkLabel(self.sideBar, text=f'Hiba:{msg}',text_color='red', font=('Arial', 10, 'bold')).pack(pady=5)

    def retrn(self,chosenStocks):

        self.dataManager.generatedSave(chosenStocks)
        self.master.restartApplication()

         
        
    
    def stockDetails(self,stock):
        for widger in self.rest.winfo_children():
            widger.destroy()
        self.currChart = None
        stockData = yf.Ticker(stock)

        currPrice = stockData.info.get('currentPrice', 0)
        lastClose = stockData.info.get('previousClose', currPrice) 
        change = currPrice - lastClose
        changePercent = (change / lastClose) * 100 if lastClose!=0 else 0

        if change >= 0:
            color = '#00FF00' 
            sign = '+'
        else:
            color = '#FF4444' 
            sign = ''

        changeTxt = f'{change:+.2f} ({changePercent:+.2f}%)'
        firstFrame = ctk.CTkFrame(self.rest, fg_color='transparent')
        firstFrame.pack(side='top', fill='x', padx=100, pady=(10, 0))
        stockName=stockData.info.get('longName',stock)
        ctk.CTkLabel(firstFrame, text = stockName, font=('Arial', 20, 'bold')).pack(padx=5,pady=(10,0),anchor='w')

        priceFrame = ctk.CTkFrame(firstFrame, fg_color='transparent')
        priceFrame.pack(anchor='w', padx=5) 

        ctk.CTkLabel(priceFrame, text=f'$ {currPrice:.2f}', font=('Arial', 24, 'bold')).pack(side='left')

        ctk.CTkLabel(priceFrame, text=f'  {changeTxt}', font=('Arial', 14, 'bold'), text_color=color).pack(side='left', pady=(8,0))

        stats = {
            'Piaci Kap.': stockData.info.get('marketCap', 'N/A'),
            'P/E Ráta': stockData.info.get('trailingPE', 'N/A'),
            'EPS': stockData.info.get('trailingEps', 'N/A'),
            '52h Csúcs': stockData.info.get('fiftyTwoWeekHigh', 'N/A'),
            'Osztalék': stockData.info.get('dividendYield', 'N/A')
        }
        
        if stats['Osztalék'] != 'N/A' and stats['Osztalék'] is not None:
             stats['Osztalék'] = stats['Osztalék'] * 100
        
        controlsFrame = ctk.CTkFrame(self.rest, fg_color='transparent')
        controlsFrame.pack(side='top', fill='x', padx=100, pady=(10, 0))

        ctk.CTkButton(controlsFrame,text='Year', width=50, height=24, fg_color='#333333', command=lambda: self.chart(stockData,'1Y')).pack(side='right', padx=2)
        ctk.CTkButton(controlsFrame,text='Month', width=50, height=24, fg_color='#333333', command=lambda: self.chart(stockData,'1mo')).pack(side='right', padx=2)
        ctk.CTkButton(controlsFrame,text='YTD', width=50, height=24, fg_color='#333333', command=lambda: self.chart(stockData,'YTD')).pack(side='right', padx=2)
        ctk.CTkButton(controlsFrame,text='Day', width=50, height=24, fg_color='#333333', command=lambda: self.chart(stockData,'1D')).pack(side='right', padx=2)

        self.chart(stockData,'1Y')
        


        container = ctk.CTkFrame(self.rest, fg_color='transparent')
        container.pack(side='bottom',fill='x', pady=(0, 20), padx=20)

        for i, (key,value) in enumerate(stats.items()):
            card = ctk.CTkFrame(container, fg_color='#333333') 
            card.grid(row=0, column=i, padx=5, sticky='ew')
            container.grid_columnconfigure(i, weight=1)
            strng = str(value)

            if value != 'N/A' and value is not None:
                if key == 'Piaci Kap.':
                    strng = f'{value/1_000_000_000:.2f}'
                    pass 
                elif key == 'Osztalék':
                    strng = f'{value:.2f}%'
                    pass
                elif key == '52h Csúcs':
                    strng = f'${value:.2f}'
            
            ctk.CTkLabel(card,text=key, font=('Arial', 11, 'bold'), text_color='gray').pack(pady=(5,0))
            ctk.CTkLabel(card,text=strng, font = ('Arial',13,'bold')).pack(pady=(0,5))

    def chart(self,stockData,period):
        if self.currChart is not None:
            self.currChart.destroy()    

        chart = Figure(figsize=(6,4), dpi=100, facecolor='#2b2b2b')
        coordinate = chart.add_subplot(111)
        coordinate.set_facecolor('#2b2b2b')
        
        histData=stockData.history(period=period)
        if 'Close' in histData.columns and len(histData)>0:
            data = histData['Close']
            coordinate.plot(data, color='#00d4ff', linewidth=2)
            coordinate.fill_between(data.index, data, data.min(), color='#00d4ff', alpha=0.3)
        else:
            coordinate.text(0.5,0.5,'Nincs adat',ha='center',va='center',color='red',fontsize=14)
        
        coordinate.tick_params(axis='x', colors='white')
        coordinate.tick_params(axis='y', colors='white')
        coordinate.xaxis.set_major_locator(ticker.MaxNLocator(6))
        
        coordinate.spines['bottom'].set_color('white')
        coordinate.spines['left'].set_color('white')
        coordinate.spines['top'].set_visible(False)
        coordinate.spines['right'].set_visible(False)
        
        coordinate.grid(True, color='#404040', linestyle='--', alpha=0.5)
        canvas = FigureCanvasTkAgg(chart, master=self.rest)
        canvas.draw()
        widget = canvas.get_tk_widget()
        widget.configure(highlightbackground='white', highlightthickness=2)
        widget.pack(side='top', fill='both', expand=True, pady=(20,10), padx=100)
        self.currChart=widget





