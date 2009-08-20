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

#include <map>
#include <string.h>
#include <jni.h>

#include "JCCEnv.h"


#if defined(_MSC_VER) || defined(__WIN32)
_DLL_EXPORT DWORD VM_ENV = 0;
#else
pthread_key_t JCCEnv::VM_ENV = (pthread_key_t) NULL;
#endif

#if defined(_MSC_VER) || defined(__WIN32)

static CRITICAL_SECTION *mutex = NULL;

class lock {
public:
    lock() {
        EnterCriticalSection(mutex);
    }
    virtual ~lock() {
        LeaveCriticalSection(mutex);
    }
};

#else

static pthread_mutex_t *mutex = NULL;

class lock {
public:
    lock() {
        pthread_mutex_lock(mutex);
    }
    virtual ~lock() {
        pthread_mutex_unlock(mutex);
    }
};

#endif

JCCEnv::JCCEnv(JavaVM *vm, JNIEnv *vm_env)
{
#if defined(_MSC_VER) || defined(__WIN32)
    if (!mutex)
    {
        mutex = new CRITICAL_SECTION();
        InitializeCriticalSection(mutex);
    }
#else
    if (!mutex)
    {
        mutex = new pthread_mutex_t();
        pthread_mutex_init(mutex, NULL);
    }
#endif

    if (vm)
        set_vm(vm, vm_env);
    else
        this->vm = NULL;
}

void JCCEnv::set_vm(JavaVM *vm, JNIEnv *vm_env)
{
    this->vm = vm;
    set_vm_env(vm_env);

    _sys = (jclass) vm_env->NewGlobalRef(vm_env->FindClass("java/lang/System"));
    _obj = (jclass) vm_env->NewGlobalRef(vm_env->FindClass("java/lang/Object"));
#ifdef _jcc_lib
    _thr = (jclass) vm_env->NewGlobalRef(vm_env->FindClass("org/apache/jcc/PythonException"));
#else
    _thr = (jclass) vm_env->NewGlobalRef(vm_env->FindClass("java/lang/RuntimeException"));
#endif
    _mids = new jmethodID[max_mid];

    _mids[mid_sys_identityHashCode] =
        vm_env->GetStaticMethodID(_sys, "identityHashCode",
                                  "(Ljava/lang/Object;)I");
    _mids[mid_sys_setProperty] =
        vm_env->GetStaticMethodID(_sys, "setProperty",
                                  "(Ljava/lang/String;Ljava/lang/String;)Ljava/lang/String;");
    _mids[mid_obj_toString] =
        vm_env->GetMethodID(_obj, "toString",
                            "()Ljava/lang/String;");
    _mids[mid_obj_hashCode] =
        vm_env->GetMethodID(_obj, "hashCode",
                            "()I");
    _mids[mid_obj_getClass] =
        vm_env->GetMethodID(_obj, "getClass",
                            "()Ljava/lang/Class;");
}

#if defined(_MSC_VER) || defined(__WIN32)

void JCCEnv::set_vm_env(JNIEnv *vm_env)
{
    if (!VM_ENV)
        VM_ENV = TlsAlloc();
    TlsSetValue(VM_ENV, (LPVOID) vm_env);
}

#else

void JCCEnv::set_vm_env(JNIEnv *vm_env)
{
    if (!VM_ENV)
        pthread_key_create(&VM_ENV, NULL);
    pthread_setspecific(VM_ENV, (void *) vm_env);
}

#endif

jclass JCCEnv::findClass(const char *className)
{
    jclass cls = NULL;

    if (vm)
    {
        JNIEnv *vm_env = get_vm_env();

        if (vm_env)
            cls = vm_env->FindClass(className);
#ifdef PYTHON
        else
        {
            PythonGIL gil;

            PyErr_SetString(PyExc_RuntimeError, "attachCurrentThread() must be called first");
            throw pythonError(NULL);
        }
#else
        else
            throw exception(NULL);
#endif
    }
#ifdef PYTHON
    else
    {
        PythonGIL gil;

        PyErr_SetString(PyExc_RuntimeError, "initVM() must be called first");
        throw pythonError(NULL);
    }
#else
    else
        throw exception(NULL);
#endif

    reportException();

    return cls;
}

void JCCEnv::registerNatives(jclass cls, JNINativeMethod *methods, int n)
{
    get_vm_env()->RegisterNatives(cls, methods, n);
}

