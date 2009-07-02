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

#ifndef _RuntimeException_H
#define _RuntimeException_H

#include <Python.h>
#include "java/lang/Class.h"
#include "java/lang/Exception.h"
#include "JArray.h"

namespace java {
    namespace lang {

        class RuntimeException : public Exception {
        public:
            static Class *class$;
            static jmethodID *_mids;
            static jclass initializeClass();

            explicit RuntimeException(jobject obj) : Exception(obj) {
                initializeClass();
            }
        };

        extern PyTypeObject RuntimeException$$Type;

        class t_RuntimeException {
        public:
            PyObject_HEAD
            RuntimeException object;
            static PyObject *wrap_Object(const RuntimeException& object);
            static PyObject *wrap_jobject(const jobject& object);
        };
    }
}

#endif /* _RuntimeException_H */
