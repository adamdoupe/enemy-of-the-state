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

import os, sys, zipfile, _jcc

python_ver = '%d.%d.%d' %(sys.version_info[0:3])
if python_ver < '2.4':
    from sets import Set as set

    def split_pkg(string, sep):
        parts = string.split(sep)
        if len(parts) > 1:
            return sep.join(parts[:-1]), parts[-1]
        return parts

    def sort(list, fn=None, key=None):
        if fn:
            list.sort(fn)
        elif key:
            def fn(x, y):
                return cmp(key(x), key(y))
            list.sort(fn)
        else:
            list.sort()

else:
    def split_pkg(string, sep):
        return string.rsplit(sep, 1)

    def sort(list, fn=None, key=None):
        if fn:
            list.sort(cmp=fn)
        elif key:
            list.sort(key=key)
        else:
            list.sort()


class JavaError(Exception):

    def getJavaException(self):
        return self.args[0]

    def __str__(self):
        writer = StringWriter()
        self.getJavaException().printStackTrace(PrintWriter(writer))

        return '\n'.join((super(JavaError, self).__str__(),
                          "Java stacktrace:", str(writer)))


class InvalidArgsError(Exception):
    pass


_jcc._setExceptionTypes(JavaError, InvalidArgsError)
from _jcc import *


INDENT = '    '
HALF_INDENT = '  '

PRIMITIVES = { 'boolean': 'Z',
               'byte': 'B',
               'char': 'C',
               'double': 'D',
               'float': 'F',
               'int': 'I',
               'long': 'J',
               'short': 'S',
               'void': 'V' }

RESERVED = set(['delete', 'and', 'or', 'not', 'xor', 'union', 'NULL',
                'register', 'const', 'bool', 'operator', 'typeof'])

def cppname(name):

    if name in RESERVED:
        return name + '$'

    return name


def cppnames(names):

    return [cppname(name) for name in names]


def typename(cls, current, const):

    if cls.isArray():
        componentType = cls.getComponentType()
        if componentType.isArray():
            name = 'JArray< %s >' %(typename(componentType, current, False))
        else:
            name = 'JArray<%s>' %(typename(componentType, current, False))

    elif cls.isPrimitive():
        name = cls.getName()
        if name != 'void':
            name = 'j' + name
        const = False

    elif cls == current:
        name = cppname(cls.getName().split('.')[-1])

    else:
        name = '::'.join([cppname(name) for name in cls.getName().split('.')])

    if const:
        return "const %s&" %(name)

    return name


def argnames(params, cls):

    if not params:
        return '', ''

    count = len(params)
    decls = ', '.join(["%s a%d" %(typename(params[i], cls, True), i)
                       for i in xrange(count)])
    args = ', '.join(['a%d%s' %(i, not params[i].isPrimitive() and '.this$' or '')
                      for i in xrange(count)])

    return decls, ', ' + args


def line(out, indent=0, string='', *args):

    out.write(INDENT * indent)
    out.write(string % args)
    out.write('\n')


def known(cls, typeset, declares, packages, excludes):

    while cls.isArray():
        cls = cls.getComponentType()

    if cls in excludes:
        return False

    if cls.isPrimitive():
        return True

    if cls in typeset:
        declares.add(cls)
        return True

    if split_pkg(cls.getName(), '.')[0] in packages:
        typeset.add(cls)
        declares.add(cls)
        cls = cls.getSuperclass()
        while cls and cls not in typeset:
            typeset.add(cls)
            cls = cls.getSuperclass()
        return True

    return False


def find_method(cls, name, params):

    declared = False
    while True:
        try:
            if declared:
                method = cls.getDeclaredMethod(name, params)
            else:
                method = cls.getMethod(name, params)
            break
        except JavaError, e:
            if (e.getJavaException().getClass().getName() == 'java.lang.NoSuchMethodException'):
                if not declared:
                    declared = True
                else:
                    cls = cls.getSuperclass()
                    if not cls:
                        return None
                continue
            raise

    modifiers = method.getModifiers()
    if Modifier.isAbstract(modifiers):
        return None
    if Modifier.isPrivate(modifiers):
        return None

    return method


