#!/usr/bin/env python

import logging
import re
import random

import htmlunit

htmlunit.initVM(':'.join([htmlunit.CLASSPATH, '.']))


# running htmlunit via JCC will override the signal halders,
# and we cannot catch ctrl-C, so let's use SIGUSR1

import signal

def signalhandler(signum, frame):
    raise KeyboardInterrupt

signal.signal(signal.SIGUSR1, signalhandler)
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

    def __str__(self):
        return "Request(%s %s)" % (self.method, self.path)


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

    @lazyproperty
    def anchors(self):
        return [Anchor(i, self.reqresp) for i in self.internal.getAnchors()]

    @lazyproperty
    def forms(self):
        return [Form(i, self.reqresp) for i in self.internal.getForms()]


class AbstractLink(object):

    def __init__(self, abspage):
        elf.abspage = abspage


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


class Buckets(dict):

    def __missing__(self, k):
        v = []
        self[k] = v
        return v

    def add(self, obj, h):
        v = self[h]
        v.append(o)
        return v


class PageClusteres(object):

    def simplehash(self, reqresp):
        page = reqresp.resp.page
        hashedval = reqresp.request.url() + '|' + repr(page.anchors) + "|" + repr(page.forms)
        return hash(hashedval)

    def __init__(self, reqresps):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.trace("clustering %d pages", len(reqresps))
        buckets = Buckets()
        for i in reqresps:
            buckets.add(i, self.simplehash(i))
        selkf.buckets = buckets

    def getAbstractPages(self):
        self.logger.trace("generating abstract pages")
        abspages = [AbstractPage(i) for i in self.buckets]
        return abspages


class AppGraphGenerator(object):

    def __init__(self, abspages):
        self.abspages = abspages



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
        if self.lastreqresp.prev is None:
            raise Crawler.EmptyHistory()
        self.currreqresp = self.lastreqresp.prev
        return self.currreqresp


class Engine(object):

    BACK, ANCHOR = range(2)

    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)

    def getUnvisitedLink(self, reqresp):
        anchors = reqresp.response.page.anchors
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
