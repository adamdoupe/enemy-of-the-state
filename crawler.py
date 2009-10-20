#!/usr/bin/env python

from __future__ import with_statement

from collections import defaultdict
import struct
import logging
import urlparse
import copy
import pydot
import heapq

import config

class Target:
    def __init__(self, target, transition, nvisits=1):
        self.target = target
        self.transition = transition
        self.nvisits = nvisits

    def __repr__(self):
        return "Target(%r, transition=%d, nvisits=%d)" % \
                (self.target, self.transition, self.nvisits)

class LinkBase:
    def __init__(self):
        # do not explore and do not plot link
        self.ignore = False
        # stop clicking on this link
        self.stopcrawling = False
        self.history = None
        self.targets = {}

    def __getitem__(self, state):
        return self.targets[state]

    def __setitem__(self, state, target):
        self.targets[state] = target

    def __contains__(self, state):
        return state in self.targets

    def __len__(self):
        return len(self.targets)

    def iterkeys(self):
        return self.targets.iterkeys()

    def iteritems(self):
        return self.targets.iteritems()

class Anchor(LinkBase):
    def __init__(self, url):
        LinkBase.__init__(self)
        self.url = url
        self.hasparams = url.find('?') != -1

    def __repr__(self):
        return 'Anchor(url=%r, target=%r)' \
                % (self.url, self.targets)

    def hashData(self):
        return self.url

    def strippedHashData(self):
        return self.url.split('?')[0]

class Form(LinkBase):
    def __init__(self, method, action, inputs=[], textarea=[],
            selects=[], hiddens=[]):
        LinkBase.__init__(self)
        self.method = method.lower()
        self.action = action
        self.inputs = inputs
        self.textarea = textarea
        self.selects = selects
        self.hiddens = hiddens
        self.isPOST = action.upper() == "POST"

    def __repr__(self):
        return ('Form(method=%r, action=%r, inputs=%r, textarea=%r,' +
                'selects=%r, hiddens=%r)') % \
                (self.method, self.action, self.inputs,
                self.textarea, self.selects, self.hiddens)

    def hashData(self):
        return '(%s,%s,%s,%s,%s)' % (self.action, self.inputs, self.textarea,
                self.selects, self.hiddens)

    def strippedUniqueHashData(self):
        return '(%s,%s,%s,%s,%s)' % (self.action, sorted(set(self.inputs)),
                sorted(set(self.textarea)), sorted(set(self.selects)),
                sorted(set(self.hiddens)))

    def getFormKeys(self):
        return self.inputs + self.textarea + self.selects


class Links:
    ANCHOR = 0
    FORM = 1
    def __init__(self, anchors, forms):
        self.anchors = anchors
        self.forms = forms

    def nAnchors(self):
        return len(self.anchors)

    def nForms(self):
        return len(self.forms)

    def len(self, what):
        if what == Links.ANCHOR:
            return self.nAnchors()
        elif what == Links.FORM:
            return self.nForms()
        else:
            raise KeyError()

    def __repr__(self):
        return '(%s, %s)' % (self.anchors, self.forms)

    def hashData(self):
        return '([%s], [%s])' % (','.join(i.hashData() for i in self.anchors),
                ','.join(i.hashData() for i in self.forms))

    def strippedHashData(self):
        return '([%s], [%s])' % (','.join(i.strippedHashData()
                    for i in self.anchors),
                ','.join(i.hashData() for i in self.forms))

    def strippedUniqueHashData(self):
        return '([%s], [%s])' % (','.join(set(i.strippedHashData()
                    for i in self.anchors)),
                ','.join(i.strippedUniqueHashData() for i in self.forms))

    def __getitem__(self, idx):
        if idx[0] == Links.ANCHOR:
            return self.anchors[idx[1]]
        elif idx[0] == Links.FORM:
            return self.forms[idx[1]]
        else:
            raise KeyError(idx)

    def __iter__(self):
        return self.iter(Links.FORM)

    def getUnvisited(self, state, what=FORM):
        for i,l in enumerate(self.anchors):
            if not l.ignore and not l.stopcrawling and not state in l:
                return (Links.ANCHOR, i)
        if what >= Links.FORM:
            for i,l in enumerate(self.forms):
                if not l.ignore and not l.stopcrawling and not state in l:
                    return (Links.FORM, i)

    def iter(self, what=FORM):
        if what == Links.ANCHOR:
            iterlist = [self.anchors]
        elif what == Links.FORM:
            iterlist = [self.anchors, self.forms]
        else:
            raise KeyError()

        for i in iterlist:
            for j in i:
                if not j.ignore and not j.stopcrawling:
                    yield j

    def enumerate(self):
        for i,k in enumerate(self.anchors):
            if not k.ignore and not k.stopcrawling:
                yield ((Links.ANCHOR, i), k)
        for i,k in enumerate(self.forms):
            if not k.ignore and not k.stopcrawling:
                yield ((Links.FORM, i), k)

    def clone(self):
        cloned = copy.copy(self)
        cloned.anchors = [copy.copy(i) for i in self.anchors]
        cloned.forms = [copy.copy(i) for i in self.forms]
        return cloned

