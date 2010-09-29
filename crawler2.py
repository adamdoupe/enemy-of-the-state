#!/usr/bin/env python

import logging
import urlparse
import re
import heapq
import itertools

import pydot

import output

import htmlunit

from collections import defaultdict, deque, namedtuple

htmlunit.initVM(':'.join([htmlunit.CLASSPATH, '.']))

# running htmlunit via JCC will override the signal halders

import signal

wanttoexit = False

def gracefulexit():
    global wanttoexit
    wanttoexit = True

def signalhandler(signum, frame):
    if wanttoexit:
        raise KeyboardInterrupt
    else:
        gracefulexit()

#signal.signal(signal.SIGUSR1, signalhandler)
signal.signal(signal.SIGINT, signalhandler)

def median(l):
    s = sorted(l)
    ln = len(s)
    if ln % 2 == 0:
        return float(s[ln/2]+s[ln/2-1])/2
    else:
        return float(s[ln/2])

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

class Constants(object):

    def __init__(self, *args):
        for a in args:
            setattr(self, a, a)

class RecursiveDict(defaultdict):
    def __init__(self, nleavesfunc=lambda x: 1):
        self.default_factory = RecursiveDict
        # when counting leaves, apply this function to non RecursiveDict objects
        self.nleavesfunc = nleavesfunc

    @lazyproperty
    def nleaves(self):
        """ number of objects in the tis subtree of the nested dictionay
        NOTE: this is a lazy property, will get stale if tree is updated!
        """
        return sum(i.nleaves if isinstance(i, self.default_factory) else self.nleavesfunc(i)
                for i in self.itervalues())

    def getpath(self, path):
        i = self
        for p in path:
            i = i[p]
        return i

    def setpath(self, path, value):
        i = self
        for p in path[:-1]:
            i = i[p]
        i[path[-1]] = value

    def applypath(self, path, func):
        i = self
        for p in path[:-1]:
            i = i[p]
        i[path[-1]] = func(i[path[-1]])

    def setapplypath(self, path, value, func):
        i = self
        for p in path[:-1]:
            i = i[p]
        if path[-1] in i:
            i[path[-1]] = func(i[path[-1]])
        else:
            i[path[-1]] = value

    def iterlevels(self):
        if self:
            queue = deque([(self,)])
            while queue:
                l = queue.pop()
                levelkeys = []
                children = []
                for c in l:
                    if isinstance(c, self.default_factory):
                        levelkeys.extend(c.iterkeys())
                        children.extend(c.itervalues())
                    else:
                        levelkeys.append(c)
                if children:
                    queue.append(children)
                #print "LK", len(queue), levelkeys, queue
                yield levelkeys

    def iterleaves(self):
        if self:
            for c in self.itervalues():
                if isinstance(c, self.default_factory):
                    for i in c.iterleaves():
                        yield i
                else:
                    yield c

    def __str__(self, level=0):
        out = ""
        for k, v in self.iteritems():
            out += "\n%s%s:"  % ("\t"*level, k)
            if isinstance(v, RecursiveDict):
                out += "%s" % v.__str__(level+1)
            else:
                out += "%s" % v
        return out


class Request(object):

    def __init__(self, webrequest):
        self.webrequest = webrequest
        self.reqresp = None
        self.absrequest = None

    @lazyproperty
    def method(self):
        return self.webrequest.getHttpMethod()

    @lazyproperty
    def isPOST(self):
        return self.method == htmlunit.HttpMethod.POST

    @lazyproperty
    def path(self):
        return self.webrequest.getUrl().getPath()

    @lazyproperty
    def query(self):
        return self.webrequest.getUrl().getQuery()

    @lazyproperty
    def fullpath(self):
        fullpath = self.path
        if self.query:
            fullpath += "?" + self.query
        return fullpath

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
        return "Request(%s %s)" % (self.method, self.fullpath)

    @lazyproperty
    def shortstr(self):
        return "%s %s" % (self.method, self.fullpath)

    @lazyproperty
    def urlvector(self):
        return urlvector(self)

    def __str__(self):
        return self._str

    def __repr__(self):
        return str(self)


class Response(object):

    InstanceCounter = 1

    def __init__(self, webresponse, page):
        self.webresponse = webresponse
        self.page = page
        self.instance = Response.InstanceCounter
        Response.InstanceCounter += 1

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

    def __cmp__(self, o):
        return cmp(self.InstanceCounter, o.InstanceCounter)


class RequestResponse(object):

    def __init__(self, request, response):
        request.reqresp = self
        self.request = request
        self.response = response
        self.prev = None
        self.next = None
        # how many pages we went back before performing this new request
        self.backto = None

    def __iter__(self):
        curr = self
        while curr:
            yield curr
            curr = curr.next

    def __str__(self):
        return "%s -> %s" % (self.request, self.response)

    def __repr__(self):
        return str(self)

class Link(object):

    xpathsimplifier = re.compile(r"\[[^\]*]\]")

    def __init__(self, internal, reqresp):
        self.internal = internal
        self.reqresp = reqresp
        self.to = []
        self.skip = False

    @lazyproperty
    def dompath(self):
        return Link.xpathsimplifier.sub("", self.internal.getCanonicalXPath())

    @lazyproperty
    def _str(self):
        raise NotImplementedError

    def __str__(self):
        return self._str

    def __repr__(self):
        return str(self)



class Anchor(Link):

    @lazyproperty
    def href(self):
        return self.internal.getHrefAttribute()

    @lazyproperty
    def hrefurl(self):
        return urlparse.urlparse(self.href)

    def click(self):
        return self.internal.click()

    @lazyproperty
    def _str(self):
        return "Anchor(%s, %s)" % (self.href, self.dompath)

    @lazyproperty
    def linkvector(self):
        return urlvector(self.hrefurl)


class Form(Link):
    GET, POST = ("GET", "POST")

    @lazyproperty
    def method(self):
        methodattr = self.internal.getMethodAttribute().upper()
        assert methodattr in ("GET", "POST")
        return methodattr

    @lazyproperty
    def action(self):
        return self.internal.getActionAttribute()

    @lazyproperty
    def actionurl(self):
        return urlparse.urlparse(self.action)

    @lazyproperty
    def _str(self):
        return "Form(%s %s)" % (self.method, self.action)

    @lazyproperty
    def linkvector(self):
        return formvector(self.method, self.actionurl, self.inputs, self.hiddens)

    @lazyproperty
    def keys(self):
        return self.inputs + self.textareas + self.selects

    @lazyproperty
    def inputs(self):
        return [e.getAttribute('name')
                for e in (htmlunit.HtmlElement.cast_(i)
                    for i in self.internal.getHtmlElementsByTagName('input'))
                if e.getAttribute('type').lower() != "hidden"]

    @lazyproperty
    def hiddens(self):
        return [e.getAttribute('name')
                for e in (htmlunit.HtmlElement.cast_(i)
                    for i in self.internal.getHtmlElementsByTagName('input'))
                if e.getAttribute('type').lower() == "hidden"]

    @lazyproperty
    def textareas(self):
        # TODO
        return []

    @lazyproperty
    def selects(self):
        # TODO
        return []


class Redirect(Link):

    @property
    def location(self):
        return self.internal

    def __str__(self):
        return "Redirect(%s)" % (self.location)

    @property
    def linkvector(self):
        return [self.location]

    @lazyproperty
    def dompath(self):
        return None


class StateSet(frozenset):

    @lazyproperty
    def _str(self):
        return "[%s]" % ', '.join(str(i) for i in sorted(self))

    def __str__(self):
        return self._str

    def __repr__(self):
        return str(self)


def validanchor(a):
    href = a.getHrefAttribute()
    return href.find('://') == -1 and href.strip()[:7] != "mailto:"

