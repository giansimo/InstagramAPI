from src.utils import *
from src.utilsDriver import *


def startFollowingRoutine(logger, account, actionData):
    logger.info("Start routine")
    config = initConfig("../config.txt")
    chrome_options = initChromeOptions(config["config"]["loadImage"], config["config"]["headlessMode"],
                                       account.userAgent)
    seleniumwire_options = initProxyOptions(config, config["config"]["useCustomProxy"], account)
    driver = getDriver(config, chrome_options, seleniumwire_options)
    loggedError = manageCookiesLogin(config, driver, account)
    if loggedError:
        try:
            driver.close()
        except:
            logger.warning("Cannot close the browser")
        finally:
            updateClient(config, account, "Cannot login with current account. Probably cookies are broken!")

    """
        LOGIC HERE USING ACTIONDATA PARAM !!!!
    """











