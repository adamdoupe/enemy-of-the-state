#!/usr/bin/env python

from collections import defaultdict
import hashlib
import struct
import logging
import pydot

import config

class WebsiteGraph(defaultdict):
    """ dictionary from Page to set of Pages """

    def __init__(self):
        defaultdict.__init__(self, set)

class Anchor:
    def __init__(self, url, visited=False, target=None):
        self.url = url
        self.visited = visited
        self.target = target

    def __repr__(self):
        return 'Anchor(url=%r, visited=%r, target=%r)' \
                % (self.url, self.visited, self.target)

class PageMapper:

    class Inner:
        def __init__(self, page):
            self.pages = {page: page}
            self.merged = None
            # we ant to use the first reached page as reference for all the
            # similar pages
            self.original = page

        def __getitem__(self, page):
            return self.pages[page]

        def __setitem__(self, page, samepage):
            assert page == samepage
            self.pages[page] = page

        def __len__(self):
            return len(self.pages)

        def __contains__(self, k):
            return k in self.pages

        def __iter__(self):
            return self.pages.__iter__()

        def smartiter(self):
            if self.merged:
                for i in [self.merged]:
                    yield i
            else:
                for i in self.pages:
                    yield i

    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.unvisited = set()
        self.first = {}

    def __getitem__(self, page):
        if page.templetized  not in self.first:
            self.logger.info("new page %s", page.url)
            self.first[page.templetized] = PageMapper.Inner(page)
            self.unvisited.update([(page, i) for i in range(len(page.links))])
        else:
            inner = self.first[page.templetized]
            if page in inner:
                if inner.merged:
                    self.logger.info("known merged page %s", page.url)
                    # XXX: may get thr crawler status out-of-sync
                    page = inner.merged
                else:
                    self.logger.info("known page %s", page.url)
                    page = inner[page]
            else:
                if inner.merged:
                    self.logger.info("new merged page %s", page.url)
                    inner[page] = page
                    # XXX: may get thr crawler status out-of-sync
                    page = inner.merged
                else:
                    self.logger.info("new similar page %s", page.url)
                    inner[page] = page
                    if len(inner) >= config.SIMILAR_JOIN_THRESHOLD:
                        self.logger.info("aggregating similar pages",
                                [p.url for p in inner])
                        inner.merged = inner.original
                        for p in inner:
                            assert len(set([l.target for l in p.links if l])) \
                                    <= 1, "TODO %r" % p.links
                        # XXX: may get thr crawler status out-of-sync
                        page = inner.merged
                    else:
                        self.unvisited.update([(page, i) for i in range(len(page.links))])

        return page

    def __iter__(self):
        for i in self.first.itervalues():
            for j in i.smartiter():
                yield j


class Page:
    HASHVALFMT = 'i'
    HASHVALFNMTSIZE = struct.calcsize(HASHVALFMT)

    def __init__(self, url, links=[], cookies=frozenset(), forms=frozenset()):
        self.url = url
        self.links = [Anchor(l) for l in links]
        self.cookies = cookies
        self.forms = forms
        self.str = ' '.join([str(self.url),
            str([l.url for l in self.links]),
            str(self.cookies),
            str(self.forms)])
        self.history = [] # list of ordered lists of pages
        self.calchash()
        self.backlinks = set()
        self.templetized = TempletizedPage(self)

    def calchash(self):
        self.md5val = hashlib.md5(self.str)
        # we need an int, so get only the first part of the md5 digest
        self.hashval = struct.unpack(Page.HASHVALFMT,
                self.md5val.digest()[:Page.HASHVALFNMTSIZE])[0]

    def __hash__(self):
        return self.hashval

    def __eq__(self, rhs):
        return self.md5val.digest() == rhs.md5val.digest()

    def __repr__(self):
        return self.str

    def linkto(self, anchorIdx, targetpage):
            self.links[anchorIdx].visited = True
            self.links[anchorIdx].target = targetpage
            targetpage.backlinks.add(self)

