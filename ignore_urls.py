import re

ignoreUrlParts = [
        re.compile(r'&sid=[a-f0-9]{32}'),
        re.compile(r'sid=[a-f0-9]{32}&'),
        re.compile(r'\?sid=[a-f0-9]{32}$'),
        re.compile(r'^sid=[a-f0-9]{32}$'),
        ]



def filterIgnoreUrlParts(s):
    if s:
        for i in ignoreUrlParts:
            s = i.sub('', s)
    return s


