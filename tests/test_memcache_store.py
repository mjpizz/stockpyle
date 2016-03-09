from unittest import TestCase
from datetime import datetime, timedelta
from tests.fixture_store import StoreFixture, ExpiringStoreFixture, Foobar
from tests.mocks import MockMemcacheClient
from stockpyle._memcache import MemcacheStore


class MemcacheStoreTestCase(StoreFixture, ExpiringStoreFixture, TestCase):
    
    store = property(lambda self: self.__mc)
    
    def setUp(self):
        self.__mc = MemcacheStore(client=MockMemcacheClient(), lifetime_cb=self.lifetime_cb)
    
    def test_must_specify_client_or_servers(self):
        self.assertRaises(ValueError, lambda: MemcacheStore())
        self.assertRaises(ValueError, lambda: MemcacheStore(client=MockMemcacheClient(), servers=["localhost:8080"]))
        try:
            MemcacheStore(servers=["localhost:8080"])
        except Exception, e:
            self.fail("should be able to create client against server list (%s)" % str(e))
    
    def test_integer_lifetime_must_be_within_memcache_api_limitation(self):
        max_int_delta = 60*60*24*30
        def lifetime_cb(obj):
            # return the 'foo' attribute as a lifetime
            return obj.foo
        mc = MemcacheStore(client=MockMemcacheClient(), lifetime_cb=lifetime_cb)
        obj1 = Foobar(max_int_delta, 2, 3)
        obj2 = Foobar(max_int_delta+1, 2, 3)
        obj3 = Foobar(max_int_delta-1, 2, 3)
        self.assertRaises(ValueError, lambda: mc.put(obj1))
        self.assertRaises(ValueError, lambda: mc.put(obj2))
        try:
            mc.put(obj3)
        except ValueError, e:
            self.fail("obj3 has a lifetime just within the API limit, this should have succeeded")
        
    def test_lifetime_must_be_datetime_timedelta_or_integer(self):
        def lifetime_cb(obj):
            # return the 'foo' attribute as a lifetime
            return obj.foo
        mc = MemcacheStore(client=MockMemcacheClient(), lifetime_cb=lifetime_cb)
        obj1 = Foobar(1.2, 2, 3)
        obj2 = Foobar('blah', 2, 3)
        obj3 = Foobar(555, 2, 3)
        obj4 = Foobar(timedelta(seconds=555), 2, 3)
        obj5 = Foobar(datetime.today(), 2, 3)
        self.assertRaises(ValueError, lambda: mc.put(obj1))
        self.assertRaises(ValueError, lambda: mc.put(obj2))
        try:
            mc.put(obj3)
        except ValueError, e:
            self.fail("obj3 has a lifetime of an integer, it should be just fine to put")
        try:
            mc.put(obj4)
        except ValueError, e:
            self.fail("obj4 has a lifetime of a timedelta, it should be just fine to put")
        try:
            mc.put(obj5)
        except ValueError, e:
            self.fail("obj4 has a lifetime of a datetime, it should be just fine to put")