def signature(fn, argsOnly=False):

    def typename(cls):
        array = ''
        while cls.isArray():
            array += '['
            cls = cls.getComponentType()
        if cls.isPrimitive():
            return array + PRIMITIVES[cls.getName()]
        return '%sL%s;' %(array, cls.getName().replace('.', '/'))
        
    if isinstance(fn, Constructor):
        returnType = 'V'
    elif isinstance(fn, Method):
        returnType = typename(fn.getReturnType())
    elif isinstance(fn, Field):
        return typename(fn.getType())

    if argsOnly:
        return '(%s)' %(''.join([typename(param)
                                 for param in fn.getParameterTypes()]))

    return '(%s)%s' %(''.join([typename(param)
                               for param in fn.getParameterTypes()]),
                       returnType)


def forward(out, namespace, indent):

    for name, entries in namespace.iteritems():
        if entries is True:
            line(out, indent, 'class %s;', cppname(name))
        else:
            line(out, indent, 'namespace %s {', cppname(name))
            forward(out, entries, indent + 1)
            line(out, indent, '}')


def expandjar(path):

    jar = zipfile.ZipFile(path, 'r')

    for member in jar.infolist():
        f = member.filename
        if f.endswith('.class'):
            yield f.split('.')[0].replace('/', '.')

    jar.close()


