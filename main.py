import customtkinter as ctk
import View.question as QuestionsDisplay
import View.profile as ProfileDisplay
from Model.data import DataManager
import sys 
import os

ctk.set_appearance_mode('Dark')
ctk.set_default_color_theme('blue')

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.attributes('-fullscreen', True)
        self.title('Stock App')
        self.dataManager = DataManager()
        if self.dataManager.isRegistered():
            self.openPortfolio(self.dataManager,True)
        else:
            self.callBack = self.openPortfolio
            self.questionTab = QuestionsDisplay.QuestionsDisplay(self, self.callBack)#self lesz a master parametere a questionnak APP a fonok
            self.questionTab.pack(fill ='both', expand = True)
        
    
    def openPortfolio(self,dataManager,wasRegistered):
        if wasRegistered == False:
            self.questionTab.destroy()
        self.dataManager = dataManager
        self.profileTab = ProfileDisplay.ProfileDisplay(self,self.dataManager)
        self.profileTab.pack(fill = 'both', expand = True)

    def restartApplication(self):
        self.destroy()
        python = sys.executable
        os.execl(python,python, *sys.argv)


if __name__ == '__main__':
    app = App()
    app.mainloop()