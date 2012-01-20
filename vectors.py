def urlvector(request):
    """ /path/to/path.html?p1=v1&p2=v2
        ->
        ['path', 'to', 'page.html', ('p1', 'p2'), ('v1', 'v2')]
    """
    # XXX "/path/to" and "path/to" will be trated the same!
    if request.path.strip() == ('/'):
        urltoks = ['/']
    else:
        urltoks = [i for i in request.path.split('/') if i]
    if not urltoks:
        urltoks = ['<SAME/PAGE>']
    query = request.query
    if query:
        querytoks = request.query.split('&')
        keys, values = zip(*(i.split('=', 1) for i in querytoks if i))
        urltoks.append(tuple(keys))
        urltoks.append(tuple(values))
    return tuple(urltoks)

def formvector(method, action, inputs, hiddens):
    urltoks = [method] + [i if i  else '/' for i in action.path.split('/')]
    query = action.query
    if query:
        querytoks = action.query.split('&')
        keys, values = zip(*(i.split('=', 1) for i in querytoks if i))
        urltoks.append(tuple(keys))
        urltoks.append(tuple(values))
    if inputs:
        urltoks.append(tuple(inputs))
    if hiddens:
        # TODO hiddens values
        urltoks.append(tuple(hiddens))
    return tuple(urltoks)

def linksvector(page):
    linksvector = tuple([tuple(i) for i in page.linkstree.iterlevels()])
    return linksvector


