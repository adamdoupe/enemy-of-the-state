#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
#

import os, sys, platform, shutil, _jcc, py_compile

from cpp import PRIMITIVES, INDENT, HALF_INDENT
from cpp import cppname, cppnames, typename
from cpp import line, signature, find_method, split_pkg, sort
from cpp import Modifier
from _jcc import findClass
from config import INCLUDES, CFLAGS, DEBUG_CFLAGS, LFLAGS, SHARED

python_ver = '%d.%d.%d' %(sys.version_info[0:3])
if python_ver < '2.4':
    from sets import Set as set


RESULTS = { 'boolean': 'Py_RETURN_BOOL(%s);',
            'byte': 'return PyString_FromStringAndSize((char *) &%s, 1);',
            'char': 'return PyUnicode_FromUnicode((Py_UNICODE *) &%s, 1);',
            'double': 'return PyFloat_FromDouble((double) %s);',
            'float': 'return PyFloat_FromDouble((double) %s);',
            'int': 'return PyInt_FromLong((long) %s);',
            'long': 'return PyLong_FromLongLong((PY_LONG_LONG) %s);',
            'short': 'return PyInt_FromLong((long) %s);',
            'java.lang.String': 'return j2p(%s);' }

CALLARGS = { 'boolean': ('O', '(%s ? Py_True : Py_False)', False),
             'byte': ('O', 'PyString_FromStringAndSize((char *) &%s, 1)', True),
             'char': ('O', 'PyUnicode_FromUnicode((Py_UNICODE *) &%s, 1)', True),
             'double': ('d', '(double) %s', False),
             'float': ('f', '(float) %s', False),
             'int': ('i', '(int) %s', False),
             'long': ('L', '(long long) %s', False),
             'short': ('i', '(int) %s', False),
             'java.lang.String': ('O', 'env->fromJString((jstring) %s)', True) }


def parseArgs(params, current):

    def signature(cls):
        array = ''
        while cls.isArray():
            array += '['
            cls = cls.getComponentType()
        clsName = cls.getName()
        if cls.isPrimitive():
            return array + PRIMITIVES[clsName]
        if clsName == 'java.lang.String':
            return array + 's'
        if clsName == 'java.lang.Object':
            return array + 'o'
        return array + 'k'

    def checkarg(cls):
        while cls.isArray():
            cls = cls.getComponentType()
        if (cls.isPrimitive() or
            cls.getName() in ('java.lang.String', 'java.lang.Object')):
            return ''
        return ', %s::initializeClass' %(typename(cls, current, False))

    def callarg(cls, i):
        return ', &a%d' %(i)

    return (''.join([signature(param) for param in params]),
            ''.join([checkarg(param) for param in params]),
            ''.join([callarg(params[i], i) for i in xrange(len(params))]))


def construct(out, indent, cls, inCase, constructor, names):

    if inCase:
        line(out, indent, '{')
        indent += 1

    params = constructor.getParameterTypes()
    count = len(params)

    for i in xrange(count):
        line(out, indent, '%s a%d%s;',
             typename(params[i], cls, False), i,
             not params[i].isPrimitive() and '((jobject) NULL)' or '')
    line(out, indent, '%s object((jobject) NULL);', cppname(names[-1]))

    line(out)
    if count:
        line(out, indent, 'if (!parseArgs(args, "%s"%s%s))',
             *parseArgs(params, cls))
        line(out, indent, '{')
        indent += 1

    line(out, indent, 'INT_CALL(object = %s(%s));',
         cppname(names[-1]), ', '.join(['a%d' %(i) for i in xrange(count)]))
    line(out, indent, 'self->object = object;')
    if inCase:
        line(out, indent, 'break;')

    if count:
        indent -= 1
        line(out, indent, '}')

    if inCase:
        indent -= 1
        line(out, indent, '}')


def rpartition(string, sep):

    if python_ver >= '2.5.0':
        return string.rpartition(sep)
    else:
        parts = split_pkg(string, sep)
        if len(parts) == 1:
            return ('', '', parts[0])
        return (parts[0], sep, parts[1])


def fieldValue(cls, value, fieldType):

    if fieldType.isArray():
        fieldType = fieldType.getComponentType()
        if fieldType.isArray():
            result = 'JArray<jobject>(%s->this$).wrap(NULL)'
        elif fieldType.isPrimitive():
            result = '%s->wrap()'
        elif fieldType.getName() == 'java.lang.String':
            result = 'JArray<jstring>(%s->this$).wrap()'
        else:
            parts = rpartition(typename(fieldType, cls, False), '::')
            result = 'JArray<jobject>(%%s->this$).wrap(%s%st_%s::wrap_jobject)' %(parts)

    elif fieldType.getName() == 'java.lang.String':
        result = 'j2p(*%s)'

    elif not fieldType.isPrimitive():
        parts = rpartition(typename(fieldType, cls, False), '::')
        result = '%s%st_%s::wrap_Object(*%%s)' %(parts)

    else:
        return value

    return result %(value)


def returnValue(cls, returnType, value):

    result = RESULTS.get(returnType.getName())
    if not result:
        if returnType.isArray():
            returnType = returnType.getComponentType()
            depth = 1
            while returnType.isArray():
                returnType = returnType.getComponentType()
                depth += 1
            if depth > 1:
                result = 'return JArray<jobject>(%s.this$).wrap(NULL);'
            elif returnType.isPrimitive():
                result = 'return %s.wrap();'
            elif returnType.getName() == 'java.lang.String':
                result = 'return JArray<jstring>(%s.this$).wrap();'
            else:
                returnName = typename(returnType, cls, False)
                parts = rpartition(returnName, '::')
                result = 'return JArray<jobject>(%%s.this$).wrap(%s%st_%s::wrap_jobject);' %(parts)
        else:
            returnName = typename(returnType, cls, False)
            parts = rpartition(returnName, '::')
            result = 'return %s%st_%s::wrap_Object(%%s);' %(parts)

    return result %(value)


