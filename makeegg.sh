VER=2.6

javac -classpath htmlunit-$VER/lib/htmlunit-$VER.jar *.java


RESERVED="--reserved READONLY --reserved T_SHORT --reserved T_INT --reserved T_LONG --reserved T_FLOAT --reserved T_DOUBLE --reserved T_STRING --reserved T_OBJECT --reserved T_CHAR --reserved T_BYTE --reserved T_UBYTE --reserved T_USHORT --reserved T_UINT --reserved T_ULONG --reserved T_STRING_INPLACE --reserved T_BOOL --reserved T_OBJECT_EX --reserved T_LONGLONG --reserved T_ULONGLONG --reserved T_PYSSIZET --reserved READONLY --reserved RO --reserved READ_RESTRICTED --reserved PY_WRITE_RESTRICTED --reserved RESTRICTED"

PARAMS="--python htmlunit --jar htmlunit-$VER/lib/htmlunit-$VER.jar --jar htmlunit-$VER/lib/htmlunit-core-js-$VER.jar $(for f in htmlunit-$VER/lib/[cnsx]*.jar; do echo ' --include' $f; done) --exclude com.gargoylesoftware.htmlunit.html.HtmlTableCell --exclude net.sourceforge.htmlunit.corejs.javascript.ScriptRuntime --exclude net.sourceforge.htmlunit.corejs.javascript.Node --version $VER.0 --package java.io --package java.net --classpath . HtmlPageWrapper HtmlElementWrapper --package java.lang java.lang.System --mapping java.util.Properties 'getProperty:(Ljava/lang/String;)Ljava/lang/String;' --files separate"

python -m jcc.__main__ $PARAMS $RESERVED --build --files 1 && python -m jcc.__main__ $PARAMS $RESERVED --bdist
