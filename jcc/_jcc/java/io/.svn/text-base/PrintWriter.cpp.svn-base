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
#include "java/io/PrintWriter.h"

namespace java {
    namespace io {

        enum {
            mid__init_,
            max_mid
        };

        java::lang::Class *PrintWriter::class$ = NULL;
        jmethodID *PrintWriter::_mids = NULL;

        jclass PrintWriter::initializeClass()
        {
            if (!class$)
            {
                jclass cls = env->findClass("java/io/PrintWriter");

                _mids = new jmethodID[max_mid];
                _mids[mid__init_] =
                    env->getMethodID(cls, "<init>", "(Ljava/io/Writer;)V");

                class$ = (java::lang::Class *) new JObject(cls);
            }

            return (jclass) class$->this$;
        }

        PrintWriter::PrintWriter(Writer writer) : Writer(env->newObject(initializeClass, &_mids, mid__init_, writer.this$)) {
        }
    }
}


#include "structmember.h"
#include "functions.h"
#include "macros.h"

namespace java {
    namespace io {

        static int t_PrintWriter_init(t_PrintWriter *self,
                                      PyObject *args, PyObject *kwds);

        static PyMethodDef t_PrintWriter__methods_[] = {
            { NULL, NULL, 0, NULL }
        };

        DECLARE_TYPE(PrintWriter, t_PrintWriter, Writer,
                     java::io::PrintWriter, t_PrintWriter_init,
                     0, 0, 0, 0, 0);

        static int t_PrintWriter_init(t_PrintWriter *self,
                                      PyObject *args, PyObject *kwds)
        {
            Writer writer((jobject) NULL);

            if (!parseArgs(args, "j", Writer::class$, &writer))
            {
                INT_CALL(self->object = PrintWriter(writer));
                return 0;
            }

            PyErr_SetString(PyExc_ValueError, "invalid args");
            return -1;
        }
    }
}