def call(out, indent, cls, inCase, method, names, cardinality, isExtension):

    if inCase:
        line(out, indent, '{')
        indent += 1

    name = method.getName()
    modifiers = method.getModifiers()
    params = method.getParameterTypes()
    returnType = method.getReturnType()
    count = len(params)

    for i in xrange(count):
        line(out, indent, '%s a%d%s;',
             typename(params[i], cls, False), i,
             not params[i].isPrimitive() and '((jobject) NULL)' or '')
    returnName = returnType.getName()
    if returnName != 'void':
        line(out, indent, '%s result%s;',
             typename(returnType, cls, False),
             not returnType.isPrimitive() and '((jobject) NULL)' or '')
        result = 'result = '
    else:
        result = ''

    if cardinality and (count or not inCase):
        s = cardinality > 1 and 's' or ''
        line(out)
        if isExtension and name == 'clone' and Modifier.isNative(modifiers):
            line(out, indent, 'if (arg)')
        else:
            line(out, indent, 'if (!parseArg%s(arg%s, "%s"%s%s))',
                 s, s, *parseArgs(params, cls))
        line(out, indent, '{')
        indent += 1

    name = cppname(name)
    if Modifier.isStatic(modifiers):
        line(out, indent, 'OBJ_CALL(%s%s::%s(%s));',
             result, '::'.join(cppnames(names)), name,
             ', '.join(['a%d' %(i) for i in xrange(count)]))
    else:
        line(out, indent, 'OBJ_CALL(%sself->object.%s(%s));',
             result, name, ', '.join(['a%d' %(i) for i in xrange(count)]))

    if isExtension and name == 'clone' and Modifier.isNative(modifiers):
        line(out)
        line(out, indent, '%s object(result.this$);', typename(cls, cls, False))
        line(out, indent, 'if (PyObject_TypeCheck(arg, &FinalizerProxy$$Type) &&')
        line(out, indent, '    PyObject_TypeCheck(((t_fp *) arg)->object, self->ob_type))')
        line(out, indent, '{')
        line(out, indent + 1, 'PyObject *_arg = ((t_fp *) arg)->object;')
        line(out, indent + 1, '((t_JObject *) _arg)->object = object;')
        line(out, indent + 1, 'Py_INCREF(_arg);')
        line(out, indent + 1, 'object.pythonExtension((jlong) (Py_intptr_t) (void *) _arg);')
        line(out, indent + 1, 'Py_INCREF(arg);')
        line(out, indent + 1, 'return arg;')
        line(out, indent, '}')
        line(out, indent, 'return PyErr_SetArgsError("%s", arg);' %(name))
    elif returnName != 'void':
        line(out, indent, returnValue(cls, returnType, 'result'))
    else:
        line(out, indent, 'Py_RETURN_NONE;')
    if cardinality and (count or not inCase):
        indent -= 1
        line(out, indent, '}')

    if inCase:
        indent -= 1
        line(out, indent, '}')


def methodargs(methods, superMethods):
        
    if len(methods) == 1 and methods[0].getName() not in superMethods:
        count = len(methods[0].getParameterTypes())
        if count == 0:
            return '', '', 0
        elif count == 1:
            return ', PyObject *arg', ', arg', 1

    return ', PyObject *args', ', args', 2


def jniname(cls):
    
    if cls.isPrimitive():
        name = cls.getName()
        if name != 'void':
            name = 'j' + name
    else:
        name = 'jobject'

    return name


def jniargs(params):

    count = len(params)
    decls = ', '.join(['%s a%d' %(jniname(params[i]), i)
                       for i in xrange(count)])
    if decls:
        return ', ' + decls

    return ''


def extension(env, out, indent, cls, names, name, count, method):

    line(out, indent, 'jlong ptr = jenv->CallLongMethod(jobj, %s::mids$[%s::mid_pythonExtension_%s]);',
         cppname(names[-1]), cppname(names[-1]), env.strhash('()J'))
    line(out, indent, 'PyObject *obj = (PyObject *) (Py_intptr_t) ptr;')

    if name == 'pythonDecRef':
        line(out)
        line(out, indent, 'if (obj != NULL)')
        line(out, indent, '{')
        line(out, indent + 1, 'jenv->CallVoidMethod(jobj, %s::mids$[%s::mid_pythonExtension_%s], (jlong) 0);',
             cppname(names[-1]), cppname(names[-1]), env.strhash('(J)V'))
        line(out, indent + 1, 'env->finalizeObject(jenv, obj);')
        line(out, indent, '}')
        return

    line(out, indent, 'PythonGIL gil(jenv);')

    returnType = method.getReturnType()
    returnName = returnType.getName()
    if returnName != 'void':
        line(out, indent, '%s value%s;',
             typename(returnType, cls, False),
             not returnType.isPrimitive() and '((jobject) NULL)' or '')

    sigs = []
    decrefs = []
    args = []
    i = 0
    for param in method.getParameterTypes():
        typeName = param.getName()
        if typeName in CALLARGS:
            sig, code, decref = CALLARGS[typeName]
        elif param.isArray():
            param = param.getComponentType()
            if param.isPrimitive():
                code = 'JArray<j%s>(%%s).wrap()' %(param.getName())
            elif param.isArray():
                code = 'JArray<jobject>(%s).wrap(NULL)'
            elif param.getName() == 'java.lang.String':
                code = 'JArray<jstring>(%s).wrap()'
            else:
                parts = rpartition(typename(param, cls, False), '::')
                code = 'JArray<jobject>(%%s).wrap(%s%st_%s::wrap_jobject)' %(parts)
            sig, decref = 'O', True
        elif param.getName() == 'java.lang.String':
            sig, code, decref = 'O', 'j2p(%%s))', True
        else:
            parts = rpartition(typename(param, cls, False), '::')
            sig, code, decref = 'O', '%s%st_%s::wrap_Object(%s%s%s(%%s))' %(parts*2), True
        if sig == 'O':
            line(out, indent, 'PyObject *o%d = %s;', i, code %('a%d' %(i)))
            args.append('o%d' %(i))
        else:
            args.append(code %('a%d' %(i)))
        sigs.append(sig)
        decrefs.append(decref)
        i += 1

    args = ', '.join(args)
    if args:
        args = ', ' + args
    line(out, indent, 'PyObject *result = PyObject_CallMethod(obj, "%s", "%s"%s);',
         name, ''.join(sigs), args)
    i = 0
    for decref in decrefs:
        if decref:
            line(out, indent, 'Py_DECREF(o%d);', i)
        i += 1
    line(out, indent, 'if (!result)')
    line(out, indent + 1, 'throwPythonError();')
    if returnName == 'void':
        line(out, indent, 'else')
        line(out, indent + 1, 'Py_DECREF(result);')
    else:
        signature, check, x = parseArgs([returnType], cls)
        line(out, indent, 'else if (parseArg(result, "%s"%s, &value))',
             signature, check)
        line(out, indent, '{')
        line(out, indent + 1, 'throwTypeError("%s", result);', name)
        line(out, indent + 1, 'Py_DECREF(result);')
        line(out, indent, '}')
        line(out, indent, 'else')
        line(out, indent, '{')
        if not returnType.isPrimitive():
            line(out, indent + 1, 'jobj = jenv->NewLocalRef(value.this$);')
        line(out, indent + 1, 'Py_DECREF(result);')
        if returnType.isPrimitive():
            line(out, indent + 1, 'return value;')
        else:
            line(out, indent + 1, 'return jobj;')
        line(out, indent, '}')
        line(out)
        if returnType.isPrimitive():
            line(out, indent, 'return (j%s) 0;', returnName)
        else:
            line(out, indent, 'return (jobject) NULL;')


