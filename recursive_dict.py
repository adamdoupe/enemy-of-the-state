import itertools
from collections import defaultdict, deque

from lazyproperty import lazyproperty

class RecursiveDict(defaultdict):
    def __init__(self, nleavesfunc=lambda x: 1 if x else 0, nleavesaggregator=sum):
        # when counting leaves, apply this function to non RecursiveDict objects
        self.nleavesfunc = nleavesfunc
        self.nleavesaggregator = nleavesaggregator
        self._nleaves = None
        # XXX no more general :(
        self.abspages = {}
        self.value = None

    def __missing__(self, key):
        v = RecursiveDict(nleavesfunc=self.nleavesfunc, nleavesaggregator=self.nleavesaggregator)
#        if str(key).find("logout") != -1 and debugstop:
#            pdb.set_trace()
        self.__setitem__(key, v)
        return v

    @property
    def nleaves(self):
        if self._nleaves is None:
            iters = (i.nleaves for i in self.itervalues())
            if self.value:
                iters = itertools.chain(
                    iters, iter([self.nleavesfunc(self.value)]))
            self._nleaves = self.nleavesaggregator(iters)
        assert self._nleaves
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
                yield i.nleaves


    def setpath(self, path, value):
        assert value
        i = self
        # invalidate leaves count
        i._nleaves = None
        for p in path[:-1]:
            i = i[p]
            # invalidate leaves count
            i._nleaves = None
#        if str(path[-1]).find("logout") != -1 and debugstop:
#            pdb.set_trace()
        i[path[-1]].value = value

    def applypath(self, path, func):
        """ apply func to the node pointed to by path """
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
        assert i[path[-1]]

    def setapplypathvalue(self, path, value, func):
        """ apply func to the value of the node pointed to by path,
        or assign value if the path does not exist """
        assert value
        i = self
        # invalidate leaves count
        i._nleaves = None
        for p in path[:-1]:
            i = i[p]
            # invalidate leaves count
            i._nleaves = None
#        if str(path[-1]).find("logout") != -1 and debugstop:
#            pdb.set_trace()
        if path[-1] in i and i[path[-1]].value is not None:
            i[path[-1]].value = func(i[path[-1]].value)
        else:
            i[path[-1]].value = value
        assert i[path[-1]].value

    def iterlevels(self):
        if self:
            queue = deque([(self,)])
            while queue:
                l = queue.pop()
                levelkeys = []
                children = []
                for c in l:
                    if c.value:
                        levelkeys.append(self.nleavesfunc(c.value))
                    levelkeys.extend(c.iterkeys())
                    children.extend(c.itervalues())
                if children:
                    queue.append(children)
                #self.logger.debug("LK", len(queue), levelkeys, queue)
                yield levelkeys

    def iterleaves(self):
        if self.value:
            yield self.value
        for c in self.itervalues():
            for i in c.iterleaves():
                yield i

    def iteridxleaves(self):
        for k, v in defaultdict.iteritems(self):
            if v.value:
                yield ((k, ), v.value)
            for kk, vv in v.iteridxleaves():
                yield (tuple([k] + list(kk)), vv)

    @lazyproperty
    def depth(self):
        return 1+max([0] + [i.depth for i in self.itervalues()])

    def __str__(self, level=0):
        out = ""
        if self.value:
            out += " %s" % (self.value, )
        for k, v in sorted(self.items()):
            out += "\n%s%s:"  % ("\t"*level, k)
            out += "%s%s" % (v.nleaves, v.__str__(level+1))
        return out

    def equals(self, o):
        return len(self) == len(o) \
                and self.value == o.value \
                and set(self.keys()) == set(o.keys()) \
                and all(self[k].equals(o[k]) if hasattr(self[k], 'equals') else 
                        self[k] == o[k] for k in self.iterkeys())
