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

#ifndef _StringWriter_H
#define _StringWriter_H

#include <Python.h>
#include "java/lang/Class.h"
#include "java/io/Writer.h"

namespace java {
    namespace io {

        class StringWriter : public Writer {
        public:
            static java::lang::Class *class$;
            static jmethodID *_mids;
            static jclass initializeClass();

            explicit StringWriter(jobject obj) : Writer(obj) {
                initializeClass();
            }
            StringWriter();
            StringWriter(const StringWriter& obj) : Writer(obj) {}
        };

        extern PyTypeObject StringWriter$$Type;

        class t_StringWriter {
        public:
            PyObject_HEAD
            StringWriter object;
            static PyObject *wrap_Object(const StringWriter& object);
            static PyObject *wrap_jobject(const jobject& object);
        };
    }
}

#endif /* _StringWriter_H */
