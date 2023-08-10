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
    host = "0.0.0.0"
    port = 8000
    logger.info("Serving on:" + host + ":" + str(port))
    serve(app, host=host, port=port)
