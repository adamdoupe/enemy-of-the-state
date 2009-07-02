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

#ifndef _PrintWriter_H
#define _PrintWriter_H

#include <Python.h>
#include "java/lang/Class.h"
#include "java/io/Writer.h"

namespace java {
    namespace io {

        class PrintWriter : public Writer {
        public:
            static java::lang::Class *class$;
            static jmethodID *_mids;
            static jclass initializeClass();

            explicit PrintWriter(jobject obj) : Writer(obj) {
                initializeClass();
            }
            PrintWriter(Writer writer);
            PrintWriter(const PrintWriter& obj) : Writer(obj) {}
        };

        extern PyTypeObject PrintWriter$$Type;

        class t_PrintWriter {
        public:
            PyObject_HEAD
            PrintWriter object;
            static PyObject *wrap_Object(const PrintWriter& object);
            static PyObject *wrap_jobject(const jobject& object);
        };
    }
}

#endif /* _PrintWriter_H */
