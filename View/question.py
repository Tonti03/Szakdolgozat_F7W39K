import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import customtkinter as ctk
from Model.data import DataManager

class QuestionsDisplay(ctk.CTkFrame):
    def __init__(self,master,callBack):
        super().__init__(master, fg_color='transparent')
        self.dataManager = DataManager()
        self.callBack = callBack
        self.questionUI()

    def questionUI(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(self, text='Kockázati és FoMO Profilalkotás', font=('Arial', 20, 'bold')).grid(row=0, column=0, columnspan=2, pady=20)

        self.leftColum = ctk.CTkFrame(self, fg_color='#1A1A1A')
        self.leftColum.grid(row=1, column=0, sticky='nsew', padx=10, pady=10)

        self.rightColum = ctk.CTkFrame(self, fg_color='#1A1A1A')
        self.rightColum.grid(row=1, column=1, sticky='nsew', padx=10, pady=10)#north souh west east

        ctk.CTkLabel(self.leftColum, text='Kockázati Preferenciák', font=('Arial', 18, 'bold')).pack(pady=15)

        ctk.CTkLabel(self.leftColum, text='1. Ha a portfóliód 20%-ot esne?',font=('Arial', 14)).pack(pady=(10,5),padx=10,anchor='w')
        self.answerOne = ctk.StringVar(value='')#aktivan modosulhato valtozo a vizualizacios feluletben es ez adja az osszekottetst a valasztomodulok kozott ha za egyik be van pipalva masik kikapcsol - igy mindig csak 1 lesz bepipalva
        ctk.CTkRadioButton(self.leftColum, text='Azonnal eladnék mindent', variable=self.answerOne, value='1').pack( padx=20,anchor='w', pady=2)
        ctk.CTkRadioButton(self.leftColum, text='Várnék / tartanám', variable=self.answerOne, value='3').pack( padx=20,anchor='w', pady=2)
        ctk.CTkRadioButton(self.leftColum, text='Vásárolnék még', variable=self.answerOne, value='5').pack( padx=20,anchor='w', pady=2)

        ctk.CTkLabel(self.leftColum, text='2. Melyik állítás illik rád a leginkább?',font=('Arial', 14)).pack(pady=(10,5),padx=10,anchor='w')
        self.answerTwo = ctk.StringVar(value='')
        ctk.CTkRadioButton(self.leftColum, text='A tőkem biztonsága a legfontosabb', variable=self.answerTwo, value='1').pack(pady=2,padx=20,anchor='w')
        ctk.CTkRadioButton(self.leftColum, text = 'A hozam és a kockázat egyensúlyát keresem', variable = self.answerTwo, value = '3').pack(pady=2,padx=20,anchor='w')
        ctk.CTkRadioButton(self.leftColum, text = 'A lehető legmagasabb hozamot célzom, még magasabb kockázat árán is', variable = self.answerTwo, value = '5').pack(pady=2,padx=20,anchor='w')

        ctk.CTkLabel(self.rightColum, text = 'FoMO Preferenciák', font=('Arial', 18, 'bold')).pack(pady=15)
        ctk.CTkLabel(self.rightColum, text = 'Értékeld 1 (Nem jellemző) - 5 (Teljesen) skálán:', font=('Arial', 14, 'bold')).pack(pady=(10,5),padx=10,anchor='w')

        fomoQuest = [
            'Félek, hogy másoknak értékesebb élményeik vannak, mint nekem',
            'Aggódom, hogy barátaimnak jobb élményeik vannak, mint nekem',
            'Ideges vagyok, ha megtudom, hogy barátaim nélkülem szórakoznak',
            'Szorongok, amikor nem tudom, mit csinálnak a barátaim',
            'Fontos számomra, hogy értsem a barátaim belsős vicceit',
            'Néha azon tűnődöm, hogy túl sok időt töltök azzal, hogy lépést tartsak az eseményekkel',
            'Zavar, amikor lemaradok egy lehetőségről, hogy találkozzak a barátaimmal',
            'Amikor jól érzem magam, fontos, hogy megosszam az élményt online (pl. státusz frissítés)',
            'Zavar, ha kimaradok egy tervezett összejövetelből',
            'Nyaralás közben is figyelemmel kísérem, mit csinálnak a barátaim'
        ]

        self.fomoAnsw = []
        
        for i in range(len(fomoQuest)):
            self.plc = ctk.CTkFrame(self.rightColum, fg_color = 'transparent')
            self.plc.pack(pady=2, fill='x')
            ctk.CTkLabel(self.plc, text = fomoQuest[i], font = ('Arial', 14)).pack(pady=2,padx=20,anchor='w',side='left')
            self.answer = ctk.IntVar(value=3)#akk igy a kozepetol lesz a csuszka
            ctk.CTkSlider(self.plc, from_ = 1, to = 5, number_of_steps = 4, variable = self.answer).pack(pady=2,padx=20,anchor='w',side='right')
            self.fomoAnsw.append(self.answer)
            
        ctk.CTkButton(self, text = 'Profil Mentése', command = self.saveProfile).grid(row = 2, columnspan=2, pady=30)

    def saveProfile(self):
        if self.answerOne.get() == '' or self.answerTwo.get() == '':
            ctk.CTkLabel(self, text = 'Kockázati preferenciák nem lehetnek üresen hagyva!', font = ('Arial', 10), text_color = 'red').grid(row = 3, columnspan=2, pady=(0,10))
            return
        
        riskScore = int(self.answerOne.get()) + int(self.answerTwo.get())
        fomoScore = sum(i.get() for i in self.fomoAnsw)
        if riskScore > 7:
            if fomoScore < 25:
                riskLevel = 3
            else:
                riskLevel = 2
        elif riskScore > 4:
            if fomoScore < 20:
                riskLevel = 3
            elif fomoScore < 40:
                riskLevel = 2
            else:
                riskLevel = 1
        else:
            if fomoScore < 25:
                riskLevel = 2
            else:
                riskLevel = 1
            
        self.dataManager.saveData([],riskLevel)

        if self.callBack:
            self.callBack(self.dataManager,False)

        
        
        
    