def python(env, out_h, out, cls, superCls, names, superNames,
           constructors, methods, protectedMethods, fields, instanceFields,
           mapping, sequence, rename, declares, typeset, excludes, moduleName):

    line(out_h)
    line(out_h, 0, '#include <Python.h>')
    line(out_h)

    indent = 0
    for name in names[:-1]:
        line(out_h, indent, 'namespace %s {', cppname(name))
        indent += 1
    line(out_h, indent, 'extern PyTypeObject %s$$Type;', names[-1])

    line(out_h)
    line(out_h, indent, 'class t_%s {', names[-1])
    line(out_h, indent, 'public:')
    line(out_h, indent + 1, 'PyObject_HEAD')
    line(out_h, indent + 1, '%s object;', cppname(names[-1]))
    line(out_h, indent + 1, 'static PyObject *wrap_Object(const %s&);',
         cppname(names[-1]))
    line(out_h, indent + 1, 'static PyObject *wrap_jobject(const jobject&);')
    line(out_h, indent + 1, 'static void install(PyObject *module);')
    line(out_h, indent + 1, 'static void initialize(PyObject *module);')
    line(out_h, indent, '};')

    iterator = findClass('java/util/Iterator')
    enumeration = findClass('java/util/Enumeration')

    while indent:
        indent -= 1
        line(out_h, indent, '}')

    line(out)
    line(out, 0, '#include "structmember.h"')
    line(out, 0, '#include "functions.h"')
    line(out, 0, '#include "macros.h"')

    for inner in cls.getDeclaredClasses():
        if inner in typeset and not inner in declares:
            if Modifier.isStatic(inner.getModifiers()):
                line(out, 0, '#include "%s.h"',
                     inner.getName().replace('.', '/'))

    for method in methods:
        if method.getName() == 'pythonExtension':
            isExtension = True
            break
    else:
        isExtension = False
                
    line(out)
    indent = 0
    for name in names[:-1]:
        line(out, indent, 'namespace %s {', cppname(name))
        indent += 1

    if not isExtension:
        line(out, indent, 'static PyObject *t_%s_cast_(PyTypeObject *type, PyObject *arg);', names[-1])
        line(out, indent, 'static PyObject *t_%s_instance_(PyTypeObject *type, PyObject *arg);', names[-1])

    if constructors:
        line(out, indent, 'static int t_%s_init_(t_%s *self, PyObject *args, PyObject *kwds);', names[-1], names[-1])
        constructorName = 't_%s_init_' %(names[-1])
    else:
        constructorName = 'abstract_init'

    if superCls:
        superMethods = set([method.getName()
                            for method in superCls.getMethods()])
    else:
        superMethods = ()

    allMethods = {}
    extMethods = {}
    propMethods = {}

    if methods:
        for method in methods:
            modifiers = method.getModifiers()
            name = method.getName()
            params = method.getParameterTypes()
            superMethod = None
            isNative = Modifier.isNative(modifiers)
            isStatic = Modifier.isStatic(modifiers)

            if (isExtension and not isStatic and superCls and isNative):
                superMethod = find_method(superCls, name, params)

            if isExtension and isNative and not isStatic:
                extMethods.setdefault(name, []).append(method)

            if superMethod or not (isExtension and isNative and not isStatic):
                if isStatic:
                    if name in allMethods:
                        if Modifier.isStatic(allMethods[name][0].getModifiers()):
                            allMethods[name].append(method)
                        elif name + '_' in allMethods:
                            allMethods[name + '_'].append(method)
                        else:
                            print >>sys.stderr, "  Warning: renaming static method '%s' on class %s to '%s_' since it is shadowed by non-static method of same name." %(name, '.'.join(names), name)
                            allMethods[name + '_'] = [method]
                    else:
                        allMethods[name] = [method]
                else:
                    if name in allMethods:
                        if Modifier.isStatic(allMethods[name][0].getModifiers()):
                            print >>sys.stderr, "  Warning: renaming static method '%s' on class %s to '%s_' since it is shadowed by non-static method of same name." %(name, '.'.join(names), name)
                            allMethods[name + '_'] = allMethods[name]
                            allMethods[name] = [method]
                        else:
                            allMethods[name].append(method)
                    else:
                        allMethods[name] = [method]

            if not (isExtension and isNative):
                nameLen = len(name)
                paramsLen = len(params)
                if nameLen > 3 and paramsLen == 0 and name.startswith('get'):
                    propMethods.setdefault(name[3].lower() + name[4:],
                                           []).append(method)
                elif nameLen > 3 and paramsLen == 1 and name.startswith('set'):
                    propMethods.setdefault(name[3].lower() + name[4:],
                                           []).append(method)
                elif nameLen > 2 and paramsLen == 0 and name.startswith('is'):
                    propMethods.setdefault(name[2].lower() + name[3:],
                                           []).append(method)

    properties = set([name for name in propMethods.iterkeys()
                      if name not in allMethods])
    propMethods = [(name, propMethods[name]) for name in properties]
    sort(propMethods, key=lambda x: x[0])

    extMethods = extMethods.items()
    sort(extMethods, key=lambda x: x[0])
    allMethods = allMethods.items()
    sort(allMethods, key=lambda x: x[0])

    iteratorMethod = None
    iteratorExt = False
    nextMethod = None
    nextExt = False
    nextElementMethod = None
    nextElementExt = False

    mappingMethod = None
    if mapping:
        mappingName, mappingSig = mapping.split(':')

    sequenceLenMethod = None
    sequenceGetMethod = None
    if sequence:
        sequenceLenName, sequenceLenSig = sequence[0].split(':')
        sequenceGetName, sequenceGetSig = sequence[1].split(':')

    for name, methods in allMethods:
        args, x, cardinality = methodargs(methods, superMethods)
        sort(methods, key=lambda x: len(x.getParameterTypes()))
        method = methods[0]
        modifiers = method.getModifiers()
        if name == 'iterator' and iteratorMethod is None:
            if (not method.getParameterTypes() and
                iterator.isAssignableFrom(method.getReturnType())):
                iteratorMethod = method
        elif name == 'next' and nextMethod is None:
            if (not method.getParameterTypes() and
                not method.getReturnType().isPrimitive()):
                nextMethod = method
        elif name == 'nextElement' and nextElementMethod is None:
            if (not method.getParameterTypes() and
                not method.getReturnType().isPrimitive()):
                nextElementMethod = method
        elif mapping and name == mappingName and mappingMethod is None:
            if signature(method) == mappingSig:
                mappingMethod = (method, cardinality)
        elif sequence and name == sequenceLenName and sequenceLenMethod is None:
            if signature(method) == sequenceLenSig:
                sequenceLenMethod = (method, cardinality)
        elif sequence and name == sequenceGetName and sequenceGetMethod is None:
            if signature(method) == sequenceGetSig:
                sequenceGetMethod = (method, cardinality)
        elif isExtension and name == 'clone' and Modifier.isNative(modifiers):
            args, x, cardinality = ', PyObject *arg', ', arg', 1

        if Modifier.isStatic(modifiers):
            line(out, indent, 'static PyObject *t_%s_%s(PyTypeObject *type%s);',
                 names[-1], name, args)
        else:
            line(out, indent, 'static PyObject *t_%s_%s(t_%s *self%s);',
                 names[-1], name, names[-1], args)

    for name, methods in extMethods:
        args, x, cardinality = methodargs(methods, superMethods)
        sort(methods, key=lambda x: len(x.getParameterTypes()))
        method = methods[0]
        modifiers = method.getModifiers()
        if name == 'iterator' and iteratorMethod is None:
            if (not method.getParameterTypes() and
                iterator.isAssignableFrom(method.getReturnType())):
                iteratorMethod = method
                iteratorExt = True
        elif name == 'next' and nextMethod is None:
            if (not method.getParameterTypes() and
                not method.getReturnType().isPrimitive()):
                nextMethod = method
                nextExt = True
        elif name == 'nextElement' and nextElementMethod is None:
            if (not method.getParameterTypes() and
                not method.getReturnType().isPrimitive()):
                nextElementMethod = method
                nextElementExt = True

    if isExtension:
        count = 0
        for name, methods in extMethods:
            for method in methods:
                line(out, indent,
                     'static %s JNICALL t_%s_%s%d(JNIEnv *jenv, jobject jobj%s);',
                     jniname(method.getReturnType()), names[-1], name, count,
                     jniargs(method.getParameterTypes()))
                count += 1
        line(out, indent, 'static PyObject *t_%s_get__self(t_%s *self, void *data);', names[-1], names[-1])

    if instanceFields:
        for field in instanceFields:
            fieldName = field.getName()
            if fieldName not in properties:
                line(out, indent, 'static PyObject *t_%s_get__%s(t_%s *self, void *data);',
                     names[-1], fieldName, names[-1])
                if not Modifier.isFinal(field.getModifiers()):
                    line(out, indent, 'static int t_%s_set__%s(t_%s *self, PyObject *arg, void *data);',
                         names[-1], field.getName(), names[-1])
        line(out)

    for fieldName, methods in propMethods:
        getter = False
        setter = False
        for method in methods:
            methodName = method.getName()
            if not getter and (methodName.startswith('get') or
                               methodName.startswith('is')):
                getter = True
                line(out, indent, 'static PyObject *t_%s_get__%s(t_%s *self, void *data);',
                     names[-1], fieldName, names[-1])
            elif not setter and methodName.startswith('set'):
                setter = True
                line(out, indent, 'static int t_%s_set__%s(t_%s *self, PyObject *arg, void *data);',
                     names[-1], fieldName, names[-1])

    if instanceFields or propMethods or isExtension:
        line(out, indent, 'static PyGetSetDef t_%s__fields_[] = {', names[-1])
        for field in instanceFields:
            fieldName = field.getName()
            if fieldName not in properties:
                if Modifier.isFinal(field.getModifiers()):
                    line(out, indent + 1, 'DECLARE_GET_FIELD(t_%s, %s),',
                         names[-1], fieldName)
                else:
                    line(out, indent + 1, 'DECLARE_GETSET_FIELD(t_%s, %s),',
                         names[-1], fieldName)
        for fieldName, methods in propMethods:
            getter = False
            setter = False
            for method in methods:
                methodName = method.getName()
                if not getter and (methodName.startswith('get') or
                                   methodName.startswith('is')):
                    getter = True
                elif not setter and methodName.startswith('set'):
                    setter = True
                if getter and setter:
                    op = 'GETSET'
                elif getter:
                    op = 'GET'
                elif setter:
                    op = 'SET'
            line(out, indent + 1, 'DECLARE_%s_FIELD(t_%s, %s),',
                 op, names[-1], fieldName)
        if isExtension:
            line(out, indent + 1, 'DECLARE_GET_FIELD(t_%s, self),', names[-1])
        line(out, indent + 1, '{ NULL, NULL, NULL, NULL, NULL }')
        line(out, indent, '};')

    line(out)
    line(out, indent, 'static PyMethodDef t_%s__methods_[] = {', names[-1])

    if not isExtension:
        line(out, indent + 1,
             'DECLARE_METHOD(t_%s, cast_, METH_O | METH_CLASS),', names[-1])
        line(out, indent + 1,
             'DECLARE_METHOD(t_%s, instance_, METH_O | METH_CLASS),', names[-1])

    for name, methods in allMethods:
        modifiers = methods[0].getModifiers()
        if len(methods) == 1 and not name in superMethods:
            count = len(methods[0].getParameterTypes())
            if count == 0:
                args = 'METH_NOARGS'
            elif count == 1:
                args = 'METH_O'
            else:
                args = 'METH_VARARGS'
        elif isExtension and name == 'clone' and Modifier.isNative(modifiers):
            args = 'METH_O'
        else:
            args = 'METH_VARARGS'
        if Modifier.isStatic(modifiers):
            args += ' | METH_CLASS'

        line(out, indent + 1, 'DECLARE_METHOD(t_%s, %s, %s),',
             names[-1], name, args)
    line(out, indent + 1, '{ NULL, NULL, 0, NULL }')
    line(out, indent, '};')

    if instanceFields or propMethods or isExtension:
        tp_getset = 't_%s__fields_' %(names[-1])
    else:
        tp_getset = '0'

    if iteratorMethod:
        if iteratorExt:
            tp_iter = 'get_extension_iterator'
        else:
            tp_iter = '((PyObject *(*)(t_%s *)) get_iterator<t_%s>)' %(names[-1], names[-1])
        tp_iternext = '0'
    elif nextMethod and iterator.isAssignableFrom(cls):
        tp_iter = 'PyObject_SelfIter'
        returnName = typename(nextMethod.getReturnType(), cls, False)
        ns, sep, n = rpartition(returnName, '::')
        if nextExt:
            tp_iternext = 'get_extension_next'
        else:
            tp_iternext = '((PyObject *(*)(java::util::t_Iterator *)) get_iterator_next<java::util::t_Iterator,%s%st_%s,%s>)' %(ns, sep, n, returnName)
    elif nextElementMethod and enumeration.isAssignableFrom(cls):
        tp_iter = 'PyObject_SelfIter'
        returnName = typename(nextElementMethod.getReturnType(), cls, False)
        ns, sep, n = rpartition(returnName, '::')
        if nextElementExt:
            tp_iternext = 'get_extension_nextElement'
        else:
            tp_iternext = '((PyObject *(*)(java::util::t_Enumeration *)) get_enumeration_next<java::util::t_Enumeration,%s%st_%s,%s>)' %(ns, sep, n, returnName)
    elif nextMethod:
        tp_iter = 'PyObject_SelfIter'
        returnName = typename(nextMethod.getReturnType(), cls, False)
        ns, sep, n = rpartition(returnName, '::')
        if nextExt:
            tp_iternext = 'get_extension_next'
        else:
            tp_iternext = '((PyObject *(*)(t_%s *)) get_next<t_%s,%s%st_%s,%s>)' %(names[-1], names[-1], ns, sep, n, returnName)
    else:
        tp_iter = '0'
        tp_iternext = '0'

    if mappingMethod:
        method, cardinality = mappingMethod
        if cardinality > 1:
            getName = 't_%s_%s_map_' %(names[-1], method.getName())
            line(out, indent, 'static PyObject *%s(t_%s *self, PyObject *key);',
                 getName, names[-1])
        else:
            getName = 't_%s_%s' %(names[-1], method.getName())
        line(out)
        line(out, indent, 'static PyMappingMethods t_%s_as_mapping = {',
             names[-1])
        line(out, indent + 1, '0,')
        line(out, indent + 1, '(binaryfunc) %s,', getName)
        line(out, indent + 1, '0,')
        line(out, indent, '};')
        tp_as_mapping = '&t_%s_as_mapping' %(names[-1])
    else:
        tp_as_mapping = '0'

    if sequenceLenMethod or sequenceGetMethod:
        if sequenceLenMethod:
            method, cardinality = sequenceLenMethod
            lenName = 't_%s_%s_seq_' %(names[-1], method.getName())
            line(out, indent, 'static int %s(t_%s *self);', lenName, names[-1])
        else:
            lenName = '0'

        if sequenceGetMethod:
            method, cardinality = sequenceGetMethod
            getName = 't_%s_%s_seq_' %(names[-1], method.getName())
            line(out, indent, 'static PyObject *%s(t_%s *self, int n);',
                 getName, names[-1])
        else:
            getName = '0'

        line(out)
        line(out, indent, 'static PySequenceMethods t_%s_as_sequence = {',
             names[-1])
        if python_ver < '2.5.0':
            line(out, indent + 1, '(inquiry) %s,', lenName)
            line(out, indent + 1, '0,')
            line(out, indent + 1, '0,')
            line(out, indent + 1, '(intargfunc) %s', getName)
            line(out, indent, '};')
        else:
            line(out, indent + 1, '(lenfunc) %s,', lenName)
            line(out, indent + 1, '0,')
            line(out, indent + 1, '0,')
            line(out, indent + 1, '(ssizeargfunc) %s', getName)
            line(out, indent, '};')
        tp_as_sequence = '&t_%s_as_sequence' %(names[-1])
    else:
        tp_as_sequence = '0'

    if len(superNames) > 1:
        base = '::'.join(('::'.join(cppnames(superNames[:-1])), superNames[-1]))
    else:
        base = superNames[-1]
    line(out)
    line(out, indent, 'DECLARE_TYPE(%s, t_%s, %s, %s, %s, %s, %s, %s, %s, %s);',
         names[-1], names[-1], base, cppname(names[-1]), constructorName,
         tp_iter, tp_iternext, tp_getset, tp_as_mapping, tp_as_sequence)

    line(out)
    line(out, indent, 'void t_%s::install(PyObject *module)', names[-1])
    line(out, indent, '{')
    line(out, indent + 1, 'installType(&%s$$Type, module, "%s", %d);',
         names[-1], rename or names[-1], isExtension and 1 or 0)
    for inner in cls.getDeclaredClasses():
        if inner in typeset:
            if Modifier.isStatic(inner.getModifiers()):
                innerName = inner.getName().split('.')[-1]
                line(out, indent + 1, 'PyDict_SetItemString(%s$$Type.tp_dict, "%s", make_descriptor(&%s$$Type));',
                     names[-1], innerName[len(names[-1])+1:], innerName)
    line(out, indent, '}')

    line(out)
    line(out, indent, 'void t_%s::initialize(PyObject *module)', names[-1])
    line(out, indent, '{')
    line(out, indent + 1, 'PyDict_SetItemString(%s$$Type.tp_dict, "class_", make_descriptor(%s::initializeClass));',
         names[-1], cppname(names[-1]))
    line(out, indent + 1, 'PyDict_SetItemString(%s$$Type.tp_dict, "wrapfn_", make_descriptor(t_%s::wrap_jobject));',
         names[-1], names[-1])

    if isExtension:
        line(out, indent + 1, 'jclass cls = %s::initializeClass();',
             cppname(names[-1]))
    elif fields:
        line(out, indent + 1, '%s::initializeClass();', cppname(names[-1]))

    if isExtension:
        count = 0
        line(out, indent + 1, 'JNINativeMethod methods[] = {')
        for name, methods in extMethods:
            for method in methods:
                line(out, indent + 2, '{ "%s", "%s", (void *) t_%s_%s%d },',
                     name, signature(method), names[-1], name, count)
                count += 1
        line(out, indent + 1, '};')
        line(out, indent + 1, 'env->registerNatives(cls, methods, %d);',
             count)

    for field in fields:
        fieldType = field.getType()
        fieldName = field.getName()
        value = '%s::%s' %(cppname(names[-1]), cppname(fieldName))
        value = fieldValue(cls, value, fieldType)
        line(out, indent + 1, 'PyDict_SetItemString(%s$$Type.tp_dict, "%s", make_descriptor(%s));',
             names[-1], fieldName, value)
    line(out, indent, '}')

    if not isExtension:
        line(out)
        line(out, indent, 'static PyObject *t_%s_cast_(PyTypeObject *type, PyObject *arg)', names[-1])
        line(out, indent, '{')
        line(out, indent + 1, 'if (!(arg = castCheck(arg, %s::initializeClass, 1)))', cppname(names[-1]))
        line(out, indent + 2, 'return NULL;')
        line(out, indent + 1, 'return t_%s::wrap_Object(%s(((t_%s *) arg)->object.this$));', names[-1], cppname(names[-1]), names[-1])
        line(out, indent, '}')

        line(out, indent, 'static PyObject *t_%s_instance_(PyTypeObject *type, PyObject *arg)', names[-1])
        line(out, indent, '{')
        line(out, indent + 1, 'if (!castCheck(arg, %s::initializeClass, 0))', cppname(names[-1]))
        line(out, indent + 2, 'Py_RETURN_FALSE;')
        line(out, indent + 1, 'Py_RETURN_TRUE;')
        line(out, indent, '}')

    if constructors:
        line(out)
        line(out, indent, 'static int t_%s_init_(t_%s *self, PyObject *args, PyObject *kwds)', names[-1], names[-1])
        line(out, indent, '{')
        if len(constructors) > 1:
            currLen = -1
            line(out, indent + 1, 'switch (PyTuple_GET_SIZE(args)) {')
            withErr = False
            for constructor in constructors:
                params = constructor.getParameterTypes()
                if len(params) != currLen:
                    if currLen >= 0:
                        withErr = True
                        line(out, indent + 2, 'goto err;')
                    currLen = len(params)
                    line(out, indent + 1, '%scase %d:', HALF_INDENT, currLen)
                construct(out, indent + 2, cls, True, constructor, names)
            line(out, indent + 1, '%sdefault:', HALF_INDENT)
            if withErr:
                line(out, indent + 1, '%serr:', HALF_INDENT)
            line(out, indent + 2, 'PyErr_SetArgsError((PyObject *) self, "__init__", args);')
            line(out, indent + 2, 'return -1;')
            line(out, indent + 1, '}')
        else:
            construct(out, indent + 1, cls, False, constructors[0], names)
            if constructors[0].getParameterTypes():
                line(out, indent + 1, 'else')
                line(out, indent + 1, '{')
                line(out, indent + 2, 'PyErr_SetArgsError((PyObject *) self, "__init__", args);')
                line(out, indent + 2, 'return -1;')
                line(out, indent + 1, '}')

        if isExtension:
            line(out)
            line(out, indent + 1, 'Py_INCREF((PyObject *) self);')
            line(out, indent + 1, 'self->object.pythonExtension((jlong) (Py_intptr_t) (void *) self);')

        line(out)
        line(out, indent + 1, 'return 0;')
        line(out, indent , '}')

    for name, methods in allMethods:
        line(out)
        modifiers = methods[0].getModifiers()

        if isExtension and name == 'clone' and Modifier.isNative(modifiers):
            declargs, args, cardinality = ', PyObject *arg', ', arg', 1
        else:
            declargs, args, cardinality = methodargs(methods, superMethods)

        static = Modifier.isStatic(modifiers)
        if static:
            line(out, indent, 'static PyObject *t_%s_%s(PyTypeObject *type%s)',
                 names[-1], name, declargs)
        else:
            line(out, indent, 'static PyObject *t_%s_%s(t_%s *self%s)',
                 names[-1], name, names[-1], declargs)

        line(out, indent, '{')
        if len(methods) > 1:
            currLen = -1
            line(out, indent + 1, 'switch (PyTuple_GET_SIZE(args)) {')
            for method in methods:
                params = method.getParameterTypes()
                if len(params) != currLen:
                    if currLen >= 0:
                        line(out, indent + 2, 'break;')
                    currLen = len(params)
                    line(out, indent + 1, '%scase %d:', HALF_INDENT, currLen)
                call(out, indent + 2, cls, True, method, names, cardinality,
                     isExtension)
            line(out, indent + 1, '}')
        else:
            call(out, indent + 1, cls, False, methods[0], names, cardinality,
                 isExtension)

        if args:
            line(out)
            if name in superMethods:
                if static:
                    line(out, indent + 1, 'return callSuper(type, "%s"%s, %d);',
                         name, args, cardinality)
                else:
                    line(out, indent + 1, 'return callSuper(&%s$$Type, (PyObject *) self, "%s"%s, %d);',
                         names[-1], name, args, cardinality)
            else:
                line(out, indent + 1, 'PyErr_SetArgsError(%s, "%s"%s);',
                     static and 'type' or '(PyObject *) self', name, args)
                line(out, indent + 1, 'return NULL;')

        line(out, indent, '}')

    if isExtension:
        count = 0
        for name, methods in extMethods:
            for method in methods:
                line(out)
                line(out, indent,
                     'static %s JNICALL t_%s_%s%d(JNIEnv *jenv, jobject jobj%s)',
                     jniname(method.getReturnType()), names[-1], name, count,
                     jniargs(method.getParameterTypes()))
                count += 1
                line(out, indent, '{')
                extension(env, out, indent + 1, cls, names, name, count, method)
                line(out, indent, '}')
        line(out)
        line(out, indent, 'static PyObject *t_%s_get__self(t_%s *self, void *data)',
             names[-1], names[-1])
        line(out, indent, '{')
        indent += 1
        line(out, indent, 'jlong ptr;')
        line(out, indent, 'OBJ_CALL(ptr = self->object.pythonExtension());')
        line(out, indent, 'PyObject *obj = (PyObject *) (Py_intptr_t) ptr;')
        line(out)
        line(out, indent, 'if (obj != NULL)')
        line(out, indent, '{')
        line(out, indent + 1, 'Py_INCREF(obj);')
        line(out, indent + 1, 'return obj;')
        line(out, indent, '}')
        line(out, indent, 'else')
        line(out, indent + 1, 'Py_RETURN_NONE;')
        indent -= 1
        line(out, indent, '}')

    if instanceFields:
        for field in instanceFields:
            fieldName = field.getName()
            if fieldName not in properties:
                line(out)
                fieldType = field.getType()
                typeName = typename(fieldType, cls, False)
                line(out, indent, 'static PyObject *t_%s_get__%s(t_%s *self, void *data)',
                     names[-1], fieldName, names[-1])
                line(out, indent, '{')
                line(out, indent + 1, '%s value%s;', typeName,
                     not fieldType.isPrimitive() and '((jobject) NULL)' or '')
                line(out, indent + 1, 'OBJ_CALL(value = self->object._get_%s());',
                     fieldName)
                line(out, indent + 1, returnValue(cls, fieldType, 'value'))
                line(out, indent, '}')

                if not Modifier.isFinal(field.getModifiers()):
                    line(out, indent, 'static int t_%s_set__%s(t_%s *self, PyObject *arg, void *data)',
                         names[-1], fieldName, names[-1])
                    line(out, indent, '{')
                    line(out, indent + 1, '%s value%s;', typeName,
                         not fieldType.isPrimitive() and '((jobject) NULL)' or '')
                    sig, check, x = parseArgs([fieldType], cls)
                    line(out, indent + 1, 'if (!parseArg(arg, "%s"%s, &value))',
                         sig, check)
                    line(out, indent + 1, '{')
                    line(out, indent + 2, 'INT_CALL(self->object._set_%s(value));',
                         fieldName)
                    line(out, indent + 2, 'return 0;')
                    line(out, indent + 1, '}')
                    line(out, indent + 1, 'PyErr_SetArgsError((PyObject *) self, "%s", arg);',
                         fieldName)
                    line(out, indent + 1, 'return -1;')
                    line(out, indent, '}')

    if propMethods:
        for fieldName, methods in propMethods:
            line(out)
            getter = None
            setters = []
            sort(methods, key=lambda x: x.getName())
            for method in methods:
                methodName = method.getName()
                if not getter and (methodName.startswith('get') or
                                   methodName.startswith('is')):
                    getter = method
                elif methodName.startswith('set'):
                    setters.append(method)

            if getter:
                methodName = getter.getName()
                returnType = getter.getReturnType()
                typeName = typename(returnType, cls, False)
                line(out, indent, 'static PyObject *t_%s_get__%s(t_%s *self, void *data)',
                     names[-1], fieldName, names[-1])
                line(out, indent, '{')
                line(out, indent + 1, '%s value%s;', typeName,
                     not returnType.isPrimitive() and '((jobject) NULL)' or '')
                line(out, indent + 1, 'OBJ_CALL(value = self->object.%s());',
                     methodName)
                line(out, indent + 1, returnValue(cls, returnType, 'value'))
                line(out, indent, '}')

            if setters:
                line(out, indent, 'static int t_%s_set__%s(t_%s *self, PyObject *arg, void *data)',
                     names[-1], fieldName, names[-1])
                line(out, indent, '{')
                methodName = setters[0].getName()
                for method in setters:
                    argType = method.getParameterTypes()[0]
                    typeName = typename(argType, cls, False)
                    line(out, indent + 1, '{')
                    line(out, indent + 2, '%s value%s;', typeName,
                         not argType.isPrimitive() and '((jobject) NULL)' or '')
                    sig, check, x = parseArgs([argType], cls)
                    line(out, indent + 2, 'if (!parseArg(arg, "%s"%s, &value))',
                         sig, check)
                    line(out, indent + 2, '{')
                    line(out, indent + 3, 'INT_CALL(self->object.%s(value));',
                         methodName)
                    line(out, indent + 3, 'return 0;')
                    line(out, indent + 2, '}')
                    line(out, indent + 1, '}')
                line(out, indent + 1, 'PyErr_SetArgsError((PyObject *) self, "%s", arg);',
                     fieldName)
                line(out, indent + 1, 'return -1;')
                line(out, indent, '}')

    if mappingMethod:
        method, cardinality = mappingMethod
        if cardinality > 1:
            methodName = method.getName()
            getName = 't_%s_%s_map_' %(names[-1], methodName)
            line(out)
            line(out, indent, 'static PyObject *%s(t_%s *self, PyObject *arg)',
                 getName, names[-1])
            line(out, indent, '{')
            call(out, indent + 1, cls, False, method, names, 1, isExtension)
            line(out)
            line(out, indent + 1, 'PyErr_SetArgsError((PyObject *) self, "%s", arg);',
                 methodName)
            line(out, indent + 1, 'return NULL;')
            line(out, indent, '}')

    if sequenceLenMethod:
        method, cardinality = sequenceLenMethod
        methodName = method.getName()
        lenName = 't_%s_%s_seq_' %(names[-1], methodName)
        line(out)
        line(out, indent, 'static int %s(t_%s *self)', lenName, names[-1])
        line(out, indent, '{')
        line(out, indent + 1, '%s len;',
             typename(method.getReturnType(), cls, False))
        line(out, indent + 1, 'INT_CALL(len = self->object.%s());', methodName)
        line(out, indent + 1, 'return (int) len;')
        line(out, indent, '}')

    if sequenceGetMethod:
        method, cardinality = sequenceGetMethod
        methodName = method.getName()
        returnType = method.getReturnType()
        getName = 't_%s_%s_seq_' %(names[-1], methodName)
        line(out)
        line(out, indent, 'static PyObject *%s(t_%s *self, int n)', getName, names[-1])
        line(out, indent, '{')
        line(out, indent + 1, '%s result%s;',
             typename(returnType, cls, False),
             not returnType.isPrimitive() and '((jobject) NULL)' or '')
        line(out, indent + 1, 'OBJ_CALL(result = self->object.%s((%s) n));',
             methodName, typename(method.getParameterTypes()[0], cls, False))
        line(out, indent + 1, returnValue(cls, returnType, 'result'))
        line(out, indent, '}')

    while indent:
        indent -= 1
        line(out, indent, '}')


