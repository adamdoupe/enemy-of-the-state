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

#ifndef _Exception_H
#define _Exception_H

#include <Python.h>
#include "java/lang/Class.h"
#include "java/lang/Throwable.h"
#include "JArray.h"

namespace java {
    namespace lang {

        class Exception : public Throwable {
        public:
            static Class *class$;
            static jmethodID *_mids;
            static jclass initializeClass();

            explicit Exception(jobject obj) : Throwable(obj) {
                initializeClass();
            }
        };

        extern PyTypeObject Exception$$Type;

        class t_Exception {
        public:
            PyObject_HEAD
            Exception object;
            static PyObject *wrap_Object(const Exception& object);
            static PyObject *wrap_jobject(const jobject& object);
        };
    }
}

#endif /* _Exception_H */
