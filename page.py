import htmlunit

from lazyproperty import lazyproperty
from anchor import Anchor, AbstractAnchor
from form import Form
from redirect import Redirect
from validanchor import validanchor
from vectors import linksvector
from link import Links

class Page(object):

    def __init__(self, internal, redirect=False, error=False):
        self.internal = internal
        self.reqresp = None
        self.abspage = None
        self.redirect = redirect
        self.error = error
        self.state = -1
        # cannot use this assert, otherwise calls the lazypropery reirects before reqresp is initialized
        #assert not self.redirect or len(self.redirects) == 1, self.redirects

    @lazyproperty
    def anchors(self):
        return [Anchor(i, self.reqresp) for i in self.internal.getAnchors() if validanchor(self.internal.url.toString(), i.getHrefAttribute().strip())] if not self.redirect and not self.error else []

    @lazyproperty
    def forms(self):
        return [Form(i, self.reqresp) for i in self.internal.getForms()] if not self.redirect and not self.error else []

    @lazyproperty
    def redirects(self):
        return [Redirect(self.internal.getResponseHeaderValue("Location"), self.reqresp)] if self.redirect else []

    @property
    def linkstree(self):
        return self.links.linkstree

    @lazyproperty
    def linksvector(self):
        return linksvector(self)

    @lazyproperty
    def links(self):
        return Links(self.anchors, self.forms, self.redirects)

    @lazyproperty
    def content(self):
        return self.internal.asXml()

    @lazyproperty
    def isHtmlPage(self):
        return htmlunit.HtmlPage.instance_(self.internal)

from collections import defaultdict
from abstract_links import AbstractLinks

class AbstractPage(object):

    InstanceCounter = 0

    def __init__(self, reqresps):
        self.instance = AbstractPage.InstanceCounter
        AbstractPage.InstanceCounter += 1
        self.reqresps = reqresps[:]
        for rr in reqresps:
            rr.response.page.abspage = self

        # maps a state to the corresponding abstract link chosen for that state
        self.statelinkmap = {}
        # maps a state to the corresponding requestresponse objects for that state
        self.statereqrespsmap = defaultdict(list)
        self.seenstates = set()
        self._str = None
        self.abslinks = AbstractLinks([rr.response.page.linkstree
                for rr in self.reqresps])


    def addPage(self, reqresp):
#        if maxstate > 155 and self.instance == 966:
#            pdb.set_trace()

        self.reqresps.append(reqresp)
        self.abslinks.tryMergeLinkstree(reqresp.response.page.linkstree)
        self._str = None


    def __str__(self):
        if self._str is None:
            self._str =  "AbstractPage(#%d, %s)%s" % (len(self.reqresps),
                    set("%s %s" % (i.request.method, i.request.fullpathref) for i in self.reqresps), self.instance)
        return self._str

    def __repr__(self):
        return str(self)

    def match(self, p):
        return self.abslinks.equals(p.abslinks)

    @lazyproperty
    def label(self):
        response = self.reqresps[0].response
        if response.page.error:
            return "%d %s" % (response.code, response.message)
        if response.page.redirect:
            redirects = ' '.join(i.location for i in response.page.redirects)
            return "%d %s\\n%s" % (response.code, response.message, redirects)
        else:
            return "Page(%d)" % self.instance

    def __cmp__(self, o):
        if o is None:
            return 1
        return cmp(self.instance, o.instance)


