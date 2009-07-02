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

#ifndef _Constructor_H
#define _Constructor_H

#include <Python.h>
#include "JArray.h"

namespace java {
    namespace lang {
        class Class;
        class String;

        namespace reflect {
            class Constructor : public Object {
            public:
                static Class *class$;
                static jmethodID *_mids;
                static jclass initializeClass();

                explicit Constructor(jobject obj) : Object(obj) {
                    initializeClass();
                }
                Constructor(const Constructor& obj) : Object(obj) {}

                int getModifiers() const;
                JArray<Class> getParameterTypes() const;
                JArray<Class> getExceptionTypes() const;
            };


            extern PyTypeObject Constructor$$Type;

            class t_Constructor {
            public:
                PyObject_HEAD
                Constructor object;
                static PyObject *wrap_Object(const Constructor& object);
                static PyObject *wrap_jobject(const jobject& object);
            };
        }
    }
}

#endif /* _Constructor_H */
