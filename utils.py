""" This module contains some utility functions.
"""

def string_or_list_into_list(s_or_l):
    """ Turns a string into a list, but if given a list will return the list.
    """
    if isinstance(s_or_l, str):
        return [s_or_l]
    else:
        return s_or_l

def all_same(iterable):
    it = iter(iterable)
    try:
        first = it.next()
    except StopIteration:
        return True
    return all(i == first for i in it)

def median(l):
    s = sorted(l)
    ln = len(s)
    if ln % 2 == 0:
        return float(s[ln/2]+s[ln/2-1])/2
    else:
        return float(s[ln/2])


class DebugDict(dict):

    def __init__(self, parent):
        self.parent = parent
        dict.__init__(self)

    def __setitem__(self, k, v):
        dict.__setitem__(self, k, v)


class CustomDict(dict):

    def __init__(self, items, missing, h=hash):
        dict.__init__(self)
        self.h = h
        self.missing = missing
        for (k, v) in items:
            self[k] = v

    def __getitem__(self, k):
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

