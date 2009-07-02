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

#ifndef _Throwable_H
#define _Throwable_H

#include <Python.h>
#include "java/lang/Object.h"
#include "java/lang/Class.h"
#include "JArray.h"

namespace java {

    namespace io {
        class PrintWriter;
    }

    namespace lang {
        class String;

        class Throwable : public Object {
        public:
            static Class *class$;
            static jmethodID *_mids;
            static jclass initializeClass();

            explicit Throwable(jobject obj) : Object(obj) {
                initializeClass();
            }

            void printStackTrace() const;
            void printStackTrace(java::io::PrintWriter) const;
            String getMessage() const;
        };

        extern PyTypeObject Throwable$$Type;

        class t_Throwable {
        public:
            PyObject_HEAD
            Throwable object;
            static PyObject *wrap_Object(const Throwable& object);
            static PyObject *wrap_jobject(const jobject& object);
        };
    }
}

#endif /* _Throwable_H */