def notVisited(page, link, state):
    l = page.links[link]
    return not l.ignore and not l.stopcrawling and not state in l

class Unvisited:
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.anchors = set()
        self.forms = set()

    def updateFromPage(self, page, state):
        self.anchors.update((page, i, state) for i in
                range(page.links.nAnchors())
                if notVisited(page, (Links.ANCHOR, i), state))
        self.forms.update((page, i, state) for i in
                range(page.links.nForms())
                if notVisited(page, (Links.FORM, i), state))

    def remove(self, page, link, state):
        if link[0] == Links.ANCHOR:
            self.anchors.remove((page, link[1], state))
        if link[0] == Links.FORM:
            self.forms.remove((page, link[1], state))
        else:
            raise KeyError(link)

    def __nonzero__(self):
        return True if self.anchors or self.forms else False

    def logInfo(self):
        self.logger.info("still unvisited: %d anchors, %d forms",
                len(self.anchors), len(self.forms))
        self.logger.debug("still unvisited: set(%r) anchors, set(%r) forms",
                [i for i in sorted(self.anchors)],
                [i for i in sorted(self.forms)])

    def len(self, what):
        if what == Links.ANCHOR:
            return len(self.anchors)
        elif what == Links.FORM:
            return len(self.forms)
        else:
            raise KeyError(idx)

    def __contains__(self, link):
        if link[1][0] == Links.ANCHOR:
            return (link[0], link[1][1], link[2]) in self.anchors
        if link[1][0] == Links.FORM:
            return (link[0], link[1][1], link[2]) in self.forms
        return False

    def __repr__(self):
        return "Unvisited(%r, %r)" % (self.anchors, self.forms)


class PageMapper:
    NOT_AGGREG = 0
    AGGREGATED = 1
    AGGREG_PENDING = 2
    AGGREG_IMPOSS = 3
    STATUS_SPLIT = 4

    class Inner:
        def __init__(self, page):
            self.pages = {page.basic: page}
            self.merged = None
            # we ant to use the first reached page as reference for all the
            # similar pages
            self.original = page
            self.aggregation = PageMapper.NOT_AGGREG
            self.templ_outlinks = defaultdict(lambda: (0, set()))

        def __getitem__(self, page):
            return self.pages[page.basic]

        def __setitem__(self, page, samepage):
            self.pages[page.basic] = samepage

        def clear(self):
            self.pages = {}

        def __len__(self):
            return len(self.pages)

        def __contains__(self, k):
            return k.basic in self.pages

        def hasvalue(self, p):
            return p in self.pages.itervalues()

        def __iter__(self):
            return self.pages.itervalues()

        def iteritems(self):
            return self.pages.iteritems()

        def itervalues(self):
            return self.pages.itervalues()

        def smartiter(self):
            if self.merged:
                for i in [self.merged]:
                    yield i
            else:
                # iter on values, as keys may be ExactPage()
                for i in self.pages.itervalues():
                    yield i

        def __repr__(self):
            return self.pages.__repr__()

    class Splits:
        def __init__(self, inner):
            self.inners = [inner]
            self.latest = inner

        def __len__(self):
            return len(self.inners)

        def __iter__(self):
            return self.inners.__iter__()

        def append(self, inner):
            self.inners.append(inner)

        def __repr__(self):
            return self.inners.__repr__()

        def __getitem__(self, idx):
            return self.inners[idx]

    class Buckets:

        def __init__(self):
            self.buckets = {}

        def __getitem__(self, page):
            return self.buckets[page.templetized]

        def __setitem__(self, page, splits):
            self.buckets[page.templetized] = splits

        def __contains__(self, page):
            return self.buckets.__contains__(page.templetized)

        def itervalues(self):
            return self.buckets.itervalues()

    class RepeatingLinksBuckets:
        def __init__(self):
            self.buckets = defaultdict(lambda: set())

        def add(self, page):
            buck = self.buckets[page.rep_templ]
            buck.add(page)
            return buck

        def get(self, page):
            self.buckets[page.rep_templ]

        def __contains__(self, page):
            return self.buckets.__contains__(page.rep_templ)

        def itervalues(self):
            return self.buckets.itervalues()

    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.unvisited = Unvisited()
        self.unsubmitted = set()
        self.buckets = PageMapper.Buckets()
        self.replinks_buckets = PageMapper.RepeatingLinksBuckets()

    def __getitem__(self, page):
        return self.get(page)

    def get(self, page, preferred=None):
        if page not in self.buckets:
            self.logger.info("new page %s", page.url)
            self.buckets[page] = \
                    PageMapper.Splits(PageMapper.Inner(page))
        else:
            splits = self.buckets[page]
            if len(splits) > 1:
                self.logger.info("potential state splitted page %s", page)
            inner = None
            if preferred:
                # return the preferred page if available
                # look inside map values as, inner maps are hashed on .basic
                for i in splits:
                    if i.hasvalue(preferred):
                        inner = i
                        self.logger.debug("preferred page found: %r", preferred)
                        break
                if not inner:
                    self.logger.debug("preferred page not available: %r", preferred)
                    inner = splits.latest
            else:
                inner = splits.latest
            # if we have a page that is not in the latest split, look for it
            # in the other splits
            if len(splits) > 1 and not page in inner:
                for i in splits:
                    if page in i:
                        inner = i
                        break
