# Enemy of the State: A State-Aware Black-Box Web Vulnerability Scanner  

This novel black-box web vulnerability scanner attempts to infer the state machine of the web application. 

It was first used for the paper [Enemy of the State: A State-Aware Black-Box Web Vulnerability Scanner](http://cs.ucsb.edu/~adoupe/static/enemy-of-the-state-usenix2012.pdf).

## Important Note

The code is proof-of-concept and demonstrates state machine inference of a web application. 

It possibly contains lots of bugs and is terrible written. Reader beware.

## Architecture

The frontend crawler is htmlunit 2.8. However, we had to patch
htmlunit to include functionality. I believe it was the ability to
click a link without executing JavaScript.

Anyway, there are two was of interfacing the java/htmlunit crawler to
the python backend.

[jcc](http://lucene.apache.org/pylucene/jcc/readme.html) and
[jython](http://www.jython.org/)

For our experiments we used jython and the corresponding jython branch
because jcc was having out-of-memory issues. But I'll leave the two
ways of installing/running here.

## How to Run

As mentioned above, understand that there are two ways of running the
crawler: jcc and jython.

The git master branch is for jcc and the jython branch is for jython.


### jcc

Note that I haven't run the scanner in this mode in a while, so these
may be wrong.

* Install the correct python egg in jcc_eggs. (If there isn't one
  available for your platform, let me know and I'll try to add one.)
  
* python crawler2.py "http://example.com"  


### jython

* Packages to install

Here are the ubuntu packages to install:
openjdk-7-jre-headless jython

* _Important note_

Your java version must be OpenJDK IcedTea >= 2.3.12 and Jython >= 2.5.2.

The jython version _does not work in Ubuntu 12.04._ However, it does
work in Ubuntu 13.10. I'm not sure why it doesn't work, and at this
point it's not worth spending the time to investigate further.

* Switch to the jython git branch
  git checkout jython

* Run the following command to tell jython to use the following
  htmlunit jars:
  
  export JYTHONPATH=./lib/apache-mime4j-0.6.jar:./lib/commons-codec-1.4.jar:./lib/commons-collections-3.2.1.jar:./lib/commons-io-1.4.jar:./lib/commons-lang-2.4.jar:./lib/commons-logging-1.1.1.jar:./lib/cssparser-0.9.5.jar:./lib/htmlunit-2.8.jar:./lib/htmlunit-core-js-2.8.jar:./lib/httpclient-4.0.1.jar:./lib/httpcore-4.0.1.jar:./lib/httpmime-4.0.1.jar:./lib/nekohtml-1.9.14.jar:./lib/sac-1.3.jar:./lib/serializer-2.7.1.jar:./lib/xalan-2.7.1.jar:./lib/xercesImpl-2.9.1.jar:./lib/xml-apis-1.3.04.jar

* jython crawler2.py "http://example.com"


### Additional Commandline Options

* -F - Do not fuzz the application.

* -R <command> - Command to reset the given web application to the
   initial state.

* -D - Debug level logging.

* -l <logfile> - Logfile. Otherwise it's stdout.

* -s - Write state graph.

* -d <dumpdir> - Directory to dump all the HTTP requests and
   responses. Can take up a lot of space.

## Credits

The fuzzing components are taken from [w3af](http://w3af.sourceforge.net/).



