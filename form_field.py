from constants import Constants
from lazyproperty import lazyproperty

class FormField(object):

    Tag = Constants("INPUT", "BUTTON", "TEXTAREA")

    Type = Constants("CHECKBOX", "TEXT", "PASSWORD", "HIDDEN", "SUBMIT", "IMAGE", "FILE", "BUTTON", "OTHER")

    def __init__(self, tag, type, name, value=None):
        self.tag = tag
        self.type = type
        self.name = name
        self.value = value

    def __str__(self):
        return self._str

    def __repr__(self):
        return self._str

    @lazyproperty
    def _str(self):
        return "FormField(%s %s %s=%s)" % (self.tag, self.type, self.name, self.value)

    def __hash__(self):
        return self.hash

    @lazyproperty
    def hash(self):
        return hash(self._str)

    def __cmp__(self, o):
        return cmp(self.hash, o.hash)

