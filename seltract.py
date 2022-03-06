# -*- coding: utf-8 -*-

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from bs4 import BeautifulSoup
from time import sleep
import numpy as np
import pandas as pd
import logging as logger
import os.path

logger.basicConfig(filename='./log/debug.log',
                            filemode='a',
                            format='%(asctime)s %(levelname)s %(message)s',
                            datefmt='%Y/%m/%d %H:%M:%S',
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
        try:
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
            #logging.info("Filtering (beta)...")
            #df.apply(self.filter, axis=1)
        
        except Exception as e:
            logging.error("Probably no data on this day...")
            logging.error(e)

        return df

    def output_csv(self):
        try:
            logging.info("Outputting CSVs...")
            df = self.createOutput()
            if os.path.isfile('./output/matchList.csv'):
                df_old = pd.read_csv('./output/matchList.csv')
                df = pd.concat([df_old, df], ignore_index=True)
            df.to_csv('./output/matchList.csv', index=False)
            #self.pickList.to_csv('./output/pickList.csv', mode='a')
            logging.info("CSV output successful")
        except Exception as e:
            logging.error("CSV permission denied probably bc it's open??")
            logging.error(e)

    def seltract(self):
        logging.info("Side/Total Tab selected")
        try:
            select = Select(self.driver.find_element(By.CLASS_NAME, 'pggc-input--actiontype'))
            select.select_by_visible_text('Side/Total')
            sleep(1)
            select2 = Select(self.driver.find_element(By.ID, 'pggcFilterSport'))
            select2.select_by_visible_text('College Basketball')
            sleep(1)
        except Exception as selection_error:
            logging.error(selection_error)
            logging.error("Failed in seltract, moving on")
            return
        html = BeautifulSoup(self.driver.page_source, 'html.parser')
        relevant_cols = ['pggc-col--time', 'pggc-col--team', 'pggc-col--open',
                            'pggc-col--current',  'pggc-col--cash', 'pggc-col--tickets']

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
            # Separator Between Matches
            append_list = ['time', 'team', 'cash', 'tickets']
            for keys in append_list:
                if keys not in self.dict:
                    self.dict[keys] = []
                self.dict[keys].append("-")

    def getSides(self):
        logging.info("Sides Tab selected")
        try:
            select = Select(self.driver.find_element(By.CLASS_NAME, 'pggc-input--actiontype'))
            select.select_by_visible_text('Sides')
            sleep(1)
            select2 = Select(self.driver.find_element(By.ID, 'pggcFilterSport'))
            select2.select_by_visible_text('College Basketball')
            sleep(1)
        except Exception as selection_error:
            logging.error(selection_error)
            logging.error("Failed in getSides, moving on")
            return

        relevant_cols = ['pggc-col--time', 'pggc-col--cash', 'pggc-col--tickets']

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
            if "cash_sides" not in self.dict:
                self.dict['cash_sides'] = []
            if "tickets_sides" not in self.dict:
                self.dict['tickets_sides'] = []
            self.dict['cash_sides'].append("-")
            self.dict['tickets_sides'].append("-")
    
    def moneyLineDelta(self):
        # ML | RL | PL
        logging.info("Getting MoneyLine Delta...")
        try:
            select = Select(self.driver.find_element(By.CLASS_NAME, 'pggc-input--actiontype'))
            select.select_by_visible_text('ML | RL | PL')
            sleep(1)
            select2 = Select(self.driver.find_element(By.ID, 'pggcFilterSport'))
            select2.select_by_visible_text('College Basketball')
            sleep(1)
        except Exception as selection_error:
            logging.error(selection_error)
            logging.error("Failed in moneyLineDelta, moving on")
            return

        relevant_cols = ['pggc-col--time', 'pggc-col--open', 'pggc-col--current']

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
        if "½" in row['Open ML']:
            sign = "+" if delta1[0] == '+' else "-"
            delta1.replace("½", ".5")
            delta1 = sign + delta1.split[1]
        if "½" in row['Current ML']:
            sign = "+" if delta2[0] == '+' else "-"
            delta2.replace("½", ".5")
            delta2 = sign + delta2.split[1]
            
        if delta1 in ['-', ''] or delta2 in ['-', '']:
            self.dict['ML_Delta'].append('-')
        else:
            delta = float(delta1) - float(delta2)
            self.dict['ML_Delta'].append(delta)

    def filter(self, row):
        # Spit out the Current +/-# get rid of rest
        # ex: +1-105 >> +1 or -3.5-115 >> -3.5
        delta = row['Delta']
        ML_Delta = row['ML Delta']
        if row['Delta'] in ['', '-'] or row['ML Delta'] in ['', '-']:
            return
        try:
            if "½" in row['Delta']:
                sign = "+" if delta[0] == '+' else "-"
                delta.replace("½", ".5")
                delta = sign + delta.split[1]
            if "½" in row['ML Delta']:
                sign = "+" if ML_Delta[0] == '+' else "-"
                ML_Delta.replace("½", ".5")
                ML_Delta = sign + ML_Delta.split[1]
        except Exception as parse_error:
            logging.error("Error parsing the 1/2 inside of Delta/ML Delta rows.")
            logging.error(parse_error)
        try:
            if float(row['Delta']) > -5 and float(row['ML Delta']) < -10 and float(row['Current ML']) < 0:
                if self.pickList.empty:
                    self.pickList = row.to_frame().T
                else:
                    self.pickList = pd.concat([self.pickList, row.to_frame().T])
        except Exception as e:
            logging.error(e)
            logging.error("how the heck do I parse these characters")

    def main(self, url):
        self.load_page(url)
        self.getSides()
        self.moneyLineDelta()
        self.seltract()
        self.output_csv()