jobject JCCEnv::newGlobalRef(jobject obj, int id)
{
    if (obj)
    {
        if (id)  /* zero when weak global ref is desired */
        {
            lock locked;

            for (std::multimap<int, countedRef>::iterator iter = refs.find(id);
                 iter != refs.end();
                 iter++) {
                if (iter->first != id)
                    break;
                if (isSame(obj, iter->second.global))
                {
                    /* If it's in the table but not the same reference,
                     * it must be a local reference and must be deleted.
                     */
                    if (obj != iter->second.global)
                        get_vm_env()->DeleteLocalRef(obj);
                        
                    iter->second.count += 1;
                    return iter->second.global;
                }
            }

            JNIEnv *vm_env = get_vm_env();
            countedRef ref;

            ref.global = vm_env->NewGlobalRef(obj);
            ref.count = 1;
            refs.insert(std::pair<const int, countedRef>(id, ref));
            vm_env->DeleteLocalRef(obj);

            return ref.global;
        }
        else
            return (jobject) get_vm_env()->NewWeakGlobalRef(obj);
    }

    return NULL;
}

jobject JCCEnv::deleteGlobalRef(jobject obj, int id)
{
    if (obj)
    {
        if (id)  /* zero when obj is weak global ref */
        {
            lock locked;

            for (std::multimap<int, countedRef>::iterator iter = refs.find(id);
                 iter != refs.end();
                 iter++) {
                if (iter->first != id)
                    break;
                if (isSame(obj, iter->second.global))
                {
                    if (iter->second.count == 1)
                    {
                        get_vm_env()->DeleteGlobalRef(iter->second.global);
                        refs.erase(iter);
                    }
                    else
                        iter->second.count -= 1;

                    return NULL;
                }
            }

            printf("deleting non-existent ref: 0x%x\n", id);
        }
        else
            get_vm_env()->DeleteWeakGlobalRef((jweak) obj);
    }

    return NULL;
}

jobject JCCEnv::newObject(jclass (*initializeClass)(), jmethodID **mids,
                          int m, ...)
{
    jclass cls = (*initializeClass)();
    JNIEnv *vm_env = get_vm_env();
    jobject obj;

    if (vm_env)
    {
        va_list ap;

        va_start(ap, m);
        obj = vm_env->NewObjectV(cls, (*mids)[m], ap);
        va_end(ap);
    }
#ifdef PYTHON
    else
    {
        PythonGIL gil;

        PyErr_SetString(PyExc_RuntimeError, "attachCurrentThread() must be called first");
        throw pythonError(NULL);
    }
#else
    else
        throw exception(NULL);
#endif

    reportException();

    return obj;
}

jobjectArray JCCEnv::newObjectArray(jclass cls, int size)
{
    jobjectArray array = get_vm_env()->NewObjectArray(size, cls, NULL);

    reportException();
    return array;
}

void JCCEnv::setObjectArrayElement(jobjectArray array, int n, jobject obj)
{
    get_vm_env()->SetObjectArrayElement(array, n, obj);
    reportException();
}

jobject JCCEnv::getObjectArrayElement(jobjectArray array, int n)
{
    jobject obj = get_vm_env()->GetObjectArrayElement(array, n);

    reportException();
    return obj;
}

int JCCEnv::getArrayLength(jarray array)
{
    int len = get_vm_env()->GetArrayLength(array);

    reportException();
    return len;
}

jclass JCCEnv::getPythonExceptionClass()
{
    return _thr;
}

void JCCEnv::reportException()
{
    JNIEnv *vm_env = get_vm_env();
    jthrowable throwable = vm_env->ExceptionOccurred();

    if (throwable)
    {
        if (!env->handlers)
            vm_env->ExceptionDescribe();

        vm_env->ExceptionClear();

#ifdef PYTHON
#ifndef _jcc_lib
        PythonGIL gil;

        if (PyErr_Occurred())
        {
#endif
            /* _thr is PythonException ifdef _jcc_lib (shared mode)
             * if not shared mode, _thr is RuntimeException
             */
            jobject cls = (jobject) vm_env->GetObjectClass(throwable);

            if (vm_env->IsSameObject(cls, _thr))
                throw pythonError(throwable);
#ifndef _jcc_lib
        }
#endif
#endif

        throw exception(throwable);
    }
}


