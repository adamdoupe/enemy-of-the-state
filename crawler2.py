#!/usr/bin/env python

import logging
def handleError(self, record):
      raise
logging.Handler.handleError = handleError

import urlparse
import re
import heapq
import itertools
import random
import math

LAST_REQUEST_BOOST=0.1
POST_BOOST=0.2
QUERY_BOOST=0.1

rng = random.Random()
rng.seed(1)

import pydot

import output

import htmlunit

from collections import defaultdict, deque, namedtuple

htmlunit.initVM(':'.join([htmlunit.CLASSPATH, '.']))

import pdb

cond = 0
debugstop = False
debug_set = set()

# running htmlunit via JCC will override the signal halders

import signal

wanttoexit = False

maxstate = -1

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
    def __init__(self, nleavesfunc=lambda x: 1, nleavesaggregator=sum):
        # when counting leaves, apply this function to non RecursiveDict objects
        self.nleavesfunc = nleavesfunc
        self.nleavesaggregator = nleavesaggregator
        self._nleaves = None
        # XXX no more general :(
        self.abspages = {}

    def __missing__(self, key):
        v = RecursiveDict(nleavesfunc=self.nleavesfunc, nleavesaggregator=self.nleavesaggregator)
#        if str(key).find("logout") != -1 and debugstop:
#            pdb.set_trace()
        self.__setitem__(key, v)
        return v

    @property
    def nleaves(self):
        if self._nleaves is None:
            self._nleaves = self.nleavesaggregator(i.nleaves if isinstance(i, RecursiveDict) else self.nleavesfunc(i)
                    for i in self.itervalues())
        return self._nleaves

    def getpath(self, path):
        i = self
        for p in path:
            i = i[p]
        return i

    def getpathnleaves(self, path):
        yield self.nleaves
        i = self
        for p in path:
            if not p in i:
                yield (0, 0)
                break
            else:
                i = i[p]
                if not isinstance(i, RecursiveDict):
                    yield i
                    break
                yield i.nleaves


    def setpath(self, path, value):
        i = self
        # invalidate leaves count
        i._nleaves = None
        for p in path[:-1]:
            i = i[p]
            # invalidate leaves count
            i._nleaves = None
#        if str(path[-1]).find("logout") != -1 and debugstop:
#            pdb.set_trace()
        i[path[-1]] = value

    def applypath(self, path, func):
        i = self
        # invalidate leaves count
        i._nleaves = None
        for p in path[:-1]:
            i = i[p]
            # invalidate leaves count
            i._nleaves = None
#        if str(path[-1]).find("logout") != -1 and debugstop:
#            pdb.set_trace()
        i[path[-1]] = func(i[path[-1]])

    def setapplypath(self, path, value, func):
        i = self
        # invalidate leaves count
        i._nleaves = None
        for p in path[:-1]:
            i = i[p]
            # invalidate leaves count
            i._nleaves = None
#        if str(path[-1]).find("logout") != -1 and debugstop:
#            pdb.set_trace()
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
                    if isinstance(c, RecursiveDict):
                        levelkeys.extend(c.iterkeys())
                        children.extend(c.itervalues())
                    else:
                        levelkeys.append(self.nleavesfunc(c))
                if children:
                    queue.append(children)
                #self.logger.debug("LK", len(queue), levelkeys, queue)
                yield levelkeys

    def iterleaves(self):
        if self:
            for c in self.itervalues():
                if isinstance(c, RecursiveDict):
                    for i in c.iterleaves():
                        yield i
                else:
                    yield c

    def iteridxleaves(self):
        for k, v in defaultdict.iteritems(self):
            if not isinstance(v, RecursiveDict):
                yield ((k, ), v)
            else:
                for kk, vv in v.iteridxleaves():
                    yield (tuple([k] + list(kk)), vv)

    @lazyproperty
    def depth(self):
        return max(i.depth+1 if isinstance(i, RecursiveDict) else 1
                for i in self.itervalues())

    def __str__(self, level=0):
        out = ""
        for k, v in sorted(self.items()):
            out += "\n%s%s:"  % ("\t"*level, k)
            if isinstance(v, RecursiveDict):
                out += "%s%s" % (v.nleaves, v.__str__(level+1))
            else:
                out += "%s" % (v, )
        return out

    def equals(self, o):
        return len(self) == len(o) \
                and set(self.keys()) == set(o.keys()) \
                and all(self[k].equals(o[k]) if hasattr(self[k], 'equals') else 
                        self[k] == o[k] for k in self.iterkeys())


