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

#ifndef _Object_H
#define _Object_H

#include <Python.h>
#include "JObject.h"

namespace java {
    namespace lang {
        class Class;
        class String;

        class Object : public JObject {
        public:
            static Class *class$;
            static jmethodID *mids$;
            static jclass initializeClass();

            explicit Object();
            explicit Object(jobject obj) : JObject(obj) {
                initializeClass();
            }

            String toString() const;
            Class getClass() const;
            int hashCode() const;
        };

        extern PyTypeObject Object$$Type;

        class t_Object {
        public:
            PyObject_HEAD
            Object object;
            static PyObject *wrap_Object(const Object& object);
            static PyObject *wrap_jobject(const jobject& object);
        };
    }
}


#endif /* _Object_H */
