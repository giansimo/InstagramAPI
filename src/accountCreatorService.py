import base64
import copy
import json
import random
import time
from datetime import datetime
from time import sleep

import requests
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import *
from selenium.webdriver.common.by import *
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from seleniumwire import webdriver
from smsactivate.api import SMSActivateAPI

from src.Account import Account
from src.utils import *


def strToBase64(strInput):
    return base64.b64encode(bytes(strInput, 'utf-8')).decode('ascii')

def getProxy(proxy):
    proxyData = proxy.split(":")
    proxyIP = proxyData[0] + ":" + proxyData[1]
    credentials = proxyData[2] + ":" + proxyData[3]
    return proxyIP, credentials


def getNumber(sa, config, verification):
    configSMSActivate = config["smsActivate"]

    result = sa.getNumber(service=configSMSActivate["service"], country=configSMSActivate["countryId"],
                          verification=verification)
    try:
        return result
    except:
        return result['message']


def setNumberStatus(sa, id, status):
    sa.setStatus(id=id, status=status)


def getSecureCode(sa, id, config, logger):
    statusMsg = sa.getStatus(id)  # STATUS_OK:XXXXXXX
    maxWaitingSecureCode = config["config"]["maxWaitingSecureCode"]
    waitedTime = 0
    while ("STATUS_OK" not in statusMsg):
        sleep(config["config"]["longWait"])
        waitedTime+= config["config"]["veryLongWait"]
        statusMsg = sa.getStatus(id)
        if waitedTime >= maxWaitingSecureCode:
            break


    if "STATUS_OK" in statusMsg:
        msg = str(statusMsg).split(":")
        logger.info("Get secure code for id: " + str(id) + " - " + str(msg))
        if len(msg[1]) == 6:
            return msg[1]
    else:
        return None

def destroy(sa, account, config, logger):
    configSMSActivate = config["smsActivate"]

    number = account.cellPhone
    if number is not None:
        activationId = number.split(":")[0]
        logger.info("Try to reject number with id {0}...current balance is: ".replace("{0}", str(activationId)) + sa.getBalance()['balance'])
        setNumberStatus(sa, activationId, configSMSActivate["cancelStatus"])
        logger.info("Balance after rejecting number: " + sa.getBalance()['balance'])
    else:
        logger.info("Number not requested yet")


def initOptions(proxy):
    proxyIp, credentials = getProxy(proxy)
    options = {
        'proxy': {
            'http': 'http://' + credentials + '@' +  proxyIp,
            'https': 'https://' + credentials + '@' +  proxyIp,
            'no_proxy': 'localhost,127.0.0.1'  # excludes
        }
    }

    return options


def getCurrentIp(config, chrome_options, seleniumwire_options, logger):
    getIpAddressUrl = str(config["utils"]["getIpAddress"])
    pathDriver = config["path"]["driver"] + config["driverVersion"]["main"]

    optionsSilent = copy.deepcopy(chrome_options)
    optionsSilent.add_argument("--headless")
    service = Service(executable_path=pathDriver)
    driver = webdriver.Chrome(service=service, options=optionsSilent,
                              seleniumwire_options=copy.deepcopy(seleniumwire_options)
                              )
    status = "OK"
    ipAddress = "IP ADDRESS NOT VALID"
    jsonData = ""
    try:
        driver.get(getIpAddressUrl)
        jsonData = driver.execute_script("return document.body.textContent;")
        ipAddress = json.loads(jsonData)["ip"]
    except WebDriverException:
        logger.error("Error tunnel connection failed")
        status = "Error tunnel connection failed"
    except json.decoder.JSONDecodeError:
        logger.error("Error converting json: " + jsonData)
        status = "JSON error"
    finally:
        driver.quit()

    return ipAddress, status

def saveAccountToFile(account, config, logger):
    logger.info("Exporting info of current account in session output")
    logger.info("User agent: " + str(account.userAgent))
    logger.info("Session id: " + str(account.sessionId))

    logger.info("Username: {0}, Password: {1}, Fullname: {2}".replace("{0}", account.username).replace("{1}",
                                                                                                       account.password).replace(
        "{2}", account.fullname))
    logger.info("Cookies: " + str(account.cookies))
    outputPath = config["path"]["output"]
    fileName = str(config["files"]["session"]).replace("{date}", str(datetime.today().strftime('%d-%m-%Y')))
    sessionPath = outputPath + fileName
    with open(sessionPath, "a+") as file:
        line = str(account.username) + "\t" + str(account.password) + "\t" + str(account.userAgent) \
               + "\t" + str(account.cookies) + "\n"
        file.write(line)