class Request(object):

    def __init__(self, webrequest):
        self.webrequest = webrequest
        self.reqresp = None
        self.absrequest = None
        self.formparams = FormFiller.Params({})
        self.state = -1
        self.statehint = False
        self.changingstate = False

    @lazyproperty
    def method(self):
        return str(self.webrequest.getHttpMethod())

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
        assert internal
        assert reqresp
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
    SUBMITTABLES = [("input", "type", "submit"),
                    ("input", "type", "image"),
                    ("input", "type", "button"),
                    ("button", "type", "submit")]
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
        return formvector(self.method, self.actionurl, self.inputnames, self.hiddennames)

    @lazyproperty
    def elemnames(self):
        return [i.name for i in self.elems]

    @lazyproperty
    def elems(self):
        return self.inputs + self.textareas + self.selects

    def buildFormField(self, e):
        etype = e.getAttribute('type').lower()
        name = e.getAttribute('name')
        value = e.getAttribute('value')
        if etype == "hidden":
            type = FormField.Type.HIDDEN
        elif etype == "text":
            type = FormField.Type.TEXT
        elif etype == "checkbox":
            type = FormField.Type.CHECKBOX
        else:
            type = FormField.Type.OTHER
        return FormField(type, name, value)

    @lazyproperty
    def inputnames(self):
        return [i.name for i in self.inputs]

    @lazyproperty
    def hiddennames(self):
        return [i.name for i in self.hiddens]

    @lazyproperty
    def textareanames(self):
        return [i.name for i in self.textareas]

    @lazyproperty
    def selectnames(self):
        return [i.name for i in self.selectnames]

    @lazyproperty
    def inputs(self):
        return [self.buildFormField(e)
                for e in (htmlunit.HtmlElement.cast_(i)
                    for i in self.internal.getHtmlElementsByTagName('input'))
                if e.getAttribute('type').lower() != "hidden"]

    @lazyproperty
    def hiddens(self):
        return [self.buildFormField(e)
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
        return urlvector(htmlunit.URL(self.reqresp.request.webrequest.getUrl(), self.location))

    @lazyproperty
    def dompath(self):
        return "REDIRECT"


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
        self.state = -1
        # cannot use this assert, otherwise calls the lazypropery reirects before reqresp is initialized
        #assert not self.redirect or len(self.redirects) == 1, self.redirects

    @lazyproperty
    def anchors(self):
        return [Anchor(i, self.reqresp) for i in self.internal.getAnchors() if validanchor(i)] if not self.redirect and not self.error else []

    @lazyproperty
    def forms(self):
        return [Form(i, self.reqresp) for i in self.internal.getForms()] if not self.redirect and not self.error else []

    @lazyproperty
    def redirects(self):
        return [Redirect(self.internal.getResponseHeaderValue("Location"), self.reqresp)] if self.redirect else []

    @property
    def linkstree(self):
        return self.links.linkstree

    @lazyproperty
    def linksvector(self):
        return linksvector(self)

    @lazyproperty
    def links(self):
        return Links(self.anchors, self.forms, self.redirects)

    def getNewRequest(self, idx, link):
#        if str(idx).find("guestbook") != -1:
#            pdb.set_trace()
        if isinstance(link, AbstractAnchor):
            if len(link.hrefs) == 1:
                href = iter(link.hrefs).next()
                if not href.strip().lower().startswith("javascript:"):
                    url = self.internal.getFullyQualifiedUrl(href)
                    return htmlunit.WebRequest(url)
        elif isinstance(link, AbstractRedirect):
            if len(link.locations) == 1:
                href = iter(link.locations).next()
                if not href.strip().lower().startswith("javascript:"):
                    url = htmlunit.URL(self.internal.getWebRequest().getUrl(),
                            href)
                    return htmlunit.WebRequest(url)
        elif isinstance(link, AbstractForm):
            if len(link.methods) == 1:
                submitter = None
                iform = self.links[idx].internal
                for submittable in Form.SUBMITTABLES:
                    try:
                        submitter = iform.getOneHtmlElementByAttribute(*submittable)
                        #self.logger.debug("SUBMITTER", submitter, submitter.getPage())
                        break
                    except htmlunit.JavaError, e:
                        javaex = e.getJavaException()
                        if not htmlunit.ElementNotFoundException.instance_(javaex):
                            raise
                        continue
                if submitter:
                    #self.logger.debug("CASTING?")
                    newreq = iform.getWebRequest(submitter)
                    if htmlunit.HtmlImageInput.instance_(submitter):
                        #pdb.set_trace()
                        url = newreq.getUrl()
                        #self.logger.debug("CASTING!", url.getQuery(), url.getPath())
                        urlstr = url.getPath()
                        if urlstr.find('?') == -1:
                            urlstr += "?"
                        query = url.getQuery()
                        if query:
                            urlstr += query
                            if query.endswith('&='):
                                # htmlunits generate a spurios &= at the end...
                                urlstr = urlstr[:-2]
                            urlstr += '&'
                        urlstr += "x=0&y=0"
                        newurl = htmlunit.URL(url, urlstr)
                        newreq.setUrl(newurl)
                    #self.logger.debug("NEWFORMREQ %s %s" % (newreq, self))
                    return newreq
        return None


class AbstractLink(object):

    def __init__(self, links):
        # map from state to AbstractRequest
        self.skip = any(i.skip for i in links)
        self.links = links
        self.parentpage = links[0].reqresp.response.page.abspage
        assert all(i.reqresp.response.page.abspage == self.parentpage
                for i in links)
        self.targets = DebugDict(self.parentpage.instance)

    @lazyproperty
    def _str(self):
        raise NotImplementedError

    def __str__(self):
        return self._str

    def __repr__(self):
        return str(self)

    @lazyproperty
    def dompath(self):
        dompaths = set(l.dompath for l in self.links)
        # XXX multiple dompaths not supported yet
        assert len(dompaths) == 1
        return iter(dompaths).next()

class AbstractAnchor(AbstractLink):

    def __init__(self, anchors):
        if not isinstance(anchors, list):
            anchors = list(anchors)
        AbstractLink.__init__(self, anchors)
        self.hrefs = set(i.href for i in anchors)
        self.type = Links.Type.ANCHOR
        self._href = None

    def update(self, anchors):
        oldlen = len(self.hrefs)
        self.hrefs = set(i.href for i in anchors)
        if oldlen != len(self.hrefs):
            self._href = None

    @property
    def _str(self):
        return "AbstractAnchor(%s, targets=%s)" % (self.hrefs, self.targets)

    def equals(self, a):
        return self.hrefs == a.hrefs

    @lazyproperty
    def hasquery(self):
        return any(i.find('?') != -1 for i in self.hrefs)

    @property
    def href(self):
        if not self._href:
            if len(self.hrefs) == 1:
                self._href = iter(self.hrefs).next()
            else:
                # return longest common substring from the beginning
                for i, cc in enumerate(zip(*self.hrefs)):
                    if any(c != cc[0] for c in cc):
                        break
                self._href = iter(self.hrefs).next()[:i]
        return self._href

class AbstractForm(AbstractLink):

    def __init__(self, forms):
        if not isinstance(forms, list):
            forms = list(forms)
        AbstractLink.__init__(self, forms)
        self.methods = set(i.method for i in forms)
        self.actions = set(i.action for i in forms)
        self.type = Links.Type.FORM

    def update(self, forms):
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

    @lazyproperty
    def action(self):
        # XXX multiple hrefs not supported yet
        assert len(self.actions) == 1
        return iter(self.actions).next()

class AbstractRedirect(AbstractLink):

    def __init__(self, redirects):
        if not isinstance(redirects, list):
            redirects = list(redirects)
        AbstractLink.__init__(self, redirects)
        self.locations = set(i.location for i in redirects)
        self.type = Links.Type.REDIRECT

    def update(self, redirects):
        self.locations = set(i.location for i in redirects)

    @property
    def _str(self):
        return "AbstractRedirect(%s, targets=%s)" % (self.locations, self.targets)

    def equals(self, a):
        return self.locations == a.locations

    @lazyproperty
    def hasquery(self):
        return any(i.find('?') != -1 for i in self.locations)

    @lazyproperty
    def location(self):
        # XXX multiple hrefs not supported yet
        assert len(self.locations) == 1
        return iter(self.locations).next()


class Links(object):
    Type = Constants("ANCHOR", "FORM", "REDIRECT")

    def __init__(self, anchors=[], forms=[], redirects=[]):
        # leaves in linkstree are counter of how many times that url occurred
        # therefore use that counter when compuing number of urls with "nleaves"
        linkstree = RecursiveDict(lambda x: len(x))
        for ltype, links in [(Links.Type.ANCHOR, anchors),
                (Links.Type.FORM, forms),
                (Links.Type.REDIRECT, redirects)]:
            for l in links:
                urlv = [ltype]
                urlv += [l.dompath] if l.dompath else []
                #self.logger.debug("LINKVETOR", l.linkvector)
                urlv += list(l.linkvector)
                #self.logger.debug("URLV", urlv)
                linkstree.applypath(urlv, lambda x: self.addlink(x, l))
                #self.logger.debug("LINKSTREE", linkstree)
        if not linkstree:
            # all pages with no links will end up in the same special bin
            linkstree.setapplypath(("<EMPTY>", ), [None], lambda x: x+[None])
        self.linkstree = linkstree

    def addlink(self, v, l):
        if v:
            nextk = max(v.keys()) + 1
        else:
            nextk = 0
        # call setpath to fix the leaves count
        v.setpath([nextk], [l])
        return v


    def nAnchors(self):
        try:
            return self.linkstree[Links.Type.ANCHOR].nleaves
        except KeyError:
            return 0

    def nForms(self):
        try:
            return self.linkstree[Links.Type.FORM].nleaves
        except KeyError:
            return 0

    def nRedirects(self):
        try:
            return self.linkstree[Links.Type.REDIRECT].nleaves
        except KeyError:
            return 0

    def __len__(self):
        return self.nAnchors() + self.nForms() + self.nRedirects()

    def __nonzero__(self):
        return self.nAnchors() != 0 or self.nForms() != 0 or self.nRedirects() != 0

    @lazyproperty
    def _str(self):
        return "Links(%s, %s, %s)" % (self.nAnchors, self.nForms, self.nRedirects)

    def __str__(self):
        return self._str

    def __getitem__(self, linkidx):
        idx = [linkidx.type] + list(linkidx.path)
        val = self.linkstree.getpath(idx)
        if hasattr(val, "nleaves"):
            self.logger.debug(output.red("******** PICKING ONE *******"))
            pdb.set_trace()
            val = val.iterleaves().next()[0]
        assert isinstance(val, list)
        if len(val) > 1:
            self.logger.debug(output.red("******** PICKING ONE *******"))
            pdb.set_trace()
        return val[0]

    def __iter__(self):
        for l in self.linkstree.iterleaves():
            assert isinstance(l, list), l
            for i in l:
                yield i

    def iteritems(self):
        for p, l in self.linkstree.iteridxleaves():
            assert isinstance(l, list), l
            if len(l) > 1:
                self.logger.debug(output.red("******** PICKING ONE *******"))
                pdb.set_trace()
            yield (LinkIdx(p[0], p[1:], None), l[0])






class AbstractLinks(object):

    def __init__(self, linktrees):
        self.linkstree = RecursiveDict()
        for t, c in [(Links.Type.ANCHOR, AbstractAnchor),
                (Links.Type.FORM, AbstractForm),
                (Links.Type.REDIRECT, AbstractRedirect)]:
            self.buildtree(self.linkstree, t, [lt[t] for lt in linktrees], c)
        #pdb.set_trace()

    def buildtree(self, level, key, ltval, c):
        assert all(isinstance(i, list) for i in ltval) or \
                all(not isinstance(i, list) for i in ltval)
        if isinstance(ltval[0], list):
            # we have reached the leaves without encountering a cluster
            # create an abstract object with all the objects in all the leaves
            # ltval is a list of leaves, ie a list of lists containing abstractlinks
            level[key] = c(i for j in ltval for i in j)
        else: #isinstance(ltval[0], RecursiveDict)
            keys = sorted(ltval[0].keys())
            if all(sorted(i.keys()) == keys for i in ltval):
                # the linkstree for all the pages in the current subtree match,
                # lets go deeper in the tree
                for k in keys:
                    self.buildtree(level[key], k, [v[k] for v in ltval], c)
            else:
                # different links have been clustered together
                # stop here and make a node containing all descending
                # abstractlinks
                # leaves are lists, so iterate teie to get links
                level[key] = c(lll for l in ltval for ll in l.iterleaves()
                        for lll in ll)

    def tryMergeLinkstree(self, pagelinkstree):
        # check if the linkstree pagelinkstree matches teh current linkstree for
        # the current AbstractPage. If not, raise an exception and go back to
        # reclustering
        for t, c in [(Links.Type.ANCHOR, AbstractAnchor),
                (Links.Type.FORM, AbstractForm),
                (Links.Type.REDIRECT, AbstractRedirect)]:
            self.tryMergeLinkstreeRec(pagelinkstree[t], self.linkstree[t])

    def tryMergeLinkstreeRec(self, pagelinkstree, baselinkstree):
        if isinstance(baselinkstree, RecursiveDict) and \
                isinstance(pagelinkstree, RecursiveDict):
            # make sure the trees have the same keys
            pagekeys = set(pagelinkstree.keys())
            basekeys = set(baselinkstree.keys())
            if pagekeys != basekeys:
                # there is difference, abort and go back reclustering
                pdb.set_trace()
                raise AppGraphGenerator.MergeLinksTreeException()
            for k in pagekeys:
                # descend into tree
                self.tryMergeLinkstreeRec(pagelinkstree[k], baselinkstree[k])
        elif isinstance(baselinkstree, AbstractLink) and \
                isinstance(pagelinkstree, list):
            pass
        else:
            pdb.set_trace()
            raise AppGraphGenerator.MergeLinksTreeException()


    def __getitem__(self, linkidx):
        idx = [linkidx.type] + list(linkidx.path)
        i = self.linkstree
        for p in idx:
            if isinstance(i, RecursiveDict) and p in i:
                i = i[p]
            else:
                break
        else:
            return i
        self.logger.debug(output.red("******** PICKING ONE *******"))
        pdb.set_trace()
        return i.iterleaves().next()

    def __iter__(self):
        return self.linkstree.iterleaves()

    def itervalues(self):
        return iter(self)

    def iteritems(self):
        for p, l in self.linkstree.iteridxleaves():
            yield (LinkIdx(p[0], p[1:], None), l)

    def getUnvisited(self, state):
        #self.printInfo()
        # unvisited if we never did the request for that state
        # third element of the tuple are the form parameters
        return [(i, l) for i, l in self.iteritems() if not l.skip \
                and (state not in l.targets
                    or not state in l.targets[state].target.targets)]

    def equals(self, l):
        return self.linkstree.equals(l.linkstree)

class AbstractPage(object):

    InstanceCounter = 0

    def __init__(self, reqresps):
        self.instance = AbstractPage.InstanceCounter
        AbstractPage.InstanceCounter += 1
        self.reqresps = reqresps[:]
        for rr in reqresps:
            rr.response.page.abspage = self

        # maps a state to the corresponding abstract link chosen for that state
        self.statelinkmap = {}
        # maps a state to the corresponding requestresponse objects for that state
        self.statereqrespsmap = defaultdict(list)
        self.seenstates = set()
        self._str = None
        #self.absanchors = [AbstractAnchor(i) for i in zip(*(rr.response.page.anchors for rr in self.reqresps))]
        #self.absforms = [AbstractForm(i) for i in zip(*(rr.response.page.forms for rr in self.reqresps))]
        #self.absredirects = [AbstractRedirect(i) for i in zip(*(rr.response.page.redirects for rr in self.reqresps))]
        #self.abslinks = Links(self.absanchors, self.absforms, self.absredirects)
        self.abslinks = AbstractLinks([rr.response.page.linkstree
                for rr in self.reqresps])


    def addPage(self, reqresp):
#        if maxstate > 155 and self.instance == 966:
#            pdb.set_trace()

        self.reqresps.append(reqresp)
        self.abslinks.tryMergeLinkstree(reqresp.response.page.linkstree)
        self._str = None


    def __str__(self):
        if self._str is None:
            self._str =  "AbstractPage(#%d, %s)%s" % (len(self.reqresps),
                    set("%s %s" % (i.request.method, i.request.fullpath) for i in self.reqresps), self.instance)
        return self._str

    def __repr__(self):
        return str(self)

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


class DebugDict(dict):

    def __init__(self, parent):
        self.parent = parent
        dict.__init__(self)

    def __setitem__(self, k, v):
#        if self.parent == 1471 and k == 46: 
#            pdb.set_trace()
        dict.__setitem__(self, k, v)

class AbstractRequest(object):

    InstanceCounter = 0

    class ReqRespsWrapper(list):

        def __init__(self, outer):
            self.outer = outer

        def append(self, rr):
            if self.outer._requestset is not None:
                self.outer._requestset.add(rr.request.shortstr)
            self.outer.changingstate = self.outer.changingstate or rr.request.changingstate
#            if maxstate >= 76 and str(rr.request).find("review") != -1:
#                pdb.set_trace()
            if rr.request.statehint:
                self.outer.statehints += 1
            return list.append(self, rr)

    def __init__(self, request):
        self.method = request.method
        self.path = request.path
        self.reqresps = AbstractRequest.ReqRespsWrapper(self)
        self.instance = AbstractRequest.InstanceCounter
        AbstractRequest.InstanceCounter += 1
        # map from state to AbstractPage
        self.targets = DebugDict(self.instance)
        # counter of how often this page gave hints for detecting a state change
        self.statehints = 0
        self._requestset = None
        self.changingstate = False

    def __str__(self):
        return "AbstractRequest(%s, %s)%d" % (self.requestset, self.targets, self.instance)

    def __repr__(self):
        return "AbstractRequest(%s)%d" % (self.requestset, self.instance)

    @property
    def requestset(self):
        if self._requestset is None:
            self._requestset = set(rr.request.shortstr for rr in self.reqresps)
        return self._requestset

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
        # Target class should never be instanciated, use derived classes
        assert self.__class__ != Target

    def __str__(self):
        return "%s(%r, transition=%d, nvisits=%d)" % \
                (self.__class__.__name__, self.target, self.transition, self.nvisits)

    def __repr__(self):
        return str(self)

class PageTarget(Target):
    def __init__(self, target, transition, nvisits=0):
        assert target is None or isinstance(target, AbstractPage)
        Target.__init__(self, target, transition, nvisits)

class ReqTarget(Target):
    def __init__(self, target, transition, nvisits=0):
        assert target is None or isinstance(target, AbstractRequest)
        Target.__init__(self, target, transition, nvisits)

class FormTarget(Target):

    class MultiDict(object):

        def __init__(self, outer):
            self.outer = outer

        def __contains__(self, k):
            return any(k in i.target.targets for i in self.outer.target.itervalues())

    class Dict(dict):

        def __init__(self, outer, d):
            self.targets = FormTarget.MultiDict(outer)
            dict.__init__(self, d)


    def __init__(self, target, transition, nvisits=0):
        assert isinstance(target, dict)
        Target.__init__(self, target, transition, nvisits)
        self._target = FormTarget.Dict(self, target)

    @property
    def target(self):
        return self._target

    @target.setter
    def target(self, target):
        assert isinstance(target, dict)
        self._target = FormTarget.Dict(self, target)


class CustomDict(dict):

    def __init__(self, items, missing, h=hash):
        dict.__init__(self)
        self.h = h
        self.missing = missing
        for (k, v) in items:
            self[k] = v

    def __getitem__(self, k):
        #self.logger.debug("GET", k)
        h = self.h(k)
        if dict.__contains__(self, h):
            return dict.__getitem__(self, self.h(k))
        else:
            v = self.missing(k)
            dict.__setitem__(self, h, v)
            return v

    def __setitem__(self, k, v):
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
        #self.logger.debug(output.yellow("%s (%s) -> %s" % (h, obj, v)))
        return v

    def getAbstractOrDefault(self, obj, default):
        h = self.h(obj)
        if h in self:
            v = self[h]
        else:
            v = default
            if v:
                self[h] = v
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
        keys, values = zip(*(i.split('=', 1) for i in querytoks))
        urltoks.append(tuple(keys))
        urltoks.append(tuple(values))
    return tuple(urltoks)

def formvector(method, action, inputs, hiddens):
    urltoks = [method] + [i if i  else '/' for i in action.path.split('/')]
    query = action.query
    if query:
        querytoks = action.query.split('&')
        keys, values = zip(*(i.split('=', 1) for i in querytoks))
        urltoks.append(tuple(keys))
        urltoks.append(tuple(values))
    if inputs:
        urltoks.append(tuple(inputs))
    if hiddens:
        # TODO hiddens values
        urltoks.append(tuple(hiddens))
    return tuple(urltoks)


def likstreedist(a, b):
    raise NotImplementedError

def linksvector(page):
    linksvector = tuple([tuple(i) for i in page.linkstree.iterlevels()])
    return linksvector


class Classifier(RecursiveDict):

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

class PageMergeException(Exception):
    def __init__(self, msg=None):
        Exception.__init__(self, msg)

class PageClusterer(object):

    class AddToClusterException(PageMergeException):
        def __init__(self, msg=None):
            PageMergeException.__init__(self, msg)

    class AddToAbstractPageException(PageMergeException):
        def __init__(self, msg=None):
            PageMergeException.__init__(self, msg)

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
                # XXX magic number
                # requrire more than X pages in a cluster

                # require some diversity in the dom path in order to create a link
#                self.logger.debug("========", n, len(k), k, level)
                if nleaves >= med and nleaves > 330*(1+1.0/(n+1)) and len(k) > 7.0*math.exp(-n) \
                        and v.depth <= n:
                    v.clusterable = True
                    level.clusterable = False
                else:
                    v.clusterable = False
                self.scanlevels(v, n+1)

    def scanlevelspath(self, level, path, n=0):
        med = median((i.nleaves if hasattr(i, "nleaves") else len(i) for i in level.itervalues()))
        #self.logger.debug(output.green(' ' * n + "MED %f / %d"), med, level.nleaves )
        v = level[path[0]]
        nleaves = v.nleaves if hasattr(v, "nleaves") else len(v)
        #self.logger.debug(output.green(' ' * n + "K %s %d %f"), k, nleaves, nleaves/med)
        if hasattr(v, "nleaves"):
            # XXX magic number
            # requrire more than X pages in a cluster

            # require some diversity in the dom path in order to create a link
            if nleaves >= med and nleaves > 330*(1+1.0/(n+1)) and len(path[0]) > 7.0*math.exp(-n) \
                    and v.depth <= n:
                v.newclusterable = True
                level.newclusterable = False
            else:
                v.newclusterable = False
            self.scanlevelspath(v, path[1:], n+1)
        if not hasattr(level, "clusterable"):
            level.clusterable = False


    def printlevelstat(self, level, n=0):
        med = median((i.nleaves if hasattr(i, "nleaves") else len(i) for i in level.itervalues()))
        self.logger.debug(output.green(' ' * n + "MED %f / %d"), med, level.nleaves )
        for k, v in level.iteritems():
            if hasattr(v, "nleaves"):
                nleaves = v.nleaves
                depth = v.depth
            else:
                nleaves = len(v)
                depth = 1
            if hasattr(v, "nleaves") and v.clusterable:
                self.logger.debug(output.yellow(' ' * n + "K %s %d %f depth %d"), k, nleaves, nleaves/med, depth)
            else:
                self.logger.debug(output.green(' ' * n + "K %s %d %f depth %d"), k, nleaves, nleaves/med, depth)
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
                    abspage = AbstractPage(reduce(lambda a, b: a + b, v.iterleaves()))
                    self.abspages.append(abspage)
                    level.abspages[k] = abspage
                else:
                    self.makeabspagesrecursive(v)
            else:
                abspage = AbstractPage(v)
                self.abspages.append(abspage)
                level.abspages[k] = abspage

    def addabstractpagepath(self, level, reqresp, path):
        v = level[path[0]]
        if hasattr(v, "nleaves"):
            if v.clusterable:
                abspage = level.abspages[path[0]]
                abspage.addPage(reqresp)
                reqresp.response.page.abspage = abspage
            else:
                self.addabstractpagepath(v, reqresp, path[1:])
        else:
            if path[0] not in level.abspages:
                abspage = AbstractPage(v)
                level.abspages[path[0]] = abspage
                self.abspages.append(abspage)
            else:
                abspage = level.abspages[path[0]]
                abspage.addPage(reqresp)
            reqresp.response.page.abspage = abspage

    def levelclustering(self, reqresps):
        classif = Classifier(lambda rr: rr.response.page.linksvector)
        classif.addall(reqresps)
        self.scanlevels(classif)
        self.printlevelstat(classif)
        self.makeabspages(classif)
        self.classif = classif

    def addtolevelclustering(self, reqresp):
        classif = self.classif
        classif.add(reqresp)
        path = classif.featuresextractor(reqresp)
        self.scanlevelspath(classif, path)
        self.printlevelstat(classif)
        self.addabstractpagepath(classif, reqresp, path)



    def getAbstractPages(self):
        return self.abspages

class PairCounter(object):

    def __init__(self, debug=False):
        self._dict = defaultdict(int)
        self.debug = debug

    def add(self, a, b):
        #if self.debug and cond  > 4 and ((a in [0, 20] and b in [0, 29]) or (a in [22, 58] and b in [22, 58])):
        #    pdb.set_trace()
        assert a != b
        if a < b:
            self._dict[(a, b)] += 1
        else:
            self._dict[(b, a)] += 1

    def addSorted(self, a, b):
        assert a < b
        self._dict[(a, b)] += 1

    def addset(self, s):
        ss = sorted(s)
        for i, a in enumerate(ss):
            for b in ss[i+1:]:
                self._dict[(a, b)] += 1

    def addallcombinations(self, bins):
        # XXX HOTSPOT
        for i, bin in enumerate(bins):
            for a in bin:
                for bin2 in bins[i+1:]:
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

    def __iter__(self):
        return iter(self._dict)

    def __contains__(self, o):
        assert False

    def containsSorted(self, a, b):
        return (a, b) in self._dict


PastPage = namedtuple("PastPage", "req page chlink cstate nvisits")
LinkIdx = namedtuple("LinkIdx", "type path params")

class Score(object):

    def __init__(self, counter, req, dist):
        self.counter = counter
        self.req = req
        self.dist = dist
#        if repr(req.absrequest).find("highqual") != -1:
#            pdb.set_trace()
        if not req.reqresp.response.page.links:
            # XXX if a page is a dead end, assume it cannot cause a state
            # transition this could actually happen, but support for handling it
            # is not in place (i.e. we will have a request from state B, but the
            # correponding abstract link in the previous page will only have
            # state A, therefore an asswert will fail
            self.hitscore = self.boost = 0
        else:
            self.hitscore = self.pagehitscore(counter)
            self.boost = self.pagescoreboost(req, dist)
        self.score = self.hitscore + self.boost

    def __str__(self):
        return "%f(%f+%f)" % (self.score, self.hitscore, self.boost)

    def __repr__(self):
        return str(self)

    def __cmp__(self, s):
        return cmp((self.score, self.hitscore), (s.score, s.hitscore))

    @staticmethod
    def pagehitscore(counter):
        if counter[0] >= 3:
            score = -(1-float(counter[1])/counter[0])**2 + 1
        else:
            score = -(1-float((counter[1]+1))/(counter[0]+1))**2 + 1
        return score

    @staticmethod
    def pagescoreboost(req, dist):
        boost = float(LAST_REQUEST_BOOST)
        if req.isPOST:
            boost += POST_BOOST
        elif req.query:
            boost += QUERY_BOOST
        boost /= dist+1
        return boost


class AppGraphGenerator(object):

    class AddToAbstractRequestException(PageMergeException):
        def __init__(self, msg=None):
            PageMergeException.__init__(self, msg)
        pass

    class AddToAppGraphException(PageMergeException):
        def __init__(self, msg=None):
            PageMergeException.__init__(self, msg)

    class MergeLinksTreeException(PageMergeException):
        def __init__(self, msg=None):
            PageMergeException.__init__(self, msg)

    def __init__(self, reqrespshead, abspages, statechangescores):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.reqrespshead = reqrespshead
        self.abspages = abspages
        self.absrequests = None
        self.statechangescores = statechangescores

    def updatepageclusters(self, abspages):
        self.abspages = abspages

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

        self.contextreqmap =  contextreqmap

        # if there are multiple requests that were assigned to the same abstractrequest
        # in the preious mapping, consider assignment final, otherwise do mapping
        # using the full path but not the next and previous pages

        reqmap = AbstractMap(AbstractRequest, lambda x: (x.method, x.path, x.query))

        absrequests = set()

        for ar, rrs in sorted(mappedrequests.iteritems()):
            #if ar.instance == 481:
            #    pdb.set_trace()
            if len(rrs) > 1 and len(set(rr.request.query for rr in rrs)) > 1:
                for rr in rrs:
                    rr.request.absrequest = ar
                    ar.reqresps.append(rr)
                    absrequests.add(ar)
            else:
                for rr in rrs:
                    absreq = reqmap.getAbstractOrDefault(rr.request, ar)
                    rr.request.absrequest = absreq
                    absreq.reqresps.append(rr)
                    absrequests.add(absreq)

        self.mappedrequests = mappedrequests
        self.reqmap = reqmap

        for r in sorted(absrequests):
            self.logger.debug(output.turquoise("%s" % r))

        self.absrequests = absrequests

    def addtorequestclusters(self, rr):
        #if str(rr.request).find("recent.php") != -1:
        #    pdb.set_trace()
        #if maxstate == 47:
        #    pdb.set_trace()
        mappedreq = self.contextreqmap.getAbstract(rr.request)
        reqs = self.mappedrequests[mappedreq]
        if len(reqs) >= 1 and mappedreq not in self.absrequests \
                and len(frozenset(self.reqmap.getAbstractOrDefault(i.request, None) for i in reqs)) > 1 :
            # failing, because we would need to break another cluster
            #pdb.set_trace()
            raise AppGraphGenerator.AddToAbstractRequestException()

        if mappedreq not in self.absrequests:
            absreq = self.reqmap.getAbstract(rr.request)
            self.absrequests.add(absreq)
        else:
            absreq = mappedreq
        rr.request.absrequest = absreq
        absreq.reqresps.append(rr)
        self.logger.debug(output.turquoise("%s" % absreq))


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
            #self.logger.debug(output.red("A %s(%d)\n\t%s " % (currabsreq, id(currabsreq),)
            #    '\n\t'.join([str((s, t)) for s, t in currabsreq.targets.iteritems()])))
            currabsreq.targets[laststate] = PageTarget(currabspage, laststate+1, nvisits=1)
            currpage.reqresp.request.state = laststate

            #self.logger.debug(output.red("B %s(%d)\n\t%s " % (currabsreq, id(currabsreq),)
            #    '\n\t'.join([str((s, t)) for s, t in currabsreq.targets.iteritems()])))
            laststate += 1

            assert currpage.state == -1 or currpage.state == laststate
            currpage.state = laststate

            # keep track of the RequestResponse object per state
            assert not currabspage.statereqrespsmap[laststate]
            currabspage.statereqrespsmap[laststate] = [curr]

            if curr.next:
                if curr.next.backto is not None:
                    currpage = curr.next.backto.response.page
                    currabspage = currpage.abspage
                # find which link goes to the next request in the history
                chosenlink = (i for i, l in currpage.links.iteritems() if curr.next in l.to).next()
                nextabsreq = curr.next.request.absrequest
                #self.logger.debug(output.green("A %s(%d)\n\t%s " % (nextabsreq, id(nextabsreq),)
                #    '\n\t'.join([str((s, t)) for s, t in nextabsreq.targets.iteritems()])))
                # XXX we cannot just use the index for more complex clustering
                #self.logger.debug("%d %s %s %s" % (laststate, chosenlink, currabspage.abslinks, currabspage))
                assert not laststate in currabspage.abslinks[chosenlink].targets
                newtgt = ReqTarget(nextabsreq, laststate, nvisits=1)
                if chosenlink.type == Links.Type.FORM:
                    #chosenlink = LinkIdx(chosenlink.type, chosenlink.dompath,
                    #        chosenlink.href, chosenlink.idx,
                    #        curr.next.request.formparams)
                    # TODO: for now assume that different FORM requests are not clustered
                    assert len(set(tuple(sorted((j[0], tuple(j[1])) for j in i.request.formparams.iteritems())) for i in nextabsreq.reqresps)) == 1
                    tgtdict = {nextabsreq.reqresps[0].request.formparams: newtgt}
                    newtgt = FormTarget(tgtdict, laststate, nvisits=1)
                currabspage.abslinks[chosenlink].targets[laststate] = newtgt
                assert not laststate in currabspage.statelinkmap
                tgt = currabspage.abslinks[chosenlink].targets[laststate]
                if isinstance(tgt, FormTarget):
                    currabspage.statelinkmap[laststate] = currabspage.abslinks[chosenlink].targets[laststate].target[nextabsreq.reqresps[0].request.formparams]
                else:
                    currabspage.statelinkmap[laststate] = currabspage.abslinks[chosenlink].targets[laststate]

            #self.logger.debug(output.green("B %s(%d)\n\t%s " % (nextabsreq, id(nextabsreq),)
            #    '\n\t'.join([str((s, t)) for s, t in nextabsreq.targets.iteritems()])))

            curr = curr.next
            currabsreq = nextabsreq
            cnt += 1

        self.maxstate = laststate
        self.logger.debug("application graph generated in %d steps", cnt)

        return laststate

    def addtoAppGraph(self, reqresp, state):
        self.addtorequestclusters(reqresp)

        curr = reqresp.prev
        currpage = curr.response.page
        currabspage = currpage.abspage

        if curr.next.backto is not None:
            currpage = curr.next.backto.response.page
            currabspage = currpage.abspage

        # find which link goes to the next request in the history
        chosenlinkidx = (i for i, l in currpage.links.iteritems() if curr.next in l.to).next()
        chosenlink = currabspage.abslinks[chosenlinkidx]
        nextabsreq = curr.next.request.absrequest

        if state in chosenlink.targets:
            tgt = chosenlink.targets[state]
            if tgt.nvisits:
                if tgt.target != nextabsreq:
                    # cannot map the page to the current state, need to redo clustering
                    raise AppGraphGenerator.AddToAppGraphException("%s != %s" % (tgt.target, nextabsreq))
                tgt.nvisits += 1
            else:
                chosenlink.targets[state] = ReqTarget(nextabsreq, state, nvisits=1)
        else:
            chosenlink.targets[state] = ReqTarget(nextabsreq, state, nvisits=1)


        curr = curr.next

        currabsreq = nextabsreq
        currpage = curr.response.page
        assert currpage == reqresp.response.page
        currabspage = currpage.abspage

        if state in currabsreq.targets:
            tgt = currabsreq.targets[state]
            if tgt.target != currabspage:
                # cannot map the page to the current state, need to redo clustering
                raise AppGraphGenerator.AddToAppGraphException("%s != %s" % (tgt.target, currabspage))
            tgt.nvisits += 1
        else:
            # if this request is know to change state changes, do not propagate the current state, but recluster
            smallerstates = [(s, t) for s, t in currabsreq.targets.iteritems()
                    if s < state]
            if smallerstates and any(t.transition != s for s, t in smallerstates):
                raise AppGraphGenerator.AddToAppGraphException("new state from %d %s" % (state, currabspage))
            tgt = PageTarget(currabspage, state, nvisits=1)
            currabsreq.targets[state] = tgt

        currabspage.statereqrespsmap[state].append(curr)

        self.logger.debug("page merged into application graph")

        return tgt.transition


    def updateSeenStates(self):
        for ar in self.absrequests:
            for t in ar.targets.itervalues():
                #if t.target.instance == 3297:
                #    pdb.set_trace()
                t.target.seenstates.add(t.transition)

        for ap in self.abspages:
            allstates = set(s for l in ap.abslinks for s in l.targets)
            # allstates empty when we step back from a page
            # allstates has one element less than seenstates when it is the last page seen
            assert not allstates or (len(ap.seenstates - allstates) <= 1 \
                    and not allstates - ap.seenstates), \
                    "%s\n\t%s\n\t%s" % (ap, sorted(ap.seenstates), sorted(allstates))

    def updateSeenStatesForPage(self, reqresp):
        ar = reqresp.request.absrequest
        for t in ar.targets.itervalues():
            #if t.target.instance == 3297:
            #    pdb.set_trace()
            if t.nvisits > 0:
                t.target.seenstates.add(t.transition)

        ap = reqresp.response.page.abspage
        allstates = set(s for l in ap.abslinks for s in l.targets)
        # allstates empty when we step back from a page
        # allstates has one element less than seenstates when it is the last page seen
        assert not allstates or (len(ap.seenstates - allstates) <= 1 \
                and not allstates - ap.seenstates), \
                "%s\n\t%s\n\t%s" % (ap, sorted(ap.seenstates), sorted(allstates))

    def fillMissingRequests(self):

        self.updateSeenStates()

        # create a map from all requests to their AbstractRequest
        # XXX using the following hash function, requests may overlap
        # we should actually have an heuristic to choose the good one...
        self.fillreqmap = CustomDict([(rr.request, ar)
            for ar in sorted(self.absrequests)
            for rr in ar.reqresps], AbstractRequest,
            h=lambda r: (r.method, r.path, r.query))

#        self.buildTmpReqMap()

        for ap in self.abspages:
            self.fillPageMissingRequests(ap)

        self.allabsrequests = set(self.fillreqmap.itervalues())
        # fillreqmap may not include all requests, i.e. in case of multiple
        # requests with same hashed value
        self.allabsrequests |= self.absrequests
        self.absrequests = self.allabsrequests


    def fillMissingRequestsForPage(self, reqresp):

        self.updateSeenStatesForPage(reqresp)

        #self.fillPageMissingRequests(reqresp.response.page.abspage)

        self.fillMissingRequests()


    def buildTmpReqMap(self):
        # build a map from any Request(.method, .path, .query) to a pre-exiting
        # AbstractRequest
        tmpreqmap = AbstractMap(AbstractRequest,
                lambda x: (x.method, x.path, x.query))
        for ar in itertools.chain(self.contextreqmap.itervalues(), self.reqmap.itervalues()):
            hashes = set(tmpreqmap.h(rr.request) for rr in ar.reqresps)
            for h in hashes:
                # there should not be overlap between contextreqmap and reqmap,
                # but not sure about that...
                assert not h in tmpreqmap
                tmpreqmap[h] = ar

        self.tmpreqmap = tmpreqmap


    def fillPageMissingRequests(self, ap):
        allstates = ap.seenstates
        #self.logger.debug("AP", ap, ap.seenstates)
        for idx, l in ap.abslinks.iteritems():
            #if str(ap).find("home") != -1 and str(ap).find("upload") != -1 \
            #        and str(l).find("Redirect") != -1:
            #    pdb.set_trace()
            #self.logger.debug("LINK", l, "TTTT", l.targets)
#            if maxstate >= 45 and str(l).find("view.php?picid=4") != -1:
#                pdb.set_trace()

            newrequest = None  # abstract request for link l
            newrequestbuilt = False # attempt has already been made to build an
                                    # abstract request
            for s in sorted(allstates):
                #if s not in l.targets or l.targets[s].nvisits == 0:
                if s not in l.targets:
                    if not newrequestbuilt:
                        newwebrequest = ap.reqresps[0].response.page.getNewRequest(idx, l)
                        #self.logger.debug("NEWWR %s %d %s %s" % (ap, s, l, newwebrequest))
                        if newwebrequest:
                            request = Request(newwebrequest)
                            #if maxstate >= 11 and str(request).find("upload"):
                            #    pdb.set_trace()
                            if request in self.fillreqmap:
                                newrequest = self.fillreqmap[request]
                            else:
                                newrequest = self.reqmap.getAbstract(request)
                            #newrequest = self.fillreqmap[request]
                            #self.logger.debug("NEWR %s %s\n\t%s" % (request, (request.method, request.path, request.query), newrequest))
                            newrequest.reqresps.append(RequestResponse(request, None))
                        newrequestbuilt = True
                    if newrequest:
                        newtgt = ReqTarget(newrequest, transition=s, nvisits=0)
                        if isinstance(l, AbstractForm):
                            # TODO: for now assume that different FORM requests are not clustered
                            tgtdict = {"": newtgt}
                            newtgt = FormTarget(tgtdict, s, nvisits=0)
                        l.targets[s] = newtgt
                        #self.logger.debug(output.red("NEWTTT %s %d %s %s" % (ap, s, l, newrequest)))
                        #for ss, tt in newrequest.targets.iteritems():
                        #    self.logger.debug(output.purple("\t %s %s" % (ss, tt)))
                else:
                    assert l.targets[s].target is not None

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
            #self.logger.debug(output.darkred("OS %s" % otherstates))
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

    def dropRedundantStateGroupsMild(self, equalstates):
        # removes sets that are subsets of others
        goodequalstates = []
        for es in equalstates:
            for es2 in equalstates:
                if es != es2 and es.issubset(es2):
                    break
            else:
                goodequalstates.append(es)
        return set(goodequalstates)

    def markDifferentStates(self, seentogether, differentpairs):
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

            #self.logger.debug(output.darkred("BINS %s %s" % (' '.join(str(i) for i in sorted(statebins)), ar)))
            #self.logger.debug(output.darkred("EQUALBINS %s" % ' '.join(str(i) for i in sorted(equalstatebins))))

            for sb in statebins:
                seentogether.addset(sb)
            for esb in equalstatebins:
                seentogether.addset(esb)

            differentpairs.addallcombinations(statebins)

        # mark as different states that have seen different concreate pages in the same abstract page
        for ap in self.abspages:
            statelist = defaultdict(list)
            for s, rrs in ap.statereqrespsmap.iteritems():
                for rr in rrs:
                    statelist[rr.response.page.linksvector].append(s)

            if len(statelist) > 1:
                self.logger.debug("DIFFSTATESABSTRACT %s %s", ap, statelist)
                self.logger.debug(output.yellow(str(statelist.values())))
                differentpairs.addallcombinations(statelist.values())


    def propagateDifferestTargetStates(self, differentpairs):
        # XXX HOTSPOT
        for ar in sorted(self.absrequests):
            targetbins = defaultdict(set)
            targetstatebins = defaultdict(set)
            for s, t in ar.targets.iteritems():
                targetbins[t.target].add(t.transition)
                targetstatebins[(t.target, t.transition)].add(s)

            for t, states in sorted(targetbins.items()):
                if len(states) > 1:
                    #targetequalstates = set([StateSet(states)])
                    #self.logger.debug("preTES", targetequalstates, ar, t)

                    statelist = sorted(states)

                    for i, a in enumerate(statelist):
                        for b in statelist[i+1:]:
                            if differentpairs.get(a, b):
                                #self.logger.debug("DIFF %d != %d  ==>   %s != %s" % (a, b, targetstatebins[(t, a)], targetstatebins[(t, b)]))
                                differentpairs.addallcombinations((targetstatebins[(t, a)], targetstatebins[(t, b)]))

    def assignColor(self, assignments, edges, node, maxused):
        neighs = [(n, assignments[n]) for n in edges[node] if n in assignments]
        neighcolors = frozenset(n[1] for n in neighs)
        for i in range(maxused, -1, -1) + [maxused+1]:
            if i not in neighcolors:
                #self.logger.debug("ASSIGN %d %d <%s>" % (node, i, sorted(neighs)))
                assignments[node] = i
                maxused = max(maxused, i)
                break
            else:
                #self.logger.debug("NEIGH %s %d" % (node, i))
                pass
        else:
            assert False
        return maxused


    def colorStateGraph(self, differentpairs, allstates):
        # XXX HOTSPOT
        #ColorNode = namedtuple("ColorNode", "coloredneighbors degree node")

        # allstates should be sorted
        assert allstates[0] == 0

        edges = defaultdict(set)
        for a, b in differentpairs:
            assert a != b
            edges[a].add(b)
            edges[b].add(a)

        #degrees = dict((n, ColorNode(0, len(edges[n]), n)) for n in allstates)

        assignments = {}

        maxused = 0

        for node in allstates:
            assert node not in assignments
            maxused = self.assignColor(assignments, edges, node, maxused)

        return assignments

    def makeset(self, statemap):
        allstatesset = frozenset(statemap)
        allstates = sorted(allstatesset)
        return allstates

    def addtodiffparis(self, allstates, seentogether, differentpairs, exceptions=frozenset()):
        for i, a in enumerate(allstates):
            for b in allstates[i+1:]:
                if a not in exceptions and b not in exceptions and not seentogether.containsSorted(a, b):
                    #self.logger.debug(output.darkred("NEVER %s" % ((a, b), )))
                    differentpairs.addSorted(a, b)

    def markNeverSeenTogether(self, statemap, seentogether, differentpairs, exceptions=frozenset()):

        allstates = self.makeset(statemap)

        self.addtodiffparis(allstates, seentogether, differentpairs, exceptions)

        return allstates

    def createColorBins(self, lenallstates, assignments):
            bins = [[] for i in range(lenallstates)]
            for n, c in assignments.iteritems():
                bins[c].append(n)
            bins = [StateSet(i) for i in bins if i]

            return bins

    def updateStatemapFromColorBins(self, bins, assignments, statemap):
            colormap = [min(nn) for nn in bins]

            #self.logger.debug("CMAP", colormap)

            for n, c in assignments.iteritems():
                statemap[n] = colormap[c]

            #self.logger.debug("SMAP", statemap)

    def refreshStatemap(self, statemap):
        for i in range(len(statemap)):
            statemap[i] = statemap[statemap[i]]

        #self.logger.debug("SMAP", statemap)

        nstates = len(set(statemap))
        return nstates

    def mergeStatesGreedyColoring(self, statemap):

        seentogether = PairCounter()
        differentpairs = PairCounter(False)

        self.markDifferentStates(seentogether, differentpairs)

        allstates = self.markNeverSeenTogether(statemap, seentogether, differentpairs, exceptions=frozenset([statemap[-1]]))
        lenallstates = len(allstates)

        olddifferentpairslen = -1

        while True:

            self.propagateDifferestTargetStates(differentpairs)


            differentpairslen = len(differentpairs)
            assert differentpairslen >= olddifferentpairslen
            if differentpairslen == olddifferentpairslen:
                break
            else:
                olddifferentpairslen = differentpairslen

            #writeColorableStateGraph(allstates, differentpairs)

            assignments = self.colorStateGraph(differentpairs, allstates)

            bins = self.createColorBins(lenallstates, assignments)

            self.updateStatemapFromColorBins(bins, assignments, statemap)

            self.logger.debug(output.darkred("almost final states %s"), sorted(bins))

            differentpairs.addallcombinations(bins)


        nstates = self.refreshStatemap(statemap)

        self.logger.debug(output.darkred("final states %d %s"), nstates, sorted(bins))




    def mergeStates(self, statemap):
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

            #self.logger.debug(output.darkred("BINS %s %s" % (' '.join(str(i) for i in sorted(statebins)), ar)))
            #self.logger.debug(output.darkred("EQUALBINS %s" % ' '.join(str(i) for i in sorted(equalstatebins))))

            for sb in statebins:
                seentogether.addset(sb)
            for esb in equalstatebins:
                seentogether.addset(esb)

            differentpairs.addallcombinations(statebins)


            equalstates = self.addStateBins(statebins, equalstates)
            self.dropRedundantStateGroups(equalstates)

            #self.logger.debug(output.darkred("ES %s" % sorted(equalstates)))


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

                    for t, states in sorted(targetbins.items()):
                        if len(states) > 1:
                            targetequalstates = set([StateSet(states)])
                            #self.logger.debug("preTES", targetequalstates, ar, t)

                            statelist = sorted(states)

                            for i, a in enumerate(statelist):
                                for b in statelist[i+1:]:
                                    if currentdifferentpairs.get(a, b):
                                        #self.logger.debug("DIFF %d != %d  ==>   %s != %s" % (a, b, targetstatebins[(t, a)], targetstatebins[(t, b)]))
                                        differentpairs.addallcombinations((targetstatebins[(t, a)], targetstatebins[(t, b)]))
                                        targetequalstates = self.addStateBins([StateSet([a]), StateSet([b])], targetequalstates)
                                        targetequalstates = self.dropRedundantStateGroupsMild(targetequalstates)

                            self.dropRedundantStateGroups(targetequalstates)
                            #self.logger.debug("TES", targetequalstates, ar, t)

                            startstatebins = set(reduce(lambda a, b: StateSet(a | b), (StateSet(targetstatebins[(t, ts)]) for ts in esb)) for esb in targetequalstates)

                            #self.logger.debug("SSB", startstatebins, ar, t)

                            newequalstates = self.addStateBins(startstatebins, equalstates)
                            self.dropRedundantStateGroups(newequalstates)
                            if newequalstates != equalstates:
                                equalstates = newequalstates
                                again2 = True
                                #self.logger.debug(output.darkred("ES %s" % sorted(equalstates)))

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
                    #self.logger.debug([i for i in zip(containingsetscores, containingsets, reducedcontainingsets)])

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


        for i in range(len(statemap)):
            statemap[i] = equalstatemap[statemap[i]]

        nstates = len(set(statemap))
        self.logger.debug("final states %d", nstates)

    def reqstatechangescore(self, absreq, dist):
#        if str(absreq).find("action.php?action=add") != -1:
#            pdb.set_trace()
        global debugstop
        debugstop = True
        scores = [[(self.pagescore(i, rr.request, dist),
                i, rr.request)
            for i in self.statechangescores.getpathnleaves(
            [rr.request.method] + list(rr.request.urlvector))]
            for rr in absreq.reqresps]
        debugstop = False
        self.logger.debug("SCORES %s", scores)
        return max(max(scores))[0]

    def pagescore(self, counter, req, dist):
        score = Score(counter, req, dist)
        return score


    def splitStatesIfNeeded(self, smallerstates, currreq, currstate, currtarget, statemap, history):
        currmapsto = self.getMinMappedState(currstate, statemap)
        cttransition = self.getMinMappedState(currtarget.transition, statemap)
        for ss in smallerstates:
            ssmapsto = self.getMinMappedState(ss, statemap)
            if ssmapsto == currmapsto:
                sstarget = currreq.targets[ss]
                ssttransition = self.getMinMappedState(sstarget.transition, statemap)
                if sstarget.target == currtarget.target:
                    assert len(sstarget.target.statereqrespsmap[sstarget.transition]) == 1
                    assert len(currtarget.target.statereqrespsmap[currtarget.transition]) == 1
                    if sstarget.target.statereqrespsmap[sstarget.transition][0].response.page.linksvector == currtarget.target.statereqrespsmap[currtarget.transition][0].response.page.linksvector:
                        continue
                    else:
                        #self.logger.debug("DIFFSTATES")
                        pass
                self.logger.debug(output.teal("need to split state for request %s")
                        % currtarget)
                self.logger.debug("\t%d(%d)->%s %d(%d)"
                        % (currstate, currmapsto, currtarget, currtarget.transition, cttransition))
                self.logger.debug("\t%d(%d)->%s %d(%d)"
                        % (ss, ssmapsto, sstarget, sstarget.transition, ssttransition))
                # mark this request as givin hints for state change detection
                currreq.statehints += 1
                pastpages = []
                for (j, (req, page, chlink, laststate)) in enumerate(reversed(history)):
                    if req == currreq or \
                            self.getMinMappedState(laststate, statemap) != currmapsto:
                        self.logger.debug("stopping at %s", req)
                        scores = [(self.reqstatechangescore(pp.req, i), pp)
                            for i, pp in enumerate(pastpages)]
                        self.logger.debug("PASTPAGES %s", '\n'.join(str(i) for i in scores))
                        bestcand = max(scores)[1]
                        self.logger.debug("BESTCAND %s", bestcand)
                        #if str(bestcand).find("review") != -1:
                        #    self.logger.debug(self.statechangescores)
                        #    pdb.set_trace()
                        target = bestcand.req.targets[bestcand.cstate]
#                        if str(bestcand).find("tos") != -1:
#                            pdb.set_trace()
                        self.logger.debug(output.teal("splitting on best candidate %d->%d request %s to page %s"), bestcand.cstate, target.transition, bestcand.req, bestcand.page)
                        assert statemap[target.transition] == bestcand.cstate
                        # this request will always change state
                        for t in bestcand.req.targets.itervalues():
                            if t.transition <= currstate:
                                statemap[t.transition] = t.transition
#                        pdb.set_trace()
                        break
                    # no longer using PastPage.nvisits
                    pastpages.append(PastPage(req, page, chlink, laststate, None))
                else:
                    # if we get hear, we need a better heuristic for splitting state
                    raise RuntimeError()
                currmapsto = self.getMinMappedState(currstate, statemap)
                assert ssmapsto != currmapsto, "%d == %d" % (ssmapsto, currmapsto)

    def minimizeStatemap(self, statemap):
        for i in range(len(statemap)):
            statemap[i] = self.getMinMappedState(i, statemap)

    def reduceStates(self):
        self.logger.debug("reducing state number from %d", self.maxstate)

        # map each state to its equivalent one
        statemap = range(self.maxstate+1)
        lenstatemap = len(statemap)

        currreq = self.headabsreq

        # need history to handle navigatin back; pair of (absrequest,absresponse)
        history = []
        currstate = 0
        tgtchosenlink = None

        while True:
            #self.logger.debug(output.green("************************** %s %s\n%s\n%s") % (currstate, currreq, currreq.targets, statemap))
            currtarget = currreq.targets[currstate]
#            if maxstate >= 75 and str(currreq).find("review") != -1:
#                pdb.set_trace()

            # if any of the previous states leading to the same target caused a state transition,
            # directly guess that this request will cause a state transition
            # this behavior is needed because it might happen that the state transition is not detected,
            # and the state assignment fails
            smallerstates = [(s, t) for s, t in currreq.targets.iteritems()
                    if s < currstate and t.target == currtarget.target]
            if smallerstates and any(statemap[t.transition] != s for s, t in smallerstates):
                #self.logger.debug(output.red("************************** %s %s\n%s") % (currstate, currreq, currreq.targets))
                currstate += 1
            else:
                # find if there are other states that we have already processed that lead to a different target
                smallerstates = sorted([i for i, t in currreq.targets.iteritems() if i < currstate], reverse=True)
                if smallerstates:
                    self.splitStatesIfNeeded(smallerstates, currreq, currstate, currtarget, statemap, history)
                currstate += 1
                statemap[currstate] = currstate-1

            respage = currtarget.target

            history.append((currreq, respage, tgtchosenlink, currstate-1))
            if currstate not in respage.statelinkmap:
                if currstate == self.maxstate:
                    # end reached
                    break
                off = 0
                while currstate not in respage.statelinkmap:
                    off -= 1
                    respage = history[off][1]

            tgtchosenlink = respage.statelinkmap[currstate]
            chosentarget = tgtchosenlink.target

            currreq = chosentarget

        self.minimizeStatemap(statemap)

        nstates = lenstatemap

        self.logger.debug("statemap states %d", nstates)
        #self.logger.debug(statemap)

        self.collapseGraph(statemap)

        #self.logger.debug(statemap)

        self.mergeStateReqRespMaps(statemap)

        self.mergeStatesGreedyColoring(statemap)
        #self.mergeStates(statemap)

        #self.logger.debug(statemap)

        self.collapseGraph(statemap)

        self.mergeStateReqRespMaps(statemap)

        self.assign_reduced_state(statemap)

#        for ar in self.absrequests:
#            if str(ar).find("users/home") != -1:
#                for s, t in ar.targets.iteritems():
#                    if s != t.transition:
#                        pdb.set_trace()

        # return last current state
        return statemap[-1]

    def assign_reduced_state(self, statemap):
        rr = self.reqrespshead
        while rr:
            assert rr.request.state != -1
            assert rr.response.page.state != -1
            rr.request.reducedstate = statemap[rr.request.state]
            rr.response.page.reducedstate = statemap[rr.response.page.state]
            rr = rr.next

    def mergeStateReqRespMaps(self, statemap):
        for ap in self.abspages:
            newstatereqrespmap = defaultdict(list)
            for s, p in ap.statereqrespsmap.iteritems():
                # warning: unsorted
                newstatereqrespmap[statemap[s]].extend(p)
            ap.statereqrespsmap = newstatereqrespmap

    def collapseNode(self, nodes, statemap):
        for aa in nodes:
            statereduce = [(st, statemap[st]) for st in aa.targets]
            for st, goodst in statereduce:
                if st == goodst:
                    aa.targets[goodst].transition = statemap[aa.targets[goodst].transition]
                else:
                    if goodst in aa.targets:
                        if isinstance(aa, AbstractForm):
                            common = frozenset(aa.targets[st].target.keys()) & frozenset(aa.targets[goodst].target.keys())
                            for c in common:
                                assert aa.targets[st].target[c].target == aa.targets[goodst].target[c].target, \
                                        "%d->%s %d->%s" % (st, aa.targets[st], goodst, aa.targets[goodst])
                                assert st == goodst or statemap[aa.targets[goodst].target[c].transition] == statemap[aa.targets[st].target[c].transition], \
                                        "%s\n\t%d->%s (%d)\n\t%d->%s (%d)" \
                                        % (aa, st, aa.targets[st], statemap[aa.targets[st].transition],
                                                goodst, aa.targets[goodst], statemap[aa.targets[goodst].transition])
                            aa.targets[goodst].nvisits += aa.targets[st].nvisits
                            aa.targets[goodst].target.update(aa.targets[st].target)
                        else:
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
            self.collapseNode(ap.abslinks.itervalues(), statemap)

        self.collapseNode(self.absrequests, statemap)


    def markChangingState(self):
        for ar in sorted(self.absrequests):
            changing = any(s != t.transition for s, t in ar.targets.iteritems())
            if changing:
                self.logger.debug("CHANGING %s", ar)
                for rr in ar.reqresps:
                    rr.request.changingstate = True


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
        except TypeError, e:
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
        error = Page(webresponse, error=True)
        response = Response(webresponse, page=error)
        request = Request(webresponse.getWebRequest())
        reqresp = RequestResponse(request, response)
        request.reqresp = reqresp
        error.reqresp = reqresp

        self.updateInternalData(reqresp)
        return self.currreqresp

    def newUnexpectedPage(self, webresponse):
        error = Page(webresponse, error=True)
        response = Response(webresponse, page=error)
        request = Request(webresponse.getWebRequest())
        reqresp = RequestResponse(request, response)
        request.reqresp = reqresp
        error.reqresp = reqresp

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
        if isinstance(e, TypeError):
            response = e.args[0].webResponse
            self.logger.info(output.purple("unexpected page"))
            reqresp = self.newHttpError(response)
        else:
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
        if str(anchor).find("action=add&picid=4") != -1:
            global cond
            cond += 1
        assert anchor.internal.getPage() == self.currreqresp.response.page.internal, \
                "Inconsistency error %s != %s" % (anchor.internal.getPage(), self.currreqresp.response.page.internal)
        try:
            htmlpage = htmlunit.HtmlPage.cast_(anchor.internal.click())
            reqresp = self.newPage(htmlpage)
        except htmlunit.JavaError, e:
            reqresp = self.handleNavigationException(e)
        except TypeError, e:
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

        for k, vv in params.iteritems():
            for i, v in zip(iform.getInputsByName(k), vv):
                if htmlunit.HtmlCheckBoxInput.instance_(i):
                    if v:
                        assert i.getValueAttribute() == v
                        i.setChecked(True)
                    else:
                        i.setChecked(False)
                else:
                    i.setValueAttribute(v)
                self.logger.debug("VALUE %s %s %s" % (i, i.getValueAttribute(), v))

        try:
            # find an element to click in order to submit the form
            # TODO: explore clickable regions in input type=image
            for submittable in Form.SUBMITTABLES:
                try:
                    submitter = iform.getOneHtmlElementByAttribute(*submittable)
                    self.logger.debug("SUBMITTER %s", submitter)
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
            assert params
            reqresp.request.formparams = FormFiller.Params(params)

        except htmlunit.JavaError, e:
            reqresp = self.handleNavigationException(e)
        except TypeError, e:
            reqresp = self.handleNavigationException(e)

        form.to.append(reqresp)
        assert reqresp.request.fullpath.split('?')[0][-len(form.action):] == form.action.split('?')[0], \
                "Unhandled redirect %s !sub %s" % (form.action, reqresp.request.fullpath)
        return reqresp

    def back(self):
        self.logger.debug(output.purple("stepping back"))
        # htmlunit has not "back" function
        if self.currreqresp.prev is None:
            raise Crawler.EmptyHistory()
        # use "backto" rather than "prev", because the page pointed by "prev"
        # might be still page for which we had to call "back()"
        # backto will point to the page having the link that generated the
        # current request
        self.currreqresp = self.currreqresp.backto if self.currreqresp.backto \
                else self.currreqresp.prev
        return self.currreqresp

def linkweigh(link, nvisits, othernvisits=0, statechange=0):
        if link.type == Links.Type.ANCHOR:
            if link.hasquery:
                dist = Dist((statechange, 0, 0, 0, 0, nvisits, othernvisits, 0, 0, 0, 0))
            else:
                dist = Dist((statechange, 0, 0, 0, 0, 0, 0, nvisits, othernvisits, 0, 0))
        elif link.type == Links.Type.FORM:
            if link.isPOST:
                dist = Dist((statechange, nvisits, othernvisits, 0, 0, 0, 0, 0, 0, 0, 0))
            else:
                dist = Dist((statechange, 0, 0, nvisits, othernvisits, 0, 0, 0, 0, 0, 0))
        elif link.type == Links.Type.REDIRECT:
            dist = Dist((statechange, 0, 0, 0, 0, 0, 0, 0, 0, nvisits, othernvisits))
        else:
            assert False, link
        return dist

class Dist(object):
    LEN = 11

    def __init__(self, v=None):
        """ The content of the vector is as follow:
        (state changing,
         POST form, GET form, anchor w/ params, anchor w/o params, redirect
         )
        the first elelement can be wither 0 or 1, whether the request proved to trigger a state change or not
        the other elements are actually doubled: one value for the number of visits in the current state, and
        one value for the number of visits in the other states
        only one pair of element can be != 0
        """
        self.val = tuple(v) if v else tuple([0]*Dist.LEN)
        assert len(self.val) == Dist.LEN

    def __add__(self, d):
        return Dist(a+b for a, b in zip(self.val, d.val))

    def __cmp__(self, d):
        return cmp(self.normalized, d.normalized)

    def __str__(self):
        return "%s[%s]" % (self.val, self.normalized)

    def __repr__(self):
        return str(self)

    def __reversed__(self):
        return reversed(self.val)

    @lazyproperty
    def normalized(self):
        #n = (self.val[0], reduce(lambda a, b: a*10 + b, self.val[1:]))
        penalty = sum(self.val)/5
        ret = (self.val[0], penalty, self.val[1:])
        #self.logger.debug("NORM %s %s" % (self.val, ret))
        return ret

    def __getitem__(self, i):
        return self.val[i]

class FormField(object):

    Type = Constants("CHECKBOX", "TEXT", "HIDDEN", "OTHER")

    def __init__(self, type, name, value=None):
        self.type = type
        self.name = name
        self.value = value

    def __str__(self):
        return self._str

    def __repr__(self):
        return self._str

    @lazyproperty
    def _str(self):
        return "FormField(%s %s=%s)" % (self.type, self.name, self.value)



class FormFiller(object):

    class Params(defaultdict):

        def __init__(self, init={}):
            defaultdict.__init__(self)
            self.update(init)

        def __hash__(self):
            return hash(tuple(sorted((i[0], tuple(i[1])) for i in self.iteritems())))

    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.forms = {}

    def add(self, k):
        self.forms[tuple(sorted(i for i in k.iterkeys()))] = k

    def __getitem__(self, k):
        return self.forms[tuple(sorted([i.name for i in k if i.name]))]

    def randfill(self, keys):
        self.logger.debug("random filling from")
        res = defaultdict(list)
        for f in keys:
            if f.type == FormField.Type.CHECKBOX:
                value = rng.choice([f.value, ''])
            elif f.type == FormField.Type.HIDDEN:
                value = f.value
            else:
                value = ''
            res[f.name].append(value)
        return res


class ParamDefaultDict(defaultdict):

    def __init__(self, factory):
        defaultdict.__init__(self)
        self._factory = factory

    def __missing__(self, key):
        return self._factory(key)

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
                for i, aa in page.links.iteritems():
                    if i.type == Links.Type.ANCHOR:
                        return i
                assert False
            else:
                self.logger.debug("abstract page not availabe, and no anchors")
                return None

        # find unvisited anchor
        for i, aa in abspage.absanchors.links.iteritems():
            if i.type == Links.Type.ANCHOR:
                if self.state not in aa.targets or aa.targets[self.state].nvisits == 0:
                    return i
        return None

    def linkcost(self, abspage, linkidx, link, state):
        if maxstate >= 453 and \
                str(linkidx).find("add_comment") != -1:
                pdb.set_trace()
        statechange = 0
        tgt = None
        # must be > 0, as it will also mark the kond of query in the dist vector
        nvisits = 1
        # count visits done for this link and the subsequent request the current
        # state
        if state in link.targets:
            tgt = link.targets[state]
            nvisits += tgt.nvisits
            # also add visit count for the subsequent request
            if linkidx.params != None:
                targets = tgt.target[linkidx.params].target.targets
            else:
                targets = tgt.target.targets
            if state in targets:
                reqtarget = targets[state]
                nvisits += reqtarget.nvisits
                statechange = reqtarget.transition != state

        # must be > 0, as it will also mark the kond of query in the dist
        # vector, in case nvisits == 0
        othernvisits = 1
        for s, t in link.targets.iteritems():
            if t.transition != s:
                # a link should never change state, it is the request that does it!
                assert False
                statechange = 1
            if tgt:
                # we need to sum only the visits to requests that have the same target
                # otherwise we might skip exploring them for some states
                if t.target == tgt.target:
                    othernvisits += t.nvisits
        # also add visit count for the subsequent request in different states
        if tgt and not isinstance(tgt, FormTarget):
            for s, t in tgt.target.targets.iteritems():
                if s != state:
                    othernvisits += t.nvisits
                # if the request has ever caused a change in state, consider it
                # state chaning even if the state is not the same. This helps
                # Dijstra stay away from potential state changing requests
                if s != t.transition:
                    statechange = True


        assert link.type == linkidx.type
        # XXX statechange is not set correctly
        # divide othernvisits by 3, so it weights less and for the first 3
        # visists it is 1
        othernvisits = int(math.ceil(othernvisits/3.0))
        dist = linkweigh(link, nvisits, othernvisits, statechange)

        return dist

    def addUnvisisted(self, dist, head, state, headpath, unvlinks, candidates, priority, new=False):
        costs = [(self.linkcost(head, i, j, state), i) for (i, j) in unvlinks]
#        self.logger.debug("COSTS", costs)
        #self.logger.debug("NCOST", [i[0].normalized for i in costs])
        mincost = min(costs)
        path = list(reversed([PathStep(head, mincost[1], state)] + headpath))
        if priority == 0:
            # for startndard priority, select unvisited links disregarding the
            # distance, provided they do not change state
            newdist = (dist[0], mincost[0], dist)
        else:
            # for non-standard priority (-1), use the real distance
            newdist = dist
        self.logger.debug("found unvisited link %s (/%d) in page %s (%d) dist %s->%s (pri %d, new=%s)",
                mincost[1], len(unvlinks), head, state, dist, newdist, priority, new)
#        if maxstate >= 158 and str(mincost[1]).find("picid'), (u'add', u'5") != -1:
#            pdb.set_trace()
#        if mincost[1].path[1:] in debug_set:
#            pdb.set_trace()
        heapq.heappush(candidates, Candidate(priority, newdist, path))

    def findPathToUnvisited(self, startpage, startstate, recentlyseen):
        # recentlyseen is the set of requests done since last state change
        heads = [(Dist(), startpage, startstate, [])]
        seen = set()
        candidates = []
        while heads:
            dist, head, state, headpath = heapq.heappop(heads)
            self.logger.debug(output.yellow("H %s %s %s %s" % (dist, head, state, headpath)))
#            if maxstate >= 297 and (str(head).find(r"view.php\?picid=") != -1 or
#                    str(head).find(r"action=add\?picid=") != -1 or
#                    str(head).find(r"recent.php") != -1):
#                pdb.set_trace()
            if (head, state) in seen:
                continue
            seen.add((head, state))
            #head.abslinks.printInfo()
            unvlinks_added = False
            for idx, link in head.abslinks.iteritems():
                if link.skip:
                    continue
                newpath = [PathStep(head, idx, state)] + headpath
#                if maxstate >= 297 and str(link).find(r"recent.php") != -1:
#                    pdb.set_trace()
                #self.logger.debug("state %s targets %s" % (state, link.targets))
                if state in link.targets:
                    linktgt = link.targets[state]
                    if isinstance(linktgt, FormTarget):
                        nextabsrequests = [(p, i.target) for p, i in linktgt.target.iteritems()]
                    else:
                        nextabsrequests = [(None, linktgt.target)]
                    for formparams, nextabsreq in nextabsrequests:
                        #self.logger.debug("NEXTABSREQ", nextabsreq)
#                        if maxstate >= 111 and str(nextabsreq).find("review"):
#                            pdb.set_trace()
                        if state == startstate and nextabsreq.statehints and \
                                not nextabsreq.changingstate and \
                                not nextabsreq in recentlyseen:
                            # this is a page known to be revealing of possible state change
                            # go there first, priority=-1 !
                            formidx = LinkIdx(idx.type, idx.path, formparams)
                            self.addUnvisisted(dist, head, state, headpath,
                                    [(formidx, link)], candidates, -1)
                        # the request associated to this link has never been
                        # made in the current state, add it as unvisited
                        if state not in nextabsreq.targets:
                            formidx = LinkIdx(idx.type, idx.path, formparams)
                            self.addUnvisisted(dist, head, state, headpath,
                                    [(formidx, link)], candidates, 0)
                            continue
                        # do not put request in the heap, but just go for the next abstract page
                        tgt = nextabsreq.targets[state]
                        assert tgt.target
                        if (tgt.target, tgt.transition) in seen:
                            continue
                        formidx = LinkIdx(idx.type, idx.path, formparams)
                        newdist = dist + self.linkcost(head, formidx, link, state)
                        #self.logger.debug("TGT %s %s %s" % (tgt, newdist, nextabsreq))
#                        if maxstate >= 297 and str(tgt.target).find(r"recent.php") != -1:
#                            pdb.set_trace()
                        heapq.heappush(heads, (newdist, tgt.target, tgt.transition, newpath))
                else:
                    if not unvlinks_added:
                        unvlinks = head.abslinks.getUnvisited(state)
#                        self.logger.debug("UNVLINKS", "\n\t".join(str(i) for i in unvlinks))
                        if unvlinks:
                            self.addUnvisisted(dist, head, state, headpath, unvlinks, candidates, 0, True)
                            unvlinks_added = True
                        else:
                            # TODO handle state changes
                            raise NotImplementedError
        nvisited = len(set(i[0] for i in seen))
        if candidates:
            self.logger.debug("CAND %s", candidates)
            return candidates[0].path, nvisited
        else:
            return None, nvisited


    def getEngineAction(self, linkidx):
        if linkidx.type == Links.Type.ANCHOR:
            engineaction = Engine.Actions.ANCHOR
        elif linkidx.type == Links.Type.FORM:
            engineaction = Engine.Actions.FORM
        elif linkidx.type == Links.Type.REDIRECT:
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
            # if there is only one REDIRECT, follow it
            abspage = reqresp.response.page.abspage
            linksiter = abspage.abslinks.iteritems()
            firstlink = None
            try:
                # extract the first link
                firstlink = linksiter.next()
                # next like will raise StopIteration if there is only 1 link
                linksiter.next()
            except StopIteration:
                # if we have at least one link, and it is the only one, and it is a redirect, 
                # then follow it
                if firstlink and firstlink[0].type == Links.Type.REDIRECT:
                    self.logger.debug("page contains only a rediect, following it")
                    return (Engine.Actions.REDIRECT, reqresp.response.page.links[firstlink[0]])

            recentlyseen = set()
            rr = reqresp
            found = False
            while rr:
                destination = rr.response.page.abspage
#                if str(rr.response.page.abspage).find("tos") != -1:
#                    pdb.set_trace()
                probablyseen = None
                for s, t in rr.request.absrequest.targets.iteritems():
                    if (t.target, t.transition) == (destination, self.state):
                        if s == self.state:
                            # state transition did not happen here
                            assert not probablyseen or \
                                    probablyseen == rr.request.absrequest
                            probablyseen = rr.request.absrequest
                        else:
                            # XXX we are matching only of tragte and anot on
                            # source state, so it might detect that there was a
                            # state transition when there was none. it should
                            # not be an issue at this stage, but could it create
                            # an inifinite loop because it keep going to the
                            # "state-change revealing" pages?
                            found = True
                            break
                else:
                    # we should always be able to find the destination page in the target object
                    assert probablyseen
                    recentlyseen.add(probablyseen)
                if found:
                    break
                rr = rr.prev
                #self.logger.debug("RRRR", rr)
            self.logger.debug("last changing request %s", rr)
            #self.logger.debug("recentlyseen", recentlyseen)
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
                #self.logger.debug(nexthop)
                assert nexthop.abspage == reqresp.response.page.abspage
                assert nexthop.state == self.state
                debug_set.add(nexthop.idx.path[1:])
                return (self.getEngineAction(nexthop.idx), reqresp.response.page.links[nexthop.idx])
            elif self.ag and float(nvisited)/len(self.ag.abspages) > 0.9:
                # we can reach almost everywhere form the current page, still we cannot find unvisited links
                # very likely we visited all the pages or we can no longer go back to some older states anyway
                return (Engine.Actions.DONE, )

        # no path found, step back
        return (Engine.Actions.BACK, )

    def submitForm(self, form):
        formkeys = form.elems
        self.logger.debug("form keys %s", formkeys)
        try:
            params = self.formfiller[formkeys]
        except KeyError:
            params = self.formfiller.randfill(formkeys)
        return self.cr.submitForm(form, params)

    def tryMergeInGraph(self, reqresp):
        if self.pc:
            self.logger.info(output.red("try to merge page into current state graph"))
            try:
                pc = self.pc
                ag = self.ag
                pc.addtolevelclustering(reqresp)
                ag.updatepageclusters(pc.getAbstractPages())
                newstate = ag.addtoAppGraph(reqresp, self.state)
                ag.fillMissingRequestsForPage(reqresp)
            except PageClusterer.AddToClusterException:
                self.logger.info(output.red("Level clustering changed, reclustering"))
                raise
            except PageClusterer.AddToAbstractPageException:
                self.logger.info(output.red("Unable to add page to current abstract page, reclustering"))
                raise
            except AppGraphGenerator.AddToAbstractRequestException:
                self.logger.info(output.red("Unable to add page to current abstract request, reclustering"))
                raise
            except AppGraphGenerator.AddToAppGraphException, e:
                #self.logger.debug("STATEHINT %s", reqresp.request)
                reqresp.request.statehint = True
                self.logger.info(output.red("Unable to add page to current application graph, reclustering. %s" % e))
                raise
            except PageMergeException, e:
                raise RuntimeError("uncaught PageMergeException %s" % e)
        else:
            self.logger.info(output.red("first execution, start clustering"))
            raise PageMergeException()

        return newstate


    def main(self, urls):
        self.pc = None
        self.ag = None
        cr = Crawler()
        self.cr = cr
        global maxstate

        for cnt, url in enumerate(urls):
            self.logger.info(output.purple("starting with URL %d/%d %s"), cnt+1, len(urls), url)
            maxstate = -1
            reqresp = cr.open(url)
            self.logger.debug(output.red("TREE %s" % (reqresp.response.page.linkstree,)))
            self.logger.debug(output.red("TREEVECTOR %s" % (reqresp.response.page.linksvector,)))
            statechangescores = None
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
                self.logger.debug(output.red("TREE %s" % (reqresp.response.page.linkstree,)))
                self.logger.debug(output.red("TREEVECTOR %s" % (reqresp.response.page.linksvector,)))
                if not nextAction[0] == Engine.Actions.BACK:
                    try:
                        if nextAction[0] == Engine.Actions.FORM:
                            # do not even try to merge forms
                            raise PageMergeException()
                        self.state = self.tryMergeInGraph(reqresp)
                        maxstate += 1
                        self.logger.debug(output.green("estimated current state %d (%d)"), self.state, maxstate)
                    except PageMergeException:
                        self.logger.info("need to recompute graph")
                        pc = PageClusterer(cr.headreqresp)
                        self.logger.debug(output.blue("AP %s" % '\n'.join(str(i) for i in pc.getAbstractPages())))
                        ag = AppGraphGenerator(cr.headreqresp, pc.getAbstractPages(), statechangescores)
                        maxstate = ag.generateAppGraph()
                        self.state = ag.reduceStates()
                        ag.markChangingState()
                        global debugstop
                        debugstop = True
                        def check(x):
                            l = list(x)
                            v = reduce(lambda a, b: (a[0] + b[0], (a[1] + b[1])), l, (0, 0))
                            v = (v[0], v[1]/2.0)
                            return v
                        statechangescores = RecursiveDict(nleavesfunc=lambda x: x,
                                #nleavesaggregator=lambda x: (1, mean(list(AppGraphGenerator.pagehitscore(i) for i in x))/2))
                                #nleavesaggregator=lambda x: (1, mean(list(float(i[1])/i[0] for i in x))/2))
                                nleavesaggregator=check)
                        debugstop = False
                        rr = cr.headreqresp
                        while rr:
                            changing = 1 if rr.request.reducedstate != rr.response.page.reducedstate else 0
                            #if changing:
                            #    self.logger.debug(output.turquoise("%d(%d)->%d(%d) %s %s" % (rr.request.reducedstate,)
                            #        rr.request.state, rr.response.page.reducedstate, rr.response.page.state,
                            #        rr.request, rr.response))
                            statechangescores.setapplypath([rr.request.method] + list(rr.request.urlvector),
                                    (1, changing), lambda x: (x[0] + 1, x[1] + changing))
                            rr.request.state = -1
                            rr.response.page.state = -1
                            rr = rr.next
                        self.logger.debug(output.turquoise("statechangescores"))
                        self.logger.debug(output.turquoise("%s" % statechangescores))

                        self.logger.debug(output.green("current state %d (%d)"), self.state, maxstate)
                        #global cond
                        #if cond >= 2: cond += 1
                        ag.fillMissingRequests()
                        for r in sorted(ag.absrequests):
                            self.logger.debug(output.turquoise("POSTMISSING %s" % r))

                        self.logger.debug(output.blue("AP %s" % '\n'.join(str(i) + "\n\t" + "\n\t".join(str(j) for j in i.statereqrespsmap.iteritems()) for i in pc.getAbstractPages())))
                        self.pc = pc
                        self.ag = ag

#                        if maxstate >= 196:
#                            pdb.set_trace()

                nextAction = self.getNextAction(reqresp)
                assert nextAction

                if wanttoexit:
                    return
                self.writeStateDot()

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
                    #self.logger.debug("LINK %s => %s" % (p, t.target))
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

    def writeStateDot(self):
        if not self.ag:
            self.logger.debug("not creating state DOT graph")
            return

        self.logger.info("creating state DOT graph")
        dot = pydot.Dot()
        nodes = ParamDefaultDict(lambda x: pydot.Node(str(x)))

        for p in self.ag.allabsrequests:
            for s, t in p.targets.iteritems():
                if s != t.transition:
                    name = str('\\n'.join(p.requestset))
                    edge = pydot.Edge(nodes[s], nodes[t.transition])
                    edge.set_label(name)
                    dot.add_edge(edge)

        self.logger.debug("%d DOT nodes", len(nodes))

        for n in nodes.itervalues():
            dot.add_node(n)

        dot.write_ps('stategraph.ps')
        #dot.write_pdf('graph.pdf')
        with open('stategraph.dot', 'w') as f:
            f.write(dot.to_string())
        self.logger.debug("DOT state graph written")


def writeColorableStateGraph(allstates, differentpairs):

    dot = pydot.Dot(graph_type='graph')
    nodes = {}
    for s in allstates:
        node = pydot.Node(str(s))
        nodes[s] = node
        dot.add_node(node)


    for s, t in differentpairs:
        edge = pydot.Edge(nodes[s], nodes[t])
        dot.add_edge(edge)

    dot.write_ps('colorablestategraph.ps')
    #dot.write_pdf('graph.pdf')
    with open('colorablestategraph.dot', 'w') as f:
        f.write(dot.to_string())


if __name__ == "__main__":
    import sys
    import getopt
    optslist, args = getopt.getopt(sys.argv[1:], "l:")
    opts = dict(optslist) if optslist else {}
    try:
        handler = logging.FileHandler(opts['-l'], 'w')
        logging.basicConfig(level=logging.DEBUG, filename=opts['-l'],
                filemode='w')
    except KeyError:
        logging.basicConfig(level=logging.DEBUG)

    ff = FormFiller()
    login = {'username': ['ludo'], 'password': ['duuwhe782osjs']}
    ff.add(login)
    login = {'user': ['ludo'], 'pass': ['ludo']}
    ff.add(login)
    login = {'userId': ['temp01'], 'password': ['Temp@67A%'], 'newURL': [""], "datasource": ["myyardi"], 'form_submit': [""]}
    ff.add(login)
    e = Engine(ff)
    try:
        e.main(args)
    except:
        import traceback
        traceback.print_exc()
        pdb.post_mortem()
    finally:
        e.writeStateDot()
        #e.writeDot()
        pass


# vim:sw=4:et:
