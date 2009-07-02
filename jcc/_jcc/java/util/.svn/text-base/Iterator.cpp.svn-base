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
#include "java/util/Iterator.h"

namespace java {
    namespace util {
        enum {
            mid_hasNext,
            mid_next,
            max_mid
        };

        Class *Iterator::class$ = NULL;
        jmethodID *Iterator::mids$ = NULL;

        jclass Iterator::initializeClass()
        {
            if (!class$)
            {
                jclass cls = env->findClass("java/util/Iterator");

                mids$ = new jmethodID[max_mid];
                mids$[mid_hasNext] = env->getMethodID(cls, "hasNext",
                                                      "()Z");
                mids$[mid_next] = env->getMethodID(cls, "next",
                                                   "()Ljava/lang/Object;");

                class$ = (Class *) new JObject(cls);
            }

            return (jclass) class$->this$;
        }

        jboolean Iterator::hasNext() const
        {
            return env->callBooleanMethod(this$, mids$[mid_hasNext]);
        }

        Object Iterator::next() const
        {
            return Object(env->callObjectMethod(this$, mids$[mid_next]));
        }
    }
}


#include "structmember.h"
#include "functions.h"
#include "macros.h"

namespace java {
    namespace util {

        static PyObject *t_Iterator_hasNext(t_Iterator *self);
        static PyObject *t_Iterator_next(t_Iterator *self);

        static PyMethodDef t_Iterator__methods_[] = {
            DECLARE_METHOD(t_Iterator, hasNext, METH_NOARGS),
            DECLARE_METHOD(t_Iterator, next, METH_NOARGS),
            { NULL, NULL, 0, NULL }
        };

        DECLARE_TYPE(Iterator, t_Iterator, JObject, java::util::Iterator,
                     abstract_init, 0, 0, 0, 0, 0);

        static PyObject *t_Iterator_hasNext(t_Iterator *self)
        {
            jboolean b;

            OBJ_CALL(b = self->object.hasNext());
            Py_RETURN_BOOL(b);
        }

        static PyObject *t_Iterator_next(t_Iterator *self)
        {
            Object next((jobject) NULL);

            OBJ_CALL(next = self->object.next());
            return t_Object::wrap_Object(next);
        }
    }
}
