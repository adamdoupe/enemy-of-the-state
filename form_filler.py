import logging
import utils
from collections import defaultdict

from lazyproperty import lazyproperty
from randgen import RandGen
from form_field import FormField

class FormFiller(object):

    rng = RandGen()

    class Params(defaultdict):

        def __init__(self, init={}):
            defaultdict.__init__(self, list)
            self.update(init)
            self.submitter = None

        def __hash__(self):
            vals = sorted((i[0], tuple(i[1])) for i in self.iteritems())
            vals.append(str(self.submitter))
            return hash(tuple(vals))

        def __str__(self):
            return "Params(%s, %s)" % (self.submitter, self.items())

        def __repr__(self):
            return str(self)

        @lazyproperty
        def sortedkeys(self):
            keys = (key for key, vals in self.iteritems() for i in range(len(vals)) if key)
            return tuple(sorted(keys))

    class ValuesList(list):

        @lazyproperty
        def generator(self):
            while True:
                values = self[:]
                FormFiller.rng.shuffle(values)
                for p in values:
                    yield p

        def getnext(self):
            #pdb.set_trace()
            return self.generator.next()

    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.forms = defaultdict(FormFiller.ValuesList)
        self.namedparams = defaultdict()

    def add_named_params(self, names, values):
        """ Add a named parameter to the FormFiller.
        name can be a string or a list of strings
        values can be a string of a list of strings        
        """
        assert values and names
        name_list = utils.string_or_list_into_list(names)
        values_list = utils.string_or_list_into_list(values)
        for name in name_list:
            if name in self.namedparams:
                self.namedparams[name].extend(values_list)
            else:
                self.namedparams[name] = values_list[:]


    def add(self, k):
        self.forms[k.sortedkeys].append(k)

    def get(self, k, form):
        keys = tuple(sorted([i.name for i in k if i.name]))
        if keys not in self.forms:
            for p in [self.emptyfill(k, submitter=s)
                        for s in form.submittables] + \
                    [self.randfill(k, submitter=s)
                        for s in form.submittables] + \
                    [self.randfill(k, samepass=True, submitter=s)
                        for s in form.submittables]:
                # record this set of form parameters for later use
                if p is not None:
                    self.add(p)
        return self.forms[keys]

    def emptyfill(self, keys, submitter=None):
        self.logger.debug("empty filling")
        res = FormFiller.Params()
        for f in keys:
            if f.type == FormField.Type.HIDDEN:
                value = f.value
            else:
                res[f.name].append("")
        res.submitter = submitter
        return res

    def randfill(self, keys, samepass=False, submitter=None):
        self.logger.debug("random filling from (samepass=%s)", samepass)
        res = FormFiller.Params()
        password = None
        multiplepass = False
        for f in keys:
            value = ''
            if f.tag == FormField.Tag.INPUT:
                if f.type == FormField.Type.CHECKBOX:
                    value = FormFiller.rng.choice([f.value, ''])
                elif f.type == FormField.Type.HIDDEN:
                    value = f.value
                elif f.type == FormField.Type.TEXT:
                    if f.name in self.namedparams:
                        value = self.namedparams[f.name]
                    else:
                        value = FormFiller.rng.getWords()
                elif f.type == FormField.Type.PASSWORD:
                    if password is None or not samepass:
                        password = FormFiller.rng.getPassword()
                    else:
                        multiplepass = True
                    value = password
            elif f.tag == FormField.Tag.TEXTAREA:
                if f.name in self.namedparams:
                    value = self.namedparams[f.name]
                else:
                    value = FormFiller.rng.getWords(10)
            res[f.name].extend(utils.string_or_list_into_list(value))
        if samepass and not multiplepass:
            # if we were asked to use the same password, but there were no muitple password fields, return None
            return None
        res.submitter = submitter
        return res

    def getrandparams(self, keys, form):
        if not keys:
            return FormFiller.Params()
        values = self.get(keys, form)
        if not values:
            return FormFiller.Params()
        return values.getnext()


