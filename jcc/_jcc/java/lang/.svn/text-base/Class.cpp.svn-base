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
#include "JCCEnv.h"

#include "JArray.h"
#include "java/lang/Object.h"
#include "java/lang/Class.h"
#include "java/lang/String.h"
#include "java/lang/reflect/Method.h"
#include "java/lang/reflect/Constructor.h"
#include "java/lang/reflect/Field.h"

namespace java {
    namespace lang {
        using namespace reflect;

        enum {
            mid_forName,
            mid_getDeclaredMethods,
            mid_getMethods,
            mid_getMethod,
            mid_getDeclaredMethod,
            mid_getDeclaredConstructors,
            mid_getDeclaredFields,
            mid_getDeclaredClasses,
            mid_isArray,
            mid_isPrimitive,
            mid_isInterface,
            mid_isAssignableFrom,
            mid_getComponentType,
            mid_getSuperclass,
            mid_getInterfaces,
            mid_getName,
            mid_getModifiers,
            mid_isInstance,
            max_mid
        };

        Class *Class::class$ = NULL;
        jmethodID *Class::_mids = NULL;

        jclass Class::initializeClass()
        {
            if (!class$)
            {
                jclass cls = env->findClass("java/lang/Class");

                _mids = new jmethodID[max_mid];
                _mids[mid_forName] =
                    env->getStaticMethodID(cls, "forName",
                                           "(Ljava/lang/String;)Ljava/lang/Class;");
                _mids[mid_getDeclaredMethods] =
                    env->getMethodID(cls, "getDeclaredMethods",
                                     "()[Ljava/lang/reflect/Method;");
                _mids[mid_getMethods] =
                    env->getMethodID(cls, "getMethods",
                                     "()[Ljava/lang/reflect/Method;");
                _mids[mid_getMethod] =
                    env->getMethodID(cls, "getMethod",
                                     "(Ljava/lang/String;[Ljava/lang/Class;)Ljava/lang/reflect/Method;");
                _mids[mid_getDeclaredMethod] =
                    env->getMethodID(cls, "getDeclaredMethod",
                                     "(Ljava/lang/String;[Ljava/lang/Class;)Ljava/lang/reflect/Method;");
                _mids[mid_getDeclaredConstructors] =
                    env->getMethodID(cls, "getDeclaredConstructors",
                                     "()[Ljava/lang/reflect/Constructor;");
                _mids[mid_getDeclaredFields] =
                    env->getMethodID(cls, "getDeclaredFields",
                                     "()[Ljava/lang/reflect/Field;");
                _mids[mid_getDeclaredClasses] =
                    env->getMethodID(cls, "getDeclaredClasses",
                                     "()[Ljava/lang/Class;");
                _mids[mid_isArray] =
                    env->getMethodID(cls, "isArray",
                                     "()Z");
                _mids[mid_isPrimitive] =
                    env->getMethodID(cls, "isPrimitive",
                                     "()Z");
                _mids[mid_isInterface] =
                    env->getMethodID(cls, "isInterface",
                                     "()Z");
                _mids[mid_isAssignableFrom] =
                    env->getMethodID(cls, "isAssignableFrom",
                                     "(Ljava/lang/Class;)Z");
                _mids[mid_getComponentType] =
                    env->getMethodID(cls, "getComponentType",
                                     "()Ljava/lang/Class;");
                _mids[mid_getSuperclass] =
                    env->getMethodID(cls, "getSuperclass",
                                     "()Ljava/lang/Class;");
                _mids[mid_getInterfaces] =
                    env->getMethodID(cls, "getInterfaces",
                                     "()[Ljava/lang/Class;");
                _mids[mid_getName] =
                    env->getMethodID(cls, "getName",
                                     "()Ljava/lang/String;");
                _mids[mid_getModifiers] =
                    env->getMethodID(cls, "getModifiers",
                                     "()I");
                _mids[mid_isInstance] =
                    env->getMethodID(cls, "isInstance",
                                     "(Ljava/lang/Object;)Z");

                class$ = (Class *) new JObject(cls);
            }

            return (jclass) class$->this$;
        }


