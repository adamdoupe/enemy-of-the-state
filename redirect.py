import htmlunit

from lazyproperty import lazyproperty
from ignore_urls import filterIgnoreUrlParts
from vectors import urlvector
from link import Link

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
        return urlvector(htmlunit.URL(self.reqresp.request.webrequest.getUrl(), self.location))

    @lazyproperty
    def dompath(self):
        return "REDIRECT"
