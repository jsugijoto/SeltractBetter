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
        
        # Todays
        self.todays_matches()

        # Archive
        #self.archive()

        end = time.time()
        logging.info(f"Script took {end-start} time")

    def todays_matches(self):
        url = "https://pregame.com/game-center"
        seltract.seltract(self.driver, url)

    def archive(self):
        self.urls = []
        self.get_url_list(self.driver)
        for days in self.urls:
            seltract.seltract(self.driver, days)

    def get_url_list(self, driver):
        logging.info("Collecting old URLs")
        url = "https://pregame.com/game-center"
        driver.get(url)
        sleep(3)

        # Getting other months w code manually (sounds weird.)
        driver.find_element(By.XPATH, "//*[@id='pggcFilterGameDate']").click()
        for x in range(3): # 3 months back
            driver.find_element(By.XPATH, "/html/body/div[1]/div/a[1]").click()
            sleep(0.75)
        for x in range(1):
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