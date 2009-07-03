#!/usr/bin/env python

from collections import defaultdict
import hashlib
import struct

class WebsiteGraph(defaultdict):
    """ dictionary from Page to set of Pages """
    
    def __init__(self):
        defaultdict.__init__(self, set)

class PageSet(set):
    """ set of visited pages (unordered) """

    def __init__(self):
        set.__init__(self)




class Page:

    def __init__(self, url, links=defaultdict(bool), cookies=frozenset(), forms=frozenset()):
        self.url = url
        self.links = links
        self.cookies = cookies
        self.forms = forms
        self.str = str(self.url) + str(self.links.keys()) + str(self.cookies) + str(self.forms)
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

    def getPage(self, url):
        htmlpage = htmlunit.HtmlPage.cast_(self.webclient.getPage(url))
        return self.createPage(htmlpage)

    def clickAnchor(self, anchor):
        htmlpage = anchor.click()
        return self.createPage(htmlpage)


    def createPage(self, htmlpage):
        htmlpagewrapped = htmlunit.HtmlPageWrapper(htmlpage)
        anchors = [htmlunit.HtmlAnchor.cast_(i).getHrefAttribute() for i in  htmlpagewrapped.getAnchors()]
        #forms = [i.getActionAttribute()  for i in htmlpage.getForms()]
        url = htmlpage.getWebResponse().getRequestUrl().toString()
        print url
        anchorsdict = defaultdict(bool)
        for a in anchors:
            anchorsdict[a] = False

        return (Page(url=url, links=anchorsdict), htmlpagewrapped) #, forms=forms)


if __name__ == "__main__":
    cr = Crawler()
    pageset = PageSet()
    websitegraph = WebsiteGraph()
    rootpage, htmlpagewrapped = cr.getPage("http://www.cs.ucsb.edu/~cavedon/")
    htmlpage = htmlpagewrapped.getHtmlPage()
    print "rootpage", rootpage
    pageset.add(rootpage)
    anchors = [htmlunit.HtmlAnchor.cast_(i) for i in  htmlpagewrapped.getAnchors()]
    nextpage, nexthtmlpagewrapped = cr.clickAnchor(anchors[0])
    rootpage.links[anchors[0].getHrefAttribute()] = True
    websitegraph[rootpage].add(nextpage)

    print "pageset", pageset
    print "websitegraph", websitegraph
    print "rootpage", rootpage
    print "nextpage", nextpage








