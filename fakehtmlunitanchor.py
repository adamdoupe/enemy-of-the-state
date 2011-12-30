import htmlunit

class FakeHtmlUnitAnchor(object):

    def __init__(self, href, webclient):
        self.href = href
        self.webclient = webclient

    class FakeAttributesMap(object):
        def __init__(self):
            pass

        def keySet(self):
            return ['href']

    def getAttributesMap(self):
        return FakeHtmlUnitAnchor.FakeAttributesMap()

    def getHrefAttribute(self):
        return self.href

    def click(self):
        return htmlunit.HtmlPage.cast_(self.webclient.getPage(self.href))

    def getCanonicalXPath(self):
        return "/html/body/added/to/end/by/adam/should/not/exist"
