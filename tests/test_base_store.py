from unittest import TestCase
from stockpyle._base import BaseStore


class ProcessMemoryStoreTestCase(TestCase):
    
    def test_must_implement_storage_methods(self):
        
        
        class MyStore(BaseStore):
            pass
        
        
        class Foo(object):
            pass
            
        
        ms = MyStore()
        dummyobj = Foo()
        
        self.assertRaises(NotImplementedError, lambda: ms.put(dummyobj))
        self.assertRaises(NotImplementedError, lambda: ms.batch_put([dummyobj]))
        self.assertRaises(NotImplementedError, lambda: ms.delete(dummyobj))
        self.assertRaises(NotImplementedError, lambda: ms.batch_delete([dummyobj]))
        self.assertRaises(NotImplementedError, lambda: ms.get(Foo, {}))
        self.assertRaises(NotImplementedError, lambda: ms.batch_get(Foo, [{}, {}]))
        self.assertRaises(NotImplementedError, lambda: ms.release())
    