# Example script that shows how the co-routines will work


def audit(self, req):
    for i in ["adam", "test", "xss", "blah"]:
        new_req = req
            
        new_req.param[0] = i

        yield new_req

        response = yield

        if i in response:
            print "VULN FOUND"



def example_crawler():
    for req in found_requests:
        xss = xss.audit(req)
        
        try:
            while True:
                new_req = xss.next()

                response = new_req.send_request()

                if crawler.changed_state():
                    crawler.put_back_to_previous_state()

                xss.send(response)
        except StopIteration:
            pass
        
