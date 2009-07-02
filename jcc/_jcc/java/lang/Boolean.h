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

#ifndef _Boolean_H
#define _Boolean_H

#include <Python.h>
#include "java/lang/Object.h"
#include "java/lang/Class.h"

namespace java {
    namespace lang {

        class Boolean : public Object {
        public:
            static Class *class$;
            static jmethodID *_mids;
            static jclass initializeClass();

            explicit Boolean(jobject obj) : Object(obj) {
                initializeClass();
            }

            static Boolean *TRUE;
            static Boolean *FALSE;
        };

        extern PyTypeObject Boolean$$Type;

        class t_Boolean {
        public:
            PyObject_HEAD
            Boolean object;
            static PyObject *wrap_Object(const Boolean& object);
            static PyObject *wrap_jobject(const jobject& object);
        };
    }
}

#endif /* _Boolean_H */
