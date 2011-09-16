""" This module contains some utility functions.
"""

def string_or_list_into_list(s_or_l):
    """ Turns a string into a list, but if given a list will return the list.
    """
    if isinstance(s_or_l, str):
        return [s_or_l]
    else:
        return s_or_l
