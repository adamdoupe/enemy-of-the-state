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

#ifndef _Enumeration_H
#define _Enumeration_H

#include <Python.h>
#include "JObject.h"

namespace java {
    namespace lang {
        class Class;
        class Object;
    }        
    namespace util {
        using namespace java::lang;

        class Enumeration : public JObject {
        public:
            static Class *class$;
            static jmethodID *mids$;
            static jclass initializeClass();

            explicit Enumeration(jobject obj) : JObject(obj) {
                initializeClass();
            }

            jboolean hasMoreElements() const;
            Object nextElement() const;
        };

        extern PyTypeObject Enumeration$$Type;

        class t_Enumeration {
        public:
            PyObject_HEAD
            Enumeration object;
            static PyObject *wrap_Object(const Enumeration& object);
            static PyObject *wrap_jobject(const jobject& object);
        };
    }
}

#endif /* _Enumeration_H */
