import com.gargoylesoftware.htmlunit as htmlunit
import java

from lazyproperty import lazyproperty
from ignore_urls import filterIgnoreUrlParts
from vectors import urlvector
from link import Link, AbstractLink, Links

class Redirect(Link):

    @lazyproperty
    def location(self):
        location = self.internal
        location = filterIgnoreUrlParts(location)
        return location

    def __str__(self):
        return "Redirect(%s)" % (self.location)

    @property
    def linkvector(self):
        return urlvector(java.net.URL(self.reqresp.request.webrequest.getUrl(), self.location))

    @lazyproperty
    def dompath(self):
        return "REDIRECT"

class AbstractRedirect(AbstractLink):

    def __init__(self, redirects):
        if not isinstance(redirects, list):
            redirects = list(redirects)
        AbstractLink.__init__(self, redirects)
        self.locations = set(i.location for i in redirects)
        self.type = Links.Type.REDIRECT

    def update(self, redirects):
        self.locations = set(i.location for i in redirects)

    @property
    def _str(self):
        return "AbstractRedirect(%s, targets=%s)" % (self.locations, self.targets)

    def equals(self, a):
        return self.locations == a.locations

    @lazyproperty
    def hasquery(self):
        return any(i.find('?') != -1 for i in self.locations)

    @lazyproperty
    def location(self):
        # XXX multiple hrefs not supported yet
        assert len(self.locations) == 1
        return iter(self.locations).next()