def package(out, allInOne, cppdir, namespace, names):

    if not allInOne:
        out = file(os.path.join(os.path.join(cppdir, *names),
                                '__init__.cpp'), 'w')

    if allInOne and not names or not allInOne:
        line(out, 0, '#include <jni.h>')
        line(out, 0, '#include <Python.h>')
        line(out, 0, '#include "JCCEnv.h"')
        line(out, 0, '#include "functions.h"')

    if not names:
        line(out)
        line(out, 0, 'PyObject *initVM(PyObject *module, PyObject *args, PyObject *kwds);')

    packages = []
    types = []

    namespaces = namespace.items()
    sort(namespaces, key=lambda x: x[0])
    for name, entries in namespaces:
        if entries is True:
            if names:
                line(out, 0, '#include "%s/%s.h"', '/'.join(names), name)
            else:
                line(out, 0, '#include "%s.h"', name)
            types.append(name)
        else:
            packages.append((name, entries))

    indent = 0
    if names:
        line(out)
        for name in names:
            line(out, indent, 'namespace %s {', cppname(name))
            indent += 1

    line(out);
    for name, entries in packages:
        line(out, indent, 'namespace %s {', cppname(name))
        line(out, indent + 1, 'void __install__(PyObject *module);')
        line(out, indent + 1, 'void __initialize__(PyObject *module);')
        line(out, indent, '}')

    line(out)
    line(out, indent, 'void __install__(PyObject *module)')
    line(out, indent, '{')
    for name in types:
        line(out, indent + 1, 't_%s::install(module);', name)
    for name, entries in packages:
        line(out, indent + 1, '%s::__install__(module);', cppname(name))
    line(out, indent, '}')

    line(out)
    if not names:
        line(out, indent, 'PyObject *__initialize__(PyObject *module, PyObject *args, PyObject *kwds)')
        line(out, indent, '{')
        line(out, indent + 1, 'PyObject *env = initVM(module, args, kwds);')
        line(out)
        line(out, indent + 1, 'if (env == NULL)')
        line(out, indent + 2, 'return NULL;')
        line(out)
        line(out, indent + 1, 'try {');
        indent += 1
    else:
        line(out, indent, 'void __initialize__(PyObject *module)')
        line(out, indent, '{')
    for name in types:
        line(out, indent + 1, 't_%s::initialize(module);', name)
    for name, entries in packages:
        line(out, indent + 1, '%s::__initialize__(module);', cppname(name))
    if not names:
        line(out, indent + 1, 'return env;')
        indent -= 1
        line(out, indent + 1, '} catch (JCCEnv::exception e) {')
        line(out, indent + 2, 'PyErr_SetJavaError(e.throwable);')
        line(out, indent + 2, 'return NULL;')
        line(out, indent + 1, '}')

    line(out, indent, '}')

    while indent:
        indent -= 1
        line(out, indent, '}')

    if not allInOne:
        out.close()
    else:
        line(out)

    for name, entries in packages:
        package(out, allInOne, cppdir, entries, names + (name,))


