from utils import DebugDict
from lazyproperty import lazyproperty

class AbstractRequest(object):

    InstanceCounter = 0

    class ReqRespsWrapper(list):

        def __init__(self, outer):
            self.outer = outer

        def append(self, rr):
            assert rr.response.page
            if self.outer._requestset is not None:
                self.outer._requestset.add(rr.request.shortstr)
            self.outer.changingstate = self.outer.changingstate or rr.request.changingstate
            if rr.request.statehint:
                self.outer.statehints += 1
            return list.append(self, rr)

    def __init__(self, request):
        self.method = request.method
        self.path = request.path
        self.initial_full_path = request.fullpath
        self.reqresps = AbstractRequest.ReqRespsWrapper(self)
        self.instance = AbstractRequest.InstanceCounter
        AbstractRequest.InstanceCounter += 1
        # map from state to AbstractPage
        self.targets = DebugDict(self.instance)
        # counter of how often this page gave hints for detecting a state change
        self.statehints = 0
        self._requestset = None
        self.changingstate = False

    def request_actually_made(self):
        """ Return true if this abstract request was actually made, false otherwise """
        return len(self.reqresps) > 0

    def __str__(self):
        return "AbstractRequest(%s, %s)%d" % (self.requestset, self.targets, self.instance)

    def __repr__(self):
        return "AbstractRequest(%s)%d" % (self.requestset, self.instance)

    @property
    def requestset(self):
        if self._requestset is None:
            self._requestset = set(rr.request.shortstr for rr in self.reqresps)
        return self._requestset

    def __cmp__(self, o):
        return cmp(self.instance, o.instance)

    @lazyproperty
    def isPOST(self):
        return any(i.request.isPOST for i in self.reqresps)
