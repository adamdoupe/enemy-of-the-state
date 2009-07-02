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

#include "java/lang/Object.h"
#include "java/lang/Class.h"
#include "java/lang/String.h"

namespace java {
    namespace lang {
        enum {
            mid__init_,
            mid_toString,
            mid_getClass,
            mid_hashCode,
            max_mid
        };

        Class *Object::class$ = NULL;
        jmethodID *Object::mids$ = NULL;

        jclass Object::initializeClass()
        {
            if (!class$)
            {
                jclass cls = env->findClass("java/lang/Object");

                mids$ = new jmethodID[max_mid];
                mids$[mid__init_] = env->getMethodID(cls, "<init>",
                                                     "()V");
                mids$[mid_toString] = env->getMethodID(cls, "toString",
                                                       "()Ljava/lang/String;");
                mids$[mid_getClass] = env->getMethodID(cls, "getClass",
                                                       "()Ljava/lang/Class;");
                mids$[mid_hashCode] = env->getMethodID(cls, "hashCode",
                                                       "()I");

                class$ = (Class *) new JObject(cls);
            }

            return (jclass) class$->this$;
        }

        Object::Object() : JObject(env->newObject(initializeClass, &mids$, mid__init_)) {
        }

        String Object::toString() const
        {
            return String(env->callObjectMethod(this$, mids$[mid_toString]));
        }

        Class Object::getClass() const
        {
            return Class(env->callObjectMethod(this$, mids$[mid_getClass]));
        }

        int Object::hashCode() const
        {
            return env->callIntMethod(this$, mids$[mid_hashCode]);
        }
    }
}


#include "structmember.h"
#include "functions.h"
#include "macros.h"

namespace java {
    namespace lang {

        static int t_Object_init(t_Object *self,
                                 PyObject *args, PyObject *kwds);
        static PyObject *t_Object_getClass(t_Object *self);

        static PyMethodDef t_Object__methods_[] = {
            DECLARE_METHOD(t_Object, getClass, METH_NOARGS),
            { NULL, NULL, 0, NULL }
        };

        DECLARE_TYPE(Object, t_Object, JObject, java::lang::Object,
                     t_Object_init, 0, 0, 0, 0, 0);

        static int t_Object_init(t_Object *self,
                                 PyObject *args, PyObject *kwds)
        {
            switch (PyTuple_Size(args)) {
              case 0:
                INT_CALL(self->object = Object());
                break;
              default:
                PyErr_SetString(PyExc_ValueError, "invalid args");
                return -1;
            }
        
            return 0;
        }

        static PyObject *t_Object_getClass(t_Object *self)
        {
            Class cls((jobject) NULL);

            OBJ_CALL(cls = self->object.getClass());
            return t_Class::wrap_Object(cls);
        }
    }
}
