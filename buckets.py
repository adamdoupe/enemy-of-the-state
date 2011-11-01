class Buckets(dict):
    """
        Sort the added values into buckets based on the given hash_function.
    """

    def __init__(self, hash_function=hash):
        self.hash_function = hash_function

    def __missing__(self, k):
        v = []
        self[k] = v
        return v

    def add(self, obj, hash_function=None):
        if hash_function is None:
            hash_function = self.hash_function
        v = self[hash_function(obj)]
        v.append(obj)
        return v