class Page(object):

    def __init__(self, internal, redirect=False, error=False):
        self.internal = internal
        self.reqresp = None
        self.abspage = None
        self.redirect = redirect
        self.error = error
        assert not self.redirect or len(self.redirects) == 1, self.redirects

    @lazyproperty
    def anchors(self):
        return [Anchor(i, self.reqresp) for i in self.internal.getAnchors() if validanchor(i)] if not self.redirect and not self.error else []

    @lazyproperty
    def forms(self):
        return [Form(i, self.reqresp) for i in self.internal.getForms()] if not self.redirect and not self.error else []

    @lazyproperty
    def redirects(self):
        return [Redirect(self.internal.getResponseHeaderValue("Location"), self.reqresp)] if self.redirect else []

    @lazyproperty
    def linkstree(self):
        return linkstree(self)

    @lazyproperty
    def linksvector(self):
        return linksvector(self)

    @lazyproperty
    def links(self):
        return Links(self.anchors, self.forms, self.redirects)

    def getNewRequest(self, link):
        if isinstance(link, AbstractAnchor):
            if len(link.hrefs) == 1:
                href = iter(link.hrefs).next()
                if not href.strip().lower().startswith("javascript:"):
                    url = self.internal.getFullyQualifiedUrl(href)
                    return htmlunit.WebRequest(url)
        return None


class AbstractLink(object):

    def __init__(self, links):
        # map from state to AbstractRequest
        self.targets = {}
        self.skip = any(i.skip for i in links)

    @lazyproperty
    def _str(self):
        raise NotImplementedError

    def __str__(self):
        return self._str

    def __repr__(self):
        return str(self)

class AbstractAnchor(AbstractLink):

    def __init__(self, anchors):
        AbstractLink.__init__(self, anchors)
        self.hrefs = set(i.href for i in anchors)

    @property
    def _str(self):
        return "AbstractAnchor(%s, targets=%s)" % (self.hrefs, self.targets)

    def equals(self, a):
        return self.hrefs == a.hrefs

    @lazyproperty
    def hasquery(self):
        return any(i.find('?') != -1 for i in self.hrefs)


class AbstractForm(AbstractLink):

    def __init__(self, forms):
        AbstractLink.__init__(self, forms)
        self.methods = set(i.method for i in forms)
        self.actions = set(i.action for i in forms)

    @property
    def _str(self):
        return "AbstractForm(targets=%s)" % (self.targets)

    def equals(self, f):
        return (self.methods, self.actions) == (f.methods, f.actions)

    @lazyproperty
    def isPOST(self):
        return Form.POST in self.methods


class AbstractRedirect(AbstractLink):

    def __init__(self, redirects):
        AbstractLink.__init__(self, redirects)
        self.locations = set(i.location for i in redirects)

    @property
    def _str(self):
        return "AbstractRedirect(%s, targets=%s)" % (self.locations, self.targets)

    def equals(self, a):
        return self.locations == a.locations

    @lazyproperty
    def hasquery(self):
        return any(i.find('?') != -1 for i in self.locations)


class Links(object):
    Type = Constants("ANCHOR", "FORM", "REDIRECT")

    def __init__(self, anchors=[], forms=[], redirects=[]):
        self.anchors = anchors
        self.forms = forms
        self.redirects = redirects

    def nAnchors(self):
        return len(self.anchors)

    def nForms(self):
        return len(self.forms)

    def nRedirects(self):
        return len(self.redirects)

    def __getitem__(self, idx):
        if idx[0] == Links.Type.ANCHOR:
            return self.anchors[idx[1]]
        elif idx[0] == Links.Type.FORM:
            return self.forms[idx[1]]
        elif idx[0] == Links.Type.REDIRECT:
            return self.redirects[idx[1]]
        else:
            raise KeyError(idx)

    def iteritems(self):
        for i, v in enumerate(self.anchors):
            yield ((Links.Type.ANCHOR, i), v)
        for i, v in enumerate(self.forms):
            yield ((Links.Type.FORM, i), v)
        for i, v in enumerate(self.redirects):
            yield ((Links.Type.REDIRECT, i), v)

    def itervalues(self):
        for v in self.anchors:
            yield v
        for v in self.forms:
            yield v
        for v in self.redirects:
            yield v

    def __iter__(self):
        return self.itervalues()

    def getUnvisited(self, state):
        # unvisited if we never did the request for that state
        return [(i, l) for i, l in self.iteritems() if not l.skip \
                and (state not in l.targets
                    or not l.targets[state].target.targets)]

    def __len__(self):
        return self.nAnchors() + self.nForms() + self.nRedirects()

    def __nonzero__(self):
        return self.nAnchors() != 0 or self.nForms() != 0 or self.nRedirects() != 0

    def equals(self, l):
        return self.nAnchors() == l.nAnchors() and self.nForms() == l.nForms() and \
                self.nRedirects() == l.nRedirects() and \
                all(a.equals(b) for a, b in zip(self.anchors, l.anchors)) and \
                all(a.equals(b) for a, b in zip(self.forms, l.forms)) and \
                all(a.equals(b) for a, b in zip(self.redirects, l.redirects))

    def __str__(self):
        return self._str

    @lazyproperty
    def _str(self):
        return "Links(%s, %s, %s)" % (self.anchors, self.forms, self.redirects)


class AbstractPage(object):

    InstanceCounter = 0

    def __init__(self, reqresps):
        self.reqresps = reqresps
        # TODO: number of links might not be the same in some more complex clustering
        self.absanchors = [AbstractAnchor(i) for i in zip(*(rr.response.page.anchors for rr in reqresps))]
        self.absforms = [AbstractForm(i) for i in zip(*(rr.response.page.forms for rr in reqresps))]
        self.absredirects = [AbstractRedirect(i) for i in zip(*(rr.response.page.redirects for rr in reqresps))]
        self.abslinks = Links(self.absanchors, self.absforms, self.absredirects)
        self.statelinkmap = {}
        self.instance = AbstractPage.InstanceCounter
        AbstractPage.InstanceCounter += 1

    @lazyproperty
    def _str(self):
        return "AbstractPage(#%d, %s)" % (len(self.reqresps),
                set("%s %s" % (i.request.method, i.request.fullpath) for i in self.reqresps))

    def __str__(self):
        return self._str

    def __repr__(self):
        return str(self) + str(self.instance)

    def match(self, p):
        return self.abslinks.equals(p.abslinks)

    @lazyproperty
    def label(self):
        response = self.reqresps[0].response
        if response.page.error:
            return "%d %s" % (response.code, response.message)
        if response.page.redirect:
            redirects = ' '.join(i.location for i in response.page.redirects)
            return "%d %s\\n%s" % (response.code, response.message, redirects)
        else:
            return "Page(%d)" % self.instance

    def __cmp__(self, o):
        return cmp(self.instance, o.instance)


class AbstractRequest(object):

    InstanceCounter = 0

    def __init__(self, request):
        # map from state to AbstractPage
        self.targets = {}
        self.method = request.method
        self.path = request.path
        self.reqresps = []
        self.instance = AbstractRequest.InstanceCounter
        AbstractRequest.InstanceCounter += 1
        # counter of how often this page gave hints for detecting a state change
        self.statehints = 0

    def __str__(self):
        return "AbstractRequest(%s)%d" % (self.requestset, self.instance)

    def __repr__(self):
        return str(self)

    @property
    def requestset(self):
        return set(rr.request.shortstr for rr in self.reqresps)

    def __cmp__(self, o):
        return cmp(self.instance, o.instance)

    @lazyproperty
    def isPOST(self):
        return any(i.request.isPOST for i in self.reqresps)


