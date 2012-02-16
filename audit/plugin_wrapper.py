import time
from collections import defaultdict

from threading import Thread, Event
from Queue import Queue
from httpQsRequest import httpQsRequest
from httpPostDataRequest import httpPostDataRequest
from urlParser import url_object
from httpResponse import httpResponse
from dataContainer import dataContainer


import com.gargoylesoftware.htmlunit as htmlunit
import java
from request import Request

class plugin_wrapper(object):
    
    def __init__(self, actual_plugin):
        self.response_queue = Queue(1)
        self.request_queue = Queue(1)
        self.do_audit = Queue(1)
        self.audit_done = Event()

        self.actual_plugin = actual_plugin((self.response_queue, self.request_queue))

        self.process = Thread(target=self.communicate_with_actual)
        self.process.start()

    def audit(self, req):
        done = False
        self.audit_done.clear()
        self.do_audit.put(request_to_fuzzable_request(req))
        while not done:
            # Everything else
            if self.request_queue.qsize() > 0:
                new_mutant = self.request_queue.get()
                new_req = mutant_to_request(new_mutant)

                response = yield new_req
                w3af_response = response_to_w3af_response(response)
                self.response_queue.put(w3af_response)
            else:
                time.sleep(.0001)                
            done = self.audit_done.isSet()

    def communicate_with_actual(self):
        while True:
            fr_initial_request = self.do_audit.get()
            if isinstance(fr_initial_request, str):
                break
            self.actual_plugin.audit(fr_initial_request)
            self.audit_done.set()

    def stop(self):
        self.do_audit.put("DONE")
    

def mutant_to_request(mutant):
    """
    This function takes a w3af mutant and transforms it to our crawler's request
    """
    url = str(mutant.getURI())
    data = mutant.getData()

    # Also add the cookie header; this is needed by the mutantCookie
    headers = mutant.getHeaders()
    cookie = mutant.getCookie()
    if cookie:
        headers['Cookie'] = str(cookie)

    method = mutant.getMethod()

    webrequest = htmlunit.WebRequest(java.net.URL(url), method_to_htmlunit_http_method(method))

    # set the headers
    for header_name, value in headers.iteritems():
        webrequest.setAdditionalHeader(header_name, value)

    # set the data
    if data:
        v = java.util.Vector()
        for data_name, data_value in data.iteritems():
            data = data_value[0]
            if isinstance(data, str):
                pass
            elif isinstance(data, unicode):
                data = data.encode('ascii', 'ignore')
            else:
                data = str(data)
            name_value_pair = htmlunit.util.NameValuePair(data_name, data)
            v.add(name_value_pair)
        webrequest.setRequestParameters(v)    

    return Request(webrequest)


def method_to_htmlunit_http_method(method_str):
    if method_str.upper() == "GET":
        return htmlunit.HttpMethod.GET
    elif method_str.upper() == "POST":
        return htmlunit.HttpMethod.POST
    else:
        raise Exception("unfilled exception http method " + method_str)

def request_to_fuzzable_request(req):
    """
    This functions takes our crawler's request and converts it to the proper fuzzable request
    """
    fuzzable_request = None
    if req.isPOST:
        fuzzable_request = httpPostDataRequest()
        url = url_object(req.webrequest.getUrl().toString())
        fuzzable_request.setURL(url)
        dc = dataContainer()
        for nv in req.webrequest.getRequestParameters():
            name = nv.getName()
            value = nv.getValue()
            dc[name] = [value]
        fuzzable_request.setDc(dc)
    else:
        # request is a GET
        fuzzable_request = httpQsRequest()
        url = url_object(req.webrequest.getUrl().toString())
        fuzzable_request.setURI(url)

    return fuzzable_request


def response_to_w3af_response(response):
    """
    This function take our crawler's response object and converts it to a w3af response object.
    """
    code = response.code
    request_url = url_object(response.page.reqresp.request.webrequest.getUrl().toString())
    actual_data = response.content

    headers = {}
    for nv in response.webresponse.getResponseHeaders():
        name = nv.getName()
        value = nv.getValue()
        headers[name] = value
    
    w3af_response = httpResponse(code, actual_data, headers, request_url, request_url, time=response.time)
    return w3af_response
