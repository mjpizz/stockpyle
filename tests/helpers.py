from collections import defaultdict


class CountingStoreWrapper(object):
    
    counts = property(lambda self: self.__counts)
    
    def __init__(self, store):
        self.__store = store
        self.__counts = defaultdict(lambda: 0)
    
    def __getattr__(self, name):
        self.__counts[name] += 1
        return getattr(self.__store, name)
