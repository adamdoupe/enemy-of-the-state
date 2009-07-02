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
#include "java/util/Enumeration.h"

namespace java {
    namespace util {
        enum {
            mid_hasMoreElements,
            mid_nextElement,
            max_mid
        };

        Class *Enumeration::class$ = NULL;
        jmethodID *Enumeration::mids$ = NULL;

        jclass Enumeration::initializeClass()
        {
            if (!class$)
            {
                jclass cls = env->findClass("java/util/Enumeration");

                mids$ = new jmethodID[max_mid];
                mids$[mid_hasMoreElements] = env->getMethodID(cls, "hasMoreElements", "()Z");
                mids$[mid_nextElement] = env->getMethodID(cls, "nextElement", "()Ljava/lang/Object;");

                class$ = (Class *) new JObject(cls);
            }

            return (jclass) class$->this$;
        }

        jboolean Enumeration::hasMoreElements() const
        {
            return env->callBooleanMethod(this$, mids$[mid_hasMoreElements]);
        }

        Object Enumeration::nextElement() const
        {
            return Object(env->callObjectMethod(this$, mids$[mid_nextElement]));
        }
    }
}


#include "structmember.h"
#include "functions.h"
#include "macros.h"

namespace java {
    namespace util {

        static PyObject *t_Enumeration_hasMoreElements(t_Enumeration *self);
        static PyObject *t_Enumeration_nextElement(t_Enumeration *self);

        static PyMethodDef t_Enumeration__methods_[] = {
            DECLARE_METHOD(t_Enumeration, hasMoreElements, METH_NOARGS),
            DECLARE_METHOD(t_Enumeration, nextElement, METH_NOARGS),
            { NULL, NULL, 0, NULL }
        };

        DECLARE_TYPE(Enumeration, t_Enumeration, JObject,
                     java::util::Enumeration, abstract_init, 0, 0, 0, 0, 0);

        static PyObject *t_Enumeration_hasMoreElements(t_Enumeration *self)
        {
            jboolean b;

            OBJ_CALL(b = self->object.hasMoreElements());
            Py_RETURN_BOOL(b);
        }

        static PyObject *t_Enumeration_nextElement(t_Enumeration *self)
        {
            Object nextElement((jobject) NULL);

            OBJ_CALL(nextElement = self->object.nextElement());
            return t_Object::wrap_Object(nextElement);
        }
    }
}
