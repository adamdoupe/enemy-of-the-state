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
#include <string.h>
#include "JCCEnv.h"
#include "java/lang/Object.h"
#include "java/lang/Class.h"
#include "java/lang/String.h"

namespace java {
    namespace lang {

        enum {
            mid__init_,
            mid_toString,
            mid_length,
            max_mid
        };

        Class *String::class$ = NULL;
        jmethodID *String::_mids = NULL;

        jclass String::initializeClass()
        {
            if (!class$)
            {
                jclass cls = env->findClass("java/lang/String");

                _mids = new jmethodID[max_mid];
                _mids[mid__init_] = 
                    env->getMethodID(cls, "<init>",
                                     "()V");
                _mids[mid_toString] = 
                    env->getMethodID(cls, "toString",
                                     "()Ljava/lang/String;");
                _mids[mid_length] = 
                    env->getMethodID(cls, "length",
                                     "()I");

                class$ = (Class *) new JObject(cls);
            }

            return (jclass) class$->this$;
        }

        String::String() : Object(env->newObject(initializeClass, &_mids, mid__init_)) {
        }

        int String::length() const
        {
            return env->callIntMethod(this$, _mids[mid_length]);
        }
    }
}


#include "structmember.h"
#include "functions.h"
#include "macros.h"

namespace java {
    namespace lang {

        static int t_String_init(t_String *self,
                                 PyObject *args, PyObject *kwds);
        static PyObject *t_String_length(t_String *self);

        static PyMethodDef t_String__methods_[] = {
            DECLARE_METHOD(t_String, length, METH_NOARGS),
            { NULL, NULL, 0, NULL }
        };

        DECLARE_TYPE(String, t_String, Object, java::lang::String,
                     t_String_init, 0, 0, 0, 0, 0);

        static int t_String_init(t_String *self,
                                 PyObject *args, PyObject *kwds)
        {
            char *bytes;

            switch (PyTuple_Size(args)) {
              case 0:
                INT_CALL(self->object = String());
                break;
              case 1:
                if (!PyArg_ParseTuple(args, "s", &bytes))
                    return -1;
                INT_CALL(self->object = String(env->fromUTF(bytes)));
                break;
              default:
                PyErr_SetString(PyExc_ValueError, "invalid args");
                return -1;
            }
        
            return 0;
        }

        static PyObject *t_String_length(t_String *self)
        {
            jint length;

            OBJ_CALL(length = self->object.length());
            return PyInt_FromLong(length);
        }
    }
}
