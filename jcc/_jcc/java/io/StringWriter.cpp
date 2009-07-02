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
#include "java/io/StringWriter.h"

namespace java {
    namespace io {

        enum {
            mid__init_,
            max_mid
        };

        java::lang::Class *StringWriter::class$ = NULL;
        jmethodID *StringWriter::_mids = NULL;

        jclass StringWriter::initializeClass()
        {
            if (!class$)
            {
                jclass cls = env->findClass("java/io/StringWriter");

                _mids = new jmethodID[max_mid];
                _mids[mid__init_] = env->getMethodID(cls, "<init>", "()V");

                class$ = (java::lang::Class *) new JObject(cls);
            }

            return (jclass) class$->this$;
        }

        StringWriter::StringWriter() : Writer(env->newObject(initializeClass, &_mids, mid__init_)) {
        }
    }
}


#include "structmember.h"
#include "functions.h"
#include "macros.h"

namespace java {
    namespace io {

        static int t_StringWriter_init(t_StringWriter *self,
                                       PyObject *args, PyObject *kwds);

        static PyMethodDef t_StringWriter__methods_[] = {
            { NULL, NULL, 0, NULL }
        };

        DECLARE_TYPE(StringWriter, t_StringWriter, Writer,
                     java::io::StringWriter, t_StringWriter_init,
                     0, 0, 0, 0, 0);

        static int t_StringWriter_init(t_StringWriter *self,
                                       PyObject *args, PyObject *kwds)
        {
            char *bytes;

            switch (PyTuple_Size(args)) {
              case 0:
                INT_CALL(self->object = StringWriter());
                break;
              default:
                PyErr_SetString(PyExc_ValueError, "invalid args");
                return -1;
            }
        
            return 0;
        }
    }
}
