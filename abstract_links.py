from anchor import AbstractAnchor
from recursive_dict import RecursiveDict
from link import Link, Links
from anchor import AbstractAnchor
from redirect import AbstractRedirect
from form import AbstractForm
from custom_exceptions import MergeLinksTreeException

class AbstractLinks(object):

    def __init__(self, linktrees):
        self.linkstree = RecursiveDict()
        for t, c in [(Links.Type.ANCHOR, AbstractAnchor),
                (Links.Type.FORM, AbstractForm),
                (Links.Type.REDIRECT, AbstractRedirect)]:
            if any(t in lt for lt in linktrees):
                self.buildtree(self.linkstree, t, [lt[t] for lt in linktrees], c)
        #pdb.set_trace()

    def buildtree(self, level, key, ltval, c):
        assert all(isinstance(i, list) for i in ltval) or \
                all(not isinstance(i, list) for i in ltval)
        if isinstance(ltval[0], list):
            assert False
            # we have reached the leaves without encountering a cluster
            # create an abstract object with all the objects in all the leaves
            # ltval is a list of leaves, ie a list of lists containing abstractlinks
            level[key] = c(i for j in ltval for i in j)
        if not ltval[0]:
            # we have reached the leaves without encountering a cluster
            # create an abstract object with all the objects in all the leaves
            # ltval is a list of leaves, ie a list of lists containing abstractlinks
            assert all(j.value for j in ltval)
            level[key].value = c(i for j in ltval for i in j.value)
        else: # we have descendants
            assert ltval[0].value is None
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
                level[key].value = c(lll for l in ltval for ll in l.iterleaves()
                        for lll in ll)

    def tryMergeLinkstree(self, pagelinkstree):
        # check if the linkstree pagelinkstree matches the current linkstree for
        # the current AbstractPage. If not, raise an exception and go back to
        # reclustering
        for t, c in [(Links.Type.ANCHOR, AbstractAnchor),
                (Links.Type.FORM, AbstractForm),
                (Links.Type.REDIRECT, AbstractRedirect)]:
            if t in pagelinkstree or t in self.linkstree:
                self.tryMergeLinkstreeRec(pagelinkstree[t], self.linkstree[t])

    def tryMergeLinkstreeRec(self, pagelinkstree, baselinkstree):
        if isinstance(baselinkstree, RecursiveDict) and \
                isinstance(pagelinkstree, RecursiveDict):
            # make sure the trees have the same keys
            pagekeys = set(pagelinkstree.keys())
            basekeys = set(baselinkstree.keys())
            if pagekeys != basekeys:
                # there is difference, abort and go back reclustering
                #pdb.set_trace()
                raise MergeLinksTreeException()
            for k in pagekeys:
                # descend into tree
                self.tryMergeLinkstreeRec(pagelinkstree[k], baselinkstree[k])
        elif isinstance(baselinkstree, AbstractLink) and \
                isinstance(pagelinkstree, list):
            pass
        else:
            pdb.set_trace()
            raise MergeLinksTreeException()


    def __getitem__(self, linkidx):
        idx = [linkidx.type] + list(linkidx.path)
        i = self.linkstree
        for p in idx:
            if p in i:
                i = i[p]
            else:
                break
        assert i.value and not i
        return i.value

    def __iter__(self):
        return self.linkstree.iterleaves()

    def itervalues(self):
        return iter(self)

    def iteritems(self):
        for p, l in self.linkstree.iteridxleaves():
            if isinstance(l, AbstractForm):
                # return a form multiple times, iterating over all form parameters we have used so far
                params = frozenset(b for a in l.targets.itervalues() for b in a.target.iterkeys())
                if params:
                    for pr in params:
                        yield (Link.LinkIdx(p[0], p[1:], pr), l)
                else:
                    yield (Link.LinkIdx(p[0], p[1:], None), l)

            else:
                yield (Link.LinkIdx(p[0], p[1:], None), l)

    def getUnvisited(self, state):
        #self.printInfo()
        # unvisited if we never did the request for that state
        # third element of the tuple are the form parameters
        return [(i, l) for i, l in self.iteritems() if not l.skip \
                and (state not in l.targets
                    or not state in l.targets[state].target.targets)]

    def equals(self, l):
        return self.linkstree.equals(l.linkstree)
