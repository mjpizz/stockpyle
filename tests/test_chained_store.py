from unittest import TestCase
from time import sleep
from collections import defaultdict
from tests.helpers import CountingStoreWrapper
from tests.fixture_store import StoreFixture, ExpiringStoreFixture
from tests.mocks import MockMemcacheClient
from stockpyle._chained import ChainedStore
from stockpyle._procmem import ProcessMemoryStore
from stockpyle._memcache import MemcacheStore


class Foobar(object):
    
    __stockpyle_keys__ = [("foo", "bar"), ("bar", "zap"), "zap"]
    
    def __init__(self, foo, bar, zap):
        self.foo = foo
        self.bar = bar
        self.zap = zap
    
    def __eq__(self, other):
        return other and (other.foo, other.bar == self.foo, self.bar)


class ChainedStoreWithLocalAndMemcacheTestCase(StoreFixture, ExpiringStoreFixture, TestCase):
    
    store = property(lambda self: self.__store)
    
    def setUp(self):
        local = ProcessMemoryStore(lifetime_cb=self.lifetime_cb)
        mc = MemcacheStore(client=MockMemcacheClient(), lifetime_cb=self.lifetime_cb)
        self.__store = ChainedStore([local, mc])
    
    def test_cannot_instantiate_with_no_stores(self):
        self.assertRaises(ValueError, lambda: ChainedStore())
        self.assertRaises(ValueError, lambda: ChainedStore([]))


class ChainedStoreWriteThroughTestCase(TestCase):
    
    def local_lifetime_cb(self, obj):
        if hasattr(obj.__class__, "__stockpyle_unittest_local_lifetime__"):
            return obj.__class__.__stockpyle_unittest_local_lifetime__
        else:
            return None
    
    def mc_lifetime_cb(self, obj):
        if hasattr(obj.__class__, "__stockpyle_unittest_mc_lifetime__"):
            return obj.__class__.__stockpyle_unittest_mc_lifetime__
        else:
            return None
    
    store = property(lambda self: self.__store)
    
    def setUp(self):
        self.__local = CountingStoreWrapper(ProcessMemoryStore(lifetime_cb=self.local_lifetime_cb))
        self.__mc = CountingStoreWrapper(MemcacheStore(client=MockMemcacheClient(), lifetime_cb=self.mc_lifetime_cb))
        self.__store = ChainedStore([self.__local, self.__mc])
    
    def test_after_writethrough_gets_from_only_local(self):
        obj = Foobar(1,2,3)
        
        self.__store.put(obj)
        
        obj_r = self.__store.get(Foobar, {"foo": 1, "bar": 2})
        self.assertEqual(obj_r, obj)
        
        self.assertEqual(self.__local.counts["get"], 1)
        self.assertEqual(self.__mc.counts["get"], 0)
        
    def test_can_expire_earlier_in_certain_caches(self):
        
        # lasts 1 second longer in memcached
        Foobar.__stockpyle_unittest_local_lifetime__ = 1
        Foobar.__stockpyle_unittest_mc_lifetime__ = 2
        
        try:
        
            obj = Foobar(1,2,3)
        
            self.__store.put(obj)
        
            obj_r = self.__store.get(Foobar, {"foo": 1, "bar": 2})
            self.assertEqual(obj_r, obj)
        
            self.assertEqual(self.__local.counts["get"], 1)
            self.assertEqual(self.__mc.counts["get"], 0)
        
            # now wait for the local cache to expire
            sleep(1)
        
            obj_r = self.__store.get(Foobar, {"foo": 1, "bar": 2})
            self.assertEqual(obj_r, obj)
        
            self.assertEqual(self.__local.counts["get"], 2)
            self.assertEqual(self.__mc.counts["get"], 1)
        
            # finally wait for all caches to expire
            sleep(2)
        
            obj_r = self.__store.get(Foobar, {"foo": 1, "bar": 2})
            self.assertEqual(obj_r, None, "object should be completely gone now")
        
            self.assertEqual(self.__local.counts["get"], 3)
            self.assertEqual(self.__mc.counts["get"], 2)
        
        finally:
            Foobar.__stockpyle_unittest_local_lifetime__ = None
            Foobar.__stockpyle_unittest_mc_lifetime__ = None

