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

#include <Python.h>
#include "macros.h"

namespace java {
    namespace lang {

        extern PyTypeObject Object$$Type;
        extern PyTypeObject String$$Type;
        extern PyTypeObject Class$$Type;
        extern PyTypeObject Throwable$$Type;
        extern PyTypeObject Exception$$Type;
        extern PyTypeObject RuntimeException$$Type;
        extern PyTypeObject Boolean$$Type;
        extern PyTypeObject Integer$$Type;
        extern PyTypeObject Long$$Type;
        extern PyTypeObject Double$$Type;
        
        namespace reflect {
            void __install__(PyObject *module);
        }

        void __install__(PyObject *m)
        {
            INSTALL_TYPE(Object, m);
            INSTALL_TYPE(String, m);
            INSTALL_TYPE(Class, m);
            INSTALL_TYPE(Throwable, m);
            INSTALL_TYPE(Exception, m);
            INSTALL_TYPE(RuntimeException, m);
            INSTALL_TYPE(Boolean, m);
            INSTALL_TYPE(Integer, m);
            INSTALL_TYPE(Long, m);
            INSTALL_TYPE(Double, m);
            reflect::__install__(m);
        }
    }
}
