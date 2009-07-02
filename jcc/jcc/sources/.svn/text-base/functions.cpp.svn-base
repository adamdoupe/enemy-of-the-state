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

#include <jni.h>
#include <stdarg.h>

#include "java/lang/Object.h"
#include "java/lang/Class.h"
#include "java/lang/String.h"
#include "java/lang/Throwable.h"
#include "java/lang/Boolean.h"
#include "java/lang/Integer.h"
#include "java/lang/Long.h"
#include "java/lang/Double.h"
#include "java/util/Iterator.h"
#include "JArray.h"
#include "functions.h"
#include "macros.h"

using namespace java::lang;
using namespace java::util;

PyObject *PyExc_JavaError = PyExc_ValueError;
PyObject *PyExc_InvalidArgsError = PyExc_ValueError;

PyObject *_setExceptionTypes(PyObject *self, PyObject *args)
{
    if (!PyArg_ParseTuple(args, "OO",
                          &PyExc_JavaError, &PyExc_InvalidArgsError))
        return NULL;

    Py_RETURN_NONE;
}

PyObject *findClass(PyObject *self, PyObject *args)
{
    char *className;

    if (!PyArg_ParseTuple(args, "s", &className))
        return NULL;

    try {
        jclass cls = env->findClass(className);

        if (cls)
            return t_Class::wrap_Object(Class(cls));
    } catch (JCCEnv::pythonError e) {
        return NULL;
    } catch (JCCEnv::exception e) {
        PyErr_SetJavaError(e.throwable);
        return NULL;
    }

    Py_RETURN_NONE;
}


#if defined(_MSC_VER) || defined(__SUNPRO_CC)
int __parseArgs(PyObject *args, char *types, ...)
{
    int count = ((PyTupleObject *)(args))->ob_size;
    va_list list, check;

    va_start(list, types);
    va_start(check, types);

    return _parseArgs(((PyTupleObject *)(args))->ob_item, count, types,
		      list, check);
}

int __parseArg(PyObject *arg, char *types, ...)
{
    va_list list, check;

    va_start(list, types);
    va_start(check, types);

    return _parseArgs(&arg, 1, types, list, check);
}

