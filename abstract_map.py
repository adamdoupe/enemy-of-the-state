class AbstractMap(dict):

    def __init__(self, absobj, h=hash):
        self.h = h
        self.absobj = absobj

    def getAbstract(self, obj):
        h = self.h(obj)
        if dict.__contains__(self, h):
            v = self[h]
        else:
            v = self.absobj(obj)
            self[h] = v
        assert all(self.h(i.request) if i.request else True
                for i in v.reqresps)
        return v

    def getAbstractOrDefault(self, obj, default):
        h = self.h(obj)
        if dict.__contains__(self, h):
            v = self[h]
        else:
            v = default
            if v:
                self[h] = v
        assert all(self.h(i.request) if i.request else True
                for i in v.reqresps)
        return v

    def __iter__(self):
        return self.itervalues()

    def setAbstract(self, obj, v):
        h = self.h(obj)
        self[h] = v

    def __contains__(self, obj):
        h = self.h(obj)
        return dict.__contains__(self, h)

