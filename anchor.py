import urlparse

from lazyproperty import lazyproperty
from link import Link
from ignore_urls import filterIgnoreUrlParts
from vectors import urlvector

class Anchor(Link):

    def __init__(self, internal, reqresp):
        # TODO: properly support it
        attrs = list(internal.getAttributesMap().keySet())
        for a in attrs:
            if a.startswith("on") or a == "target":
                internal.removeAttribute(a)
        super(Anchor, self).__init__(internal, reqresp)

    @lazyproperty
    def href(self):
        href = self.internal.getHrefAttribute()
        href = filterIgnoreUrlParts(href)
        return href

    @lazyproperty
    def hrefurl(self):
        return urlparse.urlparse(self.href)

    def click(self):
        return self.internal.click()

    @lazyproperty
    def _str(self):
        return "Anchor(%s, %s)" % (self.href, self.dompath)

    @lazyproperty
    def linkvector(self):
        return urlvector(self.hrefurl)
