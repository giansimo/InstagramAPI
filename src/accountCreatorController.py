import json
import uuid
import logging
import threading
import random
from flask import request, Blueprint, jsonify
from logging.handlers import TimedRotatingFileHandler
from src.Account import Account
from src.accountCreatorService import startCreationRoutine
from src.utils import *

accountCreatorController = Blueprint('accountCreatorController', __name__, url_prefix='/accountCreator')

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

formatter = logging.Formatter('%(asctime)s - %(levelname)s: %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')

logname = "../log/Session.log"
handler = TimedRotatingFileHandler(logname, when="midnight", backupCount=30)
handler.suffix = "%Y%m%d"
handler.setFormatter(formatter)
logger.addHandler(handler)

config = initConfig("../config.txt")
userAgents = initUserAgents(config)


@accountCreatorController.route('/create', methods=["POST"])
def create():

    if 'username' not in request.json \
            or 'fullname' not in  request.json \
            or 'password' not in request.json \
            or 'proxy' not in request.json:
        response = jsonify({
            "message" : "Be sure to insert all the params correctly"
        })
        return response, 400
    else:
        account = Account(request.json)
        account.sessionId = str(uuid.uuid4())
        account.userAgent = request.json['userAgent'] if 'userAgent' in request.json else random.choice(userAgents).replace("\n", "")
        account.mail = request.json['mail'] if 'mail' in request.json else None

        thread = threading.Thread(target=startCreationRoutine, args=(account, logger))
        thread.start()
        response = jsonify({
                "message": "Start managing request with id: " + account.sessionId,
                "sessionId": account.sessionId
        })
        return response, 200

@accountCreatorController.route('/updateClient', methods=["POST"])
def updateClient():
    response = jsonify({
            "success": request.json["success"],
            "error": request.json["error"],
            "data": request.json["data"]
        })

    return response, 200

