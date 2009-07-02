/*
 *   Licensed under the Apache License, Version 2.0 (the "License");
 *   you may not use this file except in compliance with the License.
 *   You may obtain a copy of the License at
 *
 *       http://www.apache.org/licenses/LICENSE-2.0
 *
 *   Unless required by applicable law or agreed to in writing, software
 *   distributed under the License is distributed on an "AS IS" BASIS,
 *   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 *   See the License for the specific language governing permissions and
 *   limitations under the License.
 */

#ifndef _functions_h
#define _functions_h

#include "java/util/Iterator.h"
#include "java/util/Enumeration.h"
#include "java/lang/String.h"
#include "java/lang/Object.h"
#include "macros.h"

#if PY_VERSION_HEX < 0x02050000
typedef int Py_ssize_t;
typedef inquiry lenfunc;
typedef intargfunc ssizeargfunc;
typedef intintargfunc ssizessizeargfunc;
typedef intobjargproc ssizeobjargproc;
typedef intintobjargproc ssizessizeobjargproc;
#endif

typedef jclass (*getclassfn)(void);

PyObject *PyErr_SetArgsError(char *name, PyObject *args);
PyObject *PyErr_SetArgsError(PyObject *self, char *name, PyObject *args);
PyObject *PyErr_SetArgsError(PyTypeObject *type, char *name, PyObject *args);
PyObject *PyErr_SetJavaError(jthrowable throwable);

extern PyObject *PyExc_JavaError;
extern PyObject *PyExc_InvalidArgsError;


void throwPythonError(void);
void throwTypeError(const char *name, PyObject *object);

#if defined(_MSC_VER) || defined(__SUNPRO_CC)

#define parseArgs __parseArgs
#define parseArg __parseArg

int __parseArgs(PyObject *args, char *types, ...);
int __parseArg(PyObject *arg, char *types, ...);

int _parseArgs(PyObject **args, unsigned int count, char *types,
	       va_list list, va_list check);

#else

#define parseArgs(args, types, rest...) \
    _parseArgs(((PyTupleObject *)(args))->ob_item, \
               ((PyTupleObject *)(args))->ob_size, types, ##rest)

#define parseArg(arg, types, rest...) \
    _parseArgs(&(arg), 1, types, ##rest)

int _parseArgs(PyObject **args, unsigned int count, char *types, ...);

#endif

int abstract_init(PyObject *self, PyObject *args, PyObject *kwds);

PyObject *j2p(const java::lang::String& js);
java::lang::String p2j(PyObject *object);

PyObject *make_descriptor(PyTypeObject *value);
PyObject *make_descriptor(getclassfn initializeClass);
PyObject *make_descriptor(PyObject *value);
PyObject *make_descriptor(PyObject *(*wrapfn)(const jobject &));
PyObject *make_descriptor(jboolean value);
PyObject *make_descriptor(jbyte value);
PyObject *make_descriptor(jchar value);
PyObject *make_descriptor(jdouble value);
PyObject *make_descriptor(jfloat value);
PyObject *make_descriptor(jint value);
PyObject *make_descriptor(jlong value);
PyObject *make_descriptor(jshort value);

jobjectArray make_array(jclass cls, PyObject *sequence);

PyObject *callSuper(PyTypeObject *type,
                    const char *name, PyObject *args, int cardinality);
PyObject *callSuper(PyTypeObject *type, PyObject *self,
                    const char *name, PyObject *args, int cardinality);

template<class T> PyObject *get_iterator(T *self)
{
    java::util::Iterator iterator((jobject) NULL);

    OBJ_CALL(iterator = self->object.iterator());
    return java::util::t_Iterator::wrap_Object(iterator);
}

template<class T, class U, class V> PyObject *get_iterator_next(T *self)
{
    jboolean hasNext;

    OBJ_CALL(hasNext = self->object.hasNext());
    if (!hasNext)
    {
        PyErr_SetNone(PyExc_StopIteration);
        return NULL;
    }

    V next((jobject) NULL);
    OBJ_CALL(next = self->object.next());

    jclass cls = java::lang::String::initializeClass();
    if (env->get_vm_env()->IsInstanceOf(next.this$, cls))
        return env->fromJString((jstring) next.this$);

    return U::wrap_Object(next);
}

template<class T, class U, class V> PyObject *get_enumeration_next(T *self)
{
    jboolean hasMoreElements;

    OBJ_CALL(hasMoreElements = self->object.hasMoreElements());
    if (!hasMoreElements)
    {
        PyErr_SetNone(PyExc_StopIteration);
        return NULL;
    }

    V next((jobject) NULL);
    OBJ_CALL(next = self->object.nextElement());

    jclass cls = java::lang::String::initializeClass();
    if (env->get_vm_env()->IsInstanceOf(next.this$, cls))
        return env->fromJString((jstring) next.this$);

    return U::wrap_Object(next);
}

template<class T, class U, class V> PyObject *get_next(T *self)
{
    V next((jobject) NULL);

    OBJ_CALL(next = self->object.next());
    if (!next)
    {
        PyErr_SetNone(PyExc_StopIteration);
        return NULL;
    }
        
    jclass cls = java::lang::String::initializeClass();
    if (env->get_vm_env()->IsInstanceOf(next.this$, cls))
        return env->fromJString((jstring) next.this$);

    return U::wrap_Object(next);
}

PyObject *get_extension_iterator(PyObject *self);
PyObject *get_extension_next(PyObject *self);
PyObject *get_extension_nextElement(PyObject *self);

jobjectArray fromPySequence(jclass cls, PyObject *sequence);
PyObject *castCheck(PyObject *obj, getclassfn initializeClass,
                    int reportError);
void installType(PyTypeObject *type, PyObject *module, char *name,
                 int isExtension);

extern PyTypeObject FinalizerClass$$Type;
extern PyTypeObject FinalizerProxy$$Type;

typedef struct {
    PyObject_HEAD
    PyObject *object;
} t_fp;

#endif /* _functions_h */