class Target(object):
    def __init__(self, target, transition, nvisits=0):
        self.target = target
        self.transition = transition
        self.nvisits = nvisits

    def __str__(self):
        return "Target(%r, transition=%d, nvisits=%d)" % \
                (self.target, self.transition, self.nvisits)

    def __repr__(self):
        return str(self)


class CustomDict(dict):

    def __init__(self, items, missing, h=hash):
        dict.__init__(self)
        self.h = h
        self.missing = missing
        for (k, v) in items:
            self[k] = v

    def __getitem__(self, k):
        print "GET", k
        h = self.h(k)
        if dict.__contains__(self, h):
            return dict.__getitem__(self, self.h(k))
        else:
            v = self.missing(k)
            dict.__setitem__(self, h, v)
            return v

    def __setitem__(self, k, v):
        print "SET", k, v
        return dict.__setitem__(self, self.h(k), v)

    def __contains__(self, k):
        return dict.__contains__(self, self.h(k))

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
        v.append(obj)
        return v


class AbstractMap(dict):

    def __init__(self, absobj, h=hash):
        self.h = h
        self.absobj = absobj

    def getAbstract(self, obj):
        h = self.h(obj)
        if h in self:
            v = self[h]
        else:
            v = self.absobj(obj)
            self[h] = v
        #print output.yellow("%s (%s) -> %s" % (h, obj, v))
        return v

    def __iter__(self):
        return self.itervalues()

def urlvector(request):
    """ /path/to/path.html?p1=v1&p2=v2
        ->
        ['path', 'to', 'page.html', ('p1', 'p2'), ('v1', 'v2')]
    """
    # XXX "/path/to" and "path/to" will be trated the same!
    if request.path.strip() == ('/'):
        urltoks = ['/']
    else:
        urltoks = [i for i in request.path.split('/') if i]
    query = request.query
    if query:
        querytoks = request.query.split('&')
        keys, values = zip(*(i.split('=') for i in querytoks))
        urltoks.append(tuple(keys))
        urltoks.append(tuple(values))
    return tuple(urltoks)

def formvector(method, action, inputs, hiddens):
    urltoks = [method] + [i if i  else '/' for i in action.path.split('/')]
    query = action.query
    if query:
        querytoks = action.query.split('&')
        keys, values = zip(*(i.split('=') for i in querytoks))
        urltoks.append(tuple(keys))
        urltoks.append(tuple(values))
    if inputs:
        urltoks.append(tuple(inputs))
    if hiddens:
        # TODO hiddens values
        urltoks.append(tuple(hiddens))
    return tuple(urltoks)

def linkstree(page):
    # leaves in linkstree are counter of how many times that url occurred
    # therefore use that counter when compuing number of urls with "nleaves"
    linkstree = RecursiveDict(lambda x: x)
    if page.links:
        for l in page.links.itervalues():
            urlv = [l.dompath] if l.dompath else []
            urlv += list(l.linkvector)
            # set leaf to 1 or increment
            linkstree.setapplypath(urlv, 1, lambda x: x+1)
    else:
        # all pages with no links will end up in the same special bin
        linkstree.setapplypath(("<EMPTY>", ), 1, lambda x: x+1)
    return linkstree


def likstreedist(a, b):
    raise NotImplementedError

def linksvector(page):
    linksvector = tuple([tuple(i) for i in page.linkstree.iterlevels()])
    return linksvector


class Classfier(RecursiveDict):

    def __init__(self, featuresextractor):
        self.featuresextractor = featuresextractor
        # leaves should return the number of elements in the list for nleaves
        RecursiveDict.__init__(self, lambda x: len(x))

    def add(self, obj):
        featvect = self.featuresextractor(obj)
        # hack to use lambda function instead of def func(x); x.append(obj); return x
        self.setapplypath(featvect, [obj], lambda x: (x.append(obj), x)[1])

    def addall(self, it):
        for i in it:
            self.add(i)


class PageClusterer(object):

    def simplehash(self, reqresp):
        page = reqresp.response.page
        hashedval = reqresp.request.path + ', ' + repr(page.anchors) + ", " + repr(page.forms)
        return hashedval

    def __init__(self, reqresps):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.debug("clustering pages")

        self.levelclustering(reqresps)
        #self.simpleclustering(reqresps)

    def simpleclustering(self, reqresps):
        buckets = Buckets(self.simplehash)
        cnt = 0
        for i in reqresps:
            buckets.add(i)
            cnt += 1
        self.logger.debug("clustered %d pages into %d clusters", cnt, len(buckets))
        self.abspages = [AbstractPage(i) for i in buckets.itervalues()]
        self.linktorealpages()

    def linktorealpages(self):
        for ap in self.abspages:
            for rr in ap.reqresps:
                rr.response.page.abspage = ap
        self.logger.debug("%d abstract pages generated", len(self.abspages))

    def scanlevels(self, level, n=0):
        med = median((i.nleaves if hasattr(i, "nleaves") else len(i) for i in level.itervalues()))
        #self.logger.debug(output.green(' ' * n + "MED %f / %d"), med, level.nleaves )
        for k, v in level.iteritems():
            nleaves = v.nleaves if hasattr(v, "nleaves") else len(v)
            #self.logger.debug(output.green(' ' * n + "K %s %d %f"), k, nleaves, nleaves/med)
            if hasattr(v, "nleaves"):
                # XXX remove magic number
                # requrire more than 5 pages in a cluster
                # require some diversity in the dom path in order to create a link
                if nleaves > 10 and nleaves >= med and (n > 0 or len(k) > 10):
                    v.clusterable = True
                    level.clusterable = False
                else:
                    v.clusterable = False
                self.scanlevels(v, n+1)

    def printlevelstat(self, level, n=0):
        med = median((i.nleaves if hasattr(i, "nleaves") else len(i) for i in level.itervalues()))
        self.logger.debug(output.green(' ' * n + "MED %f / %d"), med, level.nleaves )
        for k, v in level.iteritems():
            nleaves = v.nleaves if hasattr(v, "nleaves") else len(v)
            if hasattr(v, "nleaves") and v.clusterable:
                self.logger.debug(output.yellow(' ' * n + "K %s %d %f"), k, nleaves, nleaves/med)
            else:
                self.logger.debug(output.green(' ' * n + "K %s %d %f"), k, nleaves, nleaves/med)
            if hasattr(v, "nleaves"):
                self.printlevelstat(v, n+1)

    def makeabspages(self, classif):
        self.abspages = []
        self.makeabspagesrecursive(classif)
        self.linktorealpages()

    def makeabspagesrecursive(self, level):
        for k, v in level.iteritems():
            if hasattr(v, "nleaves"):
                if v.clusterable:
                    self.abspages.append(AbstractPage(reduce(lambda a, b: a + b, level.iterleaves())))
                else:
                    self.makeabspagesrecursive(v)
            else:
                self.abspages.append(AbstractPage(v))

    def levelclustering(self, reqresps):
        classif = Classfier(lambda rr: rr.response.page.linksvector)
        classif.addall(reqresps)
        self.scanlevels(classif)
        self.printlevelstat(classif)
        self.makeabspages(classif)



    def getAbstractPages(self):
        return self.abspages

class PairCounter(object):

    def __init__(self):
        self._dict = defaultdict(int)

    def add(self, a, b):
        assert a != b
        if a < b:
            self._dict[(a, b)] += 1
        else:
            self._dict[(b, a)] += 1

    def addset(self, s):
        ss = sorted(s)
        for i, a in enumerate(ss):
            for b in ss[i+1:]:
                self._dict[(a, b)] += 1

    def addallcombinations(self, bins):
        for bin in bins:
            for a in bin:
                for bin2 in bins:
                    if bin2 != bin:
                        for b in bin2:
                            if a != b:
                                self.add(a, b)

    def get(self, a, b):
        assert a != b
        if a < b:
            return self._dict.get((a, b), 0)
        else:
            return self._dict.get((b, a), 0)

    def __len__(self):
        return len(self._dict)

    def __nonzero__(self):
        return len(self) != 0

    def __str__(self):
        return str(self._dict)

    def __repr__(self):
        return repr(self._dict)

