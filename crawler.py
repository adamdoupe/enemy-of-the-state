import hashlib

class Page:

    def __init__(self, url, links=frozenset(), cookies=frozenset(), forms=frozenset()):
        self.url = url
        self.links = links
        self.cookies = cookies
        self.forms = forms
        self.str = str(self.url) + str(self.links) + str(self.cookies) + str(self.forms)
        self.hashval = hashlib.md5(self.str)

    def hash(self):
        return self.hashval

    def __cmp__(self, rhs):
        self.hashval == rhs.hashval


import htmlunit

htmlunit.initVM(htmlunit.CLASSPATH)

class Crawler:

    def __init__(self):
        self.webclient = htmlunit.WebClient()

    def getPage(self, url):
        htmlpage = htmlunit.HtmlPage.cast_(self.webclient.getPage(url))
        htmlpage = htmlunit.HtmlPageWrapper(htmlpage)
        anchors = [i.getHrefAttribute() for i in  htmlpage.getAnchors()]
        forms = [i.getActionAttribute()  for i in htmlpage.getForms()]

        return Page(url=url, links=anchors, forms=forms)


if __name__ == "__main__":
    cr = Crawler()
    print cr.getPage("http://www.cs.ucsb.edu/~cavedon/")



