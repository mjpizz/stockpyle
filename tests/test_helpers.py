from unittest import TestCase
from stockpyle._helpers import KeyValueHelper
# try:
#     import processing
#     _HAS_PYPROCESSING = True
# except ImportError:
#     import sys
#     print >> sys.stderr, "WARNING: skipping optional multi-process key generation tests, missing module 'processing' (http://pypi.python.org/pypi/processing)"
#     _HAS_PYPROCESSING = False


class DummyObject(object):
    
    __stockpyle_keys__ = [("foo", "bar")]
    foo = 1
    bar = 2


class DummyObjectSubclass(DummyObject):
    
    __stockpyle_keys__ = ["zap"]
    zap = "xyz"


class DummyObjectSubSubclassWithoutStockpyleKeys(DummyObjectSubclass):
    pass


class DummyObjectSubSubSubclass(DummyObjectSubSubclassWithoutStockpyleKeys):
    
    __stockpyle_keys__ = [("foo", "blarg")]
    blarg = "abc"


class KeyValueHelperMixin(object):
    
    def test_honors_default_prefix(self):

        key = self.kvh.generate_lookup_key(DummyObject, {"xyz": "foo", "abc": 123})
        self.assert_(key.startswith("stockpyle:"))
    
    def test_different_types_with_same_string_value_generate_different_keys(self):
        
        key1 = self.kvh.generate_lookup_key(DummyObject, {"xyz": "foo", "abc": 123})
        key2 = self.kvh.generate_lookup_key(DummyObject, {"xyz": "foo", "abc": "123"})
        self.assert_(key1 != key2)
    
    def test_different_klass_values_with_same_properties_generate_different_keys(self):
        
        key1 = self.kvh.generate_lookup_key(DummyObject, {"xyz": "foo", "abc": 123})
        key2 = self.kvh.generate_lookup_key(DummyObjectSubclass, {"xyz": "foo", "abc": 123})
        self.assert_(key1 != key2)
    
    def test_generates_deterministic_keys(self):
        
        keys = set()
        for i in range(0, 100):
            key = self.kvh.generate_lookup_key(DummyObject, {"xyz": "foo", "abc": 123})
            keys.add(key)
        self.assertEqual(len(keys), 1, "all keys should have been the same")
    
    def test_generates_deterministic_keys_for_objects(self):
        
        keys = set()
        for i in range(0, 100):
            obj = DummyObject()
            newkeys = self.kvh.generate_all_lookup_keys(obj)
            self.assertEqual(len(newkeys), 1)
            keys.add(newkeys[0])
        self.assertEqual(len(keys), 1, "all keys should have been the same (DummyObject only has one key tuple)")
    
    def test_allkeys_generates_lookup_that_can_be_queried_singly(self):
        obj = DummyObject()
        newkeys = self.kvh.generate_all_lookup_keys(obj)
        self.assertEqual(len(newkeys), 1)
        single_key = self.kvh.generate_lookup_key(DummyObject, {"foo": 1, "bar": 2})
        self.assertEqual(newkeys[0], single_key, "keys should match")
    
    # TODO: make this test actually work.  Tried it with the KeyValueHelper using id(string), which should produce different keys per process, but it didn't in fact catch that error
    # if _HAS_PYPROCESSING:
    #     
    #     import processing
    #     
    #     def test_generates_deterministic_keys_across_multiple_processes(self):
    #     
    #         the_q = processing.Queue()
    #         
    #         def make_keys(q):
    #             keys = set()
    #             for i in range(0, 100):
    #                 key = self.kvh.generate_lookup_key(DummyObject, {"xyz": "foo", "abc": 123})
    #                 keys.add(key)
    #             self.assertEqual(len(keys), 1, "all keys should have been the same")
    #             q.put(keys, block=True)
    #         
    #         proc1 = processing.Process(target=make_keys, args=[the_q])
    #         proc2 = processing.Process(target=make_keys, args=[the_q])
    #         proc3 = processing.Process(target=make_keys, args=[the_q])
    #         
    #         proc1.start()
    #         proc2.start()
    #         proc3.start()
    #         
    #         proc1.join()
    #         proc2.join()
    #         proc3.join()
    #         
    #         # do it in the main process for good measure
    #         make_keys(the_q)
    #         
    #         # look at all the items in the queue (should be 4 sets)
    #         all_items = []
    #         while not the_q.empty():
    #             all_items.append(the_q.get())
    #         self.assertEqual(len(all_items), 4, "each process should have produced a key set")
    #         
    #         # make sure all these sets union to only ONE key
    #         all_unique_items = set(list(all_items[0]) + list(all_items[1]) + list(all_items[2]))
    #         self.assertEqual(len(all_unique_items), 1, "all keys should have been the same across processes")
    #         
    #         # cleanup
    #         the_q.close()
    #         the_q.jointhread()


