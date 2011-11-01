
class PageMergeException(Exception):
    def __init__(self, msg=None):
        Exception.__init__(self, msg)


class MergeLinksTreeException(PageMergeException):
    def __init__(self, msg=None):
        PageMergeException.__init__(self, msg)

