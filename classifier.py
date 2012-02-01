from recursive_dict import RecursiveDict

class Classifier(RecursiveDict):

    def __init__(self, featuresextractor):
        self.featuresextractor = featuresextractor
        # leaves should return the number of elements in the list for nleaves
        RecursiveDict.__init__(self, lambda x: 1)

    def add(self, obj):
        featvect = self.featuresextractor(obj)
        # hack to use lambda function instead of def func(x); x.append(obj); return x
        self.setapplypathvalue(featvect, [obj], lambda x: (x.append(obj), x)[1])

    def addall(self, it):
        for i in it:
            self.add(i)

    def is_present(self, obj):
        return self.get_object(obj) is not None

    def get_object(self, obj):
        featvect = self.featuresextractor(obj)
        return self.getpath(featvect).value
