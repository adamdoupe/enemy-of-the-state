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

#ifndef _Field_H
#define _Field_H

#include <Python.h>

namespace java {
    namespace lang {
        class Class;
        class String;

        namespace reflect {
            class Field : public Object {
            public:
                static Class *class$;
                static jmethodID *_mids;
                static jclass initializeClass();

                explicit Field(jobject obj) : Object(obj) {
                    initializeClass();
                }
                Field(const Field& obj) : Object(obj) {}

                int getModifiers() const;
                Class getType() const;
                String getName() const;
            };

            extern PyTypeObject Field$$Type;

            class t_Field {
            public:
                PyObject_HEAD
                Field object;
                static PyObject *wrap_Object(const Field& object);
                static PyObject *wrap_jobject(const jobject& object);
            };
        }
    }
}

#endif /* _Field_H */
