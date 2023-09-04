import logging
import threading
import uuid

from flask import request, Blueprint, jsonify
from logging.handlers import TimedRotatingFileHandler

from src.Account import Account
from src.followingService import *

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

formatter = logging.Formatter('%(asctime)s - %(levelname)s: %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')

logname = "../log/Session.log"
handler = TimedRotatingFileHandler(logname, when="midnight", backupCount=30)
handler.suffix = "%Y%m%d"
handler.setFormatter(formatter)
logger.addHandler(handler)

actionsController = Blueprint('actionsController', __name__, url_prefix="/accountActions")

"""
tmp510931203913	Pwd1513195@	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.131 Safari/537.36 RuxitSynthetic/1.0 v4607075084599231731 t4763100215355965436 ath259cea6f altpriv cvcv=2 smf=0	[{"domain": ".instagram.com", "httpOnly": true, "name": "rur", "path": "/", "sameSite": "Lax", "secure": true, "value": "\"CLN\\05461383605204\\0541725037834:01f78e527e93f0c31ab2b5736daabd5a95065e7906c451b3532df6ffe933ff91623aa0b5\""}, {"domain": ".instagram.com", "expiry": 1724951434, "httpOnly": false, "name": "csrftoken", "path": "/", "sameSite": "Lax", "secure": true, "value": "EjzviAQ5GDpJLw1h6JdhcxMpd6xsAt3o"}, {"domain": ".instagram.com", "expiry": 1725037797, "httpOnly": true, "name": "sessionid", "path": "/", "sameSite": "Lax", "secure": true, "value": "61383605204%3ADPY2xklGWG9JIt%3A19%3AAYcNLOqvJQFpDtvevKb9S64DPRphVQzks7dW8XaAew"}, {"domain": ".instagram.com", "expiry": 1701277834, "httpOnly": false, "name": "ds_user_id", "path": "/", "sameSite": "Lax", "secure": true, "value": "61383605204"}, {"domain": ".instagram.com", "expiry": 1725037728, "httpOnly": true, "name": "ig_did", "path": "/", "sameSite": "Lax", "secure": true, "value": "7FE49B54-0E72-4C1D-A543-6CF1D12B0F1E"}, {"domain": ".instagram.com", "expiry": 1728061728, "httpOnly": false, "name": "mid", "path": "/", "sameSite": "Lax", "secure": true, "value": "ZPDJHwALAAGkOQMnxzCBeWY_0joT"}]
{
    "accountData": {
        "username": "tmp510931203913",
        "fullname": "marco_faenza41329013",
        "password": "Pwd1513195@",
        "userAgent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.131 Safari/537.36 RuxitSynthetic/1.0 v4607075084599231731 t4763100215355965436 ath259cea6f altpriv cvcv=2 smf=0",
        "cookies": "[{\"domain\": \".instagram.com\", \"httpOnly\": true, \"name\": \"rur\", \"path\": \"\/\", \"sameSite\": \"Lax\", \"secure\": true, \"value\": \"\\\"CLN\\\\05461383605204\\\\0541725037834:01f78e527e93f0c31ab2b5736daabd5a95065e7906c451b3532df6ffe933ff91623aa0b5\\\"\"}, {\"domain\": \".instagram.com\", \"expiry\": 1724951434, \"httpOnly\": false, \"name\": \"csrftoken\", \"path\": \"\/\", \"sameSite\": \"Lax\", \"secure\": true, \"value\": \"EjzviAQ5GDpJLw1h6JdhcxMpd6xsAt3o\"}, {\"domain\": \".instagram.com\", \"expiry\": 1725037797, \"httpOnly\": true, \"name\": \"sessionid\", \"path\": \"\/\", \"sameSite\": \"Lax\", \"secure\": true, \"value\": \"61383605204%3ADPY2xklGWG9JIt%3A19%3AAYcNLOqvJQFpDtvevKb9S64DPRphVQzks7dW8XaAew\"}, {\"domain\": \".instagram.com\", \"expiry\": 1701277834, \"httpOnly\": false, \"name\": \"ds_user_id\", \"path\": \"\/\", \"sameSite\": \"Lax\", \"secure\": true, \"value\": \"61383605204\"}, {\"domain\": \".instagram.com\", \"expiry\": 1725037728, \"httpOnly\": true, \"name\": \"ig_did\", \"path\": \"\/\", \"sameSite\": \"Lax\", \"secure\": true, \"value\": \"7FE49B54-0E72-4C1D-A543-6CF1D12B0F1E\"}, {\"domain\": \".instagram.com\", \"expiry\": 1728061728, \"httpOnly\": false, \"name\": \"mid\", \"path\": \"\/\", \"sameSite\": \"Lax\", \"secure\": true, \"value\": \"ZPDJHwALAAGkOQMnxzCBeWY_0joT\"}]",
        "proxy": "geo.iproyal.com:12321:Igboostify:991986nt_country-it_session-ch6au2qd_lifetime-30m"
        
    }, 
    "action": "followByUser",
    "actionData": {
        "usernames": [
            "niktot"
            ]
    } 
}
"""
@actionsController.route("/doAction", methods=["POST"])
def doAction():
    accountData = request.json['accountData']
    action = request.json['action']
    actionData = request.json['actionData']
    account = Account(accountData)
    account.sessionId = str(uuid.uuid4())

    if action == "followByUser":    # just an example!!
        thread = threading.Thread(target=startFollowingRoutine, args=(logger, account, actionData))
        thread.start()
        response = jsonify({
                "message": "Start following session for account with id: " + account.sessionId,
                "sessionId": account.sessionId
        })
        return response, 200