class VerboseKeyValueHelperTestCase(KeyValueHelperMixin, TestCase):
    
    def setUp(self):
        self.kvh = KeyValueHelper(verbose=True)


class TerseKeyValueHelperTestCase(KeyValueHelperMixin, TestCase):
    
    def setUp(self):
        self.kvh = KeyValueHelper(verbose=False)


class VerbosePolymorphicKeyValueHelperTestCase(KeyValueHelperMixin, TestCase):
    
    def setUp(self):
        self.kvh = KeyValueHelper(verbose=True, polymorphic=True)


class TersePolymorphicKeyValueHelperTestCase(KeyValueHelperMixin, TestCase):
    
    def setUp(self):
        self.kvh = KeyValueHelper(verbose=False, polymorphic=True)
    
    def test_generates_deterministic_keys_for_polymorphic_objects(self):
        
        keys = set()
        for i in range(0, 100):
            obj = DummyObjectSubclass()
            newkeys = self.kvh.generate_all_lookup_keys(obj)
            self.assertEqual(len(newkeys), 2, "base keys PLUS subclass keys")
            keys.add(newkeys[0])
            keys.add(newkeys[1])
        self.assertEqual(len(keys), 2, "all keys should have been one of two keys same (DummyObjectSubclass has its own key, plus its base class key)")
        
        # ensure that these are the keys we would use for lookups
        basekey = self.kvh.generate_lookup_key(DummyObject, {"foo": 1, "bar": 2})
        subclasskey = self.kvh.generate_lookup_key(DummyObjectSubclass, {"zap": "xyz"})
        self.assertEqual(set([basekey, subclasskey]), keys)
    
    def test_generates_all_base_class_keys(self):
        obj = DummyObjectSubSubSubclass()
        keys = self.kvh.generate_all_lookup_keys(obj)
        expected_key_substrings = [
            "DummyObject(",
            "DummyObjectSubclass(",
            "DummyObjectSubSubclassWithoutStockpyleKeys(",
            "DummyObjectSubSubSubclass(",
            ]
        self.assertEqual(len(keys), len(expected_key_substrings))
        for expected_substr in expected_key_substrings:
            found = False
            for k in keys:
                if expected_substr in k:
                    found = True
            if not found:
                self.fail("didn't find expected key for '%s'" % expected_substr)
    
        # ensure that these are the keys we would use for lookups
        dummy = self.kvh.generate_lookup_key(DummyObject, {"foo": 1, "bar": 2})
        dummysubclass = self.kvh.generate_lookup_key(DummyObjectSubclass, {"zap": "xyz"})
        dummysubclasswithout = self.kvh.generate_lookup_key(DummyObjectSubSubclassWithoutStockpyleKeys, {"zap": "xyz"})
        dummysubsubsubclass = self.kvh.generate_lookup_key(DummyObjectSubSubSubclass, {"foo": 1, "blarg": "abc"})
        self.assertEqual(set([dummy, dummysubclass, dummysubclasswithout, dummysubsubsubclass]), set(keys))
        