        Class Class::forName(const String& className)
        {
            jclass cls = initializeClass();
            jobject obj = env->callStaticObjectMethod(cls, _mids[mid_forName], className.this$);

            return Class((jclass) obj);
        }

        JArray<Method> Class::getDeclaredMethods() const
        {
            jobjectArray array = (jobjectArray)
                env->callObjectMethod(this$, _mids[mid_getDeclaredMethods]);

            return JArray<Method>(array);
        }

        JArray<Method> Class::getMethods() const
        {
            jobjectArray array = (jobjectArray)
                env->callObjectMethod(this$, _mids[mid_getMethods]);

            return JArray<Method>(array);
        }

        Method Class::getMethod(const String& name, const JArray<Class>& params) const
        {
            return Method(env->callObjectMethod(this$, _mids[mid_getMethod], name.this$, params.this$));
        }

        Method Class::getDeclaredMethod(const String& name, const JArray<Class>& params) const
        {
            return Method(env->callObjectMethod(this$, _mids[mid_getDeclaredMethod], name.this$, params.this$));
        }

        JArray<Constructor> Class::getDeclaredConstructors() const
        {
            jobjectArray array = (jobjectArray)
                env->callObjectMethod(this$, _mids[mid_getDeclaredConstructors]);

            return JArray<Constructor>(array);
        }

        JArray<Field> Class::getDeclaredFields() const
        {
            jobjectArray array = (jobjectArray)
                env->callObjectMethod(this$, _mids[mid_getDeclaredFields]);

            return JArray<Field>(array);
        }

        JArray<Class> Class::getDeclaredClasses() const
        {
            jobjectArray array = (jobjectArray)
                env->callObjectMethod(this$, _mids[mid_getDeclaredClasses]);

            return JArray<Class>(array);
        }

        int Class::isArray() const
        {
            return (int) env->callBooleanMethod(this$, _mids[mid_isArray]);
        }

        int Class::isPrimitive() const
        {
            return (int) env->callBooleanMethod(this$, _mids[mid_isPrimitive]);
        }

        int Class::isInterface() const
        {
            return (int) env->callBooleanMethod(this$, _mids[mid_isInterface]);
        }

        int Class::isAssignableFrom(const Class& obj) const
        {
            return (int) env->callBooleanMethod(this$, _mids[mid_isAssignableFrom], obj.this$);
        }

        Class Class::getComponentType() const
        {
            return Class(env->callObjectMethod(this$, _mids[mid_getComponentType]));
        }

        Class Class::getSuperclass() const
        {
            return Class(env->callObjectMethod(this$, _mids[mid_getSuperclass]));
        }

        JArray<Class> Class::getInterfaces() const
        {
            jobjectArray array = (jobjectArray)
                env->callObjectMethod(this$, _mids[mid_getInterfaces]);

            return JArray<Class>(array);
        }

        String Class::getName() const
        {
            return String(env->callObjectMethod(this$, _mids[mid_getName]));
        }

        int Class::getModifiers() const
        {
            return env->callIntMethod(this$, _mids[mid_getModifiers]);
        }

        int Class::isInstance(const Object &obj) const
        {
            return env->callBooleanMethod(this$, _mids[mid_isInstance],
                                          obj.this$);
        }
    }
}


#include "structmember.h"
#include "functions.h"
#include "macros.h"

namespace java {
    namespace lang {
        using namespace reflect;

