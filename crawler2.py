#!/usr/bin/env python

import logging
import re
import random

import htmlunit

htmlunit.initVM(':'.join([htmlunit.CLASSPATH, '.']))


# running htmlunit via JCC will override the signal halders

import signal

def signalhandler(signum, frame):
    raise KeyboardInterrupt

#signal.signal(signal.SIGUSR1, signalhandler)
signal.signal(signal.SIGINT, signalhandler)

class lazyproperty(object):
    """ from http://blog.pythonisito.com/2008/08/lazy-descriptors.html """

    def __init__(self, func):
        self._func = func
        self.__name__ = func.__name__
        self.__doc__ = func.__doc__

    def __get__(self, obj, klass=None):
        if obj is None: return None
        result = obj.__dict__[self.__name__] = self._func(obj)
        return result


class Request(object):

    def __init__(self, webrequest):
        self.webrequest = webrequest

    @lazyproperty
    def method(self):
        return self.webrequest.getHttpMethod()

    @lazyproperty
    def path(self):
        url = self.webrequest.getUrl()
        query = url.getQuery()
        path = self.webrequest.getUrl().getPath()
        if query:
            path += "?" + query
        return path

    @lazyproperty
    def params(self):
        raise NotImplemented

    @lazyproperty
    def cookies(self):
        raise NotImplemented

    @lazyproperty
    def headers(self):
        raise NotImplemented

    @lazyproperty
    def _str(self):
        return "Request(%s %s)" % (self.method, self.path)

    def __str__(self):
        return self._str

    def __repr__(self):
        return str(self)


class Response(object):

    def __init__(self, webresponse, page):
        self.webresponse = webresponse
        self.page = page

    @lazyproperty
    def code(self):
        return self.webresponse.getStatusCode()

    @lazyproperty
    def message(self):
        return self.webresponse.getStatusMessage()

    @lazyproperty
    def content(self):
        raise NotImplemented

    @lazyproperty
    def cookies(self):
        raise NotImplemented

    def __str__(self):
        return "Response(%d %s)" % (self.code, self.message)


class RequestResponse(object):

    def __init__(self, page, prev=None, next=None):
        webresponse = page.getWebResponse()
        self.response = Response(webresponse, Page(page, self))
        self.request = Request(webresponse.getWebRequest())
        self.prev = prev
        self.next = next

    def __str__(self):
        return "%s -> %s" % (self.request, self.response)


class Link(object):

    #xpathsimplifier = re.compile(r"\[[^\]*]")

    def __init__(self, internal, reqresp):
        self.internal = internal
        self.reqresp = reqresp
        self.to = []

    @lazyproperty
    def dompath(self):
        #return Link.xpathsimplifier.sub("", self.internal.getCanonicalXPath())
        return self.internal.getCanonicalXPath()


class Anchor(Link):

    @lazyproperty
    def href(self):
        return self.internal.getHrefAttribute()

    def click(self):
        return self.internal.click()

    def __str__(self):
        return "Anchor(%s, %s)" % (self.href, self.dompath)


class Form(Link):
    pass


class Page(object):

    def __init__(self, internal, reqresp):
        self.internal = internal
        self.reqresp = reqresp
        self.abspage = None

    @lazyproperty
    def anchors(self):
        return [Anchor(i, self.reqresp) for i in self.internal.getAnchors()]

    @lazyproperty
    def forms(self):
        return [Form(i, self.reqresp) for i in self.internal.getForms()]


class AbstractLink(object):

    def __init__(self, abspage):
        elf.abspage = abspage
        # map from state to AbstractRequest
        self.targets = {}


class AbstractAnchor(AbstractLink):
    pass

class AbstractForm(AbstractLink):
    pass

class AbstractPage(object):

    def __init__(self, reqresps):
        self.reqresps = reqresps
        # TODO: number of links might not be the same in some more complex clustering
        self.absanchors = [AbsstractAnchor(i) for i in zip(rr.page.anchors for rr in reqresps)]
        self.absforms = [AbsstractForm(i) for i in zip(rr.page.forms for rr in reqresps)]


class AbstractRequest(object):

    def __init__(self, abspage):
        # map from state to AbstractPage
        self.targets = {}


class Target(object):
    def __init__(self, target, transition, nvisits=1):
        self.target = target
        self.transition = transition
        self.nvisits = nvisits

    def __str__(self):
        return "Target(%r, transition=%d, nvisits=%d)" % \
                (self.target, self.transition, self.nvisits)


class Buckets(dict):

    def __init__(self, h=hash):
        self.h = h

    def __missing__(self, k):
        v = []
        self[k] = v
        return v

    def add(self, obj, h=None):
        if h is None:
            h = self.h
        v = self[h(obj)]
        v.append(o)
        return v


class AbstractMap(dict):

    def __init__(self, absobj, h=hash):
        self.h = h
        self.absobj = absobj

    def __missing__(self, k):
        v = self.absobj(l)
        self[self.h(k)] = v
        return v

    def getAbstract(obj):
        return self[self.h(obk)]



class PageClusterer(object):

    def simplehash(self, reqresp):
        page = reqresp.resp.page
        hashedval = reqresp.request.url() + '|' + repr(page.anchors) + "|" + repr(page.forms)
        return hash(hashedval)

    def __init__(self, reqresps):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.debug("clustering %d pages", len(reqresps))
        buckets = Buckets(self.simplehash)
        for i in reqresps:
            buckets.add(i)
        self.logger.debug("generating abstract pages")
        abspages = [AbstractPage(i) for i in buckets]
        for ap in abspages:
            for rr in ap.reqresps:
                rr.response.page.abspage = ap
        self.abspages = abspages


    def getAbstractPages(self):
        return abspages

