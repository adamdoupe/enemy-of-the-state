import urlparse
import htmlunit

from lazyproperty import lazyproperty
from link import Link, Links, AbstractLink
from ignore_urls import filterIgnoreUrlParts
from vectors import urlvector
from fakehtmlunitanchor import FakeHtmlUnitAnchor

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
        if isinstance(self.internal, FakeHtmlUnitAnchor):
            return self.internal.click()
        else:
            element = htmlunit.HtmlElement.cast_(self.internal)
            return element.click(False, False, False, False)

    @lazyproperty
    def _str(self):
        return "Anchor(%s, %s)" % (self.href, self.dompath)

    @lazyproperty
    def linkvector(self):
        return urlvector(self.hrefurl)

class AbstractAnchor(AbstractLink):

    def __init__(self, anchors):
        if not isinstance(anchors, list):
            anchors = list(anchors)
        AbstractLink.__init__(self, anchors)
        self.hrefs = set(i.href for i in anchors)
        self.type = Links.Type.ANCHOR
        self._href = None

    def update(self, anchors):
        oldlen = len(self.hrefs)
        self.hrefs = set(i.href for i in anchors)
        if oldlen != len(self.hrefs):
            self._href = None

    @property
    def _str(self):
        return "AbstractAnchor(%s, targets=%s)" % (self.hrefs, self.targets)

    def equals(self, a):
        return self.hrefs == a.hrefs

    @lazyproperty
    def hasquery(self):
        return any(i.find('?') != -1 for i in self.hrefs)

    @property
    def href(self):
        if not self._href:
            if len(self.hrefs) == 1:
                self._href = iter(self.hrefs).next()
            else:
                # return longest common substring from the beginning
                for i, cc in enumerate(zip(*self.hrefs)):
                    if any(c != cc[0] for c in cc):
                        break
                self._href = iter(self.hrefs).next()[:i]
        return self._href
