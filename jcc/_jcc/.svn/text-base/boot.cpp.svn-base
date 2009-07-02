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
#include <Python.h>
#include "java/lang/Class.h"
#include "java/lang/RuntimeException.h"
#include "macros.h"

extern PyTypeObject JObject$$Type, ConstVariableDescriptor$$Type;

PyObject *initJCC(PyObject *module);
PyObject *initVM(PyObject *self, PyObject *args, PyObject *kwds);

namespace java {
    namespace lang {
        void __install__(PyObject *m);
    }
    namespace io {
        void __install__(PyObject *m);
    }
}

PyObject *__initialize__(PyObject *module, PyObject *args, PyObject *kwds)
{
    PyObject *env = initVM(module, args, kwds);

    if (env == NULL)
        return NULL;

    java::lang::Class::initializeClass();
    java::lang::RuntimeException::initializeClass();

    return env;
}

#include "jccfuncs.h"

extern "C" {

    void init_jcc(void)
    {
        PyObject *m = Py_InitModule3("_jcc", jcc_funcs, "_jcc");

        initJCC(m);

        INSTALL_TYPE(JObject, m);
        INSTALL_TYPE(ConstVariableDescriptor, m);
        java::lang::__install__(m);
        java::io::__install__(m);
    }
}
