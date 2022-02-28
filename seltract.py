# -*- coding: utf-8 -*-

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import Select
from bs4 import BeautifulSoup
from time import sleep
import numpy as np
import pandas as pd
from dateutil.parser import parse
import logging as logger
import os.path
from datetime import datetime

logger.basicConfig(filename='./log/debug.log',
                            filemode='a',
                            format='%(asctime)s %(levelname)s %(message)s',
                            datefmt='%H:%M:%S',
                            level=logger.INFO)
logging = logger.getLogger(__name__)
logging.setLevel(logger.INFO)

class seltract: 
    def __init__(self, driver, url) -> None:
        self.driver = driver
        self.dict = dict()
        self.pickList = pd.DataFrame()
        self.main(url)
        
    def load_page(self, url):
        logging.info(f"Getting url: {url}")
        self.driver.get(url)
        sleep(2)

    def createOutput(self):
        logging.info("Creating output...")
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

        logging.info("Calculating Delta")
        df.apply(self.calculateDelta, axis=1)
        df['Delta'] = self.dict['delta'][:min]
        logging.info("Calculating MoneyLineDelta")
        df.apply(self.calculateMoneyLineDelta, axis=1)
        df['ML Delta'] = self.dict['ML_Delta'][:min]
        logging.info("Filtering (beta)...")
        df.apply(self.filter, axis=1)

        return df

    def output_csv(self):
        try:
            logging.info("Outputting CSVs...")
            df = self.createOutput()
            df.to_csv('./output/matchList.csv', mode='a')
            self.pickList.to_csv('./output/pickList.csv', mode='a')
            logging.info("CSV output successful")
        except Exception as e:
            logging.error("CSV permission denied probably bc it's open??")
            logging.error(e)

    def seltract(self):
        logging.info("Side/Total Tab selected")
        select = Select(self.driver.find_element(By.CLASS_NAME, 'pggc-input--actiontype'))
        select.select_by_visible_text('Side/Total')
        select2 = Select(self.driver.find_element(By.ID, 'pggcFilterSport'))
        select2.select_by_visible_text('College Basketball')
        sleep(3)
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
                                formatted = child.text.replace("½", '.5')
                                self.dict[matching[0].split('-')[-1]].append(formatted)
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
        logging.info("Sides Tab selected")
        select = Select(self.driver.find_element(By.CLASS_NAME, 'pggc-input--actiontype'))
        select.select_by_visible_text('Sides')
        sleep(3)
        select2 = Select(self.driver.find_element(By.ID, 'pggcFilterSport'))
        select2.select_by_visible_text('College Basketball')
        sleep(3)

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
                                formatted = child.text.replace("½", '.5')
                                self.dict[f"{matching[0].split('-')[-1]}_sides"].append(formatted)
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
        logging.info("Getting MoneyLine Delta...")
        select = Select(self.driver.find_element(By.CLASS_NAME, 'pggc-input--actiontype'))
        select.select_by_visible_text('ML | RL | PL')
        select2 = Select(self.driver.find_element(By.ID, 'pggcFilterSport'))
        select2.select_by_visible_text('College Basketball')
        sleep(3)

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
                                formatted = child.text.replace("½", '.5')
                                self.dict[f"{matching[0].split('-')[-1]}_ML"].append(formatted)
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
            logging.error(e)
            logging.error("Hey it's the NHL :o; how the heck do I parse these characters")

    def main(self, url):
        self.load_page(url)
        self.getSides()
        self.moneyLineDelta()
        self.seltract()
        self.output_csv()

def get_url_list(driver, urls):
    url = "https://pregame.com/game-center"
    driver.get(url)
    sleep(2)
    for row in range(1,6):
        for col in range(1,8):
            try:
                driver.find_element(By.XPATH, "//*[@id='pggcFilterGameDate']").click()
                driver.find_element(By.XPATH, f"/html/body/div[1]/table/tbody/tr[{row}]/td[{col}]/a").click()
                urls.append(driver.current_url)
                sleep(0.75)
            except Exception as e:
                print(e)
                print("Skip date bc don't exist in month yet")
            

logging.info("Starting Seltract.py")
chrome_options = Options()
#chrome_options.add_argument("--headless")
chrome_options.add_argument('log-level=3')
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), chrome_options=chrome_options)
url_lst = []
get_url_list(driver, url_lst)

# Todays
#url = "https://pregame.com/game-center"
#output = seltract(driver, url)

# Archive
start = datetime.now()
for days in url_lst:
    output = seltract(driver, days)
end = datetime.now()
logging.info(f"Script took {start-end} time")