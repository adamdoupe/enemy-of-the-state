from lazyproperty import lazyproperty

from anchor import Anchor
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
