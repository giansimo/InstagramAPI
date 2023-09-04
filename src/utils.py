import json
import requests


def updateClient(config, account, errorMessage = None):
    updateClientEndpoint = config["api"]["updateClient"]
    accountJson = account.toJSON()
    message = "" if errorMessage is None else errorMessage
    success = True if message == "" else False
    data = {
        "success": success,
        "error": message,
        "data": accountJson
    }
    response = requests.post(updateClientEndpoint, json=data)

def initUserAgents(config):
    userAgents = []
    # userAgents
    with open(config["path"]["input"] + config["files"]["userAgents"], 'r') as file:
        userAgents = file.readlines()

    return userAgents


def initConfig(path):
    with open(path, 'r') as file:
        data = file.read().replace('\n', '')
        return json.loads(data)