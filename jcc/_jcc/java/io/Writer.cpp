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
#include "java/io/Writer.h"

namespace java {
    namespace io {

        enum {
            max_mid
        };

        java::lang::Class *Writer::class$ = NULL;
        jmethodID *Writer::_mids = NULL;

        jclass Writer::initializeClass()
        {
            if (!class$)
            {
                jclass cls = env->findClass("java/io/Writer");

                _mids = new jmethodID[max_mid];
                class$ = (java::lang::Class *) new JObject(cls);
            }

            return (jclass) class$->this$;
        }
    }
}


#include "structmember.h"
#include "functions.h"
#include "macros.h"

namespace java {
    namespace io {

        static PyMethodDef t_Writer__methods_[] = {
            { NULL, NULL, 0, NULL }
        };

        DECLARE_TYPE(Writer, t_Writer, java::lang::Object, Writer,
                     abstract_init, 0, 0, 0, 0, 0);
    }
}