        static PyObject *t_Class_forName(PyTypeObject *type, PyObject *arg);
        static PyObject *t_Class_getDeclaredConstructors(t_Class *self);
        static PyObject *t_Class_getDeclaredMethods(t_Class *self);
        static PyObject *t_Class_getMethods(t_Class *self);
        static PyObject *t_Class_getMethod(t_Class *self, PyObject *args);
        static PyObject *t_Class_getDeclaredMethod(t_Class *self, PyObject *args);
        static PyObject *t_Class_getDeclaredFields(t_Class *self);
        static PyObject *t_Class_getDeclaredClasses(t_Class *self);
        static PyObject *t_Class_isArray(t_Class *self);
        static PyObject *t_Class_isPrimitive(t_Class *self);
        static PyObject *t_Class_isInterface(t_Class *self);
        static PyObject *t_Class_isAssignableFrom(t_Class *self, PyObject *arg);
        static PyObject *t_Class_getComponentType(t_Class *self);
        static PyObject *t_Class_getSuperclass(t_Class *self);
        static PyObject *t_Class_getInterfaces(t_Class *self);
        static PyObject *t_Class_getName(t_Class *self);
        static PyObject *t_Class_getModifiers(t_Class *self);

        static PyMethodDef t_Class__methods_[] = {
            DECLARE_METHOD(t_Class, forName, METH_O | METH_CLASS),
            DECLARE_METHOD(t_Class, getDeclaredConstructors, METH_NOARGS),
            DECLARE_METHOD(t_Class, getDeclaredMethods, METH_NOARGS),
            DECLARE_METHOD(t_Class, getMethods, METH_NOARGS),
            DECLARE_METHOD(t_Class, getMethod, METH_VARARGS),
            DECLARE_METHOD(t_Class, getDeclaredMethod, METH_VARARGS),
            DECLARE_METHOD(t_Class, getDeclaredFields, METH_NOARGS),
            DECLARE_METHOD(t_Class, getDeclaredClasses, METH_NOARGS),
            DECLARE_METHOD(t_Class, isArray, METH_NOARGS),
            DECLARE_METHOD(t_Class, isPrimitive, METH_NOARGS),
            DECLARE_METHOD(t_Class, isInterface, METH_NOARGS),
            DECLARE_METHOD(t_Class, isAssignableFrom, METH_O),
            DECLARE_METHOD(t_Class, getComponentType, METH_NOARGS),
            DECLARE_METHOD(t_Class, getSuperclass, METH_NOARGS),
            DECLARE_METHOD(t_Class, getInterfaces, METH_NOARGS),
            DECLARE_METHOD(t_Class, getName, METH_NOARGS),
            DECLARE_METHOD(t_Class, getModifiers, METH_NOARGS),
            { NULL, NULL, 0, NULL }
        };

        DECLARE_TYPE(Class, t_Class, Object, java::lang::Class,
                     abstract_init, 0, 0, 0, 0, 0);

        static PyObject *t_Class_forName(PyTypeObject *type, PyObject *arg)
        {
            if (!PyString_Check(arg))
            {
                PyErr_SetObject(PyExc_TypeError, arg);
                return NULL;
            }

            try {
                char *className = PyString_AsString(arg);
                String name = String(env->fromUTF(className));

                return t_Class::wrap_Object(Class::forName(name));
            } catch (JCCEnv::exception e) {
                return PyErr_SetJavaError(e.throwable);
            }
        }

        static PyObject *t_Class_getDeclaredConstructors(t_Class *self)
        {
            JArray<Constructor> constructors((jobject) NULL);

            OBJ_CALL(constructors = self->object.getDeclaredConstructors());
            return constructors.toSequence(t_Constructor::wrap_Object);
        }

        static PyObject *t_Class_getDeclaredMethods(t_Class *self)
        {
            JArray<Method> methods((jobject) NULL);

            OBJ_CALL(methods = self->object.getDeclaredMethods());
            return methods.toSequence(t_Method::wrap_Object);
        }

        static PyObject *t_Class_getMethods(t_Class *self)
        {
            JArray<Method> methods((jobject) NULL);

            OBJ_CALL(methods = self->object.getMethods());
            return methods.toSequence(t_Method::wrap_Object);
        }

