import seltract
from selenium import webdriver
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from time import sleep
import time
import logging as logger
import sys

logger.basicConfig(filename='./log/debug.log',
                            filemode='a',
                            format='%(asctime)s %(levelname)s %(message)s',
                            datefmt='%H:%M:%S',
                            level=logger.INFO)
logging = logger.getLogger(__name__)
logger.getLogger().addHandler(logger.StreamHandler(sys.stdout))
logging.setLevel(logger.INFO)

class seltract_wrapper:
    def __init__(self) -> None:
        start = time.time()
        logging.info("Starting Seltract.py")
        self.chrome_options = Options()
        self.chrome_options.add_experimental_option("excludeSwitches", ["enable-logging"])
        self.chrome_options.add_argument("--log-level=3")
        self.chrome_options.add_argument("--headless")
        self.chrome_options.add_argument("window-size=1024x768")
        self.caps = DesiredCapabilities().CHROME
        self.caps["pageLoadStrategy"] = "none"
        self.driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=self.chrome_options, desired_capabilities=self.caps)
        self.urls = []
        
        # Todays
        self.todays_matches()

        # Archive Change the input number here for the amount of months back
        #self.archive(3)

        end = time.time()
        logging.info(f"Script took {end-start} time")

    def todays_matches(self):
        '''
        Fetches todays matches that are listed on the base url
        '''
        url = "https://pregame.com/game-center"
        seltract.seltract(self.driver, url)

    def archive(self, months_back):
        '''
        Fetches the last months_back list of matches
        '''
        self.get_url_list(self.driver, months_back)
        for days in self.urls:
            seltract.seltract(self.driver, days)

    def get_url_list(self, driver, months_back):
        '''
        Fetches the list of URLs for each day in the months_back that is requested
        '''
        logging.info("Collecting old URLs")
        url = "https://pregame.com/game-center"
        driver.get(url)
        sleep(3)

        # Getting other months w code manually (sounds weird.)
        driver.find_element(By.XPATH, "//*[@id='pggcFilterGameDate']").click()
        for x in range(months_back): # 3 months back
            driver.find_element(By.XPATH, "/html/body/div[1]/div/a[1]").click()
            sleep(0.75)
        for x in range(months_back+1):
            for row in range(1,6):
                for col in range(1,8):
                    try:
                        driver.find_element(By.XPATH, "//*[@id='pggcFilterGameDate']").click()
                        driver.find_element(By.XPATH, f"/html/body/div[1]/table/tbody/tr[{row}]/td[{col}]/a").click()
                        self.urls.append(driver.current_url)
                        sleep(0.5)
                    except Exception as e:
                        logging.error(e)
                        logging.info("Skip date bc don't exist in month")
            driver.find_element(By.XPATH, "//*[@id='pggcFilterGameDate']").click()
            driver.find_element(By.XPATH, "/html/body/div[1]/div/a[2]").click()
            sleep(0.5)
        logging.info("Finished collecting URLs")

seltract_wrapper()