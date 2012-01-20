import urlparse

def validanchor(current, href):
    """ Returns true if the href on the current page is valid to visit.

    current is the string URL of the current page and href is the string in the anchor.

    We don't want to visit any other domains, mailto, emailto, javascript, and 
    fragments of the current page (although that may help with executing JavaScript.
    """

    if not href:
        return False

    joined = urlparse.urljoin(current, href)

    joined_parsed = urlparse.urlparse(joined)
    current_parsed = urlparse.urlparse(current)

    if joined_parsed.scheme != 'http':
        return False

    if joined_parsed.hostname != current_parsed.hostname:
        return False

    return True
