from unittest import TestCase
from tests.fixture_store import StoreFixture, ExpiringStoreFixture
from stockpyle._procmem import ProcessMemoryStore


class ProcessMemoryStoreTestCase(StoreFixture, ExpiringStoreFixture, TestCase):
    
    store = property(lambda self: self.__store)
    
    def setUp(self):
        self.__store = ProcessMemoryStore(lifetime_cb=self.lifetime_cb)
    