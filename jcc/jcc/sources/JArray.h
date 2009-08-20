/*
 *   Copyright (c) 2007-2008 Open Source Applications Foundation
 *
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

#ifndef _JArray_H
#define _JArray_H

#ifdef PYTHON
#include <Python.h>
#include "macros.h"

extern jobjectArray fromPySequence(jclass cls, PyObject *sequence);
extern PyObject *PyErr_SetJavaError(jthrowable throwable);

extern PyTypeObject *JArrayObject$$Type;
extern PyTypeObject *JArrayString$$Type;
extern PyTypeObject *JArrayBool$$Type;
extern PyTypeObject *JArrayByte$$Type;
extern PyTypeObject *JArrayChar$$Type;
extern PyTypeObject *JArrayDouble$$Type;
extern PyTypeObject *JArrayFloat$$Type;
extern PyTypeObject *JArrayInt$$Type;
extern PyTypeObject *JArrayLong$$Type;
extern PyTypeObject *JArrayShort$$Type;

#endif

#include "JCCEnv.h"
#include "java/lang/Object.h"


template<typename T> class JArray : public java::lang::Object {
public:
    int length;

    explicit JArray<T>(jobject obj) : java::lang::Object(obj) {
        length = this$ ? env->getArrayLength((jobjectArray) this$) : 0;
    }
    JArray<T>(const JArray<T>& obj) : java::lang::Object(obj) {
        length = obj.length;
    }

#ifdef PYTHON
    JArray<T>(PyObject *sequence) : java::lang::Object(fromPySequence(T::initializeClass(), sequence)) {
        length = this$ ? env->getArrayLength((jobjectArray) this$) : 0;
    }

    JArray<T>(jclass cls, PyObject *sequence) : java::lang::Object(fromPySequence(cls, sequence)) {
        length = this$ ? env->getArrayLength((jobjectArray) this$) : 0;
    }

    PyObject *toSequence(PyObject *(*wrapfn)(const T&))
    {
        if (this$ == NULL)
            Py_RETURN_NONE;

        PyObject *list = PyList_New(length);

        for (int i = 0; i < length; i++)
            PyList_SET_ITEM(list, i, (*wrapfn)((*this)[i]));

        return list;
    }

    PyObject *get(int n, PyObject *(*wrapfn)(const T&))
    {
        if (this$ != NULL)
        {
            if (n < 0)
                n = length + n;

            if (n >= 0 && n < length)
                return (*wrapfn)((*this)[n]);
        }

        PyErr_SetString(PyExc_IndexError, "index out of range");
        return NULL;
    }
#endif

    T operator[](int n) {
        return T(env->getObjectArrayElement((jobjectArray) this$, n));
    }
};

template<> class JArray<jobject> : public java::lang::Object {
  public:
    int length;

    JArray<jobject>(jclass cls, int n) : java::lang::Object(env->get_vm_env()->NewObjectArray(n, cls, NULL)) {
        length = env->getArrayLength((jobjectArray) this$);
    }

    JArray<jobject>(jobject obj) : java::lang::Object(obj) {
        length = this$ ? env->getArrayLength((jobjectArray) this$) : 0;
    }

    JArray<jobject>(const JArray& obj) : java::lang::Object(obj) {
        length = obj.length;
    }

#ifdef PYTHON
    JArray<jobject>(jclass cls, PyObject *sequence) : java::lang::Object(env->get_vm_env()->NewObjectArray(PySequence_Length(sequence), cls, NULL)) {
        length = env->getArrayLength((jobjectArray) this$);

        for (int i = 0; i < length; i++) {
            PyObject *obj = PySequence_GetItem(sequence, i);

            if (obj == NULL)
                break;

            if (!PyObject_TypeCheck(obj, &JObject$$Type))
            {
                PyErr_SetObject(PyExc_TypeError, obj);
                break;
            }

            jobject jobj = ((t_JObject *) obj)->object.this$;

            Py_DECREF(obj);
            try {
                env->setObjectArrayElement((jobjectArray) this$, i, jobj);
            } catch (JCCEnv::exception e) {
                PyErr_SetJavaError(e.throwable);
            }
        }
    }

    PyObject *toSequence(PyObject *(*wrapfn)(const jobject&))
    {
        return toSequence(0, length, wrapfn);
    }

    PyObject *toSequence(int lo, int hi, PyObject *(*wrapfn)(const jobject&))
    {
        if (this$ == NULL)
            Py_RETURN_NONE;

        if (lo < 0) lo = length + lo;
        if (lo < 0) lo = 0;
        else if (lo > length) lo = length;
        if (hi < 0) hi = length + hi;
        if (hi < 0) hi = 0;
        else if (hi > length) hi = length;
        if (lo > hi) lo = hi;

        PyObject *list = PyList_New(hi - lo);

        if (!wrapfn)
            wrapfn = java::lang::t_Object::wrap_jobject;

        for (int i = lo; i < hi; i++) {
            jobject jobj = env->getObjectArrayElement((jobjectArray) this$, i);
            PyObject *obj = (*wrapfn)(jobj);

            PyList_SET_ITEM(list, i - lo, obj);
        }
         
        return list;
    }

    PyObject *get(int n, PyObject *(*wrapfn)(const jobject&))
    {
        if (this$ != NULL)
        {
            if (n < 0)
                n = length + n;

            if (n >= 0 && n < length)
            {
                if (!wrapfn)
                    wrapfn = java::lang::t_Object::wrap_jobject;

                jobject jobj =
                    env->getObjectArrayElement((jobjectArray) this$, n);

                return (*wrapfn)(jobj);
            }
        }

        PyErr_SetString(PyExc_IndexError, "index out of range");
        return NULL;
    }

    int set(int n, PyObject *obj)
    {
        if (this$ != NULL)
        {
            if (n < 0)
                n = length + n;

            if (n >= 0 && n < length)
            {
                if (!PyObject_TypeCheck(obj, &JObject$$Type))
                {
                    PyErr_SetObject(PyExc_TypeError, obj);
                    return -1;
                }

                jobject jobj = ((t_JObject *) obj)->object.this$;

                try {
                    env->setObjectArrayElement((jobjectArray) this$, n, jobj);
                } catch (JCCEnv::exception e) {
                    PyErr_SetJavaError(e.throwable);
                    return -1;
                }

                return 0;
            }
        }

        PyErr_SetString(PyExc_IndexError, "index out of range");
        return -1;
    }

    PyObject *wrap(PyObject *(*wrapfn)(const jobject&));
#endif

    jobject operator[](int n) {
        return (jobject) env->getObjectArrayElement((jobjectArray) this$, n);
    }
};

template<> class JArray<jstring> : public java::lang::Object {
  public:
    int length;

    JArray<jstring>(jobject obj) : java::lang::Object(obj) {
        length = this$ ? env->getArrayLength((jobjectArray) this$) : 0;
    }

    JArray<jstring>(const JArray& obj) : java::lang::Object(obj) {
        length = obj.length;
    }

    JArray<jstring>(int n) : java::lang::Object(env->get_vm_env()->NewObjectArray(n, env->findClass("java/lang/String"), NULL)) {
        length = env->getArrayLength((jobjectArray) this$);
    }

#ifdef PYTHON
    JArray<jstring>(PyObject *sequence) : java::lang::Object(env->get_vm_env()->NewObjectArray(PySequence_Length(sequence), env->findClass("java/lang/String"), NULL)) {
        length = env->getArrayLength((jobjectArray) this$);

        for (int i = 0; i < length; i++) {
            PyObject *obj = PySequence_GetItem(sequence, i);

            if (obj == NULL)
                break;

            jstring str = env->fromPyString(obj);

            Py_DECREF(obj);
            if (PyErr_Occurred())
                break;

            env->setObjectArrayElement((jobjectArray) this$, i, str);
            env->get_vm_env()->DeleteLocalRef(str);
        }
    }

    PyObject *toSequence()
    {
        return toSequence(0, length);
    }

    PyObject *toSequence(int lo, int hi)
    {
        if (this$ == NULL)
            Py_RETURN_NONE;

        if (lo < 0) lo = length + lo;
        if (lo < 0) lo = 0;
        else if (lo > length) lo = length;
        if (hi < 0) hi = length + hi;
        if (hi < 0) hi = 0;
        else if (hi > length) hi = length;
        if (lo > hi) lo = hi;

        PyObject *list = PyList_New(hi - lo);

        for (int i = lo; i < hi; i++) {
            jstring str = (jstring)
                env->getObjectArrayElement((jobjectArray) this$, i);
            PyObject *obj = env->fromJString(str);

            env->get_vm_env()->DeleteLocalRef(str);
            PyList_SET_ITEM(list, i - lo, obj);
        }
         
        return list;
    }

    PyObject *get(int n)
    {
        if (this$ != NULL)
        {
            if (n < 0)
                n = length + n;

            if (n >= 0 && n < length)
            {
                jstring str = (jstring)
                    env->getObjectArrayElement((jobjectArray) this$, n);
                PyObject *obj = env->fromJString(str);

                env->get_vm_env()->DeleteLocalRef(str);
                return obj;
            }
        }

        PyErr_SetString(PyExc_IndexError, "index out of range");
        return NULL;
    }

    int set(int n, PyObject *obj)
    {
        if (this$ != NULL)
        {
            if (n < 0)
                n = length + n;

            if (n >= 0 && n < length)
            {
                jstring str = env->fromPyString(obj);

                if (PyErr_Occurred())
                    return -1;

                env->setObjectArrayElement((jobjectArray) this$, n, str);
                return 0;
            }
        }

        PyErr_SetString(PyExc_IndexError, "index out of range");
        return -1;
    }

    PyObject *wrap();
#endif

    jstring operator[](int n) {
        return (jstring) env->getObjectArrayElement((jobjectArray) this$, n);
    }
};

template<> class JArray<jboolean> : public java::lang::Object {
  public:
    int length;

    class arrayElements {
    private:
        jboolean isCopy;
        jbooleanArray array;
        jboolean *elts;
    public:
        arrayElements(jbooleanArray array) {
            this->array = array;
            elts = env->get_vm_env()->GetBooleanArrayElements(array, &isCopy);
        }
        virtual ~arrayElements() {
            env->get_vm_env()->ReleaseBooleanArrayElements(array, elts, isCopy);
        }
        operator jboolean *() {
            return elts;
        }
    };

    arrayElements elements() {
        return arrayElements((jbooleanArray) this$);
    }

    JArray<jboolean>(jobject obj) : java::lang::Object(obj) {
        length = this$ ? env->getArrayLength((jarray) this$) : 0;
    }

    JArray<jboolean>(const JArray& obj) : java::lang::Object(obj) {
        length = obj.length;
    }

    JArray<jboolean>(int n) : java::lang::Object(env->get_vm_env()->NewBooleanArray(n)) {
        length = env->getArrayLength((jarray) this$);
    }

#ifdef PYTHON
    JArray<jboolean>(PyObject *sequence) : java::lang::Object(env->get_vm_env()->NewBooleanArray(PySequence_Length(sequence))) {
        length = env->getArrayLength((jarray) this$);
        arrayElements elts = elements();
        jboolean *buf = (jboolean *) elts;

        for (int i = 0; i < length; i++) {
            PyObject *obj = PySequence_GetItem(sequence, i);

            if (!obj)
                break;

            if (obj == Py_True || obj == Py_False)
            {
                buf[i] = (jboolean) (obj == Py_True);
                Py_DECREF(obj);
            }
            else
            {
                PyErr_SetObject(PyExc_TypeError, obj);
                Py_DECREF(obj);
                break;
            }
        }
    }

    PyObject *toSequence()
    {
        return toSequence(0, length);
    }

    PyObject *toSequence(int lo, int hi)
    {
        if (this$ == NULL)
            Py_RETURN_NONE;

        if (lo < 0) lo = length + lo;
        if (lo < 0) lo = 0;
        else if (lo > length) lo = length;
        if (hi < 0) hi = length + hi;
        if (hi < 0) hi = 0;
        else if (hi > length) hi = length;
        if (lo > hi) lo = hi;

        PyObject *list = PyList_New(hi - lo);
        arrayElements elts = elements();
        jboolean *buf = (jboolean *) elts;

        for (int i = lo; i < hi; i++) {
            jboolean value = buf[i];
            PyObject *obj = value ? Py_True : Py_False;

            Py_INCREF(obj);
            PyList_SET_ITEM(list, i - lo, obj);
        }
         
        return list;
    }

    PyObject *get(int n)
    {
        if (this$ != NULL)
        {
            if (n < 0)
                n = length + n;

            if (n >= 0 && n < length)
                Py_RETURN_BOOL(elements()[n]);
        }

        PyErr_SetString(PyExc_IndexError, "index out of range");
        return NULL;
    }

    int set(int n, PyObject *obj)
    {
        if (this$ != NULL)
        {
            if (n < 0)
                n = length + n;

            if (n >= 0 && n < length)
            {
                elements()[n] = (jboolean) PyObject_IsTrue(obj);
                return 0;
            }
        }

        PyErr_SetString(PyExc_IndexError, "index out of range");
        return -1;
    }

    PyObject *wrap();
#endif

    jboolean operator[](int n) {
        JNIEnv *vm_env = env->get_vm_env();
        jboolean isCopy = 0;
        jboolean *elts = (jboolean *)
            vm_env->GetPrimitiveArrayCritical((jarray) this$, &isCopy);
        jboolean value = elts[n];

        vm_env->ReleasePrimitiveArrayCritical((jarray) this$, elts, isCopy);

        return value;
    }
};

template<> class JArray<jbyte> : public java::lang::Object {
  public:
    int length;

    class arrayElements {
    private:
        jboolean isCopy;
        jbyteArray array;
        jbyte *elts;
    public:
        arrayElements(jbyteArray array) {
            this->array = array;
            elts = env->get_vm_env()->GetByteArrayElements(array, &isCopy);
        }
        virtual ~arrayElements() {
            env->get_vm_env()->ReleaseByteArrayElements(array, elts, isCopy);
        }
        operator jbyte *() {
            return elts;
        }
    };

    arrayElements elements() {
        return arrayElements((jbyteArray) this$);
    }

    JArray<jbyte>(jobject obj) : java::lang::Object(obj) {
        length = this$ ? env->getArrayLength((jarray) this$) : 0;
    }

    JArray<jbyte>(const JArray& obj) : java::lang::Object(obj) {
        length = obj.length;
    }

    JArray<jbyte>(int n) : java::lang::Object(env->get_vm_env()->NewByteArray(n)) {
        length = env->getArrayLength((jarray) this$);
    }

#ifdef PYTHON
    JArray<jbyte>(PyObject *sequence) : java::lang::Object(env->get_vm_env()->NewByteArray(PySequence_Length(sequence))) {
        length = env->getArrayLength((jarray) this$);
        arrayElements elts = elements();
        jbyte *buf = (jbyte *) elts;

        if (PyString_Check(sequence))
            memcpy(buf, PyString_AS_STRING(sequence), length);
        else
            for (int i = 0; i < length; i++) {
                PyObject *obj = PySequence_GetItem(sequence, i);

                if (!obj)
                    break;

                if (PyString_Check(obj) && (PyString_GET_SIZE(obj) == 1))
                {
                    buf[i] = (jbyte) PyString_AS_STRING(obj)[0];
                    Py_DECREF(obj);
                }
                else
                {
                    PyErr_SetObject(PyExc_TypeError, obj);
                    Py_DECREF(obj);
                    break;
                }
            }
    }

    char getType()
    {
        return 'Z';
    }

    PyObject *toSequence()
    {
        return toSequence(0, length);
    }

    PyObject *toSequence(int lo, int hi)
    {
        if (this$ == NULL)
            Py_RETURN_NONE;

        if (lo < 0) lo = length + lo;
        if (lo < 0) lo = 0;
        else if (lo > length) lo = length;
        if (hi < 0) hi = length + hi;
        if (hi < 0) hi = 0;
        else if (hi > length) hi = length;
        if (lo > hi) lo = hi;

        arrayElements elts = elements();
        jbyte *buf = (jbyte *) elts;

        return PyString_FromStringAndSize((char *) buf + lo, hi - lo);
    }

    PyObject *get(int n)
    {
        if (this$ != NULL)
        {
            if (n < 0)
                n = length + n;

            if (n >= 0 && n < length)
            {
                jbyte b = (*this)[n];
                return PyString_FromStringAndSize((char *) &b, 1);
            }
        }

        PyErr_SetString(PyExc_IndexError, "index out of range");
        return NULL;
    }

    int set(int n, PyObject *obj)
    {
        if (this$ != NULL)
        {
            if (n < 0)
                n = length + n;

            if (n >= 0 && n < length)
            {
                if (!PyString_Check(obj))
                {
                    PyErr_SetObject(PyExc_TypeError, obj);
                    return -1;
                }
                if (PyString_GET_SIZE(obj) != 1)
                {
                    PyErr_SetObject(PyExc_ValueError, obj);
                    return -1;
                }

                elements()[n] = (jbyte) PyString_AS_STRING(obj)[0];
                return 0;
            }
        }

        PyErr_SetString(PyExc_IndexError, "index out of range");
        return -1;
    }

    PyObject *wrap();
#endif

    jbyte operator[](int n) {
        JNIEnv *vm_env = env->get_vm_env();
        jboolean isCopy = 0;
        jbyte *elts = (jbyte *)
            vm_env->GetPrimitiveArrayCritical((jarray) this$, &isCopy);
        jbyte value = elts[n];

        vm_env->ReleasePrimitiveArrayCritical((jarray) this$, elts, isCopy);

        return value;
    }
};

template<> class JArray<jchar> : public java::lang::Object {
  public:
    int length;

    class arrayElements {
    private:
        jboolean isCopy;
        jcharArray array;
        jchar *elts;
    public:
        arrayElements(jcharArray array) {
            this->array = array;
            elts = env->get_vm_env()->GetCharArrayElements(array, &isCopy);
        }
        virtual ~arrayElements() {
            env->get_vm_env()->ReleaseCharArrayElements(array, elts, isCopy);
        }
        operator jchar *() {
            return elts;
        }
    };

    arrayElements elements() {
        return arrayElements((jcharArray) this$);
    }

    JArray<jchar>(jobject obj) : java::lang::Object(obj) {
        length = this$ ? env->getArrayLength((jarray) this$) : 0;
    }

    JArray<jchar>(const JArray& obj) : java::lang::Object(obj) {
        length = obj.length;
    }

    JArray<jchar>(int n) : java::lang::Object(env->get_vm_env()->NewCharArray(n)) {
        length = env->getArrayLength((jarray) this$);
    }

#ifdef PYTHON
    JArray<jchar>(PyObject *sequence) : java::lang::Object(env->get_vm_env()->NewCharArray(PySequence_Length(sequence))) {
        length = env->getArrayLength((jarray) this$);
        arrayElements elts = elements();
        jchar *buf = (jchar *) elts;

        if (PyUnicode_Check(sequence))
        {
            if (sizeof(Py_UNICODE) == sizeof(jchar))
                memcpy(buf, PyUnicode_AS_UNICODE(sequence),
                       length * sizeof(jchar));
            else
            {
                Py_UNICODE *pchars = PyUnicode_AS_UNICODE(sequence);
                for (int i = 0; i < length; i++)
                    buf[i] = (jchar) pchars[i];
            }
        }
        else
            for (int i = 0; i < length; i++) {
                PyObject *obj = PySequence_GetItem(sequence, i);

                if (!obj)
                    break;

                if (PyUnicode_Check(obj) && (PyUnicode_GET_SIZE(obj) == 1))
                {
                    buf[i] = (jchar) PyUnicode_AS_UNICODE(obj)[0];
                    Py_DECREF(obj);
                }
                else
                {
                    PyErr_SetObject(PyExc_TypeError, obj);
                    Py_DECREF(obj);
                    break;
                }
            }
    }

    PyObject *toSequence()
    {
        return toSequence(0, length);
    }

    PyObject *toSequence(int lo, int hi)
    {
        if (this$ == NULL)
            Py_RETURN_NONE;

        if (lo < 0) lo = length + lo;
        if (lo < 0) lo = 0;
        else if (lo > length) lo = length;
        if (hi < 0) hi = length + hi;
        if (hi < 0) hi = 0;
        else if (hi > length) hi = length;
        if (lo > hi) lo = hi;

        arrayElements elts = elements();
        jchar *buf = (jchar *) elts;

        if (sizeof(Py_UNICODE) == sizeof(jchar))
            return PyUnicode_FromUnicode((const Py_UNICODE *) buf + lo,
                                         hi - lo);
        else
        {
            PyObject *string = PyUnicode_FromUnicode(NULL, hi - lo);
            Py_UNICODE *pchars = PyUnicode_AS_UNICODE(string);

            for (int i = lo; i < hi; i++)
                pchars[i - lo] = (Py_UNICODE) buf[i];

            return string;
        }
    }

    PyObject *get(int n)
    {
        if (this$ != NULL)
        {
            if (n < 0)
                n = length + n;

            if (n >= 0 && n < length)
            {
                jchar c = (*this)[n];

                if (sizeof(Py_UNICODE) == sizeof(jchar))
                    return PyUnicode_FromUnicode((const Py_UNICODE *) &c, 1);
                else
                {
                    PyObject *string = PyUnicode_FromUnicode(NULL, 1);
                    Py_UNICODE *pchars = PyUnicode_AS_UNICODE(string);

                    pchars[0] = (Py_UNICODE) c;

                    return string;
                }
            }
        }

        PyErr_SetString(PyExc_IndexError, "index out of range");
        return NULL;
    }

    int set(int n, PyObject *obj)
    {
        if (this$ != NULL)
        {
            if (n < 0)
                n = length + n;

            if (n >= 0 && n < length)
            {
                if (!PyUnicode_Check(obj))
                {
                    PyErr_SetObject(PyExc_TypeError, obj);
                    return -1;
                }
                if (PyUnicode_GET_SIZE(obj) != 1)
                {
                    PyErr_SetObject(PyExc_ValueError, obj);
                    return -1;
                }

                elements()[n] = (jchar) PyUnicode_AS_UNICODE(obj)[0];
                return 0;
            }
        }

        PyErr_SetString(PyExc_IndexError, "index out of range");
        return -1;
    }

    PyObject *wrap();
#endif

    jchar operator[](int n) {
        JNIEnv *vm_env = env->get_vm_env();
        jboolean isCopy = 0;
        jchar *elts = (jchar *)
            vm_env->GetPrimitiveArrayCritical((jarray) this$, &isCopy);
        jchar value = elts[n];

        vm_env->ReleasePrimitiveArrayCritical((jarray) this$, elts, isCopy);

        return value;
    }
};

template<> class JArray<jdouble> : public java::lang::Object {
  public:
    int length;

    class arrayElements {
    private:
        jboolean isCopy;
        jdoubleArray array;
        jdouble *elts;
    public:
        arrayElements(jdoubleArray array) {
            this->array = array;
            elts = env->get_vm_env()->GetDoubleArrayElements(array, &isCopy);
        }
        virtual ~arrayElements() {
            env->get_vm_env()->ReleaseDoubleArrayElements(array, elts, isCopy);
        }
        operator jdouble *() {
            return elts;
        }
    };

    arrayElements elements() {
        return arrayElements((jdoubleArray) this$);
    }

    JArray<jdouble>(jobject obj) : java::lang::Object(obj) {
        length = this$ ? env->getArrayLength((jarray) this$) : 0;
    }

    JArray<jdouble>(const JArray& obj) : java::lang::Object(obj) {
        length = obj.length;
    }

    JArray<jdouble>(int n) : java::lang::Object(env->get_vm_env()->NewDoubleArray(n)) {
        length = env->getArrayLength((jarray) this$);
    }

#ifdef PYTHON
    JArray<jdouble>(PyObject *sequence) : java::lang::Object(env->get_vm_env()->NewDoubleArray(PySequence_Length(sequence))) {
        length = env->getArrayLength((jarray) this$);
        arrayElements elts = elements();
        jdouble *buf = (jdouble *) elts;

        for (int i = 0; i < length; i++) {
            PyObject *obj = PySequence_GetItem(sequence, i);

            if (!obj)
                break;

            if (PyFloat_Check(obj))
            {
                buf[i] = (jdouble) PyFloat_AS_DOUBLE(obj);
                Py_DECREF(obj);
            }
            else
            {
                PyErr_SetObject(PyExc_TypeError, obj);
                Py_DECREF(obj);
                break;
            }
        }
    }

    PyObject *toSequence()
    {
        return toSequence(0, length);
    }

    PyObject *toSequence(int lo, int hi)
    {
        if (this$ == NULL)
            Py_RETURN_NONE;

        if (lo < 0) lo = length + lo;
        if (lo < 0) lo = 0;
        else if (lo > length) lo = length;
        if (hi < 0) hi = length + hi;
        if (hi < 0) hi = 0;
        else if (hi > length) hi = length;
        if (lo > hi) lo = hi;

        PyObject *list = PyList_New(hi - lo);
        arrayElements elts = elements();
        jdouble *buf = (jdouble *) elts;

        for (int i = lo; i < hi; i++)
            PyList_SET_ITEM(list, i - lo, PyFloat_FromDouble((double) buf[i]));

        return list;
    }

    PyObject *get(int n)
    {
        if (this$ != NULL)
        {
            if (n < 0)
                n = length + n;

            if (n >= 0 && n < length)
                return PyFloat_FromDouble((double) (*this)[n]);
        }

        PyErr_SetString(PyExc_IndexError, "index out of range");
        return NULL;
    }

    int set(int n, PyObject *obj)
    {
        if (this$ != NULL)
        {
            if (n < 0)
                n = length + n;

            if (n >= 0 && n < length)
            {
                if (!PyFloat_Check(obj))
                {
                    PyErr_SetObject(PyExc_TypeError, obj);
                    return -1;
                }

                elements()[n] = (jdouble) PyFloat_AS_DOUBLE(obj);
                return 0;
            }
        }

        PyErr_SetString(PyExc_IndexError, "index out of range");
        return -1;
    }

    PyObject *wrap();
#endif

    jdouble operator[](int n) {
        JNIEnv *vm_env = env->get_vm_env();
        jboolean isCopy = 0;
        jdouble *elts = (jdouble *)
            vm_env->GetPrimitiveArrayCritical((jarray) this$, &isCopy);
        jdouble value = elts[n];

        vm_env->ReleasePrimitiveArrayCritical((jarray) this$, elts, isCopy);

        return value;
    }
};

template<> class JArray<jfloat> : public java::lang::Object {
  public:
    int length;

    class arrayElements {
    private:
        jboolean isCopy;
        jfloatArray array;
        jfloat *elts;
    public:
        arrayElements(jfloatArray array) {
            this->array = array;
            elts = env->get_vm_env()->GetFloatArrayElements(array, &isCopy);
        }
        virtual ~arrayElements() {
            env->get_vm_env()->ReleaseFloatArrayElements(array, elts, isCopy);
        }
        operator jfloat *() {
            return elts;
        }
    };

    arrayElements elements() {
        return arrayElements((jfloatArray) this$);
    }

    JArray<jfloat>(jobject obj) : java::lang::Object(obj) {
        length = this$ ? env->getArrayLength((jarray) this$) : 0;
    }

    JArray<jfloat>(const JArray& obj) : java::lang::Object(obj) {
        length = obj.length;
    }

    JArray<jfloat>(int n) : java::lang::Object(env->get_vm_env()->NewFloatArray(n)) {
        length = env->getArrayLength((jarray) this$);
    }

#ifdef PYTHON
    JArray<jfloat>(PyObject *sequence) : java::lang::Object(env->get_vm_env()->NewFloatArray(PySequence_Length(sequence))) {
        length = env->getArrayLength((jarray) this$);
        arrayElements elts = elements();
        jfloat *buf = (jfloat *) elts;

        for (int i = 0; i < length; i++) {
            PyObject *obj = PySequence_GetItem(sequence, i);

            if (!obj)
                break;

            if (PyFloat_Check(obj))
            {
                buf[i] = (jfloat) PyFloat_AS_DOUBLE(obj);
                Py_DECREF(obj);
            }
            else
            {
                PyErr_SetObject(PyExc_TypeError, obj);
                Py_DECREF(obj);
                break;
            }
        }
    }

    PyObject *toSequence()
    {
        return toSequence(0, length);
    }

    PyObject *toSequence(int lo, int hi)
    {
        if (this$ == NULL)
            Py_RETURN_NONE;

        if (lo < 0) lo = length + lo;
        if (lo < 0) lo = 0;
        else if (lo > length) lo = length;
        if (hi < 0) hi = length + hi;
        if (hi < 0) hi = 0;
        else if (hi > length) hi = length;
        if (lo > hi) lo = hi;

        PyObject *list = PyList_New(hi - lo);
        arrayElements elts = elements();
        jfloat *buf = (jfloat *) elts;

        for (int i = lo; i < hi; i++)
            PyList_SET_ITEM(list, i - lo, PyFloat_FromDouble((double) buf[i]));

        return list;
    }

    PyObject *get(int n)
    {
        if (this$ != NULL)
        {
            if (n < 0)
                n = length + n;

            if (n >= 0 && n < length)
                return PyFloat_FromDouble((double) (*this)[n]);
        }

        PyErr_SetString(PyExc_IndexError, "index out of range");
        return NULL;
    }

    int set(int n, PyObject *obj)
    {
        if (this$ != NULL)
        {
            if (n < 0)
                n = length + n;

            if (n >= 0 && n < length)
            {
                if (!PyFloat_Check(obj))
                {
                    PyErr_SetObject(PyExc_TypeError, obj);
                    return -1;
                }

                elements()[n] = (jfloat) PyFloat_AS_DOUBLE(obj);
                return 0;
            }
        }

        PyErr_SetString(PyExc_IndexError, "index out of range");
        return -1;
    }

    PyObject *wrap();
#endif

    jfloat operator[](int n) {
        JNIEnv *vm_env = env->get_vm_env();
        jboolean isCopy = 0;
        jfloat *elts = (jfloat *)
            vm_env->GetPrimitiveArrayCritical((jarray) this$, &isCopy);
        jfloat value = elts[n];

        vm_env->ReleasePrimitiveArrayCritical((jarray) this$, elts, isCopy);

        return value;
    }
};

template<> class JArray<jint> : public java::lang::Object {
  public:
    int length;

    class arrayElements {
    private:
        jboolean isCopy;
        jintArray array;
        jint *elts;
    public:
        arrayElements(jintArray array) {
            this->array = array;
            elts = env->get_vm_env()->GetIntArrayElements(array, &isCopy);
        }
        virtual ~arrayElements() {
            env->get_vm_env()->ReleaseIntArrayElements(array, elts, isCopy);
        }
        operator jint *() {
            return elts;
        }
    };

    arrayElements elements() {
        return arrayElements((jintArray) this$);
    }

    JArray<jint>(jobject obj) : java::lang::Object(obj) {
        length = this$ ? env->getArrayLength((jarray) this$) : 0;
    }

    JArray<jint>(const JArray& obj) : java::lang::Object(obj) {
        length = obj.length;
    }

    JArray<jint>(int n) : java::lang::Object(env->get_vm_env()->NewIntArray(n)) {
        length = env->getArrayLength((jarray) this$);
    }

#ifdef PYTHON
    JArray<jint>(PyObject *sequence) : java::lang::Object(env->get_vm_env()->NewIntArray(PySequence_Length(sequence))) {
        length = env->getArrayLength((jarray) this$);
        arrayElements elts = elements();
        jint *buf = (jint *) elts;

        for (int i = 0; i < length; i++) {
            PyObject *obj = PySequence_GetItem(sequence, i);

            if (!obj)
                break;

            if (PyInt_Check(obj))
            {
                buf[i] = (jint) PyInt_AS_LONG(obj);
                Py_DECREF(obj);
            }
            else
            {
                PyErr_SetObject(PyExc_TypeError, obj);
                Py_DECREF(obj);
                break;
            }
        }
    }

    PyObject *toSequence()
    {
        return toSequence(0, length);
    }

    PyObject *toSequence(int lo, int hi)
    {
        if (this$ == NULL)
            Py_RETURN_NONE;

        if (lo < 0) lo = length + lo;
        if (lo < 0) lo = 0;
        else if (lo > length) lo = length;
        if (hi < 0) hi = length + hi;
        if (hi < 0) hi = 0;
        else if (hi > length) hi = length;
        if (lo > hi) lo = hi;

        PyObject *list = PyList_New(hi - lo);
        arrayElements elts = elements();
        jint *buf = (jint *) elts;

        for (int i = lo; i < hi; i++)
            PyList_SET_ITEM(list, i - lo, PyInt_FromLong(buf[i]));

        return list;
    }

    PyObject *get(int n)
    {
        if (this$ != NULL)
        {
            if (n < 0)
                n = length + n;

            if (n >= 0 && n < length)
                return PyInt_FromLong((*this)[n]);
        }

        PyErr_SetString(PyExc_IndexError, "index out of range");
        return NULL;
    }

    int set(int n, PyObject *obj)
    {
        if (this$ != NULL)
        {
            if (n < 0)
                n = length + n;

            if (n >= 0 && n < length)
            {
                if (!PyInt_Check(obj))
                {
                    PyErr_SetObject(PyExc_TypeError, obj);
                    return -1;
                }

                elements()[n] = (jint) PyInt_AS_LONG(obj);
                return 0;
            }
        }

        PyErr_SetString(PyExc_IndexError, "index out of range");
        return -1;
    }

    PyObject *wrap();
#endif

    jint operator[](int n) {
        JNIEnv *vm_env = env->get_vm_env();
        jboolean isCopy = 0;
        jint *elts = (jint *)
            vm_env->GetPrimitiveArrayCritical((jarray) this$, &isCopy);
        jint value = elts[n];

        vm_env->ReleasePrimitiveArrayCritical((jarray) this$, elts, isCopy);

        return value;
    }
};

template<> class JArray<jlong> : public java::lang::Object {
  public:
    int length;

    class arrayElements {
    private:
        jboolean isCopy;
        jlongArray array;
        jlong *elts;
    public:
        arrayElements(jlongArray array) {
            this->array = array;
            elts = env->get_vm_env()->GetLongArrayElements(array, &isCopy);
        }
        virtual ~arrayElements() {
            env->get_vm_env()->ReleaseLongArrayElements(array, elts, isCopy);
        }
        operator jlong *() {
            return elts;
        }
    };

    arrayElements elements() {
        return arrayElements((jlongArray) this$);
    }

    JArray<jlong>(jobject obj) : java::lang::Object(obj) {
        length = this$ ? env->getArrayLength((jarray) this$) : 0;
    }

    JArray<jlong>(const JArray& obj) : java::lang::Object(obj) {
        length = obj.length;
    }

    JArray<jlong>(int n) : java::lang::Object(env->get_vm_env()->NewLongArray(n)) {
        length = env->getArrayLength((jarray) this$);
    }

#ifdef PYTHON
    JArray<jlong>(PyObject *sequence) : java::lang::Object(env->get_vm_env()->NewLongArray(PySequence_Length(sequence))) {
        length = env->getArrayLength((jarray) this$);
        arrayElements elts = elements();
        jlong *buf = (jlong *) elts;

        for (int i = 0; i < length; i++) {
            PyObject *obj = PySequence_GetItem(sequence, i);

            if (!obj)
                break;

            if (PyLong_Check(obj))
            {
                buf[i] = (jlong) PyLong_AsLongLong(obj);
                Py_DECREF(obj);
            }
            else
            {
                PyErr_SetObject(PyExc_TypeError, obj);
                Py_DECREF(obj);
                break;
            }
        }
    }

    PyObject *toSequence()
    {
        return toSequence(0, length);
    }

    PyObject *toSequence(int lo, int hi)
    {
        if (this$ == NULL)
            Py_RETURN_NONE;

        if (lo < 0) lo = length + lo;
        if (lo < 0) lo = 0;
        else if (lo > length) lo = length;
        if (hi < 0) hi = length + hi;
        if (hi < 0) hi = 0;
        else if (hi > length) hi = length;
        if (lo > hi) lo = hi;

        PyObject *list = PyList_New(hi - lo);
        arrayElements elts = elements();
        jlong *buf = (jlong *) elts;

        for (int i = lo; i < hi; i++)
            PyList_SET_ITEM(list, i - lo, PyLong_FromLongLong((long long) buf[i]));

        return list;
    }

    PyObject *get(int n)
    {
        if (this$ != NULL)
        {
            if (n < 0)
                n = length + n;

            if (n >= 0 && n < length)
                return PyLong_FromLongLong((long long) (*this)[n]);
        }

        PyErr_SetString(PyExc_IndexError, "index out of range");
        return NULL;
    }

    int set(int n, PyObject *obj)
    {
        if (this$ != NULL)
        {
            if (n < 0)
                n = length + n;

            if (n >= 0 && n < length)
            {
                if (!PyLong_Check(obj))
                {
                    PyErr_SetObject(PyExc_TypeError, obj);
                    return -1;
                }

                elements()[n] = (jlong) PyLong_AsLongLong(obj);
                return 0;
            }
        }

        PyErr_SetString(PyExc_IndexError, "index out of range");
        return -1;
    }

    PyObject *wrap();
#endif

    jlong operator[](long n) {
        JNIEnv *vm_env = env->get_vm_env();
        jboolean isCopy = 0;
        jlong *elts = (jlong *)
            vm_env->GetPrimitiveArrayCritical((jarray) this$, &isCopy);
        jlong value = elts[n];

        vm_env->ReleasePrimitiveArrayCritical((jarray) this$, elts, isCopy);

        return value;
    }
};

template<> class JArray<jshort> : public java::lang::Object {
  public:
    int length;

    class arrayElements {
    private:
        jboolean isCopy;
        jshortArray array;
        jshort *elts;
    public:
        arrayElements(jshortArray array) {
            this->array = array;
            elts = env->get_vm_env()->GetShortArrayElements(array, &isCopy);
        }
        virtual ~arrayElements() {
            env->get_vm_env()->ReleaseShortArrayElements(array, elts, isCopy);
        }
        operator jshort *() {
            return elts;
        }
    };

    arrayElements elements() {
        return arrayElements((jshortArray) this$);
    }

    JArray<jshort>(jobject obj) : java::lang::Object(obj) {
        length = this$ ? env->getArrayLength((jarray) this$) : 0;
    }

    JArray<jshort>(const JArray& obj) : java::lang::Object(obj) {
        length = obj.length;
    }

    JArray<jshort>(int n) : java::lang::Object(env->get_vm_env()->NewShortArray(n)) {
        length = env->getArrayLength((jarray) this$);
    }

#ifdef PYTHON
    JArray<jshort>(PyObject *sequence) : java::lang::Object(env->get_vm_env()->NewShortArray(PySequence_Length(sequence))) {
        length = env->getArrayLength((jarray) this$);
        arrayElements elts = elements();
        jshort *buf = (jshort *) elts;

        for (int i = 0; i < length; i++) {
            PyObject *obj = PySequence_GetItem(sequence, i);

            if (!obj)
                break;

            if (PyInt_Check(obj))
            {
                buf[i] = (jshort) PyInt_AS_LONG(obj);
                Py_DECREF(obj);
            }
            else
            {
                PyErr_SetObject(PyExc_TypeError, obj);
                Py_DECREF(obj);
                break;
            }
        }
    }

    PyObject *toSequence()
    {
        return toSequence(0, length);
    }

    PyObject *toSequence(int lo, int hi)
    {
        if (this$ == NULL)
            Py_RETURN_NONE;

        if (lo < 0) lo = length + lo;
        if (lo < 0) lo = 0;
        else if (lo > length) lo = length;
        if (hi < 0) hi = length + hi;
        if (hi < 0) hi = 0;
        else if (hi > length) hi = length;
        if (lo > hi) lo = hi;

        PyObject *list = PyList_New(hi - lo);
        arrayElements elts = elements();
        jshort *buf = (jshort *) elts;

        for (int i = lo; i < hi; i++)
            PyList_SET_ITEM(list, i - lo, PyInt_FromLong(buf[i]));

        return list;
    }

    PyObject *get(int n)
    {
        if (this$ != NULL)
        {
            if (n < 0)
                n = length + n;

            if (n >= 0 && n < length)
                return PyInt_FromLong((long) (*this)[n]);
        }

        PyErr_SetString(PyExc_IndexError, "index out of range");
        return NULL;
    }

    int set(int n, PyObject *obj)
    {
        if (this$ != NULL)
        {
            if (n < 0)
                n = length + n;

            if (n >= 0 && n < length)
            {
                if (!PyInt_Check(obj))
                {
                    PyErr_SetObject(PyExc_TypeError, obj);
                    return -1;
                }

                elements()[n] = (jshort) PyInt_AS_LONG(obj);
                return 0;
            }
        }

        PyErr_SetString(PyExc_IndexError, "index out of range");
        return -1;
    }

    PyObject *wrap();
#endif

    jshort operator[](int n) {
        JNIEnv *vm_env = env->get_vm_env();
        jboolean isCopy = 0;
        jshort *elts = (jshort *)
            vm_env->GetPrimitiveArrayCritical((jarray) this$, &isCopy);
        jshort value = elts[n];

        vm_env->ReleasePrimitiveArrayCritical((jarray) this$, elts, isCopy);

        return value;
    }
};

#ifdef PYTHON

template<typename T> class t_jarray {
public:
    PyObject_HEAD
    JArray<T> array;
};

#endif

#endif /* _JArray_H */
