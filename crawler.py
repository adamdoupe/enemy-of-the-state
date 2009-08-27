#!/usr/bin/env python

from collections import defaultdict
import hashlib
import struct
import logging
import pydot

import config

class Anchor:
    def __init__(self, url, visited=False, target=None):
        self.url = url
        self.visited = visited
        self.target = target

    def __repr__(self):
        return 'Anchor(url=%r, visited=%r, target=%r)' \
                % (self.url, self.visited, self.target)

class Form:
    def __init__(self, method, action, inputs=None, textarea=None,
            selects=None):
        self.method = method
        self.action = action
        self.inputs = inputs
        self.textarea = textarea
        self.selects = selects
        self.target = []
        self.visited = False

    def __repr__(self):
        return ('Form(method=%r, action=%r, inputs=%r, textarea=%r,' +
                    'selects=%r)') % (self.method, self.action, self.inputs,
                            self.textarea, self.selects)

class PageMapper:
    NOT_AGGREG = 0
    AGGREGATED = 1
    AGGREG_PENDING = 2
    AGGREG_IMPOSS = 3

    class Inner:
        def __init__(self, page):
            self.pages = {page: page}
            self.merged = None
            # we ant to use the first reached page as reference for all the
            # similar pages
            self.original = page
            self.aggregation = PageMapper.NOT_AGGREG

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

        def iteritems(self):
            return self.pages.iteritems()

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
        self.unsubmitted = set()
        self.first = {}

    def __getitem__(self, page):
        if page.templetized  not in self.first:
            self.logger.info("new page %s", page.url)
            self.first[page.templetized] = PageMapper.Inner(page)
            self.unvisited.update((page, i) for i in range(len(page.links)))
            self.unsubmitted.update((page, i) for i in range(len(page.forms)))
        else:
            inner = self.first[page.templetized]
            if page in inner:
                if inner.aggregation == PageMapper.AGGREGATED:
                    self.logger.info("known aggregated page %s", page.url)
                    # XXX: may get thr crawler status out-of-sync
                    page = inner.merged
                elif inner.aggregation in \
                        [PageMapper.AGGREG_PENDING, PageMapper.AGGREG_IMPOSS]:
                    self.logger.info("known aggregatable page %s", page.url)
                    # XXX: may get thr crawler status out-of-sync
                    page = inner[page]
                else:
                    self.logger.info("known page %s", page.url)
                    page = inner[page]
            else:
                if inner.aggregation == PageMapper.AGGREGATED:
                    self.logger.info("new aggregated page %s", page.url)
                    inner[page] = page
                    # XXX: may get thr crawler status out-of-sync
                    page = inner.merged
                elif inner.aggregation in \
                        [PageMapper.AGGREG_PENDING, PageMapper.AGGREG_IMPOSS]:
                    self.logger.info("new aggregatable page %s", page.url)
                    inner[page] = page
                    page.aggregation = PageMapper.AGGREG_PENDING
                else:
                    self.logger.info("new similar page %s", page.url)
                    inner[page] = page
                    if len(inner) >= config.SIMILAR_JOIN_THRESHOLD:
                        self.logger.info("aggregatable pages %r",
                                [p.url for p in inner])
                        inner.aggregation = PageMapper.AGGREG_PENDING
                    self.unvisited.update([(page, i)
                        for i in range(len(page.links))])
                    self.unsubmitted.update([(page, i)
                        for i in range(len(page.forms))])

        return page

    def __iter__(self):
        for i in self.first.itervalues():
            for j in i.smartiter():
                yield j

    def checkAggregatable(self, page):
        # TODO: support for backformlinks
        inner = self.first[page.templetized]
        if inner.aggregation != PageMapper.AGGREG_PENDING:
            return
        # make sure we have visited all the links of the first
        # config.SIMILAR_JOIN_THRESHOLD pages
        for p in inner:
            if p.aggregation != PageMapper.AGGREG_PENDING and \
                    ((p, len(p.links)-1) in self.unvisited or
                        (p, len(p.forms)-1) in self.unsubmitted):
                return

        if self.aggregatable(page):
            self.logger.info("aggregating %r", page)
            inner.merged = inner.original
            inner.aggregation = PageMapper.AGGREGATED
            inner.merged.aggregation = PageMapper.AGGREGATED
            for p in inner:
                # update links from other pages to the merged ones
                for pred, anchor in p.backlinks:
                    assert pred.links[anchor].target == p
                    pred.links[anchor].target = inner.merged
        else:
            self.logger.info("impossible to aggregate %r", page)
            inner.aggregation = PageMapper.AGGREG_IMPOSS
            for p,v in inner.iteritems():
                assert p == v, "%r != %r" % (p, v)
                if p.aggregation != PageMapper.AGGREG_PENDING:
                    # XXX AGGREG_PENDING is used to explude nodes from plot
                    p.aggregation = PageMapper.AGGREG_IMPOSS




    def aggregatable(self, page):
        # aggregate only if all the links across aggregatable pages
        # point to the same page
        inner = self.first[page.templetized]
        for i in range(len(page.links)):
            targetset = set(p.links[i].target for p in inner
                if p.aggregation != PageMapper.AGGREG_PENDING)
            print "TARGETSET", targetset
            if len(targetset) > 1 and \
                    not all(p in inner for p in targetset):
                # different pages have different outgoing links
                # and they do not point to pages in the aggregatable set
                return False
        return True


