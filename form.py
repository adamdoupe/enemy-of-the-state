import urlparse
import com.gargoylesoftware.htmlunit as htmlunit

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
        return formvector(self.method, self.actionurl, self.elemnames, self.hiddennames)

    @lazyproperty
    def elemnames(self):
        return [i.name for i in self.elems]

    @lazyproperty
    def elems(self):
        # extension of elements by lost inputs due to incorrect html code
        return self.inputs + self.textareas + self.selects + self.submittables + self.lost_inputs

    def buildFormField(self, e):
        tag = e.getTagName().upper()
        if tag == FormField.Tag.INPUT:
            etype = e.getAttribute('type').lower()
            name = e.getAttribute('name').encode('ascii', 'ignore')
            value = e.getAttribute('value').encode('ascii', 'ignore')
            # value of placeholder is irrelevant for FormFilling, so a boolean sufficients
            placeholder = e.hasAttribute("placeholder")
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
            name = e.getAttribute('name').encode('ascii', 'ignore')
            textarea = e
            value = textarea.getText()
            # new html element attribute
            placeholder = False
        elif tag == FormField.Tag.BUTTON and \
                e.getAttribute('type').upper() == FormField.Type.SUBMIT:
            type = FormField.Type.SUBMIT
            name = e.getAttribute('name').encode('ascii', 'ignore')
            value = e.getAttribute('value').encode('ascii', 'ignore')
            # new html element attribute
            placeholder = False
        else:
            raise RuntimeError("unexpcted form field tag %s" % tag)

        # TODO: properly support it
        attrs = list(e.getAttributesMap().keySet())
        for a in attrs:
            if a.startswith("on") or a == "target":
                e.removeAttribute(a)

        return FormField(tag, type, name, value, placeholder)


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
        # getHtmlElementsByTagName changed to a htmlunit 2.36 method
        return [self.buildFormField(e)
                for e in (i
                    for i in self.internal.getElementsByTagName('input'))
                if e.getAttribute('type').lower() not in ["hidden", "button", "submit"] ]

    @lazyproperty
    def lost_inputs(self):
        # in case of incorrect HTML code
        """This method will find the form elements that may be submitted but that do not belong to the forms children in the DOM.
        See also http://htmlunit.sourceforge.net/apidocs/com/gargoylesoftware/htmlunit/html/HtmlForm.html"""
        return [self.buildFormField(e)
                for e in (i
                          for i in self.internal.getLostChildren())]

    @lazyproperty
    def hiddens(self):
        # getHtmlElementsByTagName changed to a htmlunit 2.36 method
        return [self.buildFormField(e)
                for e in (i
                    for i in self.internal.getElementsByTagName('input'))
                if e.getAttribute('type').lower() == "hidden"]

    @lazyproperty
    def textareas(self):
        # getHtmlElementsByTagName changed to a htmlunit 2.36 method
        return [self.buildFormField(e)
                for e in (i
                    for i in self.internal.getElementsByTagName('textarea'))]

    @lazyproperty
    def selects(self):
        # TODO
        return []

    @lazyproperty
    def submittables(self):
        result = []
        for submittable in Form.SUBMITTABLES:
            try:
                # also lost children can be submittable
                submitters = self.internal.getElementsByAttribute(*submittable) + [i for i in self.internal.getLostChildren() if i.getAttribute("type") == "submit"]

                result.extend(self.buildFormField(i) for i in submitters)

            except java.lang.Exception, e:
                javaex = e
                if not isinstance(javaex, htmlunit.ElementNotFoundException):
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
