import json
import uuid
import logging
import threading
from datetime import datetime
from flask import Flask, request
from waitress import serve
from logging.handlers import TimedRotatingFileHandler


from src.Account import Account
from src.accountCreatorService import startCreationRoutine

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

formatter = logging.Formatter('%(asctime)s - %(levelname)s: %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')

logname = "../log/Session.log"
handler = TimedRotatingFileHandler(logname, when="midnight", backupCount=30)
handler.suffix = "%Y%m%d"
handler.setFormatter(formatter)
logger.addHandler(handler)


app = Flask(__name__)

@app.route('/createAccount', methods=["POST"])
def createAccount():
    username = request.json['username']
    fullname = request.json['fullname']
    password = request.json['password']
    proxy = request.json['proxy']
    userAgent = request.json['userAgent']

    account = Account(fullname, username, password, str(uuid.uuid4()), proxy, userAgent=userAgent)

    thread = threading.Thread(target=startCreationRoutine, args=(account, logger))
    thread.start()
    response = app.response_class(
        response=json.dumps({
            "message": "Start managing request with id: " + account.sessionId,
            "sessionId": account.sessionId}),
        status=200,
        mimetype='application/json'
    )
    return response


if __name__ == "__main__":
    fullname = "fullnameTest"
    password = "passwordTest12345"
    username = "usernameTest15213141"
    proxy = "84.46.248.122:8008:alice:cool"
    userAgent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/101.0.4951.67 Safari/537.36 RuxitSynthetic/1.0 v6285345330506406824 t4896080028745171261 ath1fb31b7a altpriv cvcv=2 cexpw=1 smf=0"

    account = Account(fullname, username, password, str(uuid.uuid4()), proxy, userAgent=userAgent)
    startCreationRoutine(account, logger)
    """
    host = "0.0.0.0"
    port = 8000
    logger.info("Serving on:" + host + ":" + str(port))
    serve(app, host=host, port=port)
    """