int _parseArgs(PyObject **args, unsigned int count, char *types,
	       va_list list, va_list check)
{
    unsigned int typeCount = strlen(types);

    if (count > typeCount)
        return -1;
#else

int _parseArgs(PyObject **args, unsigned int count, char *types, ...)
{
    unsigned int typeCount = strlen(types);
    va_list list, check;

    if (count > typeCount)
        return -1;

    va_start(list, types);
    va_start(check, types);
#endif

    if (!env->vm)
    {
        PyErr_SetString(PyExc_RuntimeError, "initVM() must be called first");
        return -1;
    }

    JNIEnv *vm_env = env->get_vm_env();

    if (!vm_env)
    {
        PyErr_SetString(PyExc_RuntimeError, "attachCurrentThread() must be called first");
        return -1;
    }

    unsigned int pos = 0;
    int array = 0;

    for (unsigned int a = 0; a < count; a++, pos++) {
        PyObject *arg = args[a];

        switch (types[pos]) {
          case '[':
          {
              if (++array > 1)
                  return -1;

              a -= 1;
              break;
          }

          case 'j':           /* Java object, with class$    */
          case 'k':           /* Java object, with initializeClass */
          {
              jclass cls = NULL;

              switch (types[pos]) {
                case 'j':
                  cls = (jclass) va_arg(list, Class *)->this$;
                  break;
                case 'k':
                  try {
                      getclassfn initializeClass = va_arg(list, getclassfn);
                      cls = (*initializeClass)();
                  } catch (JCCEnv::pythonError e) {
                      return -1;
                  } catch (JCCEnv::exception e) {
                      PyErr_SetJavaError(e.throwable);
                      return -1;
                  }
                  break;
              }

              if (arg == Py_None)
                  break;

              /* ensure that class Class is initialized (which may not be the
               * case because of earlier recursion avoidance (JObject(cls)).
               */
              if (!Class::class$)
                  Class::initializeClass();

              if (array)
              {
                  if (PyObject_TypeCheck(arg, JArrayObject$$Type))
                      break;

                  if (PySequence_Check(arg) &&
                      !PyString_Check(arg) && !PyUnicode_Check(arg))
                  {
                      if (PySequence_Length(arg) > 0)
                      {
                          PyObject *obj = PySequence_GetItem(arg, 0);
                          int ok =
                              (obj == Py_None ||
                               (PyObject_TypeCheck(obj, &Object$$Type) &&
                                vm_env->IsInstanceOf(((t_Object *) obj)->object.this$, cls)));

                          Py_DECREF(obj);
                          if (ok)
                              break;
                      }
                      else
                          break;
                  }
              }
              else if (PyObject_TypeCheck(arg, &Object$$Type) &&
                       vm_env->IsInstanceOf(((t_Object *) arg)->object.this$, cls))
                  break;
              else if (PyObject_TypeCheck(arg, &FinalizerProxy$$Type))
              {
                  arg = ((t_fp *) arg)->object;
                  if (PyObject_TypeCheck(arg, &Object$$Type) &&
                      vm_env->IsInstanceOf(((t_Object *) arg)->object.this$, cls))
                      break;
              }

              return -1;
          }

          case 'Z':           /* boolean, strict */
          {
              if (array)
              {
                  if (arg == Py_None)
                      break;

                  if (PyObject_TypeCheck(arg, JArrayBool$$Type))
                      break;

                  if (PySequence_Check(arg))
                  {
                      if (PySequence_Length(arg) > 0)
                      {
                          PyObject *obj = PySequence_GetItem(arg, 0);
                          int ok = obj == Py_True || obj == Py_False;

                          Py_DECREF(obj);
                          if (ok)
                              break;
                      }
                      else
                          break;
                  }
              }
              else if (arg == Py_True || arg == Py_False)
                  break;

              return -1;
          }

          case 'B':           /* byte */
          {
              if (array)
              {
                  if (arg == Py_None)
                      break;
                  if (PyObject_TypeCheck(arg, JArrayByte$$Type))
                      break;
              }
              else if (PyString_Check(arg) && (PyString_Size(arg) == 1))
                  break;
              return -1;
          }

          case 'C':           /* char */
          {
              if (array)
              {
                  if (arg == Py_None)
                      break;
                  if (PyObject_TypeCheck(arg, JArrayChar$$Type))
                      break;
              }
              else if (PyUnicode_Check(arg) && PyUnicode_GET_SIZE(arg) == 1)
                  break;
              return -1;
          }

          case 'I':           /* int */
          {
              if (array)
              {
                  if (arg == Py_None)
                      break;

                  if (PyObject_TypeCheck(arg, JArrayInt$$Type))
                      break;

                  if (PySequence_Check(arg))
                  {
                      if (PySequence_Length(arg) > 0)
                      {
                          PyObject *obj = PySequence_GetItem(arg, 0);
                          int ok = PyInt_CheckExact(obj);

                          Py_DECREF(obj);
                          if (ok)
                              break;
                      }
                      else
                          break;
                  }
              }
              else if (PyInt_CheckExact(arg))
                  break;

              return -1;
          }

          case 'S':           /* short */
          {
              if (array)
              {
                  if (arg == Py_None)
                      break;

                  if (PyObject_TypeCheck(arg, JArrayShort$$Type))
                      break;

                  if (PySequence_Check(arg))
                  {
                      if (PySequence_Length(arg) > 0)
                      {
                          PyObject *obj = PySequence_GetItem(arg, 0);
                          int ok = PyInt_CheckExact(obj);

                          Py_DECREF(obj);
                          if (ok)
                              break;
                      }
                      else
                          break;
                  }
              }
              else if (PyInt_CheckExact(arg))
                  break;

              return -1;
          }

          case 'D':           /* double */
          {
              if (array)
              {
                  if (arg == Py_None)
                      break;

                  if (PyObject_TypeCheck(arg, JArrayDouble$$Type))
                      break;

                  if (PySequence_Check(arg))
                  {
                      if (PySequence_Length(arg) > 0)
                      {
                          PyObject *obj = PySequence_GetItem(arg, 0);
                          int ok = PyFloat_CheckExact(obj);

                          Py_DECREF(obj);
                          if (ok)
                              break;
                      }
                      else
                          break;
                  }
              }
              else if (PyFloat_CheckExact(arg))
                  break;

              return -1;
          }

          case 'F':           /* float */
          {
              if (array)
              {
                  if (arg == Py_None)
                      break;

                  if (PyObject_TypeCheck(arg, JArrayFloat$$Type))
                      break;

                  if (PySequence_Check(arg))
                  {
                      if (PySequence_Length(arg) > 0)
                      {
                          PyObject *obj = PySequence_GetItem(arg, 0);
                          int ok = PyFloat_CheckExact(obj);

                          Py_DECREF(obj);
                          if (ok)
                              break;
                      }
                      else
                          break;
                  }
              }
              else if (PyFloat_CheckExact(arg))
                  break;

              return -1;
          }

          case 'J':           /* long long */
          {
              if (array)
              {
                  if (arg == Py_None)
                      break;

                  if (PyObject_TypeCheck(arg, JArrayLong$$Type))
                      break;

                  if (PySequence_Check(arg))
                  {
                      if (PySequence_Length(arg) > 0)
                      {
                          PyObject *obj = PySequence_GetItem(arg, 0);
                          int ok = PyLong_CheckExact(obj);

                          Py_DECREF(obj);
                          if (ok)
                              break;
                      }
                      else
                          break;
                  }
              }
              else if (PyLong_CheckExact(arg))
                  break;

              return -1;
          }

          case 's':           /* string  */
          {
              if (array)
              {
                  if (arg == Py_None)
                      break;

                  if (PyObject_TypeCheck(arg, JArrayString$$Type))
                      break;

                  if (PySequence_Check(arg) && 
                      !PyString_Check(arg) && !PyUnicode_Check(arg))
                  {
                      if (PySequence_Length(arg) > 0)
                      {
                          PyObject *obj = PySequence_GetItem(arg, 0);
                          int ok =
                              (obj == Py_None ||
                               PyString_Check(obj) || PyUnicode_Check(obj));

                          Py_DECREF(obj);
                          if (ok)
                              break;
                      }
                      else
                          break;
                  }
              }
              else if (arg == Py_None ||
                       PyString_Check(arg) || PyUnicode_Check(arg))
                  break;

              return -1;
          }

          case 'o':         /* java.lang.Object */
            break;

          default:
            return -1;
        }

        if (types[pos] != '[')
            array = 0;
    }

    if (array)
        return -1;

    pos = 0;

    for (unsigned int a = 0; a < count; a++, pos++) {
        PyObject *arg = args[a];
        
        switch (types[pos]) {
          case '[':
          {
              if (++array > 1)
                  return -1;

              a -= 1;
              break;
          }

          case 'j':           /* Java object except String and Object */
          case 'k':           /* Java object, with initializeClass    */
          {
              jclass cls = NULL;

              switch (types[pos]) {
                case 'j':
                  cls = (jclass) va_arg(check, Class *)->this$;
                  break;
                case 'k':
                  getclassfn initializeClass = va_arg(check, getclassfn);
                  cls = (*initializeClass)();
              }

              if (array)
              {
                  JArray<jobject> *array = va_arg(list, JArray<jobject> *);

                  if (arg == Py_None)
                      *array = JArray<jobject>((jobject) NULL);
                  else if (PyObject_TypeCheck(arg, JArrayObject$$Type))
                      *array = ((t_jarray<jobject> *) arg)->array;
                  else 
                      *array = JArray<jobject>(cls, arg);

                  if (PyErr_Occurred())
                      return -1;
              }
              else
              {
                  Object *obj = va_arg(list, Object *);

                  if (PyObject_TypeCheck(arg, &FinalizerProxy$$Type))
                      arg = ((t_fp *) arg)->object;

                  *obj = arg == Py_None
                      ? Object(NULL)
                      : ((t_Object *) arg)->object;
              }
              break;
          }

          case 'Z':           /* boolean, strict */
          {
              if (array)
              {
                  JArray<jboolean> *array = va_arg(list, JArray<jboolean> *);

                  if (arg == Py_None)
                      *array = JArray<jboolean>((jobject) NULL);
                  else if (PyObject_TypeCheck(arg, JArrayBool$$Type))
                      *array = ((t_jarray<jboolean> *) arg)->array;
                  else
                      *array = JArray<jboolean>(arg);

                  if (PyErr_Occurred())
                      return -1;
              }
              else
              {
                  jboolean *b = va_arg(list, jboolean *);
                  *b = arg == Py_True;
              }
              break;
          }

          case 'B':           /* byte */
          {
              if (array)
              {
                  JArray<jbyte> *array = va_arg(list, JArray<jbyte> *);

                  if (arg == Py_None)
                      *array = JArray<jbyte>((jobject) NULL);
                  else if (PyObject_TypeCheck(arg, JArrayByte$$Type))
                      *array = ((t_jarray<jbyte> *) arg)->array;
                  else 
                      *array = JArray<jbyte>(arg);

                  if (PyErr_Occurred())
                      return -1;
              }
              else
              {
                  jbyte *a = va_arg(list, jbyte *);
                  *a = (jbyte) PyString_AS_STRING(arg)[0];
              }
              break;
          }

          case 'C':           /* char */
          {
              if (array)
              {
                  JArray<jchar> *array = va_arg(list, JArray<jchar> *);

                  if (arg == Py_None)
                      *array = JArray<jchar>((jobject) NULL);
                  else if (PyObject_TypeCheck(arg, JArrayChar$$Type))
                      *array = ((t_jarray<jchar> *) arg)->array;
                  else 
                      *array = JArray<jchar>(arg);

                  if (PyErr_Occurred())
                      return -1;
              }
              else
              {
                  jchar *c = va_arg(list, jchar *);
                  *c = (jchar) PyUnicode_AS_UNICODE(arg)[0];
              }
              break;
          }

          case 'I':           /* int */
          {
              if (array)
              {
                  JArray<jint> *array = va_arg(list, JArray<jint> *);

                  if (arg == Py_None)
                      *array = JArray<jint>((jobject) NULL);
                  else if (PyObject_TypeCheck(arg, JArrayInt$$Type))
                      *array = ((t_jarray<jint> *) arg)->array;
                  else 
                      *array = JArray<jint>(arg);

                  if (PyErr_Occurred())
                      return -1;
              }
              else
              {
                  jint *n = va_arg(list, jint *);
                  *n = (jint) PyInt_AsLong(arg);
              }
              break;
          }

          case 'S':           /* short */
          {
              if (array)
              {
                  JArray<jshort> *array = va_arg(list, JArray<jshort> *);

                  if (arg == Py_None)
                      *array = JArray<jshort>((jobject) NULL);
                  else if (PyObject_TypeCheck(arg, JArrayShort$$Type))
                      *array = ((t_jarray<jshort> *) arg)->array;
                  else 
                      *array = JArray<jshort>(arg);

                  if (PyErr_Occurred())
                      return -1;
              }
              else
              {
                  jshort *n = va_arg(list, jshort *);
                  *n = (jshort) PyInt_AsLong(arg);
              }
              break;
          }

          case 'D':           /* double */
          {
              if (array)
              {
                  JArray<jdouble> *array = va_arg(list, JArray<jdouble> *);

                  if (arg == Py_None)
                      *array = JArray<jdouble>((jobject) NULL);
                  else if (PyObject_TypeCheck(arg, JArrayDouble$$Type))
                      *array = ((t_jarray<jdouble> *) arg)->array;
                  else 
                      *array = JArray<jdouble>(arg);

                  if (PyErr_Occurred())
                      return -1;
              }
              else
              {
                  jdouble *d = va_arg(list, jdouble *);
                  *d = (jdouble) PyFloat_AsDouble(arg);
              }
              break;
          }

          case 'F':           /* float */
          {
              if (array)
              {
                  JArray<jfloat> *array = va_arg(list, JArray<jfloat> *);

                  if (arg == Py_None)
                      *array = JArray<jfloat>((jobject) NULL);
                  else if (PyObject_TypeCheck(arg, JArrayFloat$$Type))
                      *array = ((t_jarray<jfloat> *) arg)->array;
                  else 
                      *array = JArray<jfloat>(arg);

                  if (PyErr_Occurred())
                      return -1;
              }
              else
              {
                  jfloat *d = va_arg(list, jfloat *);
                  *d = (jfloat) (float) PyFloat_AsDouble(arg);
              }
              break;
          }

          case 'J':           /* long long */
          {
              if (array)
              {
                  JArray<jlong> *array = va_arg(list, JArray<jlong> *);

                  if (arg == Py_None)
                      *array = JArray<jlong>((jobject) NULL);
                  else if (PyObject_TypeCheck(arg, JArrayLong$$Type))
                      *array = ((t_jarray<jlong> *) arg)->array;
                  else 
                      *array = JArray<jlong>(arg);

                  if (PyErr_Occurred())
                      return -1;
              }
              else
              {
                  jlong *l = va_arg(list, jlong *);
                  *l = (jlong) PyLong_AsLongLong(arg);
              }
              break;
          }

          case 's':           /* string  */
          {
              if (array)
              {
                  JArray<jstring> *array = va_arg(list, JArray<jstring> *);

                  if (arg == Py_None)
                      *array = JArray<jstring>((jobject) NULL);
                  else if (PyObject_TypeCheck(arg, JArrayString$$Type))
                      *array = ((t_jarray<jstring> *) arg)->array;
                  else 
                      *array = JArray<jstring>(arg);

                  if (PyErr_Occurred())
                      return -1;
              }
              else
              {
                  String *str = va_arg(list, String *);

                  if (arg == Py_None)
                      *str = String(NULL);
                  else
                  {
                      *str = p2j(arg);
                      if (PyErr_Occurred())
                          return -1;
                  }
              }
              break;
          }

          case 'o':           /* java.lang.Object  */
          {
              if (array)
              {
                  JArray<Object> *array = va_arg(list, JArray<Object> *);

                  if (arg == Py_None)
                      *array = JArray<Object>((jobject) NULL);
                  else 
                      *array = JArray<Object>(arg);

                  if (PyErr_Occurred())
                      return -1;
              }
              else
              {
                  Object *obj = va_arg(list, Object *);

                  if (arg == Py_None)
                      *obj = Object(NULL);
                  else if (PyObject_TypeCheck(arg, &Object$$Type))
                      *obj = ((t_Object *) arg)->object;
                  else if (PyObject_TypeCheck(arg, &FinalizerProxy$$Type))
                  {
                      arg = ((t_fp *) arg)->object;
                      if (PyObject_TypeCheck(arg, &Object$$Type))
                          *obj = ((t_Object *) arg)->object;
                      else
                          return -1;
                  }
                  else if (PyString_Check(arg) || PyUnicode_Check(arg))
                  {
                      *obj = p2j(arg);
                      if (PyErr_Occurred())
                          return -1;
                  }
                  else if (arg == Py_True)
                      *obj = *Boolean::TRUE;
                  else if (arg == Py_False)
                      *obj = *Boolean::FALSE;
                  else if (PyInt_Check(arg))
                  {
                      long ln = PyInt_AS_LONG(arg);
                      int n = (int) ln;

                      if (ln != (long) n)
                          *obj = Long((jlong) ln);
                      else
                          *obj = Integer((jint) n);
                  }
                  else if (PyLong_Check(arg))
                      *obj = Long((jlong) PyLong_AsLongLong(arg));
                  else if (PyFloat_Check(arg))
                      *obj = Double((jdouble) PyFloat_AS_DOUBLE(arg));
                  else
                      return -1;
              }
              break;
          }

          default:
            return -1;
        }

        if (types[pos] != '[')
            array = 0;
    }

    if (pos == typeCount)
        return 0;

    return -1;
}


String p2j(PyObject *object)
{
    return String(env->fromPyString(object));
}

PyObject *j2p(const String& js)
{
    return env->fromJString((jstring) js.this$);
}

PyObject *PyErr_SetArgsError(char *name, PyObject *args)
{
    if (!PyErr_Occurred())
    {
        PyObject *err = Py_BuildValue("(sO)", name, args);

        PyErr_SetObject(PyExc_InvalidArgsError, err);
        Py_DECREF(err);
    }

    return NULL;
}

PyObject *PyErr_SetArgsError(PyObject *self, char *name, PyObject *args)
{
    if (!PyErr_Occurred())
    {
        PyObject *type = (PyObject *) self->ob_type;
        PyObject *err = Py_BuildValue("(OsO)", type, name, args);

        PyErr_SetObject(PyExc_InvalidArgsError, err);
        Py_DECREF(err);
    }

    return NULL;
}

PyObject *PyErr_SetArgsError(PyTypeObject *type, char *name, PyObject *args)
{
    if (!PyErr_Occurred())
    {
        PyObject *err = Py_BuildValue("(OsO)", type, name, args);

        PyErr_SetObject(PyExc_InvalidArgsError, err);
        Py_DECREF(err);
    }

    return NULL;
}

PyObject *PyErr_SetJavaError(jthrowable throwable)
{
    PyObject *err = t_Throwable::wrap_Object(Throwable(throwable));

    PyErr_SetObject(PyExc_JavaError, err);
    Py_DECREF(err);

    return NULL;
}

void throwPythonError(void)
{
    PyObject *exc = PyErr_Occurred();

    if (exc && PyErr_GivenExceptionMatches(exc, PyExc_JavaError))
    {
        PyObject *value, *traceback;

        PyErr_Fetch(&exc, &value, &traceback);
        if (value)
        {
            PyObject *je = PyObject_CallMethod(value, "getJavaException", "");

            if (!je)
                PyErr_Restore(exc, value, traceback);
            else
            {
                Py_DECREF(exc);
                Py_DECREF(value);
                Py_XDECREF(traceback);
                exc = je;

                if (exc && PyObject_TypeCheck(exc, &Throwable$$Type))
                {
                    jobject jobj = ((t_Throwable *) exc)->object.this$;

                    env->get_vm_env()->Throw((jthrowable) jobj);
                    Py_DECREF(exc);

                    return;
                }
            }
        }
        else
        {
            Py_DECREF(exc);
            Py_XDECREF(traceback);
        }
    }
    else if (exc && PyErr_GivenExceptionMatches(exc, PyExc_StopIteration))
    {
        PyErr_Clear();
        return;
    }

    if (exc)
    {
        PyObject *name = PyObject_GetAttrString(exc, "__name__");

        env->get_vm_env()->ThrowNew(env->getPythonExceptionClass(),
                                    PyString_AS_STRING(name));
        Py_DECREF(name);
    }
    else
        env->get_vm_env()->ThrowNew(env->getPythonExceptionClass(),
                                    "python error");
}

void throwTypeError(const char *name, PyObject *object)
{
    PyObject *tuple = Py_BuildValue("(ssO)", "while calling", name, object);

    PyErr_SetObject(PyExc_TypeError, tuple);
    Py_DECREF(tuple);

    env->get_vm_env()->ThrowNew(env->getPythonExceptionClass(), "type error");
}

int abstract_init(PyObject *self, PyObject *args, PyObject *kwds)
{
    PyObject *err =
        Py_BuildValue("(sO)", "instantiating java class", self->ob_type);

    PyErr_SetObject(PyExc_NotImplementedError, err);
    Py_DECREF(err);

    return -1;
}

PyObject *callSuper(PyTypeObject *type, const char *name, PyObject *args,
                    int cardinality)
{
    PyObject *super = (PyObject *) type->tp_base;
    PyObject *method =
        PyObject_GetAttrString(super, (char *) name); // python 2.4 cast
    PyObject *value;

    if (!method)
        return NULL;

    if (cardinality > 1)
        value = PyObject_Call(method, args, NULL);
    else
    {
#if PY_VERSION_HEX < 0x02040000
        PyObject *tuple = Py_BuildValue("(O)", args);
#else
        PyObject *tuple = PyTuple_Pack(1, args);
#endif   
        value = PyObject_Call(method, tuple, NULL);
        Py_DECREF(tuple);
    }

    Py_DECREF(method);

    return value;
}

PyObject *callSuper(PyTypeObject *type, PyObject *self,
                    const char *name, PyObject *args, int cardinality)
{
#if PY_VERSION_HEX < 0x02040000
    PyObject *tuple = Py_BuildValue("(OO)", type, self);
#else
    PyObject *tuple = PyTuple_Pack(2, type, self);
#endif
    PyObject *super = PyObject_Call((PyObject *) &PySuper_Type, tuple, NULL);
    PyObject *method, *value;

    Py_DECREF(tuple);
    if (!super)
        return NULL;

    method = PyObject_GetAttrString(super, (char *) name); // python 2.4 cast
    Py_DECREF(super);
    if (!method)
        return NULL;

    if (cardinality > 1)
        value = PyObject_Call(method, args, NULL);
    else
    {
#if PY_VERSION_HEX < 0x02040000
        tuple = Py_BuildValue("(O)", args);
#else
        tuple = PyTuple_Pack(1, args);
#endif
        value = PyObject_Call(method, tuple, NULL);
        Py_DECREF(tuple);
    }

    Py_DECREF(method);

    return value;
}

PyObject *castCheck(PyObject *obj, getclassfn initializeClass,
                    int reportError)
{
    if (PyObject_TypeCheck(obj, &FinalizerProxy$$Type))
        obj = ((t_fp *) obj)->object;

    if (!PyObject_TypeCheck(obj, &Object$$Type))
    {
        if (reportError)
            PyErr_SetObject(PyExc_TypeError, obj);
        return NULL;
    }

    jobject jobj = ((t_Object *) obj)->object.this$;

    if (jobj)
    {
        jclass cls;

        try {
            cls = (*initializeClass)();
        } catch (JCCEnv::pythonError e) {
            return NULL;
        } catch (JCCEnv::exception e) {
            PyErr_SetJavaError(e.throwable);
            return NULL;
        }

        if (!env->get_vm_env()->IsInstanceOf(jobj, cls))
        {
            if (reportError)
                PyErr_SetObject(PyExc_TypeError, obj);

            return NULL;
        }
    }

    return obj;
}

PyObject *get_extension_iterator(PyObject *self)
{
    return PyObject_CallMethod(self, "iterator", "");
}

PyObject *get_extension_next(PyObject *self)
{
    return PyObject_CallMethod(self, "next", "");
}

PyObject *get_extension_nextElement(PyObject *self)
{
    return PyObject_CallMethod(self, "nextElement", "");
}

jobjectArray fromPySequence(jclass cls, PyObject *sequence)
{
    if (sequence == Py_None)
        return NULL;

    if (!PySequence_Check(sequence))
    {
        PyErr_SetObject(PyExc_TypeError, sequence);
        return NULL;
    }

    int length = PySequence_Length(sequence);
    jobjectArray array;

    try {
        array = env->newObjectArray(cls, length);
    } catch (JCCEnv::pythonError) {
        return NULL;
    } catch (JCCEnv::exception e) {
        PyErr_SetJavaError(e.throwable);
        return NULL;
    }

    JNIEnv *vm_env = env->get_vm_env();

    for (int i = 0; i < length; i++) {
        PyObject *obj = PySequence_GetItem(sequence, i);
        int fromString = 0;
        jobject jobj;

        if (!obj)
            break;
        else if (obj == Py_None)
            jobj = NULL;
        else if (PyString_Check(obj) || PyUnicode_Check(obj))
        {
            jobj = env->fromPyString(obj);
            fromString = 1;
        }
        else if (PyObject_TypeCheck(obj, &JObject$$Type))
            jobj = ((t_JObject *) obj)->object.this$;
        else if (PyObject_TypeCheck(obj, &FinalizerProxy$$Type))
            jobj = ((t_JObject *) ((t_fp *) obj)->object)->object.this$;
        else /* todo: add auto-boxing of primitive types */
        {
            PyErr_SetObject(PyExc_TypeError, obj);
            Py_DECREF(obj);
            return NULL;
        }

        Py_DECREF(obj);

        try {
            env->setObjectArrayElement(array, i, jobj);
            if (fromString)
                vm_env->DeleteLocalRef(jobj);
        } catch (JCCEnv::exception e) {
            PyErr_SetJavaError(e.throwable);
            return NULL;
        }
    }

    return array;
}

void installType(PyTypeObject *type, PyObject *module, char *name,
                 int isExtension)
{
    if (PyType_Ready(type) == 0)
    {
        Py_INCREF(type);
        if (isExtension)
        {
            type->ob_type = &FinalizerClass$$Type;
            Py_INCREF(&FinalizerClass$$Type);
        }
        PyModule_AddObject(module, name, (PyObject *) type);
    }
}
