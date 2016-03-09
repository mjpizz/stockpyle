try:
    import shove
    __HAVE_SHOVE = True
except ImportError:
    import sys
    print >> sys.stderr, "WARNING: skipping optional Shove tests, missing module 'shove' (http://pypi.python.org/pypi/shove)"
    __HAVE_SHOVE = False


if __HAVE_SHOVE:

    from unittest import TestCase
    from tests.fixture_store import StoreFixture, ExpiringStoreFixture
    from stockpyle._shove import ShoveStore


    class ShoveStoreTestCase(StoreFixture, ExpiringStoreFixture, TestCase):
    
        store = property(lambda self: self.__store)
    
        def setUp(self):
            from shove import Shove
            self.__inmemory_shove = Shove("simple://")
            self.__store = ShoveStore(shove=self.__inmemory_shove, lifetime_cb=self.lifetime_cb)
    
    
    class ShoveStoreViaUriTestCase(StoreFixture, ExpiringStoreFixture, TestCase):
    
        store = property(lambda self: self.__store)
    
        def setUp(self):
            self.__store = ShoveStore(shoveuri="simple://", lifetime_cb=self.lifetime_cb)
    
    
    class ShoveStoreIntantiationTestCase(TestCase):
        
        def test_requires_shove_or_shove_uri(self):
            
            self.assertRaises(ValueError, lambda: ShoveStore())
        
        def test_cannot_provide_shove_and_shove_uri_at_same_time(self):
            
            from shove import Shove
            s = Shove()
            self.assertRaises(ValueError, lambda: ShoveStore(shove=s, shoveuri="simple://"))
            