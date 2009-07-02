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

#ifndef _JCCEnv_H
#define _JCCEnv_H

#include <stdarg.h>
#if defined(_MSC_VER) || defined(__WIN32)
#define _DLL_IMPORT __declspec(dllimport)
#define _DLL_EXPORT __declspec(dllexport)
#include <windows.h>
#undef MAX_PRIORITY
#undef MIN_PRIORITY
#else
#include <pthread.h>
#define _DLL_IMPORT
#define _DLL_EXPORT
#endif

#ifdef __SUNPRO_CC
#undef DEFAULT_TYPE
#endif

#ifdef TRUE
#undef TRUE
#endif
#ifdef FALSE
#undef FALSE
#endif

#include <map>

#ifdef PYTHON
#include <Python.h>
#endif

#undef EOF

class JCCEnv;

#if defined(_MSC_VER) || defined(__WIN32)

#ifdef _jcc_shared
_DLL_IMPORT extern JCCEnv *env;
_DLL_IMPORT extern DWORD VM_ENV;
#else
_DLL_EXPORT extern JCCEnv *env;
_DLL_EXPORT extern DWORD VM_ENV;
#endif

#else

extern JCCEnv *env;

#endif


class countedRef {
public:
    jobject global;
    int count;
};

class _DLL_EXPORT JCCEnv {
protected:
    jclass _sys, _obj, _thr;
    jmethodID *_mids;

    enum {
        mid_sys_identityHashCode,
        mid_sys_setProperty,
        mid_obj_toString,
        mid_obj_hashCode,
        mid_obj_getClass,
        max_mid
    };

public:
    JavaVM *vm;
    std::multimap<int, countedRef> refs;
    int handlers;

    class exception {
    public:
        jthrowable throwable;
        exception(jthrowable throwable) {
            this->throwable = throwable;
        }
    };

#ifdef PYTHON
    class pythonError {
    public:
        jthrowable throwable;
        pythonError(jthrowable throwable) {
            this->throwable = throwable;
        }
    };
#endif

    explicit JCCEnv(JavaVM *vm, JNIEnv *env);
    virtual ~JCCEnv() {};

#if defined(_MSC_VER) || defined(__WIN32)
    inline JNIEnv *get_vm_env()
    {
        return (JNIEnv *) TlsGetValue(VM_ENV);
    }
#else
    static pthread_key_t VM_ENV;

    inline JNIEnv *get_vm_env()
    {
        return (JNIEnv *) pthread_getspecific(VM_ENV);
    }
#endif
    virtual void set_vm(JavaVM *vm, JNIEnv *vm_env);
    virtual void set_vm_env(JNIEnv *vm_env);

    virtual jclass findClass(const char *className);
    virtual void registerNatives(jclass cls, JNINativeMethod *methods, int n);
    virtual jobject newGlobalRef(jobject obj, int id);
    virtual jobject deleteGlobalRef(jobject obj, int id);

    virtual jobject newObject(jclass (*initializeClass)(), jmethodID **mids,
                              int m, ...);

    virtual jobjectArray newObjectArray(jclass cls, int size);
    virtual void setObjectArrayElement(jobjectArray a, int n, jobject obj);
    virtual jobject getObjectArrayElement(jobjectArray a, int n);
    virtual int getArrayLength(jarray a);

    virtual jclass getPythonExceptionClass();
    virtual void reportException();

    virtual jobject callObjectMethod(jobject obj, jmethodID mid, ...);
    virtual jboolean callBooleanMethod(jobject obj, jmethodID mid, ...);
    virtual jbyte callByteMethod(jobject obj, jmethodID mid, ...);
    virtual jchar callCharMethod(jobject obj, jmethodID mid, ...);
    virtual jdouble callDoubleMethod(jobject obj, jmethodID mid, ...);
    virtual jfloat callFloatMethod(jobject obj, jmethodID mid, ...);
    virtual jint callIntMethod(jobject obj, jmethodID mid, ...);
    virtual jlong callLongMethod(jobject obj, jmethodID mid, ...);
    virtual jshort callShortMethod(jobject obj, jmethodID mid, ...);
    virtual void callVoidMethod(jobject obj, jmethodID mid, ...);

    virtual jobject callNonvirtualObjectMethod(jobject obj, jclass cls, jmethodID mid, ...);
    virtual jboolean callNonvirtualBooleanMethod(jobject obj, jclass cls, jmethodID mid, ...);
    virtual jbyte callNonvirtualByteMethod(jobject obj, jclass cls, jmethodID mid, ...);
    virtual jchar callNonvirtualCharMethod(jobject obj, jclass cls, jmethodID mid, ...);
    virtual jdouble callNonvirtualDoubleMethod(jobject obj, jclass cls, jmethodID mid, ...);
    virtual jfloat callNonvirtualFloatMethod(jobject obj, jclass cls, jmethodID mid, ...);
    virtual jint callNonvirtualIntMethod(jobject obj, jclass cls, jmethodID mid, ...);
    virtual jlong callNonvirtualLongMethod(jobject obj, jclass cls, jmethodID mid, ...);
    virtual jshort callNonvirtualShortMethod(jobject obj, jclass cls, jmethodID mid, ...);
    virtual void callNonvirtualVoidMethod(jobject obj, jclass cls, jmethodID mid, ...);

    virtual jobject callStaticObjectMethod(jclass cls, jmethodID mid, ...);
    virtual jboolean callStaticBooleanMethod(jclass cls, jmethodID mid, ...);
    virtual jbyte callStaticByteMethod(jclass cls, jmethodID mid, ...);
    virtual jchar callStaticCharMethod(jclass cls, jmethodID mid, ...);
    virtual jdouble callStaticDoubleMethod(jclass cls, jmethodID mid, ...);
    virtual jfloat callStaticFloatMethod(jclass cls, jmethodID mid, ...);
    virtual jint callStaticIntMethod(jclass cls, jmethodID mid, ...);
    virtual jlong callStaticLongMethod(jclass cls, jmethodID mid, ...);
    virtual jshort callStaticShortMethod(jclass cls, jmethodID mid, ...);
    virtual void callStaticVoidMethod(jclass cls, jmethodID mid, ...);

    virtual jmethodID getMethodID(jclass cls, const char *name,
                                  const char *signature);
    virtual jfieldID getFieldID(jclass cls, const char *name,
                                const char *signature);
    virtual jmethodID getStaticMethodID(jclass cls, const char *name,
                                        const char *signature);

    virtual jobject getStaticObjectField(jclass cls, const char *name,
                                         const char *signature);
    virtual jboolean getStaticBooleanField(jclass cls, const char *name);
    virtual jbyte getStaticByteField(jclass cls, const char *name);
    virtual jchar getStaticCharField(jclass cls, const char *name);
    virtual jdouble getStaticDoubleField(jclass cls, const char *name);
    virtual jfloat getStaticFloatField(jclass cls, const char *name);
    virtual jint getStaticIntField(jclass cls, const char *name);
    virtual jlong getStaticLongField(jclass cls, const char *name);
    virtual jshort getStaticShortField(jclass cls, const char *name);

    virtual jobject getObjectField(jobject obj, jfieldID id);
    virtual jboolean getBooleanField(jobject obj, jfieldID id);
    virtual jbyte getByteField(jobject obj, jfieldID id);
    virtual jchar getCharField(jobject obj, jfieldID id);
    virtual jdouble getDoubleField(jobject obj, jfieldID id);
    virtual jfloat getFloatField(jobject obj, jfieldID id);
    virtual jint getIntField(jobject obj, jfieldID id);
    virtual jlong getLongField(jobject obj, jfieldID id);
    virtual jshort getShortField(jobject obj, jfieldID id);

    virtual void setObjectField(jobject obj, jfieldID id, jobject value);
    virtual void setBooleanField(jobject obj, jfieldID id, jboolean value);
    virtual void setByteField(jobject obj, jfieldID id, jbyte value);
    virtual void setCharField(jobject obj, jfieldID id, jchar value);
    virtual void setDoubleField(jobject obj, jfieldID id, jdouble value);
    virtual void setFloatField(jobject obj, jfieldID id, jfloat value);
    virtual void setIntField(jobject obj, jfieldID id, jint value);
    virtual void setLongField(jobject obj, jfieldID id, jlong value);
    virtual void setShortField(jobject obj, jfieldID id, jshort value);

    int id(jobject obj) {
        return obj
            ? get_vm_env()->CallStaticIntMethod(_sys,
                                                _mids[mid_sys_identityHashCode],
                                                obj)
            : 0;
    }

    int hash(jobject obj) {
        return obj
            ? get_vm_env()->CallIntMethod(obj, _mids[mid_obj_hashCode])
            : 0;
    }

    virtual void setClassPath(const char *classPath);
    virtual jstring fromUTF(const char *bytes);
    virtual char *toUTF(jstring str);
    virtual char *toString(jobject obj);
    virtual char *getClassName(jobject obj);
#ifdef PYTHON
    virtual jstring fromPyString(PyObject *object);
    virtual PyObject *fromJString(jstring js);
    virtual void finalizeObject(JNIEnv *jenv, PyObject *obj);
#endif

    virtual inline int isSame(jobject o1, jobject o2)
    {
        return o1 == o2 || get_vm_env()->IsSameObject(o1, o2);
    }
};

#ifdef PYTHON

class PythonGIL {
  private:
    PyGILState_STATE state;
  public:
    PythonGIL()
    {
        state = PyGILState_Ensure();
    }
    PythonGIL(JNIEnv *vm_env)
    {
        state = PyGILState_Ensure();
        env->set_vm_env(vm_env);
    }
    ~PythonGIL()
    {
        PyGILState_Release(state);
    }
};

class PythonThreadState {
  private:
    PyThreadState *state;
    int handler;
  public:
    PythonThreadState(int handler=0)
    {
        state = PyEval_SaveThread();
        this->handler = handler;
        env->handlers += handler;
    }
    ~PythonThreadState()
    {
        PyEval_RestoreThread(state);
        env->handlers -= handler;
    }
};

#endif

#endif /* _JCCEnv_H */