class AppGraphGenerator(object):

    def __init__(self, reqrespshead, abspages):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.reqrespshead = reqrespshead
        self.abspages = abspages
        self.absrequests = None


    def clusterRequests(self):
        # clustering requests on the abstrct pages is a bad idea, because we do not want
        # the exact same request to be split in 2 clusters
        #reqmap = AbstractMap(AbstractRequest, lambda x: (x.method, x.path))
        # actually, if we do not cluster based on the abstract pages, we get issues with the
        # "trap.php" test case, because pages are clustered but requests are not
        # compromise: cluster based on abstract pages only if also the previous abspage is the same

        # first map all request based on method, path, and previous and next abstratc pages
        contextreqmap = AbstractMap(AbstractRequest, lambda x: (x.method, x.path, x.reqresp.response.page.abspage, x.reqresp.prev.response.page.abspage if x.reqresp.prev else None))

        mappedrequests = defaultdict(list)

        for rr in self.reqrespshead:
            mappedrequests[contextreqmap.getAbstract(rr.request)].append(rr)

        del contextreqmap

        # if there are multiple requests that were assigned to the same abstractrequest
        # in the preious mapping, consider assignment final, otherwise do mapping
        # using the full path but not the next and previous pages

        reqmap = AbstractMap(AbstractRequest, lambda x: (x.method, x.path, x.query))

        absrequests = set()

        for ar, rrs in sorted(mappedrequests.iteritems()):
            if len(rrs) > 1 and len(set(rr.request.query for rr in rrs)) > 1:
                for rr in rrs:
                    rr.request.absrequest = ar
                    ar.reqresps.append(rr)
                    absrequests.add(ar)
            else:
                for rr in rrs:
                    absreq = reqmap.getAbstract(rr.request)
                    rr.request.absrequest = absreq
                    absreq.reqresps.append(rr)
                    absrequests.add(absreq)

        del mappedrequests
        del reqmap

        for r in sorted(absrequests):
            print output.turquoise("%s" % r)

        self.absrequests = absrequests

    def generateAppGraph(self):
        self.logger.debug("generating application graph")

        # make sure we are at the beginning
        assert self.reqrespshead.prev is None

        curr = self.reqrespshead
        laststate = 0

        self.clusterRequests()

        currabsreq = curr.request.absrequest
        self.headabsreq = currabsreq


        # go through the while navigation path and link together AbstractRequests and AbstractPages
        # for now, every request will generate a new state, post processing will happen late
        cnt = 0
        while curr:
            currpage = curr.response.page
            currabspage = currpage.abspage
            assert not laststate in currabsreq.targets
            #print output.red("A %s(%d)\n\t%s " % (currabsreq, id(currabsreq),
            #    '\n\t'.join([str((s, t)) for s, t in currabsreq.targets.iteritems()])))
            currabsreq.targets[laststate] = Target(currabspage, laststate+1, nvisits=1)
            #print output.red("B %s(%d)\n\t%s " % (currabsreq, id(currabsreq),
            #    '\n\t'.join([str((s, t)) for s, t in currabsreq.targets.iteritems()])))
            laststate += 1

            if curr.next:
                if curr.next.backto is not None:
                    currpage = curr.next.backto.response.page
                    currabspage = currpage.abspage
                # find which link goes to the next request in the history
                chosenlink = (i for i, l in currpage.links.iteritems() if curr.next in l.to).next()
                nextabsreq = curr.next.request.absrequest
                #print output.green("A %s(%d)\n\t%s " % (nextabsreq, id(nextabsreq),
                #    '\n\t'.join([str((s, t)) for s, t in nextabsreq.targets.iteritems()])))
                # XXX we cannot just use the index for more complex clustering
                print "%d %s %s %s" % (laststate, chosenlink, currabspage.abslinks, currabspage)
                assert not laststate in currabspage.abslinks[chosenlink].targets
                currabspage.abslinks[chosenlink].targets[laststate] = Target(nextabsreq, laststate, nvisits=1)
                assert not laststate in currabspage.statelinkmap
                currabspage.statelinkmap[laststate] = currabspage.abslinks[chosenlink]

            #print output.green("B %s(%d)\n\t%s " % (nextabsreq, id(nextabsreq),
            #    '\n\t'.join([str((s, t)) for s, t in nextabsreq.targets.iteritems()])))

            curr = curr.next
            currabsreq = nextabsreq
            cnt += 1

        self.maxstate = laststate
        self.logger.debug("application graph generated in %d steps", cnt)

        return laststate

    def fillMissingRequests(self):

        reqmap = CustomDict([(rr.request, ar) for ar in self.absrequests for rr in ar.reqresps], AbstractRequest, h=lambda r: (r.method, r.path, r.query))
        print "REQMAP", reqmap

        for ap in self.abspages:
            allstates = set(s for l in ap.abslinks for s in l.targets)
            for l in ap.abslinks:
                newrequest = None
                newrequestbuilt = False
                for s in allstates:
                    if s not in l.targets:
                        if not newrequestbuilt:
                            newwebrequest = ap.reqresps[0].response.page.getNewRequest(l)
                            print "NEWWR %s %d %s %s" % (ap, s, l, newwebrequest)
                            if newwebrequest:
                                request = Request(newwebrequest)
                                print "NEWR %s %s" % (request, (request.method, request.path, request.query))
                                newrequest = reqmap[request]
                                newrequest.reqresps.append(RequestResponse(request, None))
                            newrequestbuilt = True
                        if newrequest:
                            l.targets[s] = Target(newrequest, transition=s, nvisits=0)
                            print output.red("NEWTTT %s %d %s %s" % (ap, s, l, newrequest))

        self.allabsrequests = set(reqmap.itervalues())

    def getMinMappedState(self, state, statemap):
        prev = state
        mapped = statemap[state]
        while mapped != prev:
            prev = mapped
            mapped = statemap[mapped]
        return mapped

    def addStateBins(self, statebins, equalstates):
        seenstates = set(itertools.chain.from_iterable(statebins))
        newequalstates = set()
        for ss in statebins:
            otherstates = seenstates - ss
            #print output.darkred("OS %s" % otherstates)
            for es in equalstates:
                newes = StateSet(es-otherstates)
                if newes:
                    newequalstates.add(newes)
        return newequalstates

    def dropRedundantStateGroups(self, equalstates):
        # if a set of states has no unique states, drop it
        # this removes sets that are subsets of others, and other state equivalences
        # that would cause the state assignment to fail
        # sort by lnegth and state number, in order to make multiple runs deterministic
        equalstateslist = [sorted(i) for i in equalstates]
        equalstateslist.sort(key=lambda x: (len(x), x))
        for es in equalstateslist:
            esset = frozenset(es)
            allothersets = equalstates - frozenset((esset, ))
            assert len(equalstates) == len(allothersets) + 1, "%s %s %s" % (equalstates , allothersets, esset)
            if allothersets:
                allothers = reduce(lambda a, b: a | b, allothersets)
                uniqueelems = esset - allothers
                if not uniqueelems:
                    equalstates -= frozenset((esset,))

    def reduceStates(self):
        self.logger.debug("reducing state number from %d", self.maxstate)

        # map each state to its equivalent one
        statemap = range(self.maxstate+1)
        lenstatemap = len(statemap)

        currreq = self.headabsreq

        # need history to handle navigatin back; pair of (absrequest,absresponse)
        history = []
        currstate = 0

        while True:
            #print output.green("************************** %s %s\n%s\n%s") % (currstate, currreq, currreq.targets, statemap)
            currtarget = currreq.targets[currstate]

            # if all the previous states leading to the same target caused a state transition,
            # directly guess that this request will cause a state transition
            # this behavior is needed because it might happen that the state transition is not detected,
            # and the state assignment fails
            smallerstates = [(s, t) for s, t in currreq.targets.iteritems()
                    if s < currstate and t.target == currtarget.target]
            if smallerstates and all(statemap[t.transition] != s for s, t in smallerstates):
                #print output.red("************************** %s %s\n%s") % (currstate, currreq, currreq.targets)
                currstate += 1
            else:
                # find if there are other states that we have already processed that lead to a different target
                smallerstates = sorted([i for i, t in currreq.targets.iteritems() if i < currstate and t.target != currtarget.target], reverse=True)
                if smallerstates:
                    currmapsto = self.getMinMappedState(currstate, statemap)
                    for ss in smallerstates:
                        ssmapsto = self.getMinMappedState(ss, statemap)
                        if ssmapsto == currmapsto:
                            self.logger.debug(output.teal("need to split state for request %s")
                                    % currtarget)
                            self.logger.debug("\t%d(%d)->%s"
                                    % (currstate, currmapsto, currtarget))
                            self.logger.debug("\t%d(%d)->%s"
                                    % (ss, ssmapsto, currreq.targets[ss]))
                            # mark this request as givin hints for state change detection
                            currreq.statehints += 1
                            stateoff = 1
                            for (j, (req, page)) in enumerate(reversed(history)):
                                laststate = currstate-j-stateoff
                                if laststate not in req.targets:
                                    # happening due to browser back(), adjust offset
                                    laststate = max(i for i in req.targets if i <= laststate)
                                    stateoff = currstate-j-laststate
                                    #print "stetoff", stateoff
                                #print laststate, j, req.targets.keys(), req
                                target = req.targets[laststate]
                                assert target.target == page, "%s != %s" % (target.target, page)
                                # the Target.nvisit has not been updated yet, because we have not finalized state assignment
                                # let's compute the number of simits by counting the states that
                                # map to the same one and share the target abstract page
                                assert target.nvisits == 1, target.nvisits
                                mappedlaststate = self.getMinMappedState(laststate, statemap)
                                #visits = [s for s, t in req.targets.iteritems() if s <= laststate and t.target == page and self.getMinMappedState(s, statemap) == mappedlaststate]
                                # the condition on t.transition and s is used to not included states that have been already proved to cause a state transition
                                visits = [s for s, t in req.targets.iteritems() if s <= laststate and t.target == page and
                                        self.getMinMappedState(t.transition, statemap) == self.getMinMappedState(s, statemap)]
                                nvisits = len(visits)
                                assert nvisits > 0, "%d, %d" % (laststate, mappedlaststate)
                                if nvisits == 1:
                                    self.logger.debug(output.teal("splitting on %d->%d request %s to page %s"), laststate, target.transition,  req, page)
                                    assert statemap[target.transition] == laststate
                                    statemap[target.transition] = target.transition
                                    #if laststate >= 100:
                                    #    gracefulexit()
                                    break
                            else:
                                # if we get hear, we need a better heuristic for splitting state
                                raise RuntimeError()
                            currmapsto = self.getMinMappedState(currstate, statemap)
                            assert ssmapsto != currmapsto, "%d == %d" % (ssmapsto, currmapsto)

                currstate += 1
                statemap[currstate] = currstate-1

            respage = currtarget.target

            history.append((currreq, respage))
            if currstate not in respage.statelinkmap:
                if currstate == self.maxstate:
                    # end reached
                    break
                while currstate not in respage.statelinkmap:
                    history.pop()
                    respage = history[-1][1]

            chosenlink = respage.statelinkmap[currstate]
            chosentarget = chosenlink.targets[currstate].target

            currreq = chosentarget

        for i in range(lenstatemap):
            statemap[i] = self.getMinMappedState(i, statemap)

        nstates = lenstatemap

        self.logger.debug("reduced states %d", nstates)
        print statemap

        self.collapseGraph(statemap)

        equalstates = set((StateSet(statemap), ))
        seentogether = PairCounter()
        differentpairs = PairCounter()

        # try to detect which states are actually equivalent to older ones
        # assume all staes are eqivalent, and split the set of states into bins
        # when two states prove to be non equivalent
        for ar in sorted(self.absrequests):
            diffbins = defaultdict(set)
            equalbins = defaultdict(set)
            for s, t in ar.targets.iteritems():
                diffbins[t.target].add(s)
                # these quality-only bins are usful in the case the last examined pages caused a state transition:
                # we need the latest state to appear in at least one bin!
                equalbins[t.target].add(t.transition)
            statebins = [StateSet(i) for i in diffbins.itervalues()]
            equalstatebins = [StateSet(i) for i in equalbins.itervalues()]

            print output.darkred("BINS %s %s" % (' '.join(str(i) for i in statebins), ar))
            print output.darkred("EQUALBINS %s" % ' '.join(str(i) for i in equalstatebins))

            for sb in statebins:
                seentogether.addset(sb)
            for esb in equalstatebins:
                seentogether.addset(esb)

            differentpairs.addallcombinations(statebins)


            equalstates = self.addStateBins(statebins, equalstates)
            self.dropRedundantStateGroups(equalstates)

            print output.darkred("ES %s" % sorted(equalstates))


        # in the previous step, we marked as different states that were leading to different target pages,
        # regardless of the target state
        # now that we know that some states are different for sure,
        # let's do a second scan taking into considereation also the state of the target page
        # marking as different state that lead to the the same target page, but in diferent states
        again1 = True
        while differentpairs:
            again1 = False
            again2 = True
            while again2:
                again2 = False
                currentdifferentpairs = differentpairs
                differentpairs = PairCounter()
                for ar in sorted(self.absrequests):
                    targetbins = defaultdict(set)
                    targetstatebins = defaultdict(set)
                    for s, t in ar.targets.iteritems():
                        targetbins[t.target].add(t.transition)
                        targetstatebins[(t.target, t.transition)].add(s)

                    for t, states in targetbins.iteritems():
                        if len(states) > 1:
                            targetequalstates = set([StateSet(states)])
                            print "preTES", targetequalstates, ar, t

                            statelist = sorted(states)

                            for i, a in enumerate(statelist):
                                for b in statelist[i+1:]:
                                    if currentdifferentpairs.get(a, b):
                                        print "DIFF %d != %d  ==>   %s != %s" % (a, b, targetstatebins[(t, a)], targetstatebins[(t, b)])
                                        differentpairs.addallcombinations((targetstatebins[(t, a)], targetstatebins[(t, b)]))
                                        targetequalstates = self.addStateBins([StateSet([a]), StateSet([b])], targetequalstates)
                                        self.dropRedundantStateGroups(targetequalstates)

                            print "TES", targetequalstates, ar, t

                            startstatebins = set(reduce(lambda a, b: StateSet(a | b), (StateSet(targetstatebins[(t, ts)]) for ts in esb)) for esb in targetequalstates)

                            print "SSB", startstatebins, ar, t

                            newequalstates = self.addStateBins(startstatebins, equalstates)
                            self.dropRedundantStateGroups(newequalstates)
                            if newequalstates != equalstates:
                                equalstates = newequalstates
                                again2 = True
                                print output.darkred("ES %s" % sorted(equalstates))

                assert len(differentpairs) > 0 or not again2, "%s %s %s" % (again2, differentpairs, (len(differentpairs) > 0))

            differentpairs = PairCounter()

            sumbinlen = sum(len(i) for i in equalstates)
            while sumbinlen != len(set(statemap)):
                again1 = True
                self.logger.debug("unable to perform state allocation %d %d\n\t%s" % (sumbinlen, len(set(statemap)), equalstates))

                cntdict = defaultdict(int)
                for es in equalstates:
                    for s in es:
                        cntdict[s] += 1
                violating = sorted(((v, s) for s, v in cntdict.iteritems() if v > 1), key=lambda x: (-x[1], x[0]))
                self.logger.debug("states in multiple groups %s" % violating)
                assert violating, "%d %d\n\t%s" % (sumbinlen, len(set(statemap)), equalstates)

                multiples = StateSet(i[1] for i in violating)

                # if a state appras in multiple sets, choose the set that contains the elements
                # it was seen together the biggest number of times
                for m in multiples:
                    containingsets = [i for i in sorted(equalstates) if m in i]
                    reducedcontainingsets = [i - multiples for i in containingsets]
                    containingsetscores = [sum(seentogether.get(m, i) for i in cs if i != m) for cs in reducedcontainingsets]

                    bestset = max((score, s) for score, s in zip(containingsetscores, containingsets))[1]

                    self.logger.debug("keep state %s in stateset %s" % (m, bestset))
                    print [i for i in zip(containingsetscores, containingsets, reducedcontainingsets)]

                    for (cs, rcs) in zip(containingsets, reducedcontainingsets):
                        if cs != bestset:
                            equalstates.remove(cs)
                            equalstates.add(StateSet(cs - frozenset([m])))
                            for ds in rcs:
                                if ds != m:
                                    differentpairs.add(ds, m)
                sumbinlen = sum(len(i) for i in equalstates)

            self.logger.debug(output.darkred("almost-final state allocation %s" % equalstates))

            assert again1 == (len(differentpairs) > 0), "%s %s %s" % (again1, differentpairs, (len(differentpairs) > 0))

        self.logger.debug(output.darkred("final state allocation %s" % equalstates))

        equalstatemap = {}
        for es in equalstates:
            mins = min(es)
            for s in es:
                equalstatemap[s] = mins


        for i in range(lenstatemap):
            statemap[i] = equalstatemap[statemap[i]]

        nstates = len(set(statemap))
        self.logger.debug("final states %d", nstates)

        self.collapseGraph(statemap)

        # return last current state
        return statemap[-1]


    def collapseNode(self, nodes, statemap):
        for aa in nodes:
            statereduce = [(st, statemap[st]) for st in aa.targets]
            for st, goodst in statereduce:
                if st == goodst:
                    aa.targets[goodst].transition = statemap[aa.targets[goodst].transition]
                else:
                    if goodst in aa.targets:
                        assert aa.targets[st].target == aa.targets[goodst].target, \
                                "%d->%s %d->%s" % (st, aa.targets[st], goodst, aa.targets[goodst])
                        assert st == goodst or statemap[aa.targets[goodst].transition] == statemap[aa.targets[st].transition], \
                                "%s\n\t%d->%s (%d)\n\t%d->%s (%d)" \
                                % (aa, st, aa.targets[st], statemap[aa.targets[st].transition],
                                        goodst, aa.targets[goodst], statemap[aa.targets[goodst].transition])
                        aa.targets[goodst].nvisits += aa.targets[st].nvisits
                    else:
                        aa.targets[goodst] = aa.targets[st]
                        # also map transition state to the reduced one
                        aa.targets[goodst].transition = statemap[aa.targets[goodst].transition]
                    del aa.targets[st]

    def collapseGraph(self, statemap):
        self.logger.debug("collapsing graph")

        # merge states that were reduced to the same one
        for ap in self.abspages:
            print "===", ap
            self.collapseNode(ap.abslinks.itervalues(), statemap)

        self.collapseNode(self.absrequests, statemap)


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

    class ActionFailure(Exception):
        pass

    class UnsubmittableForm(ActionFailure):
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
        # first RequestResponse object
        self.headreqresp = None

    def open(self, url):
        del self.refresh_urls[:]
        #webrequest = htmlunit.WebRequest(htmlunit.URL(url))
        htmlpage = htmlunit.HtmlPage.cast_(self.webclient.getPage(url))
        # TODO: handle HTTP redirects, they will throw an exception
        return self.newPage(htmlpage)

    def followRedirect(self, redirect):
        self.logger.debug(output.purple("following redirect %s"), redirect)
        lastvalidpage = self.currreqresp.response.page
        while lastvalidpage.redirect or lastvalidpage.error:
            if not lastvalidpage.reqresp.prev:
                # beginning of history
                lastvalidpage = None
                break
            lastvalidpage = lastvalidpage.reqresp.prev.response.page
        if lastvalidpage:
            fqurl = lastvalidpage.internal.getFullyQualifiedUrl(redirect.location)
        else:
            fqurl = redirect.location
        try:
            htmlpage = htmlunit.HtmlPage.cast_(self.webclient.getPage(fqurl))
        except htmlunit.JavaError, e:
            reqresp = self.handleNavigationException(e)
        reqresp = self.newPage(htmlpage)
        redirect.to.append(reqresp)
        return reqresp

    def newPage(self, htmlpage):
        page = Page(htmlpage)
        webresponse = htmlpage.getWebResponse()
        response = Response(webresponse, page=page)
        request = Request(webresponse.getWebRequest())
        reqresp = RequestResponse(request, response)
        request.reqresp = reqresp
        page.reqresp = reqresp

        self.updateInternalData(reqresp)
        return self.currreqresp

    def newHttpRedirect(self, webresponse):
        redirect = Page(webresponse, redirect=True)
        response = Response(webresponse, page=redirect)
        request = Request(webresponse.getWebRequest())
        reqresp = RequestResponse(request, response)
        request.reqresp = reqresp
        redirect.reqresp = reqresp

        self.updateInternalData(reqresp)
        return self.currreqresp

    def newHttpError(self, webresponse):
        redirect = Page(webresponse, error=True)
        response = Response(webresponse, page=redirect)
        request = Request(webresponse.getWebRequest())
        reqresp = RequestResponse(request, response)
        request.reqresp = reqresp
        redirect.reqresp = reqresp

        self.updateInternalData(reqresp)
        return self.currreqresp

    def updateInternalData(self, reqresp):
        backto = self.currreqresp if self.lastreqresp != self.currreqresp else None
        reqresp.prev = self.lastreqresp
        reqresp.backto = backto
        if self.lastreqresp is not None:
            self.lastreqresp.next = reqresp
        self.lastreqresp = reqresp
        self.currreqresp = reqresp
        if self.headreqresp is None:
            self.headreqresp = reqresp

        self.logger.info("%s", self.currreqresp)

    def handleNavigationException(self, e):
        javaex = e.getJavaException()
        if htmlunit.FailingHttpStatusCodeException.instance_(javaex):
            httpex = htmlunit.FailingHttpStatusCodeException.cast_(javaex)
            self.logger.info("%s" % httpex)
            statuscode = httpex.getStatusCode()
            message = httpex.getMessage()
            if statuscode == 303:
                response = httpex.getResponse()
                location = response.getResponseHeaderValue("Location")
                self.logger.info(output.purple("redirect to %s %d (%s)" % (location, statuscode, message)))
                reqresp = self.newHttpRedirect(response)
            elif statuscode == 404:
                response = httpex.getResponse()
                self.logger.info(output.purple("error %d (%s)" % (statuscode, message)))
                reqresp = self.newHttpError(response)
            else:
                raise
        else:
            raise
        return reqresp

    def click(self, anchor):
        self.logger.debug(output.purple("clicking on %s"), anchor)
        assert anchor.internal.getPage() == self.currreqresp.response.page.internal, \
                "Inconsistency error %s != %s" % (anchor.internal.getPage(), self.currreqresp.response.page.internal)
        try:
            htmlpage = htmlunit.HtmlPage.cast_(anchor.internal.click())
            reqresp = self.newPage(htmlpage)
        except htmlunit.JavaError, e:
            reqresp = self.handleNavigationException(e)
        anchor.to.append(reqresp)
        assert reqresp.request.fullpath[-len(anchor.href):] == anchor.href, \
                "Unhandled redirect %s !sub %s" % (anchor.href, reqresp.request.fullpath)
        return reqresp

    def submitForm(self, form, params):
        htmlpage = None

        self.logger.info(output.fuscia("submitting form %s %r and params: %r"),
                form.method.upper(), form.action,
                params)

        iform = form.internal

        for k,v in params.iteritems():
            iform.getInputByName(k).setValueAttribute(v)

        try:
            # find an element to click in order to submit the form
            # TODO: explore clickable regions in input type=image
            for submittable in [("input", "type", "submit"),
                    ("input", "type", "image"),
                    ("input", "type", "button"),
                    ("button", "type", "submit")]:
                try:
                    submitter = iform.getOneHtmlElementByAttribute(*submittable)
                    htmlpage = submitter.click()
                    break
                except htmlunit.JavaError, e:
                    javaex = e.getJavaException()
                    if not htmlunit.ElementNotFoundException.instance_(javaex):
                        raise
                    continue

            if not htmlpage:
                self.logger.warn("could not find submit button for form %s %r in page",
                        form.method,
                        form.action)
                raise Crawler.UnsubmittableForm()

            htmlpage = htmlunit.HtmlPage.cast_(htmlpage)
            reqresp = self.newPage(htmlpage)

        except htmlunit.JavaError, e:
            reqresp = self.handleNavigationException(e)

        form.to.append(reqresp)
        assert reqresp.request.fullpath.split('?')[0][-len(form.action):] == form.action.split('?')[0], \
                "Unhandled redirect %s !sub %s" % (form.action, reqresp.request.fullpath)
        return reqresp

    def back(self):
        self.logger.debug(output.purple("stepping back"))
        # htmlunit has not "back" functrion
        if self.currreqresp.prev is None:
            raise Crawler.EmptyHistory()
        self.currreqresp = self.currreqresp.prev
        return self.currreqresp

