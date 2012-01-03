import logging
import output
import math

from custom_exceptions import PageMergeException
from utils import median
from buckets import Buckets
from classifier import Classifier
from page import AbstractPage

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

    def linktorealpages(self):
        for ap in self.abspages:
            for rr in ap.reqresps:
                rr.response.page.abspage = ap
        self.logger.debug("%d abstract pages generated", len(self.abspages))

    def scanlevels(self, level, n=0):
        for k, v in level.iteritems():
            nleaves = v.nleaves
            if v: # if there are descendants
                # XXX magic number
                # require more than X pages in a cluster

                # require some diversity in the dom path in order to create a link
                med = median((i.nleaves for i in v.itervalues()))
                if nleaves > med and nleaves > 15*(1+1.0/(n+1)) and len(k) > 7.0*math.exp(-n) \
                        and v.depth <= 6 and n >= 3:
                    v.clusterable = True
                    level.clusterable = False
                else:
                    v.clusterable = False
                self.scanlevels(v, n+1)

    # XXX TODO: Merge this with scanlevels since they're the same algorithm
    # Also, newclusterable isn't used anywhere, which means that this doesn't really do anything
    def scanlevelspath(self, level, path, n=0):
        v = level[path[0]]
        nleaves = v.nleaves if hasattr(v, "nleaves") else len(v)
        if v: # if there are descendants
            # XXX magic number
            # requrire more than X pages in a cluster

            # require some diversity in the dom path in order to create a link
            med = median((i.nleaves for i in v.itervalues()))
            if nleaves > med and nleaves > 15*(1+1.0/(n+1)) and len(path[0]) > 7.0*math.exp(-n) \
                    and v.depth <= 6 and n >= 3:
                v.newclusterable = True
                level.newclusterable = False
            else:
                v.newclusterable = False
            self.scanlevelspath(v, path[1:], n+1)
        if not hasattr(level, "clusterable"):
            level.clusterable = False


    def printlevelstat(self, level, n=0):
        med = median((i.nleaves for i in level.itervalues()))
        self.logger.debug(output.green(' ' * n + "MED %f nleaves=%d len(k)=%d depth=%d"),
                                       med,
                                       level.nleaves,
                                       len(level.keys()),
                                       level.depth)
        for k, v in level.iteritems():
            nleaves = v.nleaves
            depth = v.depth
            if v and v.clusterable:
                self.logger.debug(
                        output.yellow(
                            ' ' * n + "K %s nleaves=%d r=%.2f depth=%d"),
                        k,
                        nleaves,
                        float(nleaves)/med,
                        depth)
            else:
                self.logger.debug(
                        output.green(
                            ' ' * n + "K %s nleaves=%d r=%.2f depth=%d"),
                        k,
                        nleaves,
                        float(nleaves)/med,
                        depth)
            if v:
                self.printlevelstat(v, n+1)

    def makeabspages(self, classif):
        self.abspages = []
        self.makeabspagesrecursive(classif)
        self.linktorealpages()

    def makeabspagesrecursive(self, level):
        for k, v in level.iteritems():
            if v:
                if v.clusterable:
                    abspage = AbstractPage(reduce(lambda a, b: a + b, v.iterleaves()))
                    self.abspages.append(abspage)
                    level.abspages[k] = abspage
                else:
                    self.makeabspagesrecursive(v)
            else:
                abspage = AbstractPage(v.value)
                self.abspages.append(abspage)
                level.abspages[k] = abspage

    # This function is used after adding a new page to the tree
    def addabstractpagepath(self, level, reqresp, path):
        v = level[path[0]]
        if v:
            if v.clusterable:
                abspage = level.abspages[path[0]]
                abspage.addPage(reqresp)
                reqresp.response.page.abspage = abspage
            else:
                self.addabstractpagepath(v, reqresp, path[1:])
        else:
            if path[0] not in level.abspages:
                abspage = AbstractPage(v.value)
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

