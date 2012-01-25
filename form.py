import urlparse
import htmlunit

from lazyproperty import lazyproperty
from ignore_urls import filterIgnoreUrlParts
from vectors import formvector
from form_field import FormField
from link import Link, AbstractLink, Links
from utils import all_same

class Form(Link):
    SUBMITTABLES = [("input", "type", "submit"),
                    ("input", "type", "image"),
                    ("button", "type", "submit")]
    GET, POST = ("GET", "POST")

    @lazyproperty
    def method(self):
        methodattr = self.internal.getMethodAttribute().upper()
        if not methodattr:
              methodattr = "GET"
        assert methodattr in ("GET", "POST")
        return methodattr

    @lazyproperty
    def action(self):
        action = self.internal.getActionAttribute()
        action = filterIgnoreUrlParts(action)
        return action

    @lazyproperty
    def actionurl(self):
        return urlparse.urlparse(self.action)

    @lazyproperty
    def _str(self):
        return "Form(%s %s)" % (self.method, self.action)

    @lazyproperty
    def linkvector(self):
        return formvector(self.method, self.actionurl, self.inputnames, self.hiddennames)

    @lazyproperty
    def elemnames(self):
        return [i.name for i in self.elems]

    @lazyproperty
    def elems(self):
        return self.inputs + self.textareas + self.selects + self.submittables

    def buildFormField(self, e):
        tag = e.getTagName().upper()
        if tag == FormField.Tag.INPUT:
            etype = e.getAttribute('type').lower()
            name = e.getAttribute('name')
            value = e.getAttribute('value')
            if etype == "hidden":
                type = FormField.Type.HIDDEN
            elif etype == "text":
                type = FormField.Type.TEXT
            elif etype == "password":
                type = FormField.Type.PASSWORD
            elif etype == "checkbox":
                type = FormField.Type.CHECKBOX
            elif etype == "submit":
                type = FormField.Type.SUBMIT
            elif etype == "image":
                type = FormField.Type.IMAGE
            elif etype == "button":
                type = FormField.Type.BUTTON
            elif etype == "file":
                type = FormField.Type.FILE
            else:
                type = FormField.Type.OTHER
        elif tag == FormField.Tag.TEXTAREA:
            type = None
            name = e.getAttribute('name')
            textarea = htmlunit.HtmlTextArea.cast_(e)
            value = textarea.getText()
        elif tag == FormField.Tag.BUTTON and \
                e.getAttribute('type').upper() == FormField.Type.SUBMIT:
            type = FormField.Type.SUBMIT
            name = e.getAttribute('name')
            value = e.getAttribute('value')
        else:
            raise RuntimeError("unexpcted form field tag %s" % tag)

        # TODO: properly support it
        attrs = list(e.getAttributesMap().keySet())
        for a in attrs:
            if a.startswith("on") or a == "target":
                e.removeAttribute(a)

        return FormField(tag, type, name, value)


    @lazyproperty
    def inputnames(self):
        return [i.name for i in self.inputs]

    @lazyproperty
    def hiddennames(self):
        return [i.name for i in self.hiddens]

    @lazyproperty
    def textareanames(self):
        return [i.name for i in self.textareas]

    @lazyproperty
    def selectnames(self):
        return [i.name for i in self.selectnames]

    @lazyproperty
    def inputs(self):
        return [self.buildFormField(e)
                for e in (htmlunit.HtmlElement.cast_(i)
                    for i in self.internal.getHtmlElementsByTagName('input'))
                if e.getAttribute('type').lower() not in ["hidden", "button", "submit"] ]

    @lazyproperty
    def hiddens(self):
        return [self.buildFormField(e)
                for e in (htmlunit.HtmlElement.cast_(i)
                    for i in self.internal.getHtmlElementsByTagName('input'))
                if e.getAttribute('type').lower() == "hidden"]

    @lazyproperty
    def textareas(self):
        return [self.buildFormField(e)
                for e in (htmlunit.HtmlElement.cast_(i)
                    for i in self.internal.getHtmlElementsByTagName('textarea'))]

    @lazyproperty
    def selects(self):
        # TODO
        return []

    @lazyproperty
    def submittables(self):
        result = []
        for submittable in Form.SUBMITTABLES:
            try:
                submitters = self.internal.getElementsByAttribute(*submittable)

                result.extend(self.buildFormField(
                    htmlunit.HtmlElement.cast_(i)) for i in submitters)

            except htmlunit.JavaError, e:
                javaex = e.getJavaException()
                if not htmlunit.ElementNotFoundException.instance_(javaex):
                    raise
                continue
        return result

class AbstractForm(AbstractLink):

    def __init__(self, forms):
        if not isinstance(forms, list):
            forms = list(forms)
        AbstractLink.__init__(self, forms)
        self.forms = forms
        self.methods = set(i.method for i in forms)
        self.actions = set(i.action for i in forms)
        self.type = Links.Type.FORM
        self._elemset = None

    def update(self, forms):
        self.forms = forms
        self.methods = set(i.method for i in forms)
        self.actions = set(i.action for i in forms)
        self._elemset = None

    @property
    def _str(self):
        return "AbstractForm(targets=%s)" % (self.targets)

    def equals(self, f):
        return (self.methods, self.actions) == (f.methods, f.actions)

    @lazyproperty
    def isPOST(self):
        return Form.POST in self.methods

    @lazyproperty
    def action(self):
        # XXX multiple hrefs not supported yet
        assert len(self.actions) == 1
        return iter(self.actions).next()

    @property
    def elemset(self):
        if self._elemset is None:
            elemnamesets = [frozenset(i.elemnames) for i in self.forms]
            assert all_same(elemnamesets)
            self._elemset = frozenset(self.forms[0].elems)
        return self._elemset
