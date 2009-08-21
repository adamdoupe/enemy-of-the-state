#!/usr/bin/env python

from collections import defaultdict
import hashlib
import struct
import logging
import pydot

class WebsiteGraph(defaultdict):
    """ dictionary from Page to set of Pages """
    
    def __init__(self):
        defaultdict.__init__(self, set)

class PageSet(dict):
    """ set of visited pages (unordered) 
        use a map instead of a set because we want to get a reference to
        the object in the set"""

    def __init__(self):
        dict.__init__(self)


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

    def __eq__(self, rhs):
        return self.md5val.digest() == rhs.md5val.digest()

    def __repr__(self):
        return self.str


import htmlunit

htmlunit.initVM(':'.join([htmlunit.CLASSPATH, '.']))

class Crawler:

    def __init__(self):
        self.webclient = htmlunit.WebClient()

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

class Engine:

    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)

    def findPathToUnvisited(self, page):
        seen = set([page])
        heads = {page: []}
        newheads = {}
        while heads:
            for h,p in heads.iteritems():
                if not h.links[-1].visited:
                    if not (h, len(h.links)-1) in self.unvisited:
                        self.logger.error("last link from page %r should be in unvisited list (%s)" % (h, self.unvisited))
                    # exclude the starting page from the path
                    return [i for i in reversed([h]+p[:-1])]
                newpath = [h]+p
                newheads.update([(newh, newpath)
                    for newh in (self.websitegraph[h] - seen)])
                seen |= set(newheads.keys())
            heads = newheads
            newheads = {}

    def navigatePath(self, page, path):
        assert page == self.cr.page
        for p in path:
            anchorIdx = None
            for i,l in enumerate(page.links):
                if l.target == p:
                    anchorIdx = i
                    break
            assert anchorIdx != None
            page = self.cr.clickAnchor(anchorIdx)
            page = self.mapToPageset(page)
        return page


    def processPage(self, page):
        nextlink = None
        for i,l in enumerate(page.links):
            if not l.visited:
                nextlink = i
                break
        if nextlink != None:
            return nextlink

    def mapToPageset(self, page):
        if not page in self.pageset:
            self.pageset[page] = page
            self.unvisited.update([(page, i) for i in range(len(page.links))])
            self.logger.info("new page %s", page.url)
        else:
            self.logger.info("known page %s", page.url)
            # use reference to the pre-existing page
            page = self.pageset[page]
        return page

    def main(self, url):
        self.unvisited = set()
        self.cr = Crawler()
        self.pageset = PageSet()
        self.websitegraph = WebsiteGraph()
        page = self.cr.open(url)
        page = self.mapToPageset(page)
        nextAnchorIdx = self.processPage(page)
        while nextAnchorIdx != None:
            newpage = self.cr.clickAnchor(nextAnchorIdx)
            # use reference to the pre-existing page
            newpage = self.mapToPageset(newpage)

            page.links[nextAnchorIdx].visited = True
            page.links[nextAnchorIdx].target = newpage
            self.websitegraph[page].add(newpage)
            self.unvisited.remove((page, nextAnchorIdx))
            page = newpage
            nextAnchorIdx = self.processPage(page)
            if nextAnchorIdx == None:
                if not len(self.unvisited):
                    # we are done
                    break
                self.logger.info("still %d unvisited links",
                        len(self.unvisited))
                path = self.findPathToUnvisited(page)
                self.logger.debug("found path: %r", path)
                page = self.navigatePath(page, path)
                nextAnchorIdx = self.processPage(page)
                assert nextAnchorIdx != None




    def writeDot(self):
        dot = pydot.Dot()
        nodes = dict([(p, pydot.Node(p.url.split('/')[-1])) for p in self.pageset])
        for n in nodes.itervalues():
            dot.add_node(n)

        for p,l in self.websitegraph.iteritems():
            src = nodes[p]
            for dst in l:
                dot.add_edge(pydot.Edge(src, nodes[dst]))

        dot.write_ps('graph.ps')











if __name__ == "__main__":
    import sys
    logging.basicConfig(level=logging.DEBUG)
    e = Engine()
    e.main(sys.argv[1])
    e.writeDot()








