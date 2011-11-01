from lazyproperty import lazyproperty

class Response(object):

    InstanceCounter = 1

    def __init__(self, webresponse, page):
        self.webresponse = webresponse
        self.page = page
        self.instance = Response.InstanceCounter
        Response.InstanceCounter += 1

    @lazyproperty
    def code(self):
        return self.webresponse.getStatusCode()

    @lazyproperty
    def message(self):
        return self.webresponse.getStatusMessage()

    @lazyproperty
    def content(self):
        return self.webresponse.getContentAsString()

    @lazyproperty
    def cookies(self):
        raise NotImplemented

    def __str__(self):
        return "Response(%d %s)" % (self.code, self.message)

    def __cmp__(self, o):
        return cmp(self.instance, o.instance)