def jcc(args):

    classNames = set()
    packages = set()
    jars = []
    classpath = []
    moduleName = None
    modules = []
    build = False
    install = False
    recompile = False
    output = 'build'
    debug = False
    excludes = []
    version = ''
    mappings = {}
    sequences = {}
    renames = {}
    env = None
    wrapperFiles = 1
    prefix = None
    root = None
    install_dir = None
    use_distutils = False
    shared = False
    dist = False
    wininst = False
    compiler = None

    i = 1
    while i < len(args):
        arg = args[i]
        if arg.startswith('-'):
            if arg == '--jar':
                i += 1
                classpath.append(args[i])
                classNames.update(expandjar(args[i]))
                jars.append(args[i])
            elif arg == '--include':
                i += 1
                classpath.append(args[i])
                jars.append(args[i])
            elif arg == '--package':
                i += 1
                packages.add(args[i])
            elif arg == '--classpath':
                i += 1
                classpath.append(args[i])
            elif arg == '--python':
                from python import python, module
                i += 1
                moduleName = args[i]
            elif arg == '--module':
                i += 1
                modules.append(args[i])
            elif arg == '--build':
                from python import compile
                build = True
            elif arg == '--install':
                from python import compile
                install = True
            elif arg == '--compile':
                from python import compile
                recompile = True
            elif arg == '--output':
                i += 1
                output = args[i]
            elif arg == '--debug':
                debug = True
            elif arg == '--exclude':
                i += 1
                excludes.append(args[i])
            elif arg == '--version':
                i += 1
                version = args[i]
            elif arg == '--mapping':
                mappings[args[i + 1]] = args[i + 2]
                i += 2
            elif arg == '--sequence':
                sequences[args[i + 1]] = (args[i + 2], args[i + 3])
                i += 3
            elif arg == '--rename':
                i += 1
                renames.update(dict([arg.split('=')
                                     for arg in args[i].split(',')]))
            elif arg == '--files':
                i += 1
                wrapperFiles = args[i]
                if wrapperFiles != 'separate':
                    wrapperFiles = int(wrapperFiles)
            elif arg == '--prefix':
                i += 1
                prefix = args[i]
            elif arg == '--root':
                i += 1
                root = args[i]
            elif arg == '--install-dir':
                i += 1
                install_dir = args[i]
            elif arg == '--use-distutils':
                use_distutils = True
            elif arg == '--shared':
                shared = True
            elif arg == '--bdist':
                from python import compile
                dist = True
            elif arg == '--wininst':
                from python import compile
                wininst = True
                dist = True
            elif arg == '--compiler':
                i += 1
                compiler = args[i]
            elif arg == '--reserved':
                i += 1
                RESERVED.update(args[i].split(','))
            else:
                raise ValueError, "Invalid argument: %s" %(arg)
        else:
            classNames.add(arg)
        i += 1

    env = initVM(os.pathsep.join(classpath) or None, maxstack='512k',
                 vmargs='-Djava.awt.headless=true')

    typeset = set()
    excludes = set([findClass(className.replace('.', '/'))
                    for className in excludes])

    if recompile or not build and (install or dist):
        if moduleName is None:
            raise ValueError, 'module name not specified (use --python)'
        else:
            compile(env, os.path.dirname(args[0]), output, moduleName,
                    install, dist, debug, jars, version,
                    prefix, root, install_dir, use_distutils,
                    shared, compiler, modules, wininst)
    else:
        for className in classNames:
            cls = findClass(className.replace('.', '/'))
            if cls is None:
                raise ValueError, className
            if cls in excludes:
                continue
            if Modifier.isPublic(cls.getModifiers()):
                typeset.add(cls)
                cls = cls.getSuperclass()
                while cls and cls not in typeset:
                    typeset.add(cls)
                    cls = cls.getSuperclass()
        typeset.add(findClass('java/lang/Class'))
        typeset.add(findClass('java/lang/String'))
        typeset.add(findClass('java/lang/Throwable'))
        typeset.add(findClass('java/lang/Exception'))
        typeset.add(findClass('java/lang/RuntimeException'))
        if moduleName:
            typeset.add(findClass('java/lang/Number'))
            typeset.add(findClass('java/lang/Boolean'))
            typeset.add(findClass('java/lang/Integer'))
            typeset.add(findClass('java/lang/Long'))
            typeset.add(findClass('java/lang/Double'))
            typeset.add(findClass('java/util/Iterator'))
            typeset.add(findClass('java/util/Enumeration'))
            typeset.add(findClass('java/io/StringWriter'))
            typeset.add(findClass('java/io/PrintWriter'))
            packages.add('java.lang')

        if moduleName:
            cppdir = os.path.join(output, '_%s' %(moduleName))
        else:
            cppdir = output

        allInOne = wrapperFiles != 'separate'
        if allInOne:
            if not os.path.isdir(cppdir):
                os.makedirs(cppdir)
            if wrapperFiles <= 1:
                out_cpp = file(os.path.join(cppdir, '__wrap__.cpp'), 'w')
            else:
                fileCount = 1
                fileName = '__wrap%02d__.cpp' %(fileCount)
                out_cpp = file(os.path.join(cppdir, fileName), 'w')

        done = set()
        todo = typeset - done
	if allInOne and wrapperFiles > 1:
            classesPerFile = max(1, len(todo) / wrapperFiles)
        classCount = 0
        while todo:
            for cls in todo:
                classCount += 1
                className = cls.getName()
                names = className.split('.')
                dir = os.path.join(cppdir, *names[:-1])
                if not os.path.isdir(dir):
                    os.makedirs(dir)

                fileName = os.path.join(dir, names[-1])
                out_h = file(fileName + '.h', "w")
                line(out_h, 0, '#ifndef %s_H', '_'.join(names))
                line(out_h, 0, '#define %s_H', '_'.join(names))

                (superCls, constructors, methods, protectedMethods,
                 fields, instanceFields, declares) = \
                    header(env, out_h, cls, typeset, packages, excludes)

                if not allInOne:
                    out_cpp = file(fileName + '.cpp', 'w')
                names, superNames = code(env, out_cpp,
                                         cls, superCls, constructors,
                                         methods, protectedMethods,
                                         fields, instanceFields, 
                                         declares, typeset, excludes)
                if moduleName:
                    python(env, out_h, out_cpp,
                           cls, superCls, names, superNames,
                           constructors, methods, protectedMethods,
                           fields, instanceFields,
                           mappings.get(className), sequences.get(className),
                           renames.get(className),
                           declares, typeset, excludes, moduleName)

                line(out_h)
                line(out_h, 0, '#endif')
                out_h.close()

                if not allInOne:
                    out_cpp.close()
                elif wrapperFiles > 1:
                    if classCount >= classesPerFile:
                        out_cpp.close()
	                fileCount += 1
	                fileName = '__wrap%02d__.cpp' %(fileCount)
	                out_cpp = file(os.path.join(cppdir, fileName), 'w')
                        classCount = 0
                        
            done.update(todo)
            todo = typeset - done

        if allInOne:
            out_cpp.close()

        if moduleName:
            out = file(os.path.join(cppdir, moduleName) + '.cpp', 'w')
            module(out, allInOne, done, cppdir, moduleName, shared)
            out.close()
            if build or install or dist:
                compile(env, os.path.dirname(args[0]), output, moduleName,
                        install, dist, debug, jars, version,
                        prefix, root, install_dir, use_distutils,
                        shared, compiler, modules, wininst)