#            assert len(splits) == 1 or page in inner, \
#                    "SPLITS %r\nINNER %r" % (splits, inner)
            if page in inner:
                if inner.aggregation == PageMapper.AGGREGATED:
                    self.logger.info("known aggregated page %s", page.url)
                    # XXX: may get thr crawler state out-of-sync
                    page = inner.merged
                elif inner.aggregation in \
                        [PageMapper.AGGREG_PENDING, PageMapper.AGGREG_IMPOSS]:
                    self.logger.info("known aggregatable page %s", page.url)
                    # XXX: may get thr crawler state out-of-sync
                    page = inner[page]
                else:
                    self.logger.info("known page %s", page)
                    page = inner[page]
            else:
                if inner.aggregation == PageMapper.AGGREGATED:
                    self.logger.info("new aggregated page %s", page.url)
                    inner[page] = page
                    page.aggregation = PageMapper.AGGREGATED
                    # XXX: may get thr crawler state out-of-sync
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

        # if we are getting too many pages with a different number of similar
        # links (e.g. cart) stop going to that pages
        if len(self.replinks_buckets.add(page)) \
                >= config.SIMILAR_JOIN_THRESHOLD:
            page.stopcrawling = True

        return page

    def __iter__(self):
        for i in self.buckets.itervalues():
            for j in i:
                for k in j.smartiter():
                    yield k

    def checkAggregatable(self, page, state):
        # TODO: support for backformlinks
        splits = self.buckets[page]
        inner = splits.latest
        if inner.aggregation != PageMapper.AGGREG_PENDING:
            return
        # make sure we have visited all the links of the first
        # config.SIMILAR_JOIN_THRESHOLD pages
        for p in inner:
            if p.aggregation != PageMapper.AGGREG_PENDING:
                if p.links.getUnvisited(state):
                    return

        if self.aggregatable(page, state):
            self.logger.info("aggregating %r", page)
            inner.merged = inner.original
            inner.aggregation = PageMapper.AGGREGATED
            inner.merged.aggregation = PageMapper.AGGREGATED
            for p in inner:
                # update links from other pages to the merged ones
                if p.aggregation != PageMapper.AGGREG_PENDING:
                    # XXX AGGREG_PENDING is used to exclude nodes from plot
                    p.aggregation = PageMapper.AGGREGATED
                for pred, anchor in p.backlinks:
                    assert pred.links[anchor].target == p
                    pred.links[anchor].target = inner.merged
        else:
            self.logger.info("impossible to aggregate %r", page)
            inner.aggregation = PageMapper.AGGREG_IMPOSS
            for p in inner:
                if p.aggregation != PageMapper.AGGREG_PENDING:
                    # XXX AGGREG_PENDING is used to exclude nodes from plot
                    p.aggregation = PageMapper.AGGREG_IMPOSS


    def aggregatable(self, page, state):
        # aggregate only if all the links across aggregatable pages
        # point to the same page
        # XXX if conditions is false it may be worth trying to split
        splits = self.buckets[page]
        inner = splits.latest
        state = -1
        for i,l in page.links.enumerate():
            if len(l) != 1 or not state in l:
                return False
            targetset = set(p.links[i][state].target for p in inner
                if p.aggregation != PageMapper.AGGREG_PENDING)
            #print "TARGETSET", targetset
            if len(targetset) > 1 and \
                    not all(p in inner for p in targetset):
                # different pages have different outgoing links
                # and they do not point to pages in the aggregatable set
                return False
        return True

    def setLatest(self, page, splitidx):
        splits = self.buckets[page]
        if splitidx < 0:
            inner = PageMapper.Inner(page)
            splits.append(inner)
            splits.latest = inner
        else:
            splits.latest = splits[splitidx]

    def isClone(self, page, p, link, target):
        pagetarget = page.links[link].target
        ptarget = p.links[link].target
        assert not ptarget or \
                ptarget.aggregation == pagetarget.aggregation, \
                "%r != %r" % (ptarget.aggregation, pagetarget.aggregation)
        if not ptarget or target.equiv(ptarget):
            assert p != page, "[%d], %r->%r, %r->%r, %r" \
                    % (ptarget.aggregation, p, ptarget, page,
                            pagetarget, target)
            return p
        return None

    def findClone(self, page, link, target):
        pagetarget = page.links[link].target
        assert not target.equiv(pagetarget), \
                "%d %s %s %x(%x) %x(%x)" % (pagetarget.aggregation,
                        target.split, pagetarget.split,
                        pagetarget.basic.__hash__(), pagetarget.__hash__(),
                        target.basic.__hash__(), target.__hash__())
        splits = self.buckets[page]
        for splitidx,inner in enumerate(splits):
            assert (inner.aggregation == PageMapper.AGGREGATED) \
                    == (inner.merged != None)
            if inner.merged:
                ret = self.isClone(page, inner.merged, link, target)
                if ret:
                    return (ret, splitidx)
            else:
                for p in inner:
                    # we need the follwing check because page may be
                    # aggragatable; equiv() would fail because it it checking
                    # the split values
                    if page.basic == p.basic:
                        ret = self.isClone(page, p, link, target)
                        if ret:
                            return (ret, splitidx)
        return (None, -1)

