class Account:

    def __init__(self, fullname, username, password, sessionId = None, proxy = None, cellPhone = None, cookies = None, userAgent = None):
        self.sessionId = sessionId
        self.fullname = fullname
        self.username = username
        self.password = password
        self.proxy = proxy
        self.cellPhone = cellPhone
        self.cookies = cookies
        self.userAgent = userAgent