def startCreationRoutine(account, logger):
    config = initConfig("../config.txt")

    ## waiting config
    veryShortWait = config["config"]["veryShortWait"]
    shortWait = config["config"]["shortWait"]
    mediumWait = config["config"]["mediumWait"]
    longWait = config["config"]["longWait"]

    pathDriver = config["path"]["driver"] + config["driverVersion"]["main"]

    seleniumwire_options = initOptions(account.proxy)

    # other chrome options
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--ignore-certificate-errors-spki-list')
    chrome_options.add_argument('--ignore-ssl-errors')
    chrome_options.add_argument("--lang=en-GB")
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    chrome_options.add_argument("start-maximized")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    chrome_options.add_argument(f'user-agent={account.userAgent}')

    currentIPAddress, status = getCurrentIp(config, chrome_options, seleniumwire_options, logger)

    mailMode = True if account.mail else False
    service = Service(executable_path=pathDriver)
    driver = webdriver.Chrome(service=service, options=chrome_options,
                              seleniumwire_options=copy.deepcopy(seleniumwire_options)
                              )

    logger.info("Creation account")
    logger.info("User agent: " + account.userAgent)
    logger.info("SessionId: " + account.sessionId)
    logger.info("Username: {0}, Password: {1}, Fullname: {2}".replace("{0}", account.username).replace("{1}",
                                                                                                       account.password).replace(
        "{2}", account.fullname))
    logger.info("Proxy IP Address: " + currentIPAddress)

    updateClient(config, account)

    try:
        driver.get("https://www.instagram.com/accounts/emailsignup/")
    except TimeoutException:
        driver.quit()
        updateClient(config, account, "Timeout driver")
        return
    except WebDriverException as e:
        updateClient(config, account, "Driver exception")
        logger.error(str(e))
        return
    try:
        cookie = WebDriverWait(driver, 15).until(EC.element_to_be_clickable(("xpath",
                                                                             config["findElement"]["xpath"][
                                                                                 "cookie"]))).click()
        time.sleep(shortWait)
    except:
        logger.error("Cannot find cookie banner, check XPATH in config")
        # driver.quit()
        # exit(1)

    sa = SMSActivateAPI(config["smsActivate"]["apiKey"])

    # Manage phone or mail registration
    if not mailMode:
        # Fill the phone value
        try:
            emailOrPhone = driver.find_element(By.NAME, config["findElement"]["name"]['emailOrPhone'])

            if (config["smsActivate"]["useSpecificNumber"] != "True"):
                logger.info("Requesting number...current balance is: " + sa.getBalance()['balance'])
                number = getNumber(sa, config, True)
                try:
                    logger.info("Using number: " + str(number["phone"]))
                    account.cellPhone = str(number["activation_id"]) + ":" + str(number["phone"])
                    emailOrPhone.send_keys("+" + str(number["phone"]))
                except KeyError:
                    logger.error("Number not received. " + number["message"])
                    updateClient(config, account, "Number not received! " + number["message"])
                    driver.quit()
                    exit(1)
            else:
                logger.info("Skipping activation number")
                account.cellPhone = config["smsActivate"]["activationId"] + ":" + config["smsActivate"]["number"]
                logger.info("Number info used: " + str(account.cellPhone))

                emailOrPhone.send_keys(config["smsActivate"]["number"])
        except NoSuchElementException:
            logger.error("Cannot find emailOrPhone field, check name in config or use XPATH")
            updateClient(config, account, "EmailPhone field not found! Account not created")
            destroy(sa, account, config, logger)
            driver.quit()
            return
    else:
        # Fill the mail value
        try:
            emailOrPhone = driver.find_element(By.NAME, config["findElement"]["name"]['emailOrPhone'])
            emailOrPhone.send_keys(account.mail)
        except NoSuchElementException:
            logger.error("Cannot find emailOrPhone field, check name in config or use XPATH")
            updateClient(config, account, "EmailPhone field not found! Account not created")
            destroy(sa, account, config, logger)
            driver.quit()
            return

    sleep(veryShortWait)

    try:
        # Fill the fullname value
        fullname_field = driver.find_element(By.NAME, config["findElement"]["name"]['fullName'])
        if (fullname_field is not None):
            fullname_field.send_keys(account.fullname)
            sleep(veryShortWait)
    except NoSuchElementException:
        logger.error("Cannot find fullName field, check name in config or use XPATH")
        updateClient(config, account, "Fullname field not found! Account not created")

        destroy(sa, account, config, logger)
        driver.quit()
        return

    try:
        # Fill username value
        username_field = driver.find_element(By.NAME, config["findElement"]["name"]['username'])
        if username_field is not None:
            username_field.send_keys(account.username)
            sleep(veryShortWait)
    except NoSuchElementException:
        logger.error("Cannot find username field, check name in config or use XPATH")
        updateClient(config, account, "Username field not found! Account not created")
        destroy(sa, account, config, logger)
        driver.quit()
        return

    try:
        # Fill password value
        password_field = driver.find_element(By.NAME, config["findElement"]["name"]['password'])
        if password_field is not None:
            password_field.send_keys(account.password)
            sleep(veryShortWait)
    except NoSuchElementException:
        logger.error("Cannot find password field, check name in config or use XPATH")
        updateClient(config, account, "Password field not found! Account not created")
        destroy(sa, account, config, logger)
        driver.quit()
        return

    if (fullname_field is None) or (username_field is None) or (password_field is None):
        destroy(sa, account, config, logger)

    try:
        nextBtn = WebDriverWait(driver, 20).until(EC.element_to_be_clickable(
            (By.XPATH, config["findElement"]["xpath"]["register"]["next"])))

        try:
            if nextBtn is not None:
                nextBtn.click()
        except ElementClickInterceptedException:
            driver.execute_script("arguments[0].click();", nextBtn)
        sleep(veryShortWait)
    except TimeoutException:
        logger.error("Cannot find register button, check XPATH in config file")
        updateClient(config, account, "An error occured during creation routine! Account not created")
        destroy(sa, account, config, logger)
        driver.quit()
        return


    except NoSuchElementException:
        logger.error("Cannot find register button, check XPATH in config file")
        updateClient(config, account, "An error occured during creation routine! Account not created")
        destroy(sa, account, config, logger)
        driver.quit()
        return

    sleep(shortWait)

    # try get ssfError alert
    try:
        ssfErrorAlert = driver.find_element(By.ID, config["findElement"]["id"]["ssfErrorAlert"])
        if ssfErrorAlert is not None:
            logger.warning("Username or number already used, skipping creation")
            updateClient(config, account, "Username/number/mail already used")
            destroy(sa, account, config, logger)
            driver.quit()
            return
    except:
        pass

    # Birthday verification
    try:
        monthSelect = driver.find_element(By.XPATH, config["findElement"]["xpath"]["birthday"]["monthSelect"])
        if monthSelect is not None:
            monthSelect.click()
            month = str(config["findElement"]["xpath"]["birthday"]["monthValue"]).replace("{month}",
                                                                                          str(random.randint(1, 12)))
            WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.XPATH, month))).click()
            sleep(veryShortWait)
    except ElementClickInterceptedException:
        monthSelect = driver.find_element(By.XPATH, config["findElement"]["xpath"]["birthday"]["monthSelect"])
        driver.execute_script("arguments[0].click();", monthSelect)

    except NoSuchElementException:
        logger.error("Cannot find month select or value, check XPATH in config file")
        updateClient(config, account, "An error occured during creation routine! Account not created")
        destroy(sa, account, config, logger)
        driver.quit()
        return

    try:
        daySelect = driver.find_element(By.XPATH, config["findElement"]["xpath"]["birthday"]["daySelect"])
        if daySelect is not None:
            daySelect.click()
            day = str(config["findElement"]["xpath"]["birthday"]["dayValue"]).replace("{day}",
                                                                                      str(random.randint(1, 28)))
            WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.XPATH, day))).click()
            sleep(veryShortWait)
    except NoSuchElementException:
        logger.error("Cannot find day select or value, check XPATH in config file")
        updateClient(config, account, "An error occured during creation routine! Account not created")
        destroy(sa, account, config, logger)
        driver.quit()
        return

    try:
        yearSelect = driver.find_element(By.XPATH, config["findElement"]["xpath"]["birthday"]["yearSelect"])
        if yearSelect is not None:
            yearSelect.click()
            year = str(config["findElement"]["xpath"]["birthday"]["yearValue"]).replace("{year}",
                                                                                        str(random.randint(15, 40)))
            WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.XPATH, year))).click()
            sleep(veryShortWait)
    except NoSuchElementException:
        logger.error("Cannot find year select or value, check XPATH in config file")
        updateClient(config, account, "An error occured during creation routine! Account not created")
        destroy(sa, account, config, logger)
        driver.quit()
        return

    try:
        WebDriverWait(driver, 20).until(EC.element_to_be_clickable(
            (By.XPATH, config["findElement"]["xpath"]["birthday"]["next"]))).click()
        time.sleep(veryShortWait)
    except:
        logger.error("Cannot find next button in birthday section, check XPATH in config file")
        updateClient(config, account, "An error occured during creation routine! Account not created")
        destroy(sa, account, config, logger)
        driver.quit()
        return

    if not mailMode:

        # secure code
        if (config["smsActivate"]["useSpecificNumber"] != "True"):
            secureCode = getSecureCode(sa, number["activation_id"], config, logger)
        else:
            secureCode = getSecureCode(sa, config["smsActivate"]["activationId"], config, logger)

        if (secureCode is None):
            logger.error("Cannot read secure code for the given number. Request deleting number")
            updateClient(config, account, "An error occured during validation number! Account not created")
            destroy(sa, account, config, logger)
            driver.quit()
            return

        time.sleep(shortWait)

        try:
            confirmationCode = driver.find_element(By.NAME, 'confirmationCode')
            if confirmationCode is not None:
                confirmationCode.send_keys(secureCode, Keys.ENTER)

            time.sleep(longWait)

        except NoSuchElementException:
            logger.error("Cannot find confirmation code field, check name in config file")
            updateClient(config, account, "An error occured during creation routine! Account not created")
            destroy(sa, account, config, logger)
            driver.quit()
            return

    else:
        secureCode = "12412312"
        try:
            mailConfirmationCode = driver.find_element(By.NAME, 'email_confirmation_code')
            if mailConfirmationCode is not None:
                mailConfirmationCode.send_keys(secureCode, Keys.ENTER)

            time.sleep(longWait)

        except NoSuchElementException:
            logger.error("Cannot find mail confirmation code field, check name in config file")
            updateClient(config, account, "An error occured during creation routine! Account not created")
            destroy(sa, account, config, logger)
            driver.quit()
            return

    """ Check error code message"""

    try:
        invalidCode = driver.find_element(By.XPATH, config["findElement"]["xpath"]["secureCode"]["invalidCode"])
        if invalidCode is not None:
            logger.error("Secure code received is not valid")
            updateClient(config, account, "Secure code received is not valid! Account not created")
            destroy(sa, account, config, logger)
            driver.quit()
            return
    except NoSuchElementException:
        # Everything is ok if not invalid code label has been found
        pass

    """ Check if phoneSignupConfirmErrorAlert message, if yes --> try login """

    try:
        phoneSignupConfirmErrorAlert = driver.find_element(By.ID, "phoneSignupConfirmErrorAlert")
        if phoneSignupConfirmErrorAlert is not None:
            logger.warning("Probably creation was ok, but IG has blocked the flow")

        driver.get("https://www.instagram.com/accounts/login/")
        sleep(longWait)
        try:
            username = driver.find_element(By.NAME, config["findElement"]["name"]["username"])

            if username is not None:
                username.send_keys(account.username)
                time.sleep(shortWait)
        except:
            logger.error("Cannot find username input, check XPATH in config")
            driver.quit()
            return

        try:
            password = driver.find_element(By.NAME, config["findElement"]["name"]["password"])

            if password is not None:
                password.send_keys(account.password)
                time.sleep(shortWait)
        except:
            logger.error("Cannot find username input, check XPATH in config")
            driver.quit()
            return

        try:
            loginBtn = driver.find_element(By.XPATH, config["findElement"]["xpath"]["login"]["button"])
            if loginBtn is not None:
                loginBtn.click()
        except:
            driver.quit()
            return
        time.sleep(mediumWait)
    except:
        pass

    try:
        WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.XPATH,
                                                                    config["findElement"]["xpath"][
                                                                        "cookieAfterLogin"]))).click()
    except:
        logger.warning("Cannot find cookie after login, check XPATH in config file")

    try:
        sleep(mediumWait)
        driver.get("https://www.instagram.com/")
        sleep(longWait)
    except:
        logger.warning("Instagram take too long to give a response")
        updateClient(config, account, "Instagram took too long to give a response! Account not created")

    try:
        # accepting the notifications.
        notifications = driver.find_element(By.XPATH, config["findElement"]["xpath"]["notifications"])
        if notifications is not None:
            notifications.click()
            sleep(veryShortWait)
    except:
        logger.warning("Cannot find notification button, check XPATH in config file")
        pass

    sleep(mediumWait)

    # Account creation completed...
    logger.info("Getting cookies for current account")
    logger.info(json.dumps(driver.get_cookies()))
    account.cookies = json.dumps(driver.get_cookies())

    updateClient(config, account)

    saveAccountToFile(account, config, logger)

    sleep(shortWait)
    driver.quit()

    logger.info("################### Session ended ###################")