class AppGraphGenerator(object):

    def __init__(self, abspages, reqrespshead):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.abspages = abspages
        self.reqrespshead = reqrespshead

    def generateAppGraph(self):
        self.logger.debug("generating application graph")

        # make sure we are at the beginning
        assert reqrespshead.prev is None
        curr = reqrespshead
        laststate = 0

        # map requests with same "signature" to the same AbstractRequest object
        reqmap = AbstractMap(lambda x: repr(x), AbstractRequest)
        currabsreq = reqmap.getAbstract(curr.request)

        # go through the while navigation path and link together AbstractRequests and AbstractPages
        # for now, every request will generate a new state, post processing will happen later
        while curr:
            currpage = curr.response.page
            currabspage = currpage.abspage
            assert not laststate in currabsreq.anchors
            currabsreq.targets[laststate] = Target(currabspage, laststate+1)
            laststate += 1

            if curr.next:
                # find which link goes to the next request in the history
                chosenlink = ((i, l) for i, l in enumerate(currpage.links) if curr.next in l.to).next()
                nextabsreq = reqmap.getAbstract(curr.next.request)
                assert not laststate in currabspage.absanchors.targets
                currabspage.absanchors.targets[laststate] = Target(nextabsreq, laststate)


            curr = curr.next
            currabsreq = nextabsreq









class DeferringRefreshHandler(htmlunit.RefreshHandler):

    def __init__(self, refresh_urls=[]):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.refresh_urls = refresh_urls

    def handleRefresh(self, page, url, seconds):
        self.logger.debug("%s refrsh to %s in %d s", page, url, seconds)
        self.refresh_urls.append(url)


class Crawler(object):

    class EmptyHistory(Exception):
        pass

    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        #self.webclient = htmlunit.WebClient(htmlunit.BrowserVersion.INTERNET_EXPLORER_6)
        #self.webclient = htmlunit.WebClient(htmlunit.BrowserVersion.FIREFOX_3)
        #bw = htmlunit.BrowserVersion(
        #    htmlunit.BrowserVersion.NETSCAPE, "5.0 (Windows; en-US)",
        #            "Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.9.0.1) Gecko/2008070208 Firefox/3.0.1 Safari", 3.0)
            #        "Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.9.0.1) Gecko/2008070208 Firefox/3.0.1 Safari", "1.2", 3.0, "FF3", None)

        #self.webclient = htmlunit.WebClient(bw)
        self.webclient = htmlunit.WebClient()
        self.webclient.setThrowExceptionOnScriptError(True);
        self.webclient.setUseInsecureSSL(True)
        self.webclient.setRedirectEnabled(False)
        self.refresh_urls = []
        # XXX the refresh handler does not tget called, why?
        self.webclient.setRefreshHandler(DeferringRefreshHandler(self.refresh_urls))
        # last generated RequestResponse object
        self.lastreqresp = None
        # current RequestResponse object (will differ from lastreqresp when back() is invoked)
        self.currreqresp = None

    def open(self, url):
        del self.refresh_urls[:]
        #webrequest = htmlunit.WebRequest(htmlunit.URL(url))
        htmlpage = htmlunit.HtmlPage.cast_(self.webclient.getPage(url))
        # TODO: handle HTTP redirects, they will throw an exception
        return self.newPage(htmlpage)

    def newPage(self, htmlpage):
        self.updateInternalData(htmlpage)
        self.logger.info("%s", self.currreqresp)
        return self.currreqresp

    def updateInternalData(self, htmlpage):
        self.lastreqresp = RequestResponse(htmlpage, self.lastreqresp)
        self.currreqresp = self.lastreqresp

    def click(self, anchor):
        self.logger.debug("clicking on %s", anchor)
        assert anchor.internal.getPage() == self.currreqresp.response.page.internal, \
                "Inconsistency error %s != %s" % (anchor.internal.getPage(), self.currreqresp.response.page.internal)
        htmlpage = htmlunit.HtmlPage.cast_(anchor.internal.click())
        # TODO: handle HTTP redirects, they will throw an exception
        reqresp = self.newPage(htmlpage)
        anchor.to.append(reqresp)
        assert reqresp.request.path[-len(anchor.href):] == anchor.href, \
                "Unhandled redirect %s !sub %s" % (anchor.href, reqresp.request.path)
        return reqresp

    def back(self):
        self.logger.debug("stepping back")
        # htmlunit has not "back" functrion
        if self.currreqresp.prev is None:
            raise Crawler.EmptyHistory()
        self.currreqresp = self.currreqresp.prev
        return self.currreqresp


class Engine(object):

    BACK, ANCHOR = range(2)

    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)

    def getUnvisitedLink(self, reqresp):
        anchors = [i for i in reqresp.response.page.anchors if not i.to]
        if len(anchors) > 0:
            anchor = random.choice(anchors)
        else:
            anchor = None
        return anchor

    def getNextAction(self, reqresp):
        unvisited = self.getUnvisitedLink(reqresp)
        if unvisited is not None:
            return (Engine.ANCHOR, unvisited)
        return (Engine.BACK, )

    def main(self, urls):
        cr = Crawler()

        for cnt, url in enumerate(urls):
            self.logger.info("starting with URL %d/%d %s", cnt+1, len(urls), url)
            reqresp = cr.open(url)
            nextAction = self.getNextAction(reqresp)
            while nextAction:
                if nextAction[0] == Engine.ANCHOR:
                    reqresp = cr.click(nextAction[1])
                if nextAction[0] == Engine.BACK:
                    reqresp = cr.back()
                nextAction = self.getNextAction(reqresp)


if __name__ == "__main__":
    import sys
    logging.basicConfig(level=logging.DEBUG)
    Engine().main(sys.argv[1:])


# vim:sw=4:et:
