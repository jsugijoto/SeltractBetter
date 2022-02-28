from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import Select
from bs4 import BeautifulSoup
from time import sleep
import numpy as np
import pandas as pd
from dateutil.parser import parse

class seltract: 
    def __init__(self) -> None:
        self.driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
        self.dict = dict()
        self.pickList = pd.DataFrame()
        self.urls = []
        self.main()
        
    def load_page(self):
        url = "https://pregame.com/game-center"
        self.driver.get(url)
        sleep(3)

        #for row in range(1,5):
        #    for col in range(1,8):
        #        try:
        #            self.driver.find_element_by_xpath("//*[@id='pggcFilterGameDate']").click()
        #            self.driver.find_element_by_xpath(f"/html/body/div[1]/table/tbody/tr[{row}]/td[{col}]/a").click()
        #            self.urls.append(self.driver.current_url)
        #        except Exception as e:
        #            print(e)
        #            print("Skip date bc don't exist in month yet")
        #        sleep(0.05)
        #sleep(3)

    def createOutput(self):
        df = pd.DataFrame()
        min = np.inf
        for keys in self.dict.keys():
            if len(self.dict[keys]) < min:
                min = len(self.dict[keys])
        df['Date'] = self.dict['time'][:min]
        df['Team'] = self.dict['team'][:min]
        df['Cash'] = self.dict['cash'][:min]
        df['Tickets'] = self.dict['tickets'][:min]
        df['Cash Sides'] = self.dict['cash_sides'][:min]
        df['Ticket Sides'] = self.dict['tickets_sides'][:min]
        df['Open ML'] = self.dict['open_ML'][:min]
        df['Current ML'] = self.dict['current_ML'][:min]

        df.apply(self.calculateDelta, axis=1)
        df['Delta'] = self.dict['delta']
        df.apply(self.calculateMoneyLineDelta, axis=1)
        df['ML Delta'] = self.dict['ML_Delta']
        df.apply(self.filter, axis=1)

        return df

    def output_csv(self):
        df = self.createOutput()
        df.to_csv('matchList.csv')
        self.pickList.to_csv('pickList.csv')

    def seltract(self):
        select = Select(self.driver.find_element_by_class_name('pggc-input--actiontype'))
        select.select_by_visible_text('Side/Total')
        sleep(5)
        html = BeautifulSoup(self.driver.page_source, 'html.parser')
        relevant_cols = ['pggc-col--time', 'pggc-col--team', 'pggc-col--open',
                            'pggc-col--current',  'pggc-col--cash', 'pggc-col--tickets']
        tomorrow = False

        # Get matches that aren't complete and only of todays games.
        for match in html.find_all('div', {'class': 'pggc-game'}):
            for col in match.find('div', {'class': 'pggc-game-col--table'}).table.tbody.tr:
                if col != '\n':
                    matching = list(set(col['class']) & set(relevant_cols))
                    if len(matching) != 0:
                        for child in col.children:
                            if child != '\n':
                                if matching[0].split('-')[-1] not in self.dict:
                                    self.dict[matching[0].split('-')[-1]] = []
                                self.dict[matching[0].split('-')[-1]].append(child.text)
                if tomorrow:
                    break
            if tomorrow:
                break
            # Separator Between Matches
            append_list = ['time', 'team', 'cash', 'tickets']
            for keys in append_list:
                if keys not in self.dict:
                    self.dict[keys] = []
                self.dict[keys].append("-")

    def getSides(self):
        select = Select(self.driver.find_element_by_class_name('pggc-input--actiontype'))
        select.select_by_visible_text('Sides')
        sleep(5)

        relevant_cols = ['pggc-col--time', 'pggc-col--cash', 'pggc-col--tickets']
        tomorrow = False

        html = BeautifulSoup(self.driver.page_source, 'html.parser')
        for match in html.find_all('div', {'class': 'pggc-game'}):
            for col in match.find('div', {'class': 'pggc-game-col--table'}).table.tbody.tr:
                if col != '\n':
                    matching = list(set(col['class']) & set(relevant_cols))
                    if len(matching) != 0:
                        for child in col.children:
                            if child != '\n': 
                                if f"{matching[0].split('-')[-1]}_sides" not in self.dict:
                                    self.dict[f"{matching[0].split('-')[-1]}_sides"] = []
                                self.dict[f"{matching[0].split('-')[-1]}_sides"].append(child.text)
                if tomorrow:
                    break
            if tomorrow:
                break
            
            if "cash_sides" not in self.dict:
                self.dict['cash_sides'] = []
            if "tickets_sides" not in self.dict:
                self.dict['tickets_sides'] = []
            self.dict['cash_sides'].append("-")
            self.dict['tickets_sides'].append("-")
    
    def moneyLineDelta(self):
        # ML | RL | PL
        select = Select(self.driver.find_element_by_class_name('pggc-input--actiontype'))
        select.select_by_visible_text('ML | RL | PL')
        sleep(5)

        relevant_cols = ['pggc-col--time', 'pggc-col--open', 'pggc-col--current']
        tomorrow = False

        html = BeautifulSoup(self.driver.page_source, 'html.parser')
        for match in html.find_all('div', {'class': 'pggc-game'}):
            for col in match.find('div', {'class': 'pggc-game-col--table'}).table.tbody.tr:
                if col != '\n':
                    matching = list(set(col['class']) & set(relevant_cols))
                    if len(matching) != 0:
                        for child in col.children:
                            if child != '\n': 
                                if f"{matching[0].split('-')[-1]}_ML" not in self.dict:
                                    self.dict[f"{matching[0].split('-')[-1]}_ML"] = []
                                self.dict[f"{matching[0].split('-')[-1]}_ML"].append(child.text)
                if tomorrow:
                    break
            if tomorrow:
                break
            if "open_ML" not in self.dict:
                self.dict['open_ML'] = []
            if "current_ML" not in self.dict:
                self.dict['current_ML'] = []
            self.dict['open_ML'].append("-")
            self.dict['current_ML'].append("-")

    def calculateDelta(self, row):
        if 'delta' not in self.dict:
                self.dict['delta'] = []
        delta1 = row['Cash Sides'].strip('%')
        delta2 = row['Ticket Sides'].strip('%')
        if delta1 == '-' or delta2 == '-':
            self.dict['delta'].append('-')
        else:
            delta = float(''.join(filter(str.isdigit, delta1))) - float(''.join(filter(str.isdigit, delta2)))
            self.dict['delta'].append(delta)

    def calculateMoneyLineDelta(self, row):
        if 'ML_Delta' not in self.dict:
            self.dict['ML_Delta'] = []
        delta1 = row['Open ML']
        delta2 = row['Current ML']
        if delta1 in ['-', ''] or delta2 in ['-', '']:
            self.dict['ML_Delta'].append('-')
        else:
            delta = float(''.join(filter(str.isdigit, delta1))) - float(''.join(filter(str.isdigit, delta2)))
            self.dict['ML_Delta'].append(delta)

    def filter(self, row):
        # Spit out the Current +/-# get rid of rest
        # ex: +1-105 >> +1 or -3.5-115 >> -3.5
        if row['Delta'] in ['', '-'] or row['ML Delta'] in ['', '-']:
            return
        try:
            if float(row['Delta']) > -5 and float(row['ML Delta']) < -10 and float(row['Current ML']) < 0:
                if self.pickList.empty:
                    self.pickList = row.to_frame().T
                else:
                    self.pickList = pd.concat([self.pickList, row.to_frame().T])
        except Exception as e:
            print("Hey it's the NHL :o")

    def main(self):
        self.load_page()
        self.getSides()
        self.moneyLineDelta()
        self.seltract()
        self.output_csv()

output = seltract()