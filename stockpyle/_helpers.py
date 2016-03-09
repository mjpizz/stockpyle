import md5

def _generate_verbose_key(prefix, klass, properties):
    return "%s:%s.%s(%s)" % (prefix, klass.__module__, klass.__name__, properties)

def _generate_terse_key(prefix, klass, properties):
    compressed_hash = md5.new("%s.%s(%s)" % (klass.__module__, klass.__name__, properties)).hexdigest()
    return "%s:%s(%s)" % (prefix, klass.__name__, compressed_hash)


class KeyValueHelper(object):
    """Internal helper object that can generate unique keys for a store that
    stores objects in key/value pairs.  Given a class/instance and a property
    dictionary, this helper creates a unique lookup key (e.g. 'mymodule.MyClass(foo=abc;bar=123)')"""
    
    def __init__(self, verbose=False, polymorphic=False, prefix="stockpyle"):
        self.__stockpyle_bases_lookup = {}
        self.__polymorphic = polymorphic
        self.__prefix = prefix
        # TODO: create cython callbacks to speed up this operation
        if verbose:
            self.__generate_key_cb = _generate_verbose_key
        else:
            self.__generate_key_cb = _generate_terse_key
    
    def generate_lookup_key(self, target_klass, property_dict):
        return self.__generate_key_cb(self.__prefix, target_klass, sorted([kv for kv in property_dict.iteritems()]))
        
    def generate_all_lookup_keys(self, obj):

        lookup_keys = []
        klasses = [obj.__class__]
        if self.__polymorphic:
            klasses += self.__get_stockpyle_base_classes(obj.__class__)
            
        for klass in klasses:
            for stockpyle_key in klass.__stockpyle_keys__:
                if isinstance(stockpyle_key, basestring):
                    property_list = [(stockpyle_key, getattr(obj, stockpyle_key))]
                else:
                    property_list = [(pn, getattr(obj, pn)) for pn in sorted(stockpyle_key)]
                lookup_keys.append(self.__generate_key_cb(self.__prefix, klass, property_list))
        return lookup_keys
    
    def __get_stockpyle_base_classes(self, klass):
        """returns an ordered list of stockpyle-managed base classes by recursing
        up the inheritance tree of the given class and collecting any base classes
        that have __stockpyle_keys__ defined"""
        if klass not in self.__stockpyle_bases_lookup:
            
            # we haven't calculated the stockpyle bases for this class yet
            # calculate them
            bases = []
            def collect(current_klass):
                for b in current_klass.__bases__:
                    if hasattr(b, "__stockpyle_keys__"):
                        bases.append(b)
                    collect(b)
            collect(klass)
            
            # and then save for for faster lookup later
            self.__stockpyle_bases_lookup[klass] = bases
            
        # return those bases
        return self.__stockpyle_bases_lookup[klass]


# if __name__ == "__main__":
#     
#     # performance testing
#     import time
#     import cProfile
#     # import psyco
#     # psyco.full()
#     
#     
#     class Foo(object):
#         __stockpyle_keys__ = [("foo", "bar")]
#         foo = 1
#         bar = "x"
#     
#     
#     kvh_terse = KeyValueHelper()
#     kvh_verbose = KeyValueHelper(verbose=True)
#     
#     def perform_verbose_keygen():
#         start = time.time()
#         for i in range(0, 50000):
#             kvh_verbose.generate_lookup_key(Foo, {"foo": 1, "bar": "x"})
#         delta = time.time() - start
#         return delta
#     
#     def perform_terse_keygen():
#         start = time.time()
#         for i in range(0, 50000):
#             kvh_terse.generate_lookup_key(Foo, {"foo": 1, "bar": "x"})
#         delta = time.time() - start
#         return delta
#     
#     def perform_verbose_objkeygen():
#         start = time.time()
#         obj = Foo()
#         for i in range(0, 50000):
#             kvh_verbose.generate_all_lookup_keys(obj)
#         delta = time.time() - start
#         return delta
#     
#     def perform_terse_objkeygen():
#         start = time.time()
#         obj = Foo()
#         for i in range(0, 50000):
#             kvh_terse.generate_all_lookup_keys(obj)
#         delta = time.time() - start
#         return delta
#         
#     
#     print ">>> verbose keygen"
#     print perform_verbose_keygen()
#     print perform_verbose_keygen()
#     print perform_verbose_keygen()
#     print ">>> terse keygen"
#     print perform_terse_keygen()
#     print perform_terse_keygen()
#     print perform_terse_keygen()
#     print ">>> verbose objkeygen"
#     print perform_verbose_objkeygen()
#     print perform_verbose_objkeygen()
#     print perform_verbose_objkeygen()
#     print ">>> terse objkeygen"
#     print perform_terse_objkeygen()
#     print perform_terse_objkeygen()
#     print perform_terse_objkeygen()
#     print
#     print
#     print ">>> verbose keygen"
#     cProfile.run("perform_verbose_keygen()")
#     print ">>> terse keygen"
#     cProfile.run("perform_terse_keygen()")
#     print ">>> verbose objkeygen"
#     cProfile.run("perform_verbose_objkeygen()")
#     print ">>> terse objkeygen"
#     cProfile.run("perform_terse_objkeygen()")
#     