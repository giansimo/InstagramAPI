import copy
import json
import logging
from logging.handlers import TimedRotatingFileHandler
from time import sleep

from selenium.common import NoSuchElementException
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from seleniumwire import webdriver

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

formatter = logging.Formatter('%(asctime)s - %(levelname)s: %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')

logname = "../log/Session.log"
handler = TimedRotatingFileHandler(logname, when="midnight", backupCount=30)
handler.suffix = "%Y%m%d"
handler.setFormatter(formatter)
logger.addHandler(handler)

def initProxyOptions(config, useCustomProxy, account = None):

    if useCustomProxy:
        proxy = account.proxy.split(":", 2)
        credentials = proxy[2]
        proxyIp = proxy[0] + ":" + proxy[1]
    else:
        credentials = config["proxyConfig"]["credentials"]
        proxyIp = config["proxyConfig"]["proxyIp"]


    options = {
        'proxy': {
            'http': 'http://' + credentials + '@' + proxyIp,
            'https': 'https://' + credentials + '@' + proxyIp,
            'no_proxy': 'localhost,127.0.0.1,dev_server:8080'
        }
    }

    return options

def initChromeOptions(loadImage = False, headlessMode = False, userAgent = None):
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument("start-maximized")
    chrome_options.add_argument("--lang=en-GB")
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument("disable-infobars")
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument('--disable-application-cache')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument('--ignore-certificate-errors-spki-list')
    chrome_options.add_argument('--ignore-ssl-errors')
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    if headlessMode:
        chrome_options.add_argument("--headless")
        chrome_options.add_argument('window-size=1920x1080')
    if not loadImage:
        prefs = {"profile.managed_default_content_settings.images": 2}
        chrome_options.add_experimental_option("prefs", prefs)
    if userAgent is not None:
        chrome_options.add_argument(f'user-agent={userAgent}')
    return chrome_options


def getDriver(config, chrome_options, seleniumwire_options = None):
    pathDriver = config["path"]["driver"] + config["driverVersion"]["main"]
    service = Service(executable_path=pathDriver)
    driver = webdriver.Chrome(service=service, options=chrome_options,
                              seleniumwire_options=copy.deepcopy(seleniumwire_options))
    return driver

def manageCookiesLogin(config, driver, account):
    # cookie setting
    driver.get(config["url"]["igBasePath"])
    driver.delete_all_cookies()

    for cookie in json.loads(account.cookies):
        driver.add_cookie({
            'name': cookie["name"],
            'value': cookie["value"],
            'domain': cookie["domain"]
        })


    logger.info("Going to instagram.com")
    driver.get(config["url"]["igBasePath"])


    # try to check if login worked
    try:
        loginInSignUp = driver.find_element(
            By.XPATH, config["findElement"]["xpath"]["loginInSignUp"]
        )
        if loginInSignUp is not None:
            logger.info("Login by cookies was not successful, skip the current profile")
            return True
    except NoSuchElementException:
        pass
