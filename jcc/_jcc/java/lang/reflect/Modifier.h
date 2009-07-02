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

#ifndef _Modifier_H
#define _Modifier_H

#include <Python.h>
#include "JArray.h"

namespace java {
    namespace lang {
        class Class;
        class String;

        namespace reflect {
            class Modifier : public Object {
            private:
                explicit Modifier();
            public:
                explicit Modifier(jobject obj) : Object(obj) {
                    initializeClass();
                }
                static Class *class$;
                static jmethodID *_mids;
                static jclass initializeClass();

                static int isPublic(int mod);
                static int isStatic(int mod);
                static int isNative(int mod);
                static int isFinal(int mod);
                static int isAbstract(int mod);
                static int isPrivate(int mod);
                static int isProtected(int mod);
            };

            extern PyTypeObject Modifier$$Type;

            class t_Modifier {
            public:
                PyObject_HEAD
                Modifier object;
                static PyObject *wrap_Object(const Modifier& object);
                static PyObject *wrap_jobject(const jobject& object);
            };
        }
    }
}

#endif /* _Modifier_H */
