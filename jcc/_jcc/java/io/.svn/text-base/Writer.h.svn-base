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

#ifndef _Writer_H
#define _Writer_H

#include <Python.h>
#include "java/lang/Object.h"
#include "java/lang/Class.h"
#include "JArray.h"

namespace java {
    namespace io {

        class Writer : public java::lang::Object {
        public:
            static java::lang::Class *class$;
            static jmethodID *_mids;
            static jclass initializeClass();

            explicit Writer(jobject obj) : Object(obj) {
                initializeClass();
            }
        };

        extern PyTypeObject Writer$$Type;

        class t_Writer {
        public:
            PyObject_HEAD
            Writer object;
            static PyObject *wrap_Object(const Writer& object);
            static PyObject *wrap_jobject(const jobject& object);
        };
    }
}

#endif /* _Writer_H */
