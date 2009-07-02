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

#ifndef _Method_H
#define _Method_H

#include <Python.h>
#include "JArray.h"

namespace java {
    namespace lang {
        class Class;
        class String;

        namespace reflect {
            class Method : public Object {
            public:
                static Class *class$;
                static jmethodID *_mids;
                static jclass initializeClass();

                explicit Method(jobject obj) : Object(obj) {
                    initializeClass();
                }
                Method(const Method& obj) : Object(obj) {}

                int getModifiers() const;
                Class getReturnType() const;
                String getName() const;
                JArray<Class> getParameterTypes() const;
                JArray<Class> getExceptionTypes() const;
                Class getDeclaringClass() const;
            };

            extern PyTypeObject Method$$Type;

            class t_Method {
            public:
                PyObject_HEAD
                Method object;
                static PyObject *wrap_Object(const Method& object);
                static PyObject *wrap_jobject(const jobject& object);
            };
        }
    }
}

#endif /* _Method_H */
