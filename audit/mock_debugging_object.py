import pdb
import collections

class mock_debugging_object(object):
    def __init__(self, name):
        self.name = name
        self.called_attrs = {}
        self.function_calls = {}

    def __getattr__(self, attr_name):
        if attr_name not in self.called_attrs:
            pdb.set_trace()
            self.called_attrs[attr_name] = mock_debugging_object(self.name + "." + attr_name)
        return self.called_attrs[attr_name]

    def __call__(self, *args):
        args_tuple = tuple(args)
        if isinstance(args_tuple, collections.Hashable):
            if args not in self.function_calls:
                pdb.set_trace()
                self.function_calls[args_tuple] = mock_debugging_object(self.name + "(" + (", ".join(args_tuple))  + ")")
            return self.function_calls[args_tuple]
        else:
            pdb.set_trace()
            return mock_debugging_object(self.name + "(" + (", ".join(args_tuple))  + ")")
    
            
            