class Page:
    HASHVALFMT = 'i'
    HASHVALFNMTSIZE = struct.calcsize(HASHVALFMT)

    def __init__(self, url, anchors=[], forms=[], cookies=[]):
        self.url = url
        self.links = Links(anchors, forms)
        self.cookies = cookies
        self.str = 'Page(%s)' % ','.join([str(self.url),
            self.links.hashData(),
            str(self.cookies)])
        self.histories = []
        self.strhash = self.str.__hash__()
        self.hashval = id(self)
        self.backlinks = set()
        self.aggregation = PageMapper.NOT_AGGREG
        self.templetized = TempletizedPage(self)
        self.basic = BasicPage(self)
        self.split = False
        self.rep_templ = RepeatingLinksTempletizedPage(self)
        self.stopcrawling = False

    def __hash__(self):
        return self.hashval

    def __eq__(self, rhs):
        return self.hashval == rhs.hashval

    def __ne__(self, rhs):
        return self.hashval != rhs.hashval

    def __cmp__(self, rhs):
        return self.strhash.__cmp__(rhs.strhash)

    def __repr__(self):
        return self.str

    def linkto(self, idx, targetpage, state, transition):
        link = self.links[idx]
        assert state not in link
        link[state] = Target(targetpage, nvisits=1,
                transition=transition)
#        link.history = self.histories[-1]
        # TODO fix backlinks with state
        targetpage.backlinks.add((self, idx))
        link.stopcrawling = targetpage.stopcrawling

    def getUnvisitedLink(self, state):
        return self.links.getUnvisited(state)

    def clone(self):
        cloned = copy.copy(self)
        cloned.histories = []
        cloned.backlinks = set()
        cloned.links = self.links.clone()
        cloned.hashval = id(cloned)
        cloned.split = self.split
        return cloned

    def equiv(self, rhs):
        return not (self.split or rhs.split) and self.basic == rhs.basic \
                or self == rhs

class BasicPage(Page):

    def __init__(self, page):
        self.page = page
        self.str = 'Basic' + self.page.str
        self.hashval = self.str.__hash__()

class TempletizedPage(Page):

    def __init__(self, page):
        self.page = page
        self.str = 'TempletizedPage(%s)' % \
                ','.join([self.page.url.split('?')[0], page.links.strippedHashData(),
                    str(page.cookies)])
        self.hashval = self.str.__hash__()

class RepeatingLinksTempletizedPage(Page):

    def __init__(self, page):
        self.page = page
        self.str = 'RepatingLinksTempletizedPagePage(%s)' % \
                ','.join([self.page.url.split('?')[0],
                    page.links.strippedUniqueHashData(),
                    str(page.cookies)])
        self.hashval = self.str.__hash__()

class FormFiller:
    def __init__(self):
        self.forms = {}

    def add(self, k):
        self.forms[tuple(sorted(k.keys()))] = k

    def __getitem__(self, k):
        return self.forms[tuple(sorted([i for i in k if i]))]


import htmlunit

htmlunit.initVM(':'.join([htmlunit.CLASSPATH, '.']))


# running htmlunit via JCC will override the signal halders,
# and we cannot catch ctrl-C, so let's use SIGUSR1

import signal

def signalhandler(signum, frame):
    raise KeyboardInterrupt

signal.signal(signal.SIGUSR1, signalhandler)

class CrawlerEmptyHistory(Exception):
    pass

class CrawlerActionFailure(Exception):
    pass

class CrawlerUnsubmittableForm(CrawlerActionFailure):
    pass

class Crawler:

    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        #self.webclient = htmlunit.WebClient(htmlunit.BrowserVersion.INTERNET_EXPLORER_6)
        self.webclient = htmlunit.WebClient()
        self.webclient.setThrowExceptionOnScriptError(False);
        self.webclient.setUseInsecureSSL(True)

    def open(self, url):
        self.history = []
        htmlpage = htmlunit.HtmlPage.cast_(self.webclient.getPage(url))
        return self.newPage(htmlpage)

    def createAnchor(self, a):
        return Anchor(a.getHrefAttribute())

    def createForm(self, f):
        element = htmlunit.HtmlElementWrapper(f)
        inputs = [n.getAttribute('name')
                for n in element.getHtmlElementsByTagName('input')
                if n.getAttribute('type') != "hidden"]
        hiddens = ["%s=%s" % (n.getAttribute('name'), n.getAttribute('value'))
                for n in element.getHtmlElementsByTagName('hidden')
                if n.getAttribute('type') == "hidden"]
        return Form(method=f.getMethodAttribute(),
                action=f.getActionAttribute(),
                inputs=inputs, hiddens=hiddens)

    def validAnchor(self, a):
        aHref = a.getHrefAttribute()
        ret = not aHref.split(':', 1)[0].lower() in ['mailto'] \
                and (not aHref.startswith('http') or aHref.startswith("https://support.myyardi.com/crmportal/"))
        if not ret:
            self.logger.info("skipping %r", aHref)
        else:
            self.logger.debug("valid anchor %r", aHref)
        return ret


    def updateInternalData(self, htmlpage):
        # XXX cast should not be needed
        self.htmlpage = htmlunit.HtmlPage.cast_(htmlpage)
        htmlpagewrapped = htmlunit.HtmlPageWrapper(htmlpage)
        self.url = htmlpage.getWebResponse().getRequestUrl().toString()
        self.anchors = [a for a in htmlpagewrapped.getAnchors()
                if self.validAnchor(a)]
        self.forms = [f for f in htmlpagewrapped.getForms()]
