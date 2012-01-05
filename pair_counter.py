from collections import defaultdict

class PairCounter(object):

    def __init__(self, debug=False):
        self._dict = defaultdict(int)
        self.debug = debug

    def add(self, a, b):
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
