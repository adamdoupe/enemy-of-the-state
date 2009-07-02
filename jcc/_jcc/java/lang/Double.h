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

#ifndef _Double_H
#define _Double_H

#include <Python.h>
#include "java/lang/Object.h"
#include "java/lang/Class.h"

namespace java {
    namespace lang {

        class Double : public Object {
        public:
            static Class *class$;
            static jmethodID *_mids;
            static jclass initializeClass();

            explicit Double(jobject obj) : Object(obj) {
                initializeClass();
            }
            Double(jdouble);
        };

        extern PyTypeObject Double$$Type;

        class t_Double {
        public:
            PyObject_HEAD
            Double object;
            static PyObject *wrap_Object(const Double& object);
            static PyObject *wrap_jobject(const jobject& object);
        };
    }
}

#endif /* _Double_H */