#                if f.getMethodAttribute().lower() == 'get']
        self.page = Page(url=self.url,
                anchors=[self.createAnchor(a) for a in self.anchors],
                forms=[self.createForm(f) for f in self.forms])

    def newPage(self, htmlpage):
        self.updateInternalData(htmlpage)
        self.logger.info("got page %r %r %r", self.url, self.anchors, self.forms)
#        self.logger.debug("got page content %s", self.htmlpage.getWebResponse().getContentAsString())
        return self.page

    def clickAnchor(self, idx):
        self.history.append(self.htmlpage)
        try:
            self.logger.debug("clicking on %r", self.anchors[idx])
            htmlpage = self.anchors[idx].click()
        except htmlunit.JavaError, e:
            javaex = e.getJavaException()
            if htmlunit.FailingHttpStatusCodeException.instance_(javaex):
                javaex = htmlunit.FailingHttpStatusCodeException.cast_(javaex)
                ecode = javaex.getStatusCode()
                emsg = javaex.getStatusMessage()
                self.logger.warn("%d %s, %s", ecode, emsg,
                        self.anchors[idx].getHrefAttribute())
                return self.errorPage(ecode)
            elif htmlunit.IllegalArgumentException.instance_(javaex):
                import traceback
                traceback.print_exc()
                return self.errorPage(666)
        return self.newPage(htmlpage)

    def printChild(self, e, n=0):
        print ' '*n, e
        try:
            for i in e.getChildElements():
                self.printChild(i, n+1)
        except AttributeError:
            pass

    def submitForm(self, idx, params):
        htmlpage = None

        form = self.forms[idx]

        self.logger.info("submitting form %s %r and params: %r",
                form.getMethodAttribute().upper(), form.getActionAttribute(),
                params)

#        print "===========", self.url
#        for f in self.forms:
#            print "***", f
#            for n in htmlunit.HtmlElementWrapper(f).getHtmlElementsByTagName("input"):
#                print n
#            self.printChild(f)

        for k,v in params.iteritems():
            form.getInputByName(k).setValueAttribute(v)

        try:
            # find an element to click in order to submit the form
            # TODO: explore clickable regions in input type=image
            for submittable in [("input", "type", "submit"),
                    ("input", "type", "image"),
                    ("input", "type", "button"),
                    ("button", "type", "submit")]:
                try:
                    submitter = self.forms[idx].\
                            getOneHtmlElementByAttribute(*submittable)
                    htmlpage = submitter.click()
                    break
                except htmlunit.JavaError, e:
                    javaex = e.getJavaException()
                    if not htmlunit.ElementNotFoundException.instance_(javaex):
                        raise
                    continue

            if not htmlpage:
                self.logger.warn("could not find submit button for form %s %r in page %r",
                        form.getMethodAttribute().upper(),
                        form.getActionAttribute(), self.url)
                raise CrawlerUnsubmittableForm()
        except htmlunit.JavaError, e:
            javaex = e.getJavaException()
            if not htmlunit.FailingHttpStatusCodeException.instance_(javaex):
                raise
            javaex = htmlunit.FailingHttpStatusCodeException.cast_(javaex)
            ecode = javaex.getStatusCode()
            emsg = javaex.getStatusMessage()
            self.logger.warn("%d %s, %s", ecode, emsg,
                    self.anchors[idx].getHrefAttribute())
            self.history.append(self.htmlpage)
            return self.errorPage(ecode)

        self.history.append(self.htmlpage)
        return self.newPage(htmlpage)


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
    def __init__(self, formfiller=None):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.formfiller = formfiller
        self.maxstate = 1

    def getWeight(self, idx, link):
        if idx[0] == Links.FORM:
            return 1 if link.isPOST else 2
        else: #if idx[0] == Links.ANCHOR:
            return 3 if link.hasparams else 4

    def findPathToUnvisited(self, page, state):
        unvisited = [None] * 4
        haveunvanchors = self.pagemap.unvisited.len(Links.ANCHOR) > 0
        seen = set()
        # distance is (unknown_state, post, get, link_with_?, link)
        heads = [((0, 0, 0, 0, 0), page, state, [])]
        while heads:
            d, h, s, p = heapq.heappop(heads)