def module(out, allInOne, classes, cppdir, moduleName, shared):

    extname = '_%s' %(moduleName)
    line(out, 0, '#include <Python.h>')
    line(out, 0, '#include "macros.h"')
    line(out, 0, '#include "jccfuncs.h"')

    if allInOne:
        out_init = file(os.path.join(cppdir, '__init__.cpp'), 'w')
    namespaces = {}
    for cls in classes:
        namespace = namespaces
        classNames = cls.getName().split('.')
        for className in classNames[:-1]:
            namespace = namespace.setdefault(className, {})
        namespace[classNames[-1]] = True
    if allInOne:
        package(out_init, True, cppdir, namespaces, ())
        out_init.close()
    else:
        package(None, False, cppdir, namespaces, ())

    line(out)
    line(out, 0, 'PyObject *initJCC(PyObject *module);')
    line(out, 0, 'void __install__(PyObject *module);')
    line(out, 0, 'extern PyTypeObject JObject$$Type, ConstVariableDescriptor$$Type, FinalizerClass$$Type, FinalizerProxy$$Type;')
    line(out, 0, 'extern void _install_jarray(PyObject *);')
    line(out)
    line(out, 0, 'extern "C" {')

    line(out)
    line(out, 1, 'void init%s(void)', extname)
    line(out, 1, '{')
    line(out, 2, 'PyObject *module = Py_InitModule3("%s", jcc_funcs, "");',
         extname);
    line(out)
    line(out, 2, 'initJCC(module);')
    line(out)
    line(out, 2, 'INSTALL_TYPE(JObject, module);')
    line(out, 2, 'INSTALL_TYPE(ConstVariableDescriptor, module);')
    line(out, 2, 'INSTALL_TYPE(FinalizerClass, module);')
    line(out, 2, 'INSTALL_TYPE(FinalizerProxy, module);')
    line(out, 2, '_install_jarray(module);')
    line(out, 2, '__install__(module);')
    line(out, 1, '}')
    line(out, 0, '}')