class Page:
    HASHVALFMT = 'i'
    HASHVALFNMTSIZE = struct.calcsize(HASHVALFMT)

    def __init__(self, url, links=[], cookies=frozenset(), forms=frozenset()):
        self.url = url
        self.links = links
        self.cookies = cookies
        self.forms = forms
        self.str = 'Page(%s)' % ','.join([str(self.url),
            str([l.url for l in self.links]),
            str(self.cookies),
            str(self.forms)])
        self.history = [] # list of ordered lists of pages
        self.calchash()
        self.backlinks = set()
        self.backformlinks = set()
        self.aggregation = PageMapper.NOT_AGGREG
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
            targetpage.backlinks.add((self, anchorIdx))

    def linkFormto(self, formIdx, targetpage):
            self.forms[formIdx].visited = True
            self.forms[formIdx].target = targetpage
            targetpage.backformlinks.add((self, formIdx))

class TempletizedPage(Page):

    def __init__(self, page):
        self.page = page
        self.strippedlinks = [str(l.url).split('?')[0] for l in page.links]
        self.str = 'TempletizedPage(%s)' % ','.join([str(self.strippedlinks),
            str(page.cookies),
            str(page.forms)])
        self.calchash()


import htmlunit

htmlunit.initVM(':'.join([htmlunit.CLASSPATH, '.']))

class CrawlerEmptyHistory(Exception):
    pass

class Crawler:

    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.webclient = htmlunit.WebClient()

    def open(self, url):
        self.history = []
        htmlpage = htmlunit.HtmlPage.cast_(self.webclient.getPage(url))
        return self.newPage(htmlpage)

    def createAnchor(self, a):
        return Anchor(a.getHrefAttribute())

    def createForm(self, f):
        return Form(method=f.getMethodAttribute(),
                action=f.getActionAttribute())

    def updateInternalData(self, htmlpage):
        self.htmlpage = htmlpage
        htmlpagewrapped = htmlunit.HtmlPageWrapper(htmlpage)
        self.url = htmlpage.getWebResponse().getRequestUrl().toString()
        self.anchors = [a for a in htmlpagewrapped.getAnchors()
                if not a.getHrefAttribute().split(':', 1)[0].lower()
                in ['mailto']]
        self.forms = [f for f in htmlpagewrapped.getForms()
                if f.getMethodAttribute().lower() == 'get']
        self.page = Page(url=self.url,
                links=[self.createAnchor(a) for a in self.anchors],
                forms=[self.createForm(f) for f in self.forms])

    def newPage(self, htmlpage):
        self.updateInternalData(htmlpage)
        return self.page

    def clickAnchor(self, idx):
        self.history.append(self.htmlpage)
        try:
            htmlpage = self.anchors[idx].click()
        except htmlunit.JavaError, e:
            javaex = e.getJavaException()
            if not htmlunit.FailingHttpStatusCodeException.instance_(javaex):
                raise
            javaex = htmlunit.FailingHttpStatusCodeException.cast_(javaex)
            ecode = javaex.getStatusCode()
            emsg = javaex.getStatusMessage()
            self.logger.warn("%d %s, %s", ecode, emsg,
                    self.anchors[idx].getHrefAttribute())
            return self.errorPage(ecode)
        return self.newPage(htmlpage)

    def submitForm(self, idx, input=None):
        assert not input, "Not implemented"
        self.history.append(self.htmlpage)
        htmlpage = None

        try:
            for submittable in [("input", "type", "submit"),
                    ("input", "type", "image"),
                    ("button", "type", "submit")]:
                try:
                    submitter = self.forms[idx].\
                            getOneHtmlElementByAttribute(*submittable)
                    htmlpage = submitter.click()
                except htmlunit.JavaError, e:
                    javaex = e.getJavaException()
                    if not htmlunit.ElementNotFoundException.instance_(javaex):
                        raise
                    continue
            assert htmlpage, "Could not find submit button"
        except htmlunit.JavaError, e:
            javaex = e.getJavaException()
            if not htmlunit.FailingHttpStatusCodeException.instance_(javaex):
                raise
            javaex = htmlunit.FailingHttpStatusCodeException.cast_(javaex)
            ecode = javaex.getStatusCode()
            emsg = javaex.getStatusMessage()
            self.logger.warn("%d %s, %s", ecode, emsg,
                    self.anchors[idx].getHrefAttribute())
            return self.errorPage(ecode)
        return self.newPage(htmlpage)




#        for f in self.forms:
#            print "***", f
#            for n in htmlunit.HtmlElementWrapper(f).getHtmlElementsByTagName("input"):
#                print n

    def back(self):
        # htmlunit has not "back" functrion
        try:
            htmlpage = self.history.pop()
        except IndexError:
            raise CrawlerEmptyHistory()
        self.updateInternalData(htmlpage)
        return self.page

    def errorPage(self, code):
        self.page = Page(url="%d" % code)
        return self.page


class Engine:
    ANCHOR = 0
    FORM = 1

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
                newheads.update((newh, newpath) for newh in
                    (set(l.target for l in self.pagemap[h].links) - seen))
                seen |= set(newheads.keys())
            heads = newheads
            newheads = {}

    def findPathToUnsubmitted(self, page):
        seen = set([page])
        heads = {page: []}
        newheads = {}
        while heads:
            for h,p in heads.iteritems():
                if h.forms and not h.forms[-1].visited:
                    if not (h, len(h.forms)-1) in self.pagemap.unsubmitted:
                        self.logger.error("last form from page %r should be in unsubmitted list (%s)" % (h, self.pagemap.unsubmitted))
                    # exclude the starting page from the path
                    return [i for i in reversed([h]+p[:-1])]
                newpath = [h]+p
                newheads.update((newh, newpath) for newh in
                    (set(l.target for l in self.pagemap[h].links) - seen))
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
        if page.aggregation == PageMapper.AGGREG_PENDING:
            self.logger.info("not exploring additional aggregatable pages")
            return None
        for i,l in enumerate(page.links):
            if not l.visited:
                return (Engine.ANCHOR, i)
        for i,l in enumerate(page.forms):
            if not l.visited:
                return (Engine.FORM, i)

    def findNextStep(self, page):
        nextAction = None
        while nextAction == None:
            nextAction = self.processPage(page)
            if nextAction == None:
                path = None
                if len(self.pagemap.unvisited):
                    self.logger.info("still %d unvisited links",
                            len(self.pagemap.unvisited))
                    self.logger.debug("unvisited links %r",
                            self.pagemap.unvisited)
                    if page.aggregation != PageMapper.AGGREG_PENDING:
                        path = self.findPathToUnvisited(page)
                elif len(self.pagemap.unsubmitted):
                    self.logger.info("still %d unsubmitted forms",
                            len(self.pagemap.unsubmitted))
                    self.logger.debug("unsubmitted forms %r",
                            self.pagemap.unsubmitted)
                    if page.aggregation != PageMapper.AGGREG_PENDING:
                        path = self.findPathToUnsubmitted(page)
                else:
                    self.logger.info("we are done")
                    # we are done
                    return (None, page)
                if path:
                    self.logger.debug("found path: %r", path)
                    page = self.navigatePath(page, path)
                    nextAction = self.processPage(page)
                    assert nextAction != None
                else:
                    self.logger.info("no path found, stepping back")
                    page = self.cr.back()
                    page = self.pagemap[page]
        self.logger.debug("next action %r", nextAction)
        return (nextAction, page)

    def doAction(self, page, action):
        if action[0] == Engine.ANCHOR:
            newpage = self.cr.clickAnchor(action[1])
            # use reference to the pre-existing page
            newpage = self.pagemap[newpage]

            page.linkto(action[1], newpage)
            try:
                self.pagemap.unvisited.remove((page, action[1]))
            except KeyError:
                # might have been alredy removed by a page merge
                pass

        elif action[0] == Engine.FORM:
            newpage = self.cr.submitForm(action[1])
            # use reference to the pre-existing page
            newpage = self.pagemap[newpage]

            page.linkFormto(action[1], newpage)
            try:
                self.pagemap.unsubmitted.remove((page, action[1]))
            except KeyError:
                # might have been alredy removed by a page merge
                pass
        else:
            assert False, "Unknown action %r" % action
        return newpage

    def main(self, url):
        self.cr = Crawler()
        self.pagemap = PageMapper()
        self.templates = defaultdict(lambda: set())
        page = self.cr.open(url)
        page = self.pagemap[page]
        nextAction = self.processPage(page)
        while nextAction != None:
            newpage = self.doAction(page, nextAction)

            self.pagemap.checkAggregatable(page)
            page = newpage
            nextAction, page = self.findNextStep(page)

    def writeDot(self):
        dot = pydot.Dot()
        nodes = {}
        for p in self.pagemap:
            if p.aggregation != PageMapper.AGGREG_PENDING:
                node = pydot.Node(p.url.split('/')[-1])
                if p.aggregation == PageMapper.AGGREGATED:
                    node.set_color('green')
                elif p.aggregation == PageMapper.AGGREG_IMPOSS:
                    node.set_color('red')
                nodes[p] = node

        for n in nodes.itervalues():
            dot.add_node(n)

        for n,dn in nodes.iteritems():
            src = dn
            for dst in n.links:
                if not dst.target:
                    self.logger.warn("found null target")
                elif dst.target.aggregation != PageMapper.AGGREG_PENDING:
                    dot.add_edge(pydot.Edge(src, nodes[dst.target]))

        dot.write_ps('graph.ps')
        #dot.write_pdf('graph.pdf')

if __name__ == "__main__":
    import sys
    logging.basicConfig(level=logging.DEBUG)
    e = Engine()
    try:
        e.main(sys.argv[1])
    except:
        raise
    finally:
        e.writeDot()








