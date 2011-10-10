from lazyproperty import lazyproperty

class StateSet(frozenset):

    @lazyproperty
    def _str(self):
        return "[%s]" % ', '.join(str(i) for i in sorted(self))

    def __str__(self):
        return self._str

    def __repr__(self):
        return str(self)