        static PyObject *t_Class_getMethod(t_Class *self, PyObject *args)
        {
            String name((jobject) NULL);
            JArray<Class> params((jobject) NULL);
            Method method((jobject) NULL);

            if (!parseArgs(args, "s[j", Class::class$, &name, &params))
            {
                OBJ_CALL(method = self->object.getMethod(name, params));
                return t_Method::wrap_Object(method);
            }

            return PyErr_SetArgsError((PyObject *) self, "getMethod", args);
        }

        static PyObject *t_Class_getDeclaredMethod(t_Class *self, PyObject *args)
        {
            String name((jobject) NULL);
            JArray<Class> params((jobject) NULL);
            Method method((jobject) NULL);

            if (!parseArgs(args, "s[j", Class::class$, &name, &params))
            {
                OBJ_CALL(method = self->object.getDeclaredMethod(name, params));
                return t_Method::wrap_Object(method);
            }

            return PyErr_SetArgsError((PyObject *) self, "getMethod", args);
        }

        static PyObject *t_Class_getDeclaredFields(t_Class *self)
        {
            JArray<Field> fields((jobject) NULL);

            OBJ_CALL(fields = self->object.getDeclaredFields());
            return fields.toSequence(t_Field::wrap_Object);
        }

        static PyObject *t_Class_getDeclaredClasses(t_Class *self)
        {
            JArray<Class> array((jobject) NULL);

            OBJ_CALL(array = self->object.getDeclaredClasses());
            return array.toSequence(t_Class::wrap_Object);
        }

        static PyObject *t_Class_isArray(t_Class *self)
        {
            int isArray;

            OBJ_CALL(isArray = self->object.isArray());
            Py_RETURN_BOOL(isArray);
        }

        static PyObject *t_Class_isPrimitive(t_Class *self)
        {
            int isPrimitive;

            OBJ_CALL(isPrimitive = self->object.isPrimitive());
            Py_RETURN_BOOL(isPrimitive);
        }

        static PyObject *t_Class_isInterface(t_Class *self)
        {
            int isInterface;

            OBJ_CALL(isInterface = self->object.isInterface());
            Py_RETURN_BOOL(isInterface);
        }

        static PyObject *t_Class_isAssignableFrom(t_Class *self, PyObject *arg)
        {
            if (!PyObject_TypeCheck(arg, &Class$$Type))
            {
                PyErr_SetObject(PyExc_TypeError, arg);
                return NULL;
            }

            try {
                Class cls = ((t_Class *) arg)->object;
                int isAssignableFrom = self->object.isAssignableFrom(cls);

                Py_RETURN_BOOL(isAssignableFrom);
            } catch (JCCEnv::exception e) {
                return PyErr_SetJavaError(e.throwable);
            }
        }

        static PyObject *t_Class_getComponentType(t_Class *self)
        {
            Class cls((jobject) NULL);

            OBJ_CALL(cls = self->object.getComponentType());
            return t_Class::wrap_Object(cls);
        }

        static PyObject *t_Class_getSuperclass(t_Class *self)
        {
            Class cls((jobject) NULL);

            OBJ_CALL(cls = self->object.getSuperclass());
            return t_Class::wrap_Object(cls);
        }

        static PyObject *t_Class_getInterfaces(t_Class *self)
        {
            JArray<Class> interfaces((jobject) NULL);

            OBJ_CALL(interfaces = self->object.getInterfaces());
            return interfaces.toSequence(t_Class::wrap_Object);
        }

        static PyObject *t_Class_getName(t_Class *self)
        {
            String name((jobject) NULL);

            OBJ_CALL(name = self->object.getName());
            return j2p(name);
        }

        static PyObject *t_Class_getModifiers(t_Class *self)
        {
            jint modifiers;

            OBJ_CALL(modifiers = self->object.getModifiers());
            return PyInt_FromLong(modifiers);            
        }

    }
}
