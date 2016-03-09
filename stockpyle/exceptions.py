class NonUniqueKeyError(Exception):
    """raised when a 'get' operation will not return a unique entity"""
    
    klass = property(lambda self: self.__key)
    key = property(lambda self: self.__key)
    
    def __init__(self, klass, key):
        Exception.__init__(self, "the key '%s' does not uniquely reference objects of type %s" % (key, klass))
        self.__klass = klass
        self.__key = key