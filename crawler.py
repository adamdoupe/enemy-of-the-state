#!/usr/bin/env python

from collections import defaultdict
import hashlib
import struct
import logging

class WebsiteGraph(defaultdict):
    """ dictionary from Page to set of Pages """
    
    def __init__(self):
        defaultdict.__init__(self, set)

class PageSet(set):
    """ set of visited pages (unordered) """

    def __init__(self):
        set.__init__(self)


class Anchor:
    def __init__(self, url, visited=False, target=None):
        self.url = url
        self.visited = visited
        self.target = target

    def __repr__(self):
        return 'Anchor(url=%r, visited=%r, target=%r)' \
                % (self.url, self.visited, self.target)

class Page:

    def __init__(self, url, links=[], cookies=frozenset(), forms=frozenset()):
        self.url = url
        self.links = [Anchor(l) for l in links]
        self.cookies = cookies
        self.forms = forms
        self.str = ' '.join([str(self.url),
            str([l.url for l in self.links]),
            str(self.cookies),
            str(self.forms)])
        self.md5val = hashlib.md5(self.str)
        self.hashval = struct.unpack('i', self.md5val.digest()[:4])[0]
        self.history = [] # list of ordered lists of pages
        self.raw = defaultdict(int) # raw text of pages, i.e. cluster of similar pages

    def __hash__(self):
        return self.hashval

    def __cmp__(self, rhs):
        self.md5val == rhs.md5val

    def __str__(self):
        return self.str


import htmlunit

htmlunit.initVM(':'.join([htmlunit.CLASSPATH, '.']))

class Crawler:

    def __init__(self):
        self.webclient = htmlunit.WebClient()
        self.currentPage = None

    def open(self, url):
        htmlpage = htmlunit.HtmlPage.cast_(self.webclient.getPage(url))
        return self.newPage(htmlpage)

    def newPage(self, htmlpage):
        self.htmlpagewrapped = htmlunit.HtmlPageWrapper(htmlpage)
        self.url = htmlpage.getWebResponse().getRequestUrl().toString()
        self.anchors = self.htmlpagewrapped.getAnchors()
        self.page = Page(url=self.url,
                links=[a.getHrefAttribute() for a in self.anchors])
        return self.page

    def clickAnchor(self, idx):
        htmlpage = self.anchors[idx].click()
        return self.newPage(htmlpage)


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    logger = logging.getLogger("main")
    cr = Crawler()
    pageset = PageSet()
    websitegraph = WebsiteGraph()
    rootpage = cr.open("http://www.cs.ucsb.edu/~cavedon/")
    logger.debug("ROOTPAGE %s", rootpage)
    pageset.add(rootpage)
    nextpage = cr.clickAnchor(0)
    logger.debug("LINK %s", rootpage.links)
    rootpage.links[0].visited = True
    websitegraph[rootpage].add(nextpage)