class TempletizedPage(Page):

    def __init__(self, page):
        self.page = page
        self.strippedlinks = [str(l.url).split('?')[0] for l in page.links]
        self.str = ' '.join([str(self.strippedlinks),
            str(page.cookies),
            str(page.forms)])
        self.calchash()


import htmlunit

htmlunit.initVM(':'.join([htmlunit.CLASSPATH, '.']))

class CrawlerEmptyHistory(Exception):
    pass

class Crawler:

    def __init__(self):
        self.webclient = htmlunit.WebClient()

    def open(self, url):
        self.history = []
        htmlpage = htmlunit.HtmlPage.cast_(self.webclient.getPage(url))
        return self.newPage(htmlpage)

    def updateInternalData(self, htmlpage):
        self.htmlpage = htmlpage
        htmlpagewrapped = htmlunit.HtmlPageWrapper(htmlpage)
        self.url = htmlpage.getWebResponse().getRequestUrl().toString()
        self.anchors = htmlpagewrapped.getAnchors()
        self.page = Page(url=self.url,
                links=[a.getHrefAttribute() for a in self.anchors])

    def newPage(self, htmlpage):
        self.updateInternalData(htmlpage)
        return self.page

    def clickAnchor(self, idx):
        self.history.append(self.htmlpage)
        htmlpage = self.anchors[idx].click()
        return self.newPage(htmlpage)

    def back(self):
        # htmlunit has not "back" functrion
        try:
            htmlpage = self.history.pop()
        except IndexError:
            raise CrawlerEmptyHistory()
        self.updateInternalData(htmlpage)
        return self.page

class Engine:

    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)

    def findPathToUnvisited(self, page):
        seen = set([page])
        heads = {page: []}
        newheads = {}
        while heads:
            for h,p in heads.iteritems():
                if h.links and not h.links[-1].visited:
                    if not (h, len(h.links)-1) in self.pagemap.unvisited:
                        self.logger.error("last link from page %r should be in unvisited list (%s)" % (h, self.pagemap.unvisited))
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
            page = self.pagemap[page]
            assert page == p, 'unexpected link target "%s" instead of "%s"' \
                    % (page, p)
        return page


    def processPage(self, page):
        nextlink = None
        for i,l in enumerate(page.links):
            if not l.visited:
                nextlink = i
                break
        if nextlink != None:
            return nextlink

    def findNextStep(self, page):
        nextAnchorIdx = None
        while nextAnchorIdx == None:
            nextAnchorIdx = self.processPage(page)
            if nextAnchorIdx == None:
                if not len(self.pagemap.unvisited):
                    # we are done
                    return (None, page)
                self.logger.info("still %d unvisited links",
                        len(self.pagemap.unvisited))
                path = self.findPathToUnvisited(page)
                if path:
                    self.logger.debug("found path: %r", path)
                    page = self.navigatePath(page, path)
                    nextAnchorIdx = self.processPage(page)
                    assert nextAnchorIdx != None
                else:
                    self.logger.info("no path found, stepping back")
                    page = self.cr.back()
                    page = self.pagemap[page]
        return (nextAnchorIdx, page)

    def main(self, url):
        self.cr = Crawler()
        self.pagemap = PageMapper()
        self.templates = defaultdict(lambda: set())
        self.websitegraph = WebsiteGraph()
        page = self.cr.open(url)
        page = self.pagemap[page]
        nextAnchorIdx = self.processPage(page)
        while nextAnchorIdx != None:
            newpage = self.cr.clickAnchor(nextAnchorIdx)
            # use reference to the pre-existing page
            newpage = self.pagemap[newpage]

            page.linkto(nextAnchorIdx, newpage)
            self.websitegraph[page].add(newpage)
            self.pagemap.unvisited.remove((page, nextAnchorIdx))
            page = newpage
            nextAnchorIdx, page = self.findNextStep(page)

    def writeDot(self):
        dot = pydot.Dot()
        nodes = dict([(p, pydot.Node(p.url.split('/')[-1])) for p in self.pagemap])
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








