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
#include "java/lang/RuntimeException.h"

namespace java {
    namespace lang {

        enum {
            mid_printStackTrace,
            max_mid
        };

        Class *RuntimeException::class$ = NULL;
        jmethodID *RuntimeException::_mids = NULL;

        jclass RuntimeException::initializeClass()
        {
            if (!class$)
            {
                jclass cls = env->findClass("java/lang/RuntimeException");

                class$ = (Class *) new JObject(cls);
            }

            return (jclass) class$->this$;
        }
    }
}


#include "structmember.h"
#include "functions.h"
#include "macros.h"

namespace java {
    namespace lang {


        static PyMethodDef t_RuntimeException__methods_[] = {
            { NULL, NULL, 0, NULL }
        };

        DECLARE_TYPE(RuntimeException, t_RuntimeException, Object,
                     java::lang::RuntimeException, abstract_init,
                     0, 0, 0, 0, 0);
    }
}