def compile(env, jccPath, output, moduleName, install, dist, debug, jars,
            version, prefix, root, install_dir, use_distutils,
            shared, compiler, modules, wininst):

    try:
        if use_distutils:
            raise ImportError
        from setuptools import setup, Extension
        with_setuptools = True
        if shared and not SHARED:
            raise NotImplementedError, "JCC was not built with --shared mode support, see JCC's INSTALL file for more information"
    except ImportError:
        if python_ver < '2.4':
            raise ImportError, 'setuptools is required when using Python 2.3'
        if shared:
            raise ImportError, 'setuptools is required when using --shared'
        from distutils.core import setup, Extension
        with_setuptools = False

    extname = '_%s' %(moduleName)

    modulePath = os.path.join(output, moduleName)
    if not os.path.isdir(modulePath):
        os.makedirs(modulePath)

    out = file(os.path.join(modulePath, '__init__.py'), 'w')
    line(out)
    if shared:
        line(out, 0, "import os, sys")
        line(out)
        line(out, 0, "if sys.platform == 'win32':")
        line(out, 1, "import jcc, %s", extname)
        line(out, 0, "else:")
        line(out, 1, "import %s", extname)
    else:
        line(out, 0, 'import os, %s', extname)
    line(out)
    line(out, 0, '__dir__ = os.path.abspath(os.path.dirname(__file__))')

    package_data = []
    for jar in jars:
        shutil.copy2(jar, modulePath)
        package_data.append(os.path.basename(jar))

    if modules:
        for module in modules:
            pfile = module.split('.')[0] + '.py'
            shutil.copy2(pfile, modulePath)
            pfile = os.path.basename(pfile)
            cfile = pfile + (__debug__ and 'c' or 'o')
            py_compile.compile(os.path.join(modulePath, pfile),
                               os.path.join(modulePath, cfile),
                               doraise=True)

    line(out)
    line(out, 0, 'class JavaError(Exception):')
    line(out, 1, 'def getJavaException(self):')
    line(out, 2, 'return self.args[0]')
    line(out, 1, 'def __str__(self):')
    line(out, 2, 'writer = %s.StringWriter()', extname)
    line(out, 2, 'self.getJavaException().printStackTrace(%s.PrintWriter(writer))', extname)
    line(out, 2, 'return "\\n".join((super(JavaError, self).__str__(), "    Java stacktrace:", str(writer)))')
    line(out)
    line(out, 0, 'class InvalidArgsError(Exception):')
    line(out, 1, 'pass')
    line(out)
    line(out, 0, '%s._setExceptionTypes(JavaError, InvalidArgsError)', extname)

    if version:
        line(out)
        line(out, 0, 'VERSION = "%s"', version)
        
    line(out, 0, 'CLASSPATH = [%s]' %(', '.join(['os.path.join(__dir__, "%s")' %(os.path.basename(jar)) for jar in jars])))
    line(out, 0, 'CLASSPATH = os.pathsep.join(CLASSPATH)')

    line(out)
    line(out, 0, 'from %s import *', extname)
    out.close()

    includes = [os.path.join(output, extname),
                os.path.join(jccPath, 'sources')]

    sources = ['JObject.cpp', 'JArray.cpp', 'functions.cpp', 'types.cpp']
    if not shared:
        sources.append('jcc.cpp')
        sources.append('JCCEnv.cpp')
    for source in sources:
	shutil.copy2(os.path.join(jccPath, 'sources', source),
                     os.path.join(output, extname))

    sources = []
    for path, dirs, names in os.walk(os.path.join(output, extname)):
        for name in names:
            if name.endswith('.cpp'):
                sources.append(os.path.join(path, name))

    script_args = ['build_ext']

    includes[0:0] = INCLUDES
    compile_args = CFLAGS
    link_args = LFLAGS
    defines=['PYTHON']

    if compiler:
        script_args.append('--compiler=%s' %(compiler))

    if shared:
        defines.append('_jcc_shared')
    script_args.append('--define=%s' %(','.join(defines)))

    if debug:
        script_args.append('--debug')
        compile_args += DEBUG_CFLAGS
    elif sys.platform == 'win32':
        pass
    elif sys.platform == 'sunos5':
        link_args.append('-Wl,-s')
    else:
        link_args.append('-Wl,-S')

    if install:
        script_args.append('install')
    if prefix:
        script_args.append('--prefix=%s' % prefix)
    if root:
        script_args.append('--root=%s' % root)
    if install_dir:
        script_args.append('--install-lib=%s' % install_dir)

    if dist:
        if wininst:
            script_args.append('bdist_wininst')
        elif with_setuptools:
            script_args.append('bdist_egg')
        else:
            script_args.append('bdist')

    args = {
        'extra_compile_args': compile_args,
        'extra_link_args': link_args,
        'include_dirs': includes,
        'sources': sources
    }
    if shared:
        shlibdir = os.path.dirname(os.path.dirname(_jcc.__file__))
        if sys.platform == 'darwin':   # distutils no good with -R
            machine = platform.machine()
            if machine.startswith('iPod') or machine.startswith('iPhone'):
                args['extra_link_args'] += ['-L' + shlibdir]
            else:
                args['extra_link_args'] += ['-Wl,-rpath', shlibdir]
            args['library_dirs'] = [shlibdir]
            args['libraries'] = ['jcc']
        elif sys.platform == 'linux2': # distutils no good with -R
            args['extra_link_args'] += ['-Wl,-rpath', shlibdir]
            args['library_dirs'] = [shlibdir]
            args['libraries'] = ['jcc']
        elif sys.platform == 'win32':
            jcclib = 'jcc%s.lib' %(debug and '_d' or '')
            args['extra_link_args'] += [os.path.join(shlibdir, 'jcc', jcclib)]
        else:
            raise NotImplementedError, "shared mode on %s" %(sys.platform)

    extensions = [Extension('.'.join([moduleName, extname]), **args)]

    args = {
        'name': moduleName,
        'packages': [moduleName],
        'package_dir': {moduleName: modulePath},
        'package_data': {moduleName: package_data},
        'version': version,
        'ext_modules': extensions,
        'script_args': script_args
    }
    if with_setuptools:
        args['zip_safe'] = False

    setup(**args)
