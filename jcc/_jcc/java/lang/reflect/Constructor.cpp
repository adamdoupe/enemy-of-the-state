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

#include "java/lang/Class.h"
#include "java/lang/Object.h"
#include "java/lang/String.h"
#include "java/lang/reflect/Constructor.h"

namespace java {
    namespace lang {
        namespace reflect {

            enum {
                mid_getModifiers,
                mid_getSignature,
                mid_getParameterTypes,
                mid_getExceptionTypes,
                max_mid
            };

            Class *Constructor::class$ = NULL;
            jmethodID *Constructor::_mids = NULL;

            jclass Constructor::initializeClass()
            {
                if (!class$)
                {
                    jclass cls = env->findClass("java/lang/reflect/Constructor");

                    _mids = new jmethodID[max_mid];
                    _mids[mid_getModifiers] =
                        env->getMethodID(cls, "getModifiers",
                                         "()I");
                    _mids[mid_getParameterTypes] =
                        env->getMethodID(cls, "getParameterTypes",
                                         "()[Ljava/lang/Class;");
                    _mids[mid_getExceptionTypes] =
                        env->getMethodID(cls, "getExceptionTypes",
                                         "()[Ljava/lang/Class;");

                    class$ = (Class *) new JObject(cls);
                }
                
                return (jclass) class$->this$;
            }

            int Constructor::getModifiers() const
            {
                return env->callIntMethod(this$, _mids[mid_getModifiers]);
            }

            JArray<Class> Constructor::getParameterTypes() const
            {
                jobjectArray array = (jobjectArray)
                    env->callObjectMethod(this$, _mids[mid_getParameterTypes]);

                return JArray<Class>(array);
            }

            JArray<Class> Constructor::getExceptionTypes() const
            {
                jobjectArray array = (jobjectArray)
                    env->callObjectMethod(this$, _mids[mid_getExceptionTypes]);

                return JArray<Class>(array);
            }
        }
    }
}


#include "structmember.h"
#include "functions.h"
#include "macros.h"

namespace java {
    namespace lang {
        namespace reflect {

            static PyObject *t_Constructor_getModifiers(t_Constructor *self);
            static PyObject *t_Constructor_getParameterTypes(t_Constructor *self);
            static PyObject *t_Constructor_getExceptionTypes(t_Constructor *self);

            static PyMethodDef t_Constructor__methods_[] = {
                DECLARE_METHOD(t_Constructor, getModifiers, METH_NOARGS),
                DECLARE_METHOD(t_Constructor, getParameterTypes, METH_NOARGS),
                DECLARE_METHOD(t_Constructor, getExceptionTypes, METH_NOARGS),
                { NULL, NULL, 0, NULL }
            };

            DECLARE_TYPE(Constructor, t_Constructor, Object, Constructor,
                         abstract_init, 0, 0, 0, 0, 0);

            static PyObject *t_Constructor_getModifiers(t_Constructor *self)
            {
                jint modifiers;

                OBJ_CALL(modifiers = self->object.getModifiers());
                return PyInt_FromLong(modifiers);                
            }

            static PyObject *t_Constructor_getParameterTypes(t_Constructor *self)
            {
                JArray<Class> types((jobject) NULL);
                OBJ_CALL(types = self->object.getParameterTypes());
                return types.toSequence(t_Class::wrap_Object);
            }

            static PyObject *t_Constructor_getExceptionTypes(t_Constructor *self)
            {
                JArray<Class> types((jobject) NULL);
                OBJ_CALL(types = self->object.getExceptionTypes());
                return types.toSequence(t_Class::wrap_Object);
            }
        }
    }
}
