import sys
sys.path.append("/home/adamd/research/black-box/blackbox/crawler/audit")
sys.path.append("/home/adamd/research/black-box/blackbox/crawler")
print sys.path
from fuzzableRequest import fuzzableRequest
from httpQsRequest import httpQsRequest
from urlParser import url_object
from xss import xss
from plugin_wrapper import *

url = url_object("http://127.0.0.1/adam.php?test=blah")
fr = httpQsRequest()
fr.setURI(url)

plugin = xss("crawler")

plugin.audit(fr)
