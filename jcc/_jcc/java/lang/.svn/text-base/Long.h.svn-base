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

#ifndef _Long_H
#define _Long_H

#include <Python.h>
#include "java/lang/Object.h"
#include "java/lang/Class.h"

namespace java {
    namespace lang {

        class Long : public Object {
        public:
            static Class *class$;
            static jmethodID *_mids;
            static jclass initializeClass();

            explicit Long(jobject obj) : Object(obj) {
                initializeClass();
            }
            Long(jlong);
        };

        extern PyTypeObject Long$$Type;

        class t_Long {
        public:
            PyObject_HEAD
            Long object;
            static PyObject *wrap_Object(const Long& object);
            static PyObject *wrap_jobject(const jobject& object);
        };
    }
}

#endif /* _Long_H */
