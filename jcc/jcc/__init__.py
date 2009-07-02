#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.

# jcc package

import os, sys

if sys.platform == 'win32':
    from jcc.config import SHARED
    if SHARED:
        path = os.environ['Path'].split(os.pathsep)
        eggpath = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
        if eggpath not in path:
            path.insert(0, eggpath)
            os.environ['Path'] = os.pathsep.join(path)

if __name__ == '__main__':
    import jcc.__main__
else:
    from _jcc import initVM

CLASSPATH=os.path.join(os.path.abspath(os.path.dirname(__file__)), "classes")