def header(env, out, cls, typeset, packages, excludes):

    names = cls.getName().split('.')
    superCls = cls.getSuperclass()
    declares = set([cls.getClass()])

    interfaces = []
    for interface in cls.getInterfaces():
        if superCls and interface.isAssignableFrom(superCls):
            continue
        if known(interface, typeset, declares, packages, excludes):
            interfaces.append(interface)

    if cls.isInterface():
        if interfaces:
            superCls = interfaces.pop(0)
        else:
            superCls = findClass('java/lang/Object')
        superClsName = superCls.getName()
    elif superCls:
        superClsName = superCls.getName()
    else:
        superClsName = 'JObject'

    constructors = []
    for constructor in cls.getDeclaredConstructors():
        if Modifier.isPublic(constructor.getModifiers()):
            params = constructor.getParameterTypes()
            if len(params) == 1 and params[0] == cls:
                continue
            for param in params:
                if not known(param, typeset, declares, packages, excludes):
                    break
            else:
                constructors.append(constructor)
    sort(constructors, key=lambda x: len(x.getParameterTypes()))

    methods = {}
    protectedMethods = []
    for method in cls.getDeclaredMethods():
        modifiers = method.getModifiers()
        if Modifier.isPublic(modifiers):
            returnType = method.getReturnType()
            if not known(returnType, typeset, declares, packages, excludes):
                continue
            sig = "%s:%s" %(method.getName(), signature(method, True))
            if sig in methods and returnType != cls:
                continue
            for param in method.getParameterTypes():
                if not known(param, typeset, declares, packages, excludes):
                    break
            else:
                methods[sig] = method
        elif Modifier.isProtected(modifiers):
            protectedMethods.append(method)
    for interface in interfaces:
        for method in interface.getMethods():
            sig = "%s:%s" %(method.getName(), signature(method, True))
            if sig not in methods:
                param = method.getReturnType()
                if not known(param, typeset, declares, packages, excludes):
                    continue
                for param in method.getParameterTypes():
                    if not known(param, typeset, declares, packages, excludes):
                        break
                else:
                    methods[sig] = method

    def _compare(m0, m1):
        value = cmp(m0.getName(), m1.getName())
        if value == 0:
            value = len(m0.getParameterTypes()) - len(m1.getParameterTypes())
        return value

    methods = methods.values()
    sort(methods, fn=_compare)

    for constructor in constructors:
        for exception in constructor.getExceptionTypes():
            known(exception, typeset, declares, packages, excludes)
    for method in methods:
        for exception in method.getExceptionTypes():
            known(exception, typeset, declares, packages, excludes)

    fields = []
    instanceFields = []
    for field in cls.getDeclaredFields():
        modifiers = field.getModifiers()
        if Modifier.isPublic(modifiers):
            if not known(field.getType(),
                         typeset, declares, packages, excludes):
                continue
            if Modifier.isStatic(modifiers):
                fields.append(field)
            else:
                instanceFields.append(field)
    sort(fields, key=lambda x: x.getName())
    sort(instanceFields, key=lambda x: x.getName())

    line(out)
    superNames = superClsName.split('.')
    line(out, 0, '#include "%s.h"', '/'.join(superNames))

    line(out, 0)
    namespaces = {}
    for declare in declares:
        namespace = namespaces
        if declare not in (cls, superCls):
            declareNames = declare.getName().split('.')
            for declareName in declareNames[:-1]:
                namespace = namespace.setdefault(declareName, {})
            namespace[declareNames[-1]] = True
    forward(out, namespaces, 0)
    line(out, 0, 'template<class T> class JArray;')

    indent = 0;
    line(out)
    for name in names[:-1]:
        line(out, indent, 'namespace %s {', cppname(name))
        indent += 1

    line(out)
    if superClsName == 'JObject':
        line(out, indent, 'class %s : public JObject {', cppname(names[-1]))
    else:
        line(out, indent, 'class %s : public %s {',
             cppname(names[-1]), '::'.join(cppnames(superNames)))
        
    line(out, indent, 'public:')
    indent += 1

    if methods or protectedMethods or constructors:
        line(out, indent, 'enum {')
        for constructor in constructors:
            line(out, indent + 1, 'mid_init$_%s,',
                 env.strhash(signature(constructor)))
        for method in methods:
            line(out, indent + 1, 'mid_%s_%s,', method.getName(),
                 env.strhash(signature(method)))
        for method in protectedMethods:
            line(out, indent + 1, 'mid_%s_%s,', method.getName(),
                 env.strhash(signature(method)))
        line(out, indent + 1, 'max_mid')
        line(out, indent, '};')

    if instanceFields:
        line(out)
        line(out, indent, 'enum {')
        for field in instanceFields:
            line(out, indent + 1, 'fid_%s,', field.getName())
        line(out, indent + 1, 'max_fid')
        line(out, indent, '};')

    line(out)
    line(out, indent, 'static java::lang::Class *class$;');
    line(out, indent, 'static jmethodID *mids$;');
    if instanceFields:
        line(out, indent, 'static jfieldID *fids$;');
    line(out, indent, 'static jclass initializeClass();');
    line(out)

    line(out, indent, 'explicit %s(jobject obj) : %s(obj) {',
         cppname(names[-1]), '::'.join(cppnames(superNames)))
    line(out, indent + 1, 'if (obj != NULL)');
    line(out, indent + 2, 'initializeClass();')
    line(out, indent, '}')
    line(out, indent, '%s(const %s& obj) : %s(obj) {}',
         cppname(names[-1]), cppname(names[-1]),
         '::'.join(cppnames(superNames)))

    if fields:
        line(out)
        for field in fields:
            fieldType = field.getType()
            fieldName = cppname(field.getName())
            if fieldType.isPrimitive():
                line(out, indent, 'static %s %s;',
                     typename(fieldType, cls, False), fieldName)
            else:
                line(out, indent, 'static %s *%s;',
                     typename(fieldType, cls, False), fieldName)

    if instanceFields:
        line(out)
        for field in instanceFields:
            fieldType = field.getType()
            fieldName = field.getName()
            modifiers = field.getModifiers()
            line(out, indent, '%s _get_%s() const;',
                 typename(fieldType, cls, False), fieldName)
            if not Modifier.isFinal(modifiers):
                line(out, indent, 'void _set_%s(%s) const;',
                     fieldName, typename(fieldType, cls, True))

    if constructors:
        line(out)
        for constructor in constructors:
            params = [typename(param, cls, True)
                      for param in constructor.getParameterTypes()]
            line(out, indent, '%s(%s);', cppname(names[-1]), ', '.join(params))

    if methods:
        line(out)
        for method in methods:
            modifiers = method.getModifiers()
            if Modifier.isStatic(modifiers):
                prefix = 'static '
                const = ''
            else:
                prefix = ''
                const = ' const'
            params = [typename(param, cls, True)
                      for param in method.getParameterTypes()]
            methodName = cppname(method.getName())
            line(out, indent, '%s%s %s(%s)%s;',
                 prefix, typename(method.getReturnType(), cls, False),
                 methodName, ', '.join(params), const)

    indent -= 1
    line(out, indent, '};')

    while indent:
        indent -= 1
        line(out, indent, '}')

    return (superCls, constructors, methods, protectedMethods,
            fields, instanceFields, declares)