class Dist(object):
    LEN = 5

    def __init__(self, v=None):
        """ The content of the vector is as follow:
        (POST form, GET form, anchor w/ params, anchor w/o params, redirect)
        only one element can be != 0, and contains the numb er of times that link has been visited
        """
        self.val = tuple(v) if v else tuple([0]*Dist.LEN)
        assert len(self.val) == Dist.LEN

    def __add__(self, d):
        return Dist(a+b for a, b in zip(self.val, d.val))

    def __cmp__(self, d):
        return cmp(self.val, d.val)

    def __str__(self):
        return str(self.val)

class FormFiller:
    def __init__(self):
        self.forms = {}

    def add(self, k):
        self.forms[tuple(sorted(k.keys()))] = k

    def __getitem__(self, k):
        return self.forms[tuple(sorted([i for i in k if i]))]

Candidate = namedtuple("Candidate", "priority dist path")
PathStep = namedtuple("PathStep", "abspage idx state")

class Engine(object):

    Actions = Constants("BACK", "ANCHOR", "FORM", "REDIRECT", "DONE")

    def __init__(self, formfiller=None):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.state = -1
        self.followingpath = False
        self.pathtofollow = []
        self.formfiller = formfiller

    def getUnvisitedLink(self, reqresp):
        page = reqresp.response.page
        abspage = page.abspage

        # if we do not have an abstract graph, pick first anchor
        # this should happen only at the first iteration
        if abspage is None:
            if len(page.anchors) > 0:
                self.logger.debug("abstract page not availabe, picking first anchor")
                return (Links.Type.ANCHOR, 0)
            else:
                self.logger.debug("abstract page not availabe, and no anchors")
                return None

        # find unvisited anchor
        for i, aa in enumerate(abspage.absanchors):
            if self.state not in aa.targets or aa.targets[self.state].nvisits == 0:
                return (Links.Type.ANCHOR, i)
        return None

    def linkcost(self, abspage, linkidx, link, state):
        if state in link.targets:
            nvisits = link.targets[state].nvisits + 1
        else:
            # never visited, but it must be > 0
            nvisits = 1
        if linkidx[0] == Links.Type.ANCHOR:
            if link.hasquery:
                dist = Dist((0, 0, nvisits, 0, 0))
            else:
                dist = Dist((0, 0, 0, nvisits, 0))
        elif linkidx[0] == Links.Type.FORM:
            if link.isPOST:
                dist = Dist((nvisits, 0, 0, 0, 0))
            else:
                dist = Dist((0, nvisits, 0, 0, 0))
        elif linkidx[0] == Links.Type.REDIRECT:
            dist = Dist((0, 0, 0, 0, nvisits))
        else:
            assert False, linkidx

        return dist

    def addUnvisisted(self, dist, head, state, headpath, unvlinks, candidates, priority):
        unvlink = unvlinks[0]
        self.logger.debug("found unvisited link %s in page %s (%d) dist %s", unvlink,
                head, state, dist)
        mincost = min((self.linkcost(head, i, j, state), i) for (i, j) in unvlinks)
        path = list(reversed([PathStep(head, mincost[1], state)] + headpath))
        heapq.heappush(candidates, Candidate(priority, dist + mincost[0], path))

    def findPathToUnvisited(self, startpage, startstate, recentlyseen):
        # recentlyseen is the set of requests done since last state change
        heads = [(Dist(), startpage, startstate, [])]
        seen = set()
        candidates = []
        while heads:
            dist, head, state, headpath = heapq.heappop(heads)
            print output.yellow("H %s %s %s %s" % (dist, head, state, headpath))
            if (head, state) in seen:
                continue
            seen.add((head, state))
            unvlinks = head.abslinks.getUnvisited(state)
            if unvlinks:
                self.addUnvisisted(dist, head, state, headpath, unvlinks, candidates, 0)
                continue
            for idx, link in head.abslinks.iteritems():
                if link.skip:
                    continue
                newpath = [PathStep(head, idx, state)] + headpath
                #print "state %s targets %s" % (state, link.targets)
                if state in link.targets:
                    nextabsreq = link.targets[state].target
                    if state == startstate and nextabsreq.statehints and nextabsreq not in recentlyseen:
                        # this is a page known to be revelaing of possible state change
                        # go there first, priority=-1 !
                        self.addUnvisisted(dist, head, state, headpath, [(idx, link)], candidates, -1)
                    if state not in nextabsreq.targets:
                        self.addUnvisisted(dist, head, state, headpath, [(idx, link)], candidates, 0)
                        continue
                    # do not put request in the heap, but just go for the next abstract page
                    tgt = nextabsreq.targets[state]
                    assert tgt.target
                    if (tgt.target, tgt.transition) in seen:
                        continue
                    newdist = dist + self.linkcost(head, idx, link, state)
                    #print "TGT %s %s %s" % (tgt, newdist, nextabsreq)
                    heapq.heappush(heads, (newdist, tgt.target, tgt.transition, newpath))
                else:
                    # TODO handle state changes
                    raise NotImplementedError
        nvisited = len(set(i[0] for i in seen))
        if candidates:
            return candidates[0].path, nvisited
        else:
            return None, nvisited


    def getEngineAction(self, linkidx):
        if linkidx[0] == Links.Type.ANCHOR:
            engineaction = Engine.Actions.ANCHOR
        elif linkidx[0] == Links.Type.FORM:
            engineaction = Engine.Actions.FORM
        elif linkidx[0] == Links.Type.REDIRECT:
            engineaction = Engine.Actions.REDIRECT
        else:
            assert False, linkidx
        return engineaction




    def getNextAction(self, reqresp):
        if self.pathtofollow:
            assert self.followingpath
            nexthop = self.pathtofollow.pop(0)
            if not reqresp.response.page.abspage.match(nexthop.abspage) or nexthop.state != self.state:
                self.logger.debug(output.red("got %s (%d) not matching expected %s (%d)"),
                        reqresp.response.page.abspage, self.state, nexthop.abspage, nexthop.state)
                self.logger.debug(output.red(">>>>>>>>>>>>>>>>>>>>>>>>>>>>> ABORT following path"))
                self.followingpath = False
                self.pathtofollow = []
            else:
                assert nexthop.state == self.state
                if nexthop.idx is None:
                    assert not self.pathtofollow
                else:
                    return (self.getEngineAction(nexthop.idx), reqresp.response.page.links[nexthop.idx])
        if self.followingpath and not self.pathtofollow:
            self.logger.debug(output.red(">>>>>>>>>>>>>>>>>>>>>>>>>>>>> DONE following path"))
            self.followingpath = False

        if not reqresp.response.page.abspage:
            unvisited = self.getUnvisitedLink(reqresp)
            if unvisited:
                self.logger.debug(output.green("unvisited in current page: %s"), unvisited)
                return (Engine.Actions.ANCHOR, reqresp.response.page.links[unvisited])

        if reqresp.response.page.abspage:
            recentlyseen = set()
            rr = reqresp
            found = False
            while rr:
                destination = rr.response.page.abspage
                for s, t in rr.request.absrequest.targets.iteritems():
                    if (t.target, t.transition) == (destination, self.state):
                        if s == self.state:
                            # state transition did not happen here
                            recentlyseen.add(rr.request.absrequest)
                            break
                        else:
                            found = True
                            break
                else:
                    # we should always be able to find the destination page in ta target object
                    assert False
                if found:
                    break
                rr = rr.prev
                print "RRRR", rr
            self.logger.debug("last changing request %s", rr)
            print "recentlyseen", recentlyseen
            path, nvisited = self.findPathToUnvisited(reqresp.response.page.abspage, self.state, recentlyseen)
            if self.ag:
                self.logger.debug("visited %d/%d abstract pages", nvisited, len(self.ag.abspages))
            self.logger.debug(output.green("PATH %s"), path)
            if path:
                # if there is a state change along the path, drop all following steps
                for i, p in enumerate(path):
                    if i > 0 and p.state != path[i-1].state:
                        path[i:] = []
                        break
                self.logger.debug(output.green("REDUCED PATH %s"), path)
                self.logger.debug(output.red("<<<<<<<<<<<<<<<<<<<<<<<<<<<<< START following path"))
                self.followingpath = True
                assert not self.pathtofollow
                self.pathtofollow = path
                nexthop = self.pathtofollow.pop(0)
                print nexthop
                assert nexthop.abspage == reqresp.response.page.abspage
                assert nexthop.state == self.state
                return (self.getEngineAction(nexthop.idx), reqresp.response.page.links[nexthop.idx])
            elif self.ag and float(nvisited)/len(self.ag.abspages) > 0.9:
                # we can reach almost everywhere form the current page, still we cannot find unvisited links
                # very likely we visited all the pages or we can no longer go back to some older states anyway
                return (Engine.Actions.DONE, )

        # no path found, step back
        return (Engine.Actions.BACK, )

    def submitForm(self, form):
        try:
            formkeys = form.keys
            self.logger.debug("form keys %r", formkeys)
            params = self.formfiller[formkeys]
        except KeyError:
            # we do not have parameters for the form
            params = {}
        return self.cr.submitForm(form, params)


    def main(self, urls):
        self.pc = None
        self.ag = None
        cr = Crawler()
        self.cr = cr

        for cnt, url in enumerate(urls):
            self.logger.info(output.purple("starting with URL %d/%d %s"), cnt+1, len(urls), url)
            reqresp = cr.open(url)
            print output.red("TREE %s" % (reqresp.response.page.linkstree,))
            print output.red("TREEVECTOR %s" % (reqresp.response.page.linksvector,))
            nextAction = self.getNextAction(reqresp)
            while nextAction[0] != Engine.Actions.DONE:
                if nextAction[0] == Engine.Actions.ANCHOR:
                    reqresp = cr.click(nextAction[1])
                elif nextAction[0] == Engine.Actions.FORM:
                    try:
                        reqresp = self.submitForm(nextAction[1])
                    except Crawler.UnsubmittableForm:
                        nextAction[1].skip = True
                        nextAction = self.getNextAction(reqresp)
                elif nextAction[0] == Engine.Actions.BACK:
                    reqresp = cr.back()
                elif nextAction[0] == Engine.Actions.REDIRECT:
                    reqresp = cr.followRedirect(nextAction[1])
                else:
                    assert False, nextAction
                print output.red("TREE %s" % (reqresp.response.page.linkstree,))
                print output.red("TREEVECTOR %s" % (reqresp.response.page.linksvector,))
                pc = PageClusterer(cr.headreqresp)
                print output.blue("AP %s" % '\n'.join(str(i) for i in pc.getAbstractPages()))
                ag = AppGraphGenerator(cr.headreqresp, pc.getAbstractPages())
                maxstate = ag.generateAppGraph()
                self.state = ag.reduceStates()
                self.logger.debug(output.green("current state %d (%d)"), self.state, maxstate)
                ag.fillMissingRequests()
                nextAction = self.getNextAction(reqresp)
                assert nextAction

                self.pc = pc
                self.ag = ag

                if wanttoexit:
                    return

    def writeDot(self):
        if not self.ag:
            self.logger.debug("not creating DOT graph")
            return

        self.logger.info("creating DOT graph")
        dot = pydot.Dot()
        nodes = {}

        for p in self.ag.abspages:
            name = p.label
            node = pydot.Node(name)
            nodes[p] = node

        for p in self.ag.allabsrequests:
            name = str('\\n'.join(p.requestset))
            node = pydot.Node(name)
            nodes[p] = node

        self.logger.debug("%d DOT nodes", len(nodes))

        for n in nodes.itervalues():
            dot.add_node(n)

        for p in self.ag.abspages:
            for l in p.abslinks:
                linksequal = defaultdict(list)
                for s, t in l.targets.iteritems():
                    assert s == t.transition
                    linksequal[t.target].append(s)
                for t, ss in linksequal.iteritems():
                    try:
                        edge = pydot.Edge(nodes[p], nodes[t])
                    except KeyError, e:
                        self.logger.warn("Cannot find node %s", e.args[0])
                        continue
                    ss.sort()
                    edge.set_label(",".join(str(i) for i in ss))
                    dot.add_edge(edge)

        for p in self.ag.absrequests:
            linksequal = defaultdict(list)
            for s, t in p.targets.iteritems():
                if s != t.transition:
                    edge = pydot.Edge(nodes[p], nodes[t.target])
                    #print "LINK %s => %s" % (p, t.target)
                    edge.set_label("%s->%s" % (s, t.transition))
                    edge.set_color("red")
                    dot.add_edge(edge)
                else:
                    linksequal[t.target].append(s)
            for t, ss in linksequal.iteritems():
                try:
                    edge = pydot.Edge(nodes[p], nodes[t])
                except KeyError, e:
                    self.logger.warn("Cannot find node %s", e.args[0])
                    continue
                ss.sort()
                edge.set_label(",".join(str(i) for i in ss))
                dot.add_edge(edge)
                edge.set_color("blue")

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
        e.main(sys.argv[1:])
    except:
        import traceback
        traceback.print_exc()
    finally:
        e.writeDot()


# vim:sw=4:et:
