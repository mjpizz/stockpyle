from time import sleep
from datetime import datetime, timedelta
from sqlalchemy import engine_from_config, Column
from sqlalchemy.types import Integer, String
from sqlalchemy.ext.declarative import declarative_base


_DUMMY_EXPIRE_TIME = 1


DeclarativeBase = declarative_base()


class Foobar(DeclarativeBase):
    
    __tablename__ = "foobars"
    
    zap = Column(Integer, primary_key=True)
    foo = Column(Integer)
    bar = Column(Integer)
    
    __stockpyle_keys__ = [("foo", "bar"), ("bar", "zap"), "zap"]
    
    def __init__(self, foo, bar, zap):
        self.foo = foo
        self.bar = bar
        self.zap = zap
    
    def __eq__(self, other):
        return other and (other.foo, other.bar == self.foo, self.bar)


class StoreFixture(object):
    
    def _raise_not_implemented(self):
        raise NotImplementedError("all StoreFixtures must implement the 'store' property")
    
    store = property(_raise_not_implemented)
    
    def test_can_store_objects(self):
        obj = Foobar(1,2,3)
        try:
            self.store.put(obj)
        except Exception, e:
            self.fail("should be able to put objects (%s)" % str(e))
    
    def test_can_store_and_retrieve_by_key_foo_and_bar(self):
        obj = Foobar(1,2,3)
        self.store.put(obj)
        obj_r = self.store.get(Foobar, {"foo": 1, "bar": 2})
        self.assertEqual(obj_r, obj)
    
    def test_can_store_and_retrieve_by_key_bar_and_zap(self):
        obj = Foobar(1,2,3)
        self.store.put(obj)
        obj_r = self.store.get(Foobar, {"bar": 2, "zap": 3})
        self.assertEqual(obj_r, obj)
    
    def test_can_store_and_retrieve_by_key_zap(self):
        obj = Foobar(1,2,3)
        self.store.put(obj)
        obj_r = self.store.get(Foobar, {"zap": 3})
        self.assertEqual(obj_r, obj)
    
    def test_can_store_and_delete(self):
        obj = Foobar(1,2,3)
        self.store.put(obj)

        obj_r = self.store.get(Foobar, {"zap": 3})
        self.assertEqual(obj_r, obj)

        self.store.delete(obj)
        obj_r = self.store.get(Foobar, {"zap": 3})
        self.assertEqual(obj_r, None)
        obj_r = self.store.get(Foobar, {"foo": 1, "bar": 2})
        self.assertEqual(obj_r, None)
        obj_r = self.store.get(Foobar, {"bar": 2, "zap": 3})
        self.assertEqual(obj_r, None)
    
    def test_can_store_multiple_objects_and_retrieve_in_batch(self):
        
        obj1 = Foobar(1,2,3)
        obj2 = Foobar(4,5,6)
        
        self.store.put(obj1)
        self.store.put(obj2)
        
        obj1_r, obj2_r = self.store.batch_get(Foobar, [
            {"foo": 1, "bar": 2}, #obj1
            {"foo": 4, "bar": 5}, #obj2
            ])
        
        self.assertEqual(obj1_r, obj1)
        self.assertEqual(obj2_r, obj2)
        
        obj1_r, obj2_r = self.store.batch_get(Foobar, [
            {"bar": 2, "zap": 3}, #obj1
            {"bar": 5, "zap": 6}, #obj2
            ])
        
        self.assertEqual(obj1_r, obj1)
        self.assertEqual(obj2_r, obj2)
        
    def test_can_do_batch_put(self):
        
        obj1 = Foobar(1,2,3)
        obj2 = Foobar(4,5,6)
        
        self.store.batch_put([obj1, obj2])
        
        obj1_r, obj2_r = self.store.batch_get(Foobar, [
            {"foo": 1, "bar": 2}, #obj1
            {"foo": 4, "bar": 5}, #obj2
            ])
        
        self.assertEqual(obj1_r, obj1)
        self.assertEqual(obj2_r, obj2)
        
    def test_can_do_batch_delete_on_original_objects(self):
        
        obj1 = Foobar(1,2,3)
        obj2 = Foobar(4,5,6)
        
        self.store.put(obj1)
        self.store.put(obj2)
        
        obj1_r, obj2_r = self.store.batch_get(Foobar, [
            {"foo": 1, "bar": 2}, #obj1
            {"foo": 4, "bar": 5}, #obj2
            ])
        
        self.assertEqual(obj1_r, obj1)
        self.assertEqual(obj2_r, obj2)
        
        # now delete them
        self.store.batch_delete([obj1, obj2])
        
        obj1_r, obj2_r = self.store.batch_get(Foobar, [
            {"foo": 1, "bar": 2}, #obj1
            {"foo": 4, "bar": 5}, #obj2
            ])
        
        self.assertEqual(obj1_r, None)
        self.assertEqual(obj2_r, None)
        
    def test_can_do_batch_delete_on_retrieved_objects(self):
        
        obj1 = Foobar(1,2,3)
        obj2 = Foobar(4,5,6)
        
        self.store.put(obj1)
        self.store.put(obj2)
        
        obj1_r, obj2_r = self.store.batch_get(Foobar, [
            {"foo": 1, "bar": 2}, #obj1
            {"foo": 4, "bar": 5}, #obj2
            ])
        
        self.assertEqual(obj1_r, obj1)
        self.assertEqual(obj2_r, obj2)
        
        # now delete them
        self.store.batch_delete([obj1_r, obj2_r])
        
        obj1_r, obj2_r = self.store.batch_get(Foobar, [
            {"foo": 1, "bar": 2}, #obj1
            {"foo": 4, "bar": 5}, #obj2
            ])
        
        self.assertEqual(obj1_r, None)
        self.assertEqual(obj2_r, None)
    
    def test_can_close_stockpyle_and_other_methods_lazily_reopen(self):
        
        obj = Foobar(1,2,3)
        self.store.put(obj)
        self.store.release()
        
        obj_r = self.store.get(Foobar, {"foo": 1, "bar": 2})
        
        self.assertEqual(obj_r.foo, 1)
        self.assertEqual(obj_r.bar, 2)
        self.assertEqual(obj_r.zap, 3)
    

class ExpiringStoreFixture(object):
    
    def lifetime_cb(self, obj):
        if hasattr(obj.__class__, "__stockpyle_unittest_lifetime__"):
            return obj.__class__.__stockpyle_unittest_lifetime__
        else:
            return None

    def test_can_store_and_expire_later(self):
        
        Foobar.__stockpyle_unittest_lifetime__ = _DUMMY_EXPIRE_TIME
        try:

            obj = Foobar(1,2,3)
            self.store.put(obj)
        
            obj_r = self.store.get(Foobar, {"zap": 3})
            self.assertEqual(obj, obj_r)
        
            # wait for expiration and check again
            sleep(_DUMMY_EXPIRE_TIME)
        
            obj_r = self.store.get(Foobar, {"zap": 3})
            self.assertEqual(obj_r, None)

        finally:
            Foobar.__stockpyle_unittest_lifetime__ = None
    
    def test_can_store_and_expire_later_with_datetime(self):
        
        d = datetime.today() + timedelta(seconds=_DUMMY_EXPIRE_TIME)
        Foobar.__stockpyle_unittest_lifetime__ = d
        
        try:

            obj = Foobar(1,2,3)
            self.store.put(obj)
        
            obj_r = self.store.get(Foobar, {"zap": 3})
            self.assertEqual(obj, obj_r)
        
            # wait for expiration and check again
            sleep(_DUMMY_EXPIRE_TIME)
        
            obj_r = self.store.get(Foobar, {"zap": 3})
            self.assertEqual(obj_r, None)

        finally:
            Foobar.__stockpyle_unittest_lifetime__ = None
    
    def test_can_store_and_expire_later_with_timedelta(self):
        
        td = timedelta(seconds=_DUMMY_EXPIRE_TIME)
        Foobar.__stockpyle_unittest_lifetime__ = td
        
        try:
            obj = Foobar(1,2,3)
            self.store.put(obj)
        
            obj_r = self.store.get(Foobar, {"zap": 3})
            self.assertEqual(obj, obj_r)
        
            # wait for expiration and check again
            sleep(_DUMMY_EXPIRE_TIME)
        
            obj_r = self.store.get(Foobar, {"zap": 3})
            self.assertEqual(obj_r, None)

        finally:
            Foobar.__stockpyle_unittest_lifetime__ = None
