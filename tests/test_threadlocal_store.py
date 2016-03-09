from unittest import TestCase
import threading
from tests.fixture_store import StoreFixture, ExpiringStoreFixture
from stockpyle._threadlocal import ThreadLocalStore


class Foo(object):
    
    __stockpyle_keys__ = ["key"]
    
    key = property(lambda self: self.__key)
    
    def __init__(self, key):
        self.__key = key


class ThreadLocalStoreTestCase(StoreFixture, ExpiringStoreFixture, TestCase):
    
    store = property(lambda self: self.__store)
    
    def setUp(self):
        self.__store = ThreadLocalStore(lifetime_cb=self.lifetime_cb)
    
    def test_storage_only_exists_per_thread(self):
        store = ThreadLocalStore()
        this = self

        def first_cb():
            obj = Foo(123)
            store.put(obj)
            obj_r = store.get(Foo, {"key": 123})
            this.assert_(obj_r)

        def second_cb():
            obj = store.get(Foo, {"key": 123})
            this.assertEqual(obj, None)

        first_thr = threading.Thread(target=first_cb)
        second_thr = threading.Thread(target=second_cb)

        first_thr.start()
        first_thr.join()
        second_thr.start()
        second_thr.join()