#define DEFINE_CALL(jtype, Type)                                        \
    jtype JCCEnv::call##Type##Method(jobject obj,                       \
                                     jmethodID mid, ...)                \
    {                                                                   \
        va_list ap;                                                     \
        jtype result;                                                   \
                                                                        \
        va_start(ap, mid);                                              \
        result = get_vm_env()->Call##Type##MethodV(obj, mid, ap);       \
        va_end(ap);                                                     \
                                                                        \
        reportException();                                              \
                                                                        \
        return result;                                                  \
    }

#define DEFINE_NONVIRTUAL_CALL(jtype, Type)                             \
    jtype JCCEnv::callNonvirtual##Type##Method(jobject obj, jclass cls, \
                                               jmethodID mid, ...)      \
    {                                                                   \
        va_list ap;                                                     \
        jtype result;                                                   \
                                                                        \
        va_start(ap, mid);                                              \
        result = get_vm_env()->CallNonvirtual##Type##MethodV(obj, cls,  \
                                                             mid, ap);  \
        va_end(ap);                                                     \
                                                                        \
        reportException();                                              \
                                                                        \
        return result;                                                  \
    }

#define DEFINE_STATIC_CALL(jtype, Type)                                 \
    jtype JCCEnv::callStatic##Type##Method(jclass cls,                  \
                                           jmethodID mid, ...)          \
    {                                                                   \
        va_list ap;                                                     \
        jtype result;                                                   \
                                                                        \
        va_start(ap, mid);                                              \
        result = get_vm_env()->CallStatic##Type##MethodV(cls, mid, ap); \
        va_end(ap);                                                     \
                                                                        \
        reportException();                                              \
                                                                        \
        return result;                                                  \
    }
        
DEFINE_CALL(jobject, Object)
DEFINE_CALL(jboolean, Boolean)
DEFINE_CALL(jbyte, Byte)
DEFINE_CALL(jchar, Char)
DEFINE_CALL(jdouble, Double)
DEFINE_CALL(jfloat, Float)
DEFINE_CALL(jint, Int)
DEFINE_CALL(jlong, Long)
DEFINE_CALL(jshort, Short)

DEFINE_NONVIRTUAL_CALL(jobject, Object)
DEFINE_NONVIRTUAL_CALL(jboolean, Boolean)
DEFINE_NONVIRTUAL_CALL(jbyte, Byte)
DEFINE_NONVIRTUAL_CALL(jchar, Char)
DEFINE_NONVIRTUAL_CALL(jdouble, Double)
DEFINE_NONVIRTUAL_CALL(jfloat, Float)
DEFINE_NONVIRTUAL_CALL(jint, Int)
DEFINE_NONVIRTUAL_CALL(jlong, Long)
DEFINE_NONVIRTUAL_CALL(jshort, Short)

DEFINE_STATIC_CALL(jobject, Object)
DEFINE_STATIC_CALL(jboolean, Boolean)
DEFINE_STATIC_CALL(jbyte, Byte)
DEFINE_STATIC_CALL(jchar, Char)
DEFINE_STATIC_CALL(jdouble, Double)
DEFINE_STATIC_CALL(jfloat, Float)
DEFINE_STATIC_CALL(jint, Int)
DEFINE_STATIC_CALL(jlong, Long)
DEFINE_STATIC_CALL(jshort, Short)

void JCCEnv::callVoidMethod(jobject obj, jmethodID mid, ...)
{
    va_list ap;

    va_start(ap, mid);
    get_vm_env()->CallVoidMethodV(obj, mid, ap);
    va_end(ap);

    reportException();
}

void JCCEnv::callNonvirtualVoidMethod(jobject obj, jclass cls,
                                      jmethodID mid, ...)
{
    va_list ap;

    va_start(ap, mid);
    get_vm_env()->CallNonvirtualVoidMethodV(obj, cls, mid, ap);
    va_end(ap);

    reportException();
}

void JCCEnv::callStaticVoidMethod(jclass cls, jmethodID mid, ...)
{
    va_list ap;

    va_start(ap, mid);
    get_vm_env()->CallStaticVoidMethodV(cls, mid, ap);
    va_end(ap);

    reportException();
}


jmethodID JCCEnv::getMethodID(jclass cls, const char *name,
                              const char *signature)
{
    jmethodID id = get_vm_env()->GetMethodID(cls, name, signature);

    reportException();

    return id;
}

jfieldID JCCEnv::getFieldID(jclass cls, const char *name,
                            const char *signature)
{
    jfieldID id = get_vm_env()->GetFieldID(cls, name, signature);

    reportException();

    return id;
}


jmethodID JCCEnv::getStaticMethodID(jclass cls, const char *name,
                                    const char *signature)
{
    jmethodID id = get_vm_env()->GetStaticMethodID(cls, name, signature);

    reportException();

    return id;
}

jobject JCCEnv::getStaticObjectField(jclass cls, const char *name,
                                     const char *signature)
{
    JNIEnv *vm_env = get_vm_env();
    jfieldID id = vm_env->GetStaticFieldID(cls, name, signature);

    reportException();

    return vm_env->GetStaticObjectField(cls, id);
}

#define DEFINE_GET_STATIC_FIELD(jtype, Type, signature)                 \
    jtype JCCEnv::getStatic##Type##Field(jclass cls, const char *name)  \
    {                                                                   \
        JNIEnv *vm_env = get_vm_env();                                  \
        jfieldID id = vm_env->GetStaticFieldID(cls, name, #signature);  \
        reportException();                                              \
        return vm_env->GetStatic##Type##Field(cls, id);                 \
    }

DEFINE_GET_STATIC_FIELD(jboolean, Boolean, Z)
DEFINE_GET_STATIC_FIELD(jbyte, Byte, B)
DEFINE_GET_STATIC_FIELD(jchar, Char, C)
DEFINE_GET_STATIC_FIELD(jdouble, Double, D)
DEFINE_GET_STATIC_FIELD(jfloat, Float, F)
DEFINE_GET_STATIC_FIELD(jint, Int, I)
DEFINE_GET_STATIC_FIELD(jlong, Long, J)
DEFINE_GET_STATIC_FIELD(jshort, Short, S)

#define DEFINE_GET_FIELD(jtype, Type)                                   \
    jtype JCCEnv::get##Type##Field(jobject obj, jfieldID id)            \
    {                                                                   \
        jtype value = get_vm_env()->Get##Type##Field(obj, id);          \
        reportException();                                              \
        return value;                                                   \
    }

DEFINE_GET_FIELD(jobject, Object)
DEFINE_GET_FIELD(jboolean, Boolean)
DEFINE_GET_FIELD(jbyte, Byte)
DEFINE_GET_FIELD(jchar, Char)
DEFINE_GET_FIELD(jdouble, Double)
DEFINE_GET_FIELD(jfloat, Float)
DEFINE_GET_FIELD(jint, Int)
DEFINE_GET_FIELD(jlong, Long)
DEFINE_GET_FIELD(jshort, Short)

#define DEFINE_SET_FIELD(jtype, Type)                                    \
    void JCCEnv::set##Type##Field(jobject obj, jfieldID id, jtype value) \
    {                                                                    \
        get_vm_env()->Set##Type##Field(obj, id, value);                  \
        reportException();                                               \
    }

DEFINE_SET_FIELD(jobject, Object)
DEFINE_SET_FIELD(jboolean, Boolean)
DEFINE_SET_FIELD(jbyte, Byte)
DEFINE_SET_FIELD(jchar, Char)
DEFINE_SET_FIELD(jdouble, Double)
DEFINE_SET_FIELD(jfloat, Float)
DEFINE_SET_FIELD(jint, Int)
DEFINE_SET_FIELD(jlong, Long)
DEFINE_SET_FIELD(jshort, Short)

void JCCEnv::setClassPath(const char *classPath)
{
    JNIEnv *vm_env = get_vm_env();
    jclass _ucl = (jclass) vm_env->FindClass("java/net/URLClassLoader");
    jclass _fil = (jclass) vm_env->FindClass("java/io/File");
    jmethodID mid = vm_env->GetStaticMethodID(_ucl, "getSystemClassLoader",
                                              "()Ljava/lang/ClassLoader;");
    jobject classLoader = vm_env->CallStaticObjectMethod(_ucl, mid);
    jmethodID mf = vm_env->GetMethodID(_fil, "<init>", "(Ljava/lang/String;)V");
    jmethodID mu = vm_env->GetMethodID(_fil, "toURL", "()Ljava/net/URL;");
    jmethodID ma = vm_env->GetMethodID(_ucl, "addURL", "(Ljava/net/URL;)V");
#ifdef WINDOWS
    char *pathsep = ";";
#else
    char *pathsep = ":";
#endif
    char *path = strdup(classPath);

    for (char *cp = strtok(path, pathsep);
         cp != NULL;
         cp = strtok(NULL, pathsep)) {
        jstring string = vm_env->NewStringUTF(cp);
        jobject file = vm_env->NewObject(_fil, mf, string);
        jobject url = vm_env->CallObjectMethod(file, mu);

        vm_env->CallVoidMethod(classLoader, ma, url);
    }
    free(path);
}

jstring JCCEnv::fromUTF(const char *bytes)
{
    jstring str = get_vm_env()->NewStringUTF(bytes);

    reportException();

    return str;
}

char *JCCEnv::toUTF(jstring str)
{
    JNIEnv *vm_env = get_vm_env();
    int len = vm_env->GetStringUTFLength(str);
    char *bytes = new char[len + 1];
    jboolean isCopy = 0;
    const char *utf = vm_env->GetStringUTFChars(str, &isCopy);

    if (!bytes)
        return NULL;

    memcpy(bytes, utf, len);
    bytes[len] = '\0';

    vm_env->ReleaseStringUTFChars(str, utf);

    return bytes;
}

char *JCCEnv::toString(jobject obj)
{
    return obj
        ? toUTF((jstring) callObjectMethod(obj, _mids[mid_obj_toString]))
        : NULL;
}

char *JCCEnv::getClassName(jobject obj)
{
    return obj
        ? toString(callObjectMethod(obj, _mids[mid_obj_getClass]))
        : NULL;
}

#ifdef PYTHON

jstring JCCEnv::fromPyString(PyObject *object)
{
    if (object == Py_None)
        return NULL;

    if (PyUnicode_Check(object))
    {
        if (sizeof(Py_UNICODE) == sizeof(jchar))
        {
            jchar *buf = (jchar *) PyUnicode_AS_UNICODE(object);
            jsize len = (jsize) PyUnicode_GET_SIZE(object);

            return get_vm_env()->NewString(buf, len);
        }
        else
        {
            jsize len = PyUnicode_GET_SIZE(object);
            Py_UNICODE *pchars = PyUnicode_AS_UNICODE(object);
            jchar *jchars = new jchar[len];
            jstring str;

            for (int i = 0; i < len; i++)
                jchars[i] = (jchar) pchars[i];

            str = get_vm_env()->NewString(jchars, len);
            delete jchars;

            return str;
        }
    }
    else if (PyString_Check(object))
        return fromUTF(PyString_AS_STRING(object));
    else
    {
        PyObject *tuple = Py_BuildValue("(sO)", "expected a string", object);

        PyErr_SetObject(PyExc_TypeError, tuple);
        Py_DECREF(tuple);

        return NULL;
    }
}

PyObject *JCCEnv::fromJString(jstring js)
{
    if (!js)
        Py_RETURN_NONE;

    JNIEnv *vm_env = get_vm_env();

    if (sizeof(Py_UNICODE) == sizeof(jchar))
    {
        jboolean isCopy;
        const jchar *buf = vm_env->GetStringChars(js, &isCopy);
        jsize len = vm_env->GetStringLength(js);
        PyObject *string = PyUnicode_FromUnicode((const Py_UNICODE *) buf, len);

        vm_env->ReleaseStringChars(js, buf);
        return string;
    }
    else
    {
        jsize len = vm_env->GetStringLength(js);
        PyObject *string = PyUnicode_FromUnicode(NULL, len);

        if (!string)
            return NULL;

        jboolean isCopy;
        const jchar *jchars = vm_env->GetStringChars(js, &isCopy);
        Py_UNICODE *pchars = PyUnicode_AS_UNICODE(string);

        for (int i = 0; i < len; i++)
            pchars[i] = (Py_UNICODE) jchars[i];
        
        vm_env->ReleaseStringChars(js, jchars);
        return string;
    }
}

/* may be called from finalizer thread which has no vm_env thread local */
void JCCEnv::finalizeObject(JNIEnv *jenv, PyObject *obj)
{
    PythonGIL gil;

    set_vm_env(jenv);
    Py_DECREF(obj);
}

#endif /* PYTHON */