def code(env, out, cls, superCls, constructors, methods, protectedMethods,
         fields, instanceFields, declares, typeset, excludes):

    className = cls.getName()
    names = className.split('.')

    if superCls:
        superClsName = superCls.getName()
    else:
        superClsName = 'JObject'
    superNames = superClsName.split('.')

    line(out, 0, '#include <jni.h>')
    line(out, 0, '#include "JCCEnv.h"')
    line(out, 0, '#include "%s.h"', className.replace('.', '/'))
    for declare in declares:
        if declare not in (cls, superCls):
            line(out, 0, '#include "%s.h"', declare.getName().replace('.', '/'))
    line(out, 0, '#include "JArray.h"')

    indent = 0
    line(out)
    for name in names[:-1]:
        line(out, indent, 'namespace %s {', cppname(name))
        indent += 1

    line(out)
    line(out, indent, 'java::lang::Class *%s::class$ = NULL;',
         cppname(names[-1]))
    line(out, indent, 'jmethodID *%s::mids$ = NULL;', cppname(names[-1]))
    if instanceFields:
        line(out, indent, 'jfieldID *%s::fids$ = NULL;', cppname(names[-1]))

    for field in fields:
        fieldType = field.getType()
        fieldName = cppname(field.getName())
        typeName = typename(fieldType, cls, False)
        if fieldType.isPrimitive():
            line(out, indent, '%s %s::%s = (%s) 0;',
                 typeName, cppname(names[-1]), fieldName, typeName)
        else:
            line(out, indent, '%s *%s::%s = NULL;',
                 typeName, cppname(names[-1]), fieldName)

    line(out)
    line(out, indent, 'jclass %s::initializeClass()', cppname(names[-1]))
    line(out, indent, '{')
    line(out, indent + 1, 'if (!class$)')
    line(out, indent + 1, '{')
    line(out)
    line(out, indent + 2, 'jclass cls = (jclass) env->findClass("%s");',
         className.replace('.', '/'))

    if methods or protectedMethods or constructors:
        line(out)
        line(out, indent + 2, 'mids$ = new jmethodID[max_mid];')
        for constructor in constructors:
            sig = signature(constructor)
            line(out, indent + 2,
                 'mids$[mid_init$_%s] = env->getMethodID(cls, "<init>", "%s");',
                 env.strhash(sig), sig)
        isExtension = False
        for method in methods:
            methodName = method.getName()
            if methodName == 'pythonExtension':
                isExtension = True
            sig = signature(method)
            line(out, indent + 2,
                 'mids$[mid_%s_%s] = env->get%sMethodID(cls, "%s", "%s");',
                 methodName, env.strhash(sig),
                 Modifier.isStatic(method.getModifiers()) and 'Static' or '',
                 methodName, sig)
        for method in protectedMethods:
            methodName = method.getName()
            sig = signature(method)
            line(out, indent + 2,
                 'mids$[mid_%s_%s] = env->get%sMethodID(cls, "%s", "%s");',
                 methodName, env.strhash(sig),
                 Modifier.isStatic(method.getModifiers()) and 'Static' or '',
                 methodName, sig)

    if instanceFields:
        line(out)
        line(out, indent + 2, 'fids$ = new jfieldID[max_fid];')
        for field in instanceFields:
            fieldName = field.getName()
            line(out, indent + 2,
                 'fids$[fid_%s] = env->getFieldID(cls, "%s", "%s");',
                 fieldName, fieldName, signature(field))

    line(out)
    line(out, indent + 2, 'class$ = (java::lang::Class *) new JObject(cls);')

    if fields:
        line(out, indent + 2, 'cls = (jclass) class$->this$;')
        line(out)
        for field in fields:
            fieldType = field.getType()
            fieldName = field.getName()
            if fieldType.isPrimitive():
                line(out, indent + 2,
                     '%s = env->getStatic%sField(cls, "%s");',
                     cppname(fieldName), fieldType.getName().capitalize(),
                     fieldName)
            else:
                line(out, indent + 2,
                     '%s = new %s(env->getStaticObjectField(cls, "%s", "%s"));',
                     cppname(fieldName), typename(fieldType, cls, False),
                     fieldName, signature(field))

    line(out, indent + 1, '}')
    line(out, indent + 1, 'return (jclass) class$->this$;')
    line(out, indent, '}')

    for constructor in constructors:
        line(out)
        sig = signature(constructor)
        decls, args = argnames(constructor.getParameterTypes(), cls)

        line(out, indent, "%s::%s(%s) : %s(env->newObject(initializeClass, &mids$, mid_init$_%s%s)) {}",
             cppname(names[-1]), cppname(names[-1]), decls,
             '::'.join(cppnames(superNames)),
             env.strhash(sig), args)

    for method in methods:
        modifiers = method.getModifiers()
        returnType = method.getReturnType()
        params = method.getParameterTypes()
        methodName = method.getName()
        superMethod = None
        isStatic = Modifier.isStatic(modifiers)

        if (isExtension and not isStatic and superCls and
            Modifier.isNative(modifiers)):
            superMethod = find_method(superCls, methodName, params)
            if superMethod is None:
                continue

        if isStatic:
            qualifier = 'Static'
            this = 'cls'
            midns = ''
            const = ''
        else:
            isStatic = False
            if superMethod is not None:
                qualifier = 'Nonvirtual'
                this = 'this$, (jclass) %s::class$->this$' %('::'.join(cppnames(superNames)))
                declaringClass = superMethod.getDeclaringClass()
                midns = '%s::' %(typename(declaringClass, cls, False))
            else:
                qualifier = ''
                this = 'this$'
                midns = ''
            const = ' const'

        sig = signature(method)
        decls, args = argnames(params, cls)

        line(out)
        line(out, indent, '%s %s::%s(%s)%s',
             typename(returnType, cls, False), cppname(names[-1]),
             cppname(methodName), decls, const)
        line(out, indent, '{')
        if isStatic:
            line(out, indent + 1, 'jclass cls = initializeClass();');
        if returnType.isPrimitive():
            line(out, indent + 1,
                 '%senv->call%s%sMethod(%s, %smids$[%smid_%s_%s]%s);',
                 not returnType.getName() == 'void' and 'return ' or '',
                 qualifier, returnType.getName().capitalize(), this,
                 midns, midns, methodName, env.strhash(sig), args)
        else:
            line(out, indent + 1,
                 'return %s(env->call%sObjectMethod(%s, %smids$[%smid_%s_%s]%s));',
                 typename(returnType, cls, False), qualifier, this,
                 midns, midns, methodName, env.strhash(sig), args)
        line(out, indent, '}')

    if instanceFields:
        for field in instanceFields:
            fieldType = field.getType()
            fieldName = field.getName()
            line(out)
            line(out, indent, '%s %s::_get_%s() const',
                 typename(fieldType, cls, False), cppname(names[-1]), fieldName)
            line(out, indent, '{')
            if fieldType.isPrimitive():
                line(out, indent + 1,
                     'return env->get%sField(this$, fids$[fid_%s]);',
                     fieldType.getName().capitalize(), fieldName)
            else:
                line(out, indent + 1,
                     'return %s(env->getObjectField(this$, fids$[fid_%s]));',
                     typename(fieldType, cls, False), fieldName)
            line(out, indent, '}')

            if not Modifier.isFinal(field.getModifiers()):
                line(out)
                line(out, indent, 'void %s::_set_%s(%s a0) const',
                     cppname(names[-1]), fieldName,
                     typename(fieldType, cls, True))
                line(out, indent, '{')
                if fieldType.isPrimitive():
                    line(out, indent + 1,
                         'env->set%sField(this$, fids$[fid_%s], a0);',
                         fieldType.getName().capitalize(), fieldName)
                else:
                    line(out, indent + 1,
                         'env->setObjectField(this$, fids$[fid_%s], a0.this$);',
                         fieldName)
                line(out, indent, '}')

    while indent:
        indent -= 1
        line(out, indent, '}')

    return names, superNames


if __name__ == '__main__':
    jcc(sys.argv)
