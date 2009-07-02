/* ====================================================================
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
 * ====================================================================
 */

package org.apache.jcc;


public class PythonException extends RuntimeException {
    public boolean withTrace = true;
    protected String message, errorName, traceback;

    public PythonException(String message)
    {
        super(message);
        getErrorInfo();  // sets errorName, message and traceback 
    }

    public String getMessage(boolean trace)
    {
        if (message == null)
            message = super.getMessage();

        if (trace)
            return message + "\n" + traceback;

        return message;
    }

    public String getMessage()
    {
        return getMessage(withTrace);
    }

    public String getErrorName()
    {
        return errorName;
    }

    public String getTraceback()
    {
        return traceback;
    }

    protected native void getErrorInfo();
    public native void clear();
}
