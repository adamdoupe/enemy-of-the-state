.from response import Response
from request import Request

class RequestResponse(object):

    InstanceCounter = 1

    def __init__(self, request, response):
        request.reqresp = self
        self.request = request
        self.response = response
        self.prev = None
        self.next = None
        # how many pages we went back before performing this new request
        self.backto = None
        self.instance = Response.InstanceCounter
        Response.InstanceCounter += 1

    def __iter__(self):
        curr = self
        while curr:
            yield curr
            curr = curr.next

    def __str__(self):
        return "%s -> %s %d" % (self.request, self.response, self.instance)

    def __repr__(self):
        return str(self)

    def __cmp__(self, o):
        return cmp(self.instance, o.instance)

