from form_filler import FormFiller
from page import AbstractPage
from abstract_request import AbstractRequest

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
    """ FormTarget.target is a dictionary containing ReqTarget objects as values
    and form parameters as keys """

    class MultiDict(object):
        """ The purpos of the MultiDict object is allowing searchin for a
        key (state) in the ReqTarget.tagets dictionaries of all values of the
        FormTarget.target dictiornay """

        def __init__(self, outer):
            self.outer = outer

        def __contains__(self, k):
            return any(k in i.target.targets for i in self.outer.target.itervalues())

    class Dict(dict):

        def __init__(self, outer, d):
            self.outer = outer
            self.targets = FormTarget.MultiDict(outer)
            assert all(isinstance(i, FormFiller.Params) for i in d)
            dict.__init__(self, d)

        def __setitem__(self, k, v):
            assert isinstance(k, FormFiller.Params)
            assert isinstance(v, ReqTarget)
            # a ReqTarget should never cause a state transition
            assert self.outer.transition == v.tranistion
            return dict.__setitem__(k, v)


    def __init__(self, target, transition, nvisits=0):
        assert isinstance(target, dict)
        Target.__init__(self, target, transition, nvisits)
        self._target = FormTarget.Dict(self, target)

    def get_target(self):
        return self._target

    def set_target(self, target):
        assert isinstance(target, dict)
        self._target = FormTarget.Dict(self, target)

    target = property(get_target, set_target)

