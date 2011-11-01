import re
import output

from lazyproperty import lazyproperty
from collections import namedtuple

class Link(object):
    LinkIdx = namedtuple("LinkIdx", "type path params")
    
    xpathsimplifier = re.compile(r"\[[^\]]*\]")

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


import logging
import pdb

from constants import Constants
from recursive_dict import RecursiveDict
from randgen import RandGen

class Links(object):
    Type = Constants("ANCHOR", "FORM", "REDIRECT")
    rng = RandGen()

    def __init__(self, anchors=[], forms=[], redirects=[]):
        self.logger = logging.getLogger(self.__class__.__name__)
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
            linkstree.setapplypathvalue(("<EMPTY>", ), [None], lambda x: x+[None])
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
        if Links.Type.ANCHOR in self.linkstree:
            return self.linkstree[Links.Type.ANCHOR].nleaves
        else:
            return 0

    def nForms(self):
        if Links.Type.FORM in self.linkstree:
            return self.linkstree[Links.Type.FORM].nleaves
        else:
            return 0

    def nRedirects(self):
        if Links.Type.REDIRECT in self.linkstree:
            return self.linkstree[Links.Type.REDIRECT].nleaves
        else:
            return 0

    def __len__(self):
        return self.nAnchors() + self.nForms() + self.nRedirects()

    def __nonzero__(self):
        return self.nAnchors() != 0 or self.nForms() != 0 or self.nRedirects() != 0

    @lazyproperty
    def _str(self):
        return "Links(%s, %s, %s)" % (self.nAnchors(), self.nForms(), self.nRedirects())

    def __str__(self):
        return self._str

    def __getitem__(self, linkidx):
        idx = [linkidx.type] + list(linkidx.path)
        val = self.linkstree.getpath(idx)
        assert val.nleaves == len(list(val.iterleaves()))
        if val.nleaves > 1:
            self.logger.debug(output.red("******** PICKING ONE *******"))
            ret = Links.rng.choice([i for i in val.iterleaves()])
        if not val.value:
            self.logger.debug(output.red("******** INCOMPLETE PATH %s *******"), linkidx)
        ret = val.iterleaves().next()
        assert not val.value or val.value == ret
        assert isinstance(ret, list)
        if len(ret) > 1:
            self.logger.debug(output.red("******** PICKING ONE *******"))
            pdb.set_trace()
        return ret[0]

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
            yield (Link.LinkIdx(p[0], p[1:], None), l[0])

from utils import DebugDict

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