#            print "HH", d, h, p
            if (h,s) in seen:
                continue
            seen.add((h, s))
            unvlink = h.links.getUnvisited(s)
#            print 'U', unvlink
            if unvlink:
                assert (h, unvlink, s) in self.pagemap.unvisited, "page %r(%d)  link %r not in %r" % (h, s, unvlink, self.pagemap.unvisited)
                # exclude the starting page from the path
                path = [i for i in reversed([(h,None,s)]+p)]
                weight = self.getWeight(unvlink, h.links[unvlink])
                if weight == 4 or \
                        not haveunvanchors and weight >= 2:
                    # anchor with no '?' or GET form if no unvisited anchors
                    return path
                if not unvisited[weight]:
                    unvisited[weight] = path
            for idx,link in h.links.enumerate():
                newpath = [(h,idx,s)]+p
                if link.ignore or link.stopcrawling:
                    continue
                if s in link:
                    # links we already know as outgoing from this state
                    t = link[s]
                    if not t.target or (t.target, t.transition) in seen:
                        continue
                    newdist = list(d)
                    newdist[self.getWeight(idx, link)] += 1
#                    print "P1", heads, (tuple(newdist), t.target, s, newpath)
                    heapq.heappush(heads, (tuple(newdist), t.target, s,
                        newpath))
                for tos,t in link.iteritems():
                    # other outgoing links we already observed form other states
                    if tos == s:
                        continue
#                    if t.transition == s:
#                        # assume the link is state preserving
#                        tos = s
                    newdist = list(d)
                    newdist[self.getWeight(idx, link)] += 1
                    newdist[0] += 1 # as we actually really not sure this
                                    # transition will work from this state
#                    print "P2", heads, (tuple(newdist), t.target, s, newpath)
                    heapq.heappush(heads, (tuple(newdist), t.target, s,
                        newpath))


        for p in unvisited:
            if p: return p
        self.logger.warn("unexplored forms not reachable!")

    def navigatePath(self, page, path):
        assert page.basic == self.cr.page.basic
        assert path[0][0] == page
        for currpage,linkidx,currst,nextpage,nextst in \
                [(curr[0],curr[1],curr[2],next[0],next[2])
                        for curr,next in zip(path[:-1], path[1:])]:

            newpage,newst = self.doAction(currpage, linkidx, currst,
                    preferred=nextpage, preferredstate=nextst)

            self.validateHistory(currpage)
            # that old page might be newpage, so nthe history may have changed
            # so do not add the following exception
            # (actually also the check about might be at riks)
            #self.validateHistory(page.histories[-1][-1][0])

            link = currpage.links[linkidx]
            target = link[currst]
            assert target.target == nextpage, "target %r\nnext %r" % \
                    (target.target, nextpage)
            # XXX is this if ever true? btw, it it happen to be false you
            # will now get an exception two lines above here!
            if not currst in link:
                self.logger.info('new link target "%s" (%d->%d)"',
                            newpage, currst, newst)
                self.updateOutLinks(currpage, linkidx, newpage, currst,
                    newst)
                if (newpage,newst) != (nextpage,nextst):
                    self.logger.info('unexpected newpage "%s" (%d) instead ' +
                        'of "%s" (%d)', newpage, newst, nextpage, nextst)
                    return (newpage, newst)
            else:
                target = link[currst]
                # next values are computing using a pre-existing path,
                # so the state must be consistent, if the newpage is the
                # expected one
                assert not newpage == nextpage or newst == nextst,\
                        "%r(%d), %r(%d)" % (newpage, newst, nextpage, nextst)
                if newpage != nextpage:
                    self.logger.info('unexpected link target "%s" instead of' +
                            ' "%s"', newpage, nextpage)
                    clonedpage, clonedst = self.splitPage(currpage, linkidx, currst,
                            newpage, newst)
                    # update history (which was set by doAction())
                    self.history = clonedpage.histories[-1] + \
                            [(clonedpage, linkidx, clonedst)]
                    newpage.histories[-1] = self.history[:]
                    return (newpage, newst)
                else:
                    self.validateHistory(newpage)
                    if newpage.split:
                        assert target.target == newpage
                    if target.nvisits == 0:
                        newpage.backlinks.add((page, linkidx, currst))
                    target.nvisits += 1

        return (newpage, newst)

    def validateHistory(self, page):
        if not page.aggregation in [PageMapper.NOT_AGGREG]:
                # XXX history not correct for aggregated pages!
                return
        prevpage, prevlinkidx, prevst = page.histories[-1][-1]
        prevlink =  prevpage.links[prevlinkidx][prevst]
        assert prevlink.target == page, "%r %r %r %r" % (prevlink.target, page, prevlink.target.links, page.links)
        assert page.equiv(prevlink.target), \
                "%r{%r} %r{%r} --- %r" % (prevlink.target, prevlink.target.links, page, page.links, self)

    def splitPage(self, page, linkidx, currst, newpage, newst, splitstate=-1):
        self.logger.info("diverging %r", page)

        self.validateHistory(page)
        # that old page might be newpage, so nthe history may have changed
        # so do not add the following exception
        # (actually also the check about might be at riks)
        #self.validateHistory(page.histories[-1][-1][0])

        assert currst in page.links[linkidx]

        link = page.links[linkidx]
        validtargets = {}
        for s,t in link.iteritems():
            if currst == 1 and s == 6:
                print "TTT", t
            # XXX for now force destination state to match
            # in the future we could try to adjust the destination state
            if s != currst and t.target == newpage and t.transition == newst:
                assert s not in validtargets
                validtargets[s] = t.transition
        newstate = None
        if validtargets:
            # pick the most recent seen state with the correct target
            for prevpage, prevlinkidx, prevst in page.histories[-1]:
                if prevst in validtargets:
                    newstate = prevst
                    assert s in validtargets, "%r %r" % (s, validtargets)
                    tostate = validtargets[s]
                    break
            self.logger.debug("changing from state %d to %d", currst, newstate)
            assert newstate and newstate != currst
            link[newstate].nvisits += 1
        else: # no validstates
            # page has not been already seen
            if splitstate < 0:
                # create new state
                self.maxstate += 1
                newstate = self.maxstate
            else:
                # reuse the state that has just been used by splitState()
                newstate = splitstate
            # keep state for the target page
            tostate = newst
            self.logger.debug("changing from state %d to new %d", currst,
                    newstate)
            link[newstate] = Target(newpage, transition=tostate)
            link.stopcrawling = newpage.stopcrawling

        # XXX for now force destination state to match
        assert tostate == newst

        lasthistory = page.histories.pop()

        # remove last histories entry as it proved to be incorrect
        prevpage, prevlinkidx, prevst = lasthistory[-1]
        prevlink =  prevpage.links[prevlinkidx]
        prevtgt =  prevlink[prevst]

        assert prevtgt.target == page, "%r %r %r" % (prevtgt.target, page, \
                prevpage)
        assert prevtgt.nvisits > 0
        if prevtgt.nvisits == 1:
            prevtgt.transition = newstate
        else:
            # we have already gone through that link with a different account, 
            # we need to go back and split again
            clonedprev, newprevst = self.splitPage(prevpage, prevlinkidx,
                    prevst, page, newstate, newstate)
            prevtgt.nvisits -= 1
            prevpage = clonedprev
            prevst = newprevst

        # append correct new history
        page.histories.append(prevpage.histories[-1] +
                    [(prevpage, prevlinkidx, prevst)])

        return page, newstate


    def processPage(self, page, state):
        if page.aggregation == PageMapper.AGGREG_PENDING:
            # XXX in this way we forse the crawler to use the "back" function
            # instead of using a potential back-link; what happen if the latest 
            # page we are not exploring changes the in-server state?
            self.logger.info("not exploring additional aggregatable pages")
            prevpage, prevlink, prevst = page.histories[-1][-1]
            prevpage.links[prevlink].ignore = True
            return None
        return page.getUnvisitedLink(state)

    def findNextStep(self, page, state):
        nextAction = None
        while nextAction == None:
            nextAction = self.processPage(page, state)
            if nextAction == None:
                path = None
                if self.pagemap.unvisited:
                    self.pagemap.unvisited.logInfo()
                    if page.aggregation != PageMapper.AGGREG_PENDING:
                        path = self.findPathToUnvisited(page, state)
                else:
                    self.logger.info("we are done")
                    # we are done
                    return (None, page, state)
                if path:
                    self.logger.debug("found path: \n%s", '\n'.join(
                        [str(i) for i in path]))
                    page,state = self.navigatePath(page, path)
                    nextAction = self.processPage(page, state)
                else:
                    self.logger.info("no path found, stepping back")
                    prevcrpage = self.cr.back()
                    prevcrpage = self.pagemap[prevcrpage]
                    prevpage, prevlink, prevst = self.history.pop()
                    assert prevcrpage == prevpage
                    assert prevpage == page.histories[-1][-1][0], \
                            "%s != %s / %s" % (prevpage,
                                    page.histories[-1][-1][0], page)
                    page.histories.pop()
                    page = prevpage
                    state = prevst
        self.logger.debug("next action %r %r(%d)", nextAction, page, state)
        return (nextAction, page, state)

    def doAction(self, page, action, state, preferred=None,
            preferredstate=None):
        if action[0] == Links.ANCHOR:
            self.logger.info("clicking %s in %s", action[1], page)
            newpage = self.cr.clickAnchor(action[1])
        elif action[0] == Links.FORM:
            try:
                formkeys = page.links[action].getFormKeys()
                self.logger.debug("form keys %r", formkeys)
                params = self.formfiller[formkeys]
            except KeyError:
                # we do not have parameters for the form
                params = {}
            newpage = self.cr.submitForm(action[1], params)
        else:
            assert False, "Unknown action %r" % action

        # use reference to the pre-existing page
        newpage = self.pagemap.get(newpage, preferred)
        if preferred and newpage == preferred and preferredstate:
            newstate = preferredstate
        elif newpage.histories and newpage.histories[0]:
            # get latest newpage state
            #print "H", page.histories[-1][-1]
            prevpage, prevlinkidx, prevst = page.histories[-1][-1]
            newstate = prevpage.links[prevlinkidx][prevst].transition
        else:
            # if new page, propagate state
            newstate = state

        # update engine and new page history
        self.history.append((page, action, state))
        newpage.histories.append(self.history[:])

        # update set of unvisited links
        if newpage.aggregation != PageMapper.AGGREG_PENDING:
            # if some pages are aggregatable, do not keep visiting new
            # aggregatable pages
            self.pagemap.unvisited.updateFromPage(newpage, newstate)

        #print "P", newpage, state
        return newpage, newstate

    def updateOutLinks(self, page, action, newpage, state,
            transition=None):
        page.linkto(action, newpage, state, transition)
        try:
            # XXX should we keep also state in unvisited set?
            self.pagemap.unvisited.remove(page, action, state)
        except KeyError:
            # might have been alredy removed by a page merge
            pass

    def main(self, urls):
        self.cr = Crawler()
        self.pagemap = PageMapper()
        self.history = []
        state = self.maxstate
        for url in urls:
            page = self.cr.open(url)
            page = self.pagemap[page]
            if len(page.histories) == 0:
                page.histories = [[]]
            nextAction = self.processPage(page, state)
            while nextAction != None:
                assert type(state) == int
                try:
                    try:
                        self.validateHistory(page)
                    except IndexError:
                        # will happen on first itration when there is not
                        # history
                        pass

                    newpage, newstate = self.doAction(page, nextAction, state)
                    self.updateOutLinks(page, nextAction, newpage, state,
                            newstate)

                    self.validateHistory(newpage)

                    self.pagemap.checkAggregatable(page, state)
                    page,state = newpage,newstate
                except CrawlerActionFailure:
                    page.links[nextAction].ignore = True
                    self.pagemap.unvisited.remove(page, nextAction, state)

                nextAction, page, state = self.findNextStep(page, state)

    def writeDot(self):
        self.logger.info("creating DOT graph")
        dot = pydot.Dot()
        nodes = {}
        for p in self.pagemap:
            if p.aggregation != PageMapper.AGGREG_PENDING:
                url = urlparse.urlparse(p.url)
                name = url.path
                if url.query:
                    name += '?' + url.query
                name += '\\n%x ' % id(p)
                allstates = []
                for l in p.links:
                    allstates.extend(l.iterkeys())
                name += str(list(set(allstates)))
                node = pydot.Node(name)
                if p.aggregation == PageMapper.AGGREGATED:
                    node.set_color('green')
                elif p.aggregation == PageMapper.AGGREG_IMPOSS:
                    node.set_color('red')
                nodes[p] = node

        self.logger.debug("%d DOT nodes", len(nodes))

        for n in nodes.itervalues():
            dot.add_node(n)

        with open("nodelist.txt", 'w') as f:
            for i in sorted(j.get_name() for j in nodes.itervalues()):
                f.write(i)
                f.write('\n')


        nulltargets = 0

        for n,dn in nodes.iteritems():
            src = dn
            links = defaultdict(lambda: [])
            for dst in n.links:
                if not dst.targets:
                    nulltargets += 1
                else:
                    for s,t in dst.iteritems():
                        if t.target.aggregation != PageMapper.AGGREG_PENDING:
                            if dst.__class__.__name__ == 'Form':
                                if dst.method == 'post':
                                    color = 'purple'
                                else:
                                    color = 'blue'
                            else:
                                color = 'black'
                            if not t.nvisits:
                                style = 'dotted'
                            else:
                                style = 'solid'
                            links[(t.target, color, style)].append(
                                    (s, t.transition))
            for k,states in links.iteritems():
                try:
                    target, color, style = k
                    edge = pydot.Edge(src, nodes[target])
                    edge.set_color(color)
                    edge.set_style(style)
                    edge.set_label(''.join('%d>%d' % i for i in set(states)))
                    dot.add_edge(edge)
                except KeyError:
                    self.logger.error("unable to find target node")

        if nulltargets:
            self.logger.warn("found null %d targets", nulltargets)

        dot.write_ps('graph.ps')
        #dot.write_pdf('graph.pdf')
        with open('graph.dot', 'w') as f:
            f.write(dot.to_string())
        self.logger.debug("DOT graph written")

if __name__ == "__main__":
    import sys
    logging.basicConfig(level=logging.DEBUG)
    ff = FormFiller()
    login = {'username': 'ludo', 'password': 'duuwhe782osjs'}
    ff.add(login)
    login = {'user': 'ludo', 'pass': 'ludo'}
    ff.add(login)
    login = {'userId': 'temp01', 'password': 'Temp@67A%', 'newURL': "", "datasource": "myyardi", 'form_submit': ""}
    ff.add(login)
    e = Engine(ff)
    try:
        #htmlunit.System.setProperty("org.apache.commons.logging.simplelog.defaultlog", "trace")
        e.main(sys.argv[1:])
    except:
        raise
    finally:
        try:
            e.writeDot()
        except:
            import traceback
            traceback.print_exc()








