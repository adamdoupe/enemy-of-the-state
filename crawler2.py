#!/usr/bin/env python

import logging

import htmlunit

htmlunit.initVM(':'.join([htmlunit.CLASSPATH, '.']))


# running htmlunit via JCC will override the signal halders,
# and we cannot catch ctrl-C, so let's use SIGUSR1

import signal

def signalhandler(signum, frame):
    raise KeyboardInterrupt

signal.signal(signal.SIGUSR1, signalhandler)
signal.signal(signal.SIGINT, signalhandler)

class Request(object):

    def __init__(self, webrequest):
        self.webrequest = webrequest

    @property
    def method(self):
        return self.webrequest.getHttpMethod()

    @property
    def path(self):
        return self.webrequest.getUrl()

    @property
    def params(self):
        raise NotImplemented

    @property
    def cookies(self):
        raise NotImplemented

    @property
    def headers(self):
        raise NotImplemented

    def __str__(self):
        return "Request(%s %s)" % (self.method, self.path)


class Response(object):

    def __init__(self, webresponse, page):
        self.webresponse = webresponse
        self._page = page

    @property
    def code(self):
        return self.webresponse.getStatusCode()

    @property
    def message(self):
        return self.webresponse.getStatusMessage()

    @property
    def content(self):
        raise NotImplemented

    @property
    def cookies(self):
        raise NotImplemented

    @property
    def page(self):
        return _page

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


class Page(object):

    def __init__(self, page, reqresp):
        self.page = page
        self.reqresp = reqresp

    @property
    def anchors(self):
        raise NotImplemented

    @property
    def forms(self):
        raise NotImplemented

class DeferringRefreshHandler(htmlunit.RefreshHandler):

    def __init__(self, refresh_urls=[]):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.refresh_urls = refresh_urls

    def handleRefresh(self, page, url, seconds):
        self.logger.debug("%s refrsh to %s in %d s", page, url, seconds)
        self.refresh_urls.append(url)


class Crawler(object):


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
        self.reqresp = None

    def open(self, url):
        del self.refresh_urls[:]
        #webrequest = htmlunit.WebRequest(htmlunit.URL(url))
        htmlpage = htmlunit.HtmlPage.cast_(self.webclient.getPage(url))
        # TODO: handle HTTP redirects, they will throw an exception
        return self.newPage(htmlpage)

    def newPage(self, htmlpage):
        self.updateInternalData(htmlpage)
        self.logger.info("%s", self.reqresp)
        return self.reqresp

    def updateInternalData(self, htmlpage):
        self.reqresp = RequestResponse(htmlpage, self.reqresp)


def main(urls):
    cr = Crawler()

    for url in urls:
        page = cr.open(url)


if __name__ == "__main__":
    import sys
    logging.basicConfig(level=logging.DEBUG)
    main(sys.argv[1:])


# vim:sw=4:et:
