import htmlunit

from ignore_urls import filterIgnoreUrlParts
from lazyproperty import lazyproperty
from form_filler import FormFiller
from vectors import urlvector, formvector

class Request(object):

    def __init__(self, webrequest):
        self.webrequest = webrequest
        self.reqresp = None
        self.absrequest = None
        self.formparams = FormFiller.Params({})
        self.state = -1
        self.statehint = False
        self.changingstate = False
        self.test = self.signature_vector

    @lazyproperty
    def method(self):
        return str(self.webrequest.getHttpMethod())

    @lazyproperty
    def isPOST(self):
        return self.method == str(htmlunit.HttpMethod.POST)

    @lazyproperty
    def path(self):
        return self.webrequest.getUrl().getPath()

    @lazyproperty
    def query(self):
        query = self.webrequest.getUrl().getQuery()
        query = filterIgnoreUrlParts(query)
        return query if query else None

    @lazyproperty
    def ref(self):
        return self.webrequest.getUrl().getRef()

    @lazyproperty
    def fullpath(self):
        fullpath = self.path
        if self.query:
            fullpath += "?" + self.query
        return fullpath

    @lazyproperty
    def fullpathref(self):
        fullpathref = self.fullpath
        if self.ref:
            fullpathref += "#" + self.ref
        return fullpathref

    @lazyproperty
    def params(self):
        return tuple(sorted((nv.getName(), nv.getValue())
                for nv in self.webrequest.getRequestParameters()))

    @lazyproperty
    def cookies(self):
        raise NotImplemented

    @lazyproperty
    def headers(self):
        raise NotImplemented

    @lazyproperty
    def _str(self):
        return "Request(%s %s)" % (self.method, self.fullpathref)

    @lazyproperty
    def shortstr(self):
        return "%s %s" % (self.method, self.fullpath)

    @lazyproperty
    def urlvector(self):
        return urlvector(self)

    @lazyproperty
    def signature_vector(self):
        if self.isPOST:
            # handle post request
            return formvector("POST", self, None, None)
        else:
            return tuple(["GET"] + list(self.urlvector))

    def __str__(self):
        return self._str

    def __repr__(self):
        return str(self)

    @lazyproperty
    def dump(self):
        lines = []
        lines.append(self.method + " " + self.fullpathref)
        for h in self.webrequest.getAdditionalHeaders().entrySet():
            me = htmlunit.Map.Entry.cast_(h)
            lines.append("%s: %s" % (me.key, me.value))
        body = self.webrequest.getRequestBody()
        if body:
            lines.append("")
            lines.append(body)
        if self.params:
            lines.append("\n\nParams:")
            for p in self.params:
                lines.append("%s=%s" % p)
        lines.append("")
        return '\n'.join(lines)

