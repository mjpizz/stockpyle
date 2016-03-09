from unittest import TestCase
import os
import sys
from time import time
from datetime import datetime, timedelta

_MEMCACHED_HOST = "localhost:9876"
_PERF_SQLITE_FILENAME = "stockpyle.performance.sqlite"
_SINGLE_LIST_LEN = 500
_BATCH_LIST_LEN = 10
_BATCH_LEN = 50
_PERFORMANCE_FILE = None
_DUMMY_TIME = datetime.today() + timedelta(days=10)

_HAS_SHOVE = False
_HAS_SQLALCHEMY = False
_HAS_MEMCACHED = False

try:
    import shove
    _HAS_SHOVE = True
except ImportError:
    import sys
    print >> sys.stderr, "WARNING: skipping optional Shove performance tests, missing module 'shove' (http://pypi.python.org/pypi/shove)"
    _HAS_SHOVE = False

try:
    import sqlalchemy
    _HAS_SQLALCHEMY = True
except ImportError:
    import sys
    print >> sys.stderr, "WARNING: skipping optional SQLAlchemy performance tests, missing module 'SQLAlchemy' (http://pypi.python.org/pypi/SQLAlchemy)"
    _HAS_SQLALCHEMY = False

try:
    import memcache
    if memcache.Client([_MEMCACHED_HOST]).get_stats():
        _HAS_MEMCACHED = True
    else:
        import sys
        print >> sys.stderr, "WARNING: skipping memcache performance tests (you don't have the daemon running at %s)" % _MEMCACHED_HOST
        _HAS_MEMCACHED = False
except ImportError:
    import sys
    print >> sys.stderr, "WARNING: skipping optional memcache tests, missing module 'python-memcached' (http://pypi.python.org/pypi/python-memcached)"
    _HAS_MEMCACHED = False


if _HAS_SQLALCHEMY:

    from sqlalchemy import create_engine, Column
    from sqlalchemy.types import Integer, String
    from sqlalchemy.ext.declarative import declarative_base
    
    ObjectBase = declarative_base()
    
    
    class BazbotForSA(declarative_base()):
        
        __tablename__ = "performance_bazbots"
        
        zap = Column(Integer, primary_key=True)
        foo = Column(Integer)
        bar = Column(Integer)
        
        __stockpyle_keys__ = [("bar", "zap"), "zap"]
    
        def __init__(self, foo, bar, zap):
            self.foo = foo
            self.bar = bar
            self.zap = zap
    
        def __eq__(self, other):
            return other and (other.foo, other.bar == self.foo, self.bar)



    class FoobarForSA(BazbotForSA):
    
        __stockpyle_keys__ = [("foo", "bar")]



class Bazbot(object):
        
    __stockpyle_keys__ = [("bar", "zap"), "zap"]
    
    def __init__(self, foo, bar, zap):
        self.foo = foo
        self.bar = bar
        self.zap = zap
    
    def __eq__(self, other):
        return other and (other.foo, other.bar == self.foo, self.bar)



class Foobar(Bazbot):
    
    __stockpyle_keys__ = [("foo", "bar")]


def _lazy_open_performance_file():
    global _PERFORMANCE_FILE
    if not _PERFORMANCE_FILE:
        path = "performance.csv"
        if os.path.exists(path):
            os.remove(path)
        _PERFORMANCE_FILE = open(path, "w+")
        _PERFORMANCE_FILE.write("testcase, operation, time (seconds)\n")
    return _PERFORMANCE_FILE


class PerformanceTestCaseMixin(object):
    
    def __init__(self, *args, **kwargs):
        super(PerformanceTestCaseMixin, self).__init__(*args, **kwargs)
        self.__pkey = 0
        self.bazbot_klass = Bazbot
        self.foobar_klass = Foobar
    
    def __create_objects(self, num):
        objlist = []
        for i in range(0, num):
            obj = Foobar(1,2,self.__pkey)
            objlist.append(obj)
            self.__pkey += 1
        return objlist
    
    def test_put_speed(self):
        objs = self.__create_objects(_SINGLE_LIST_LEN)
        def lots_of_puts():
            for o in objs:
                self.store.put(o)
        self.__write_timing_information("put", lots_of_puts)
    
    def test_batch_put_speed(self):
        batches = [self.__create_objects(_BATCH_LIST_LEN) for i in range(_BATCH_LEN)]
        def lots_of_batch_puts():
            for objs in batches:
                self.store.batch_put(objs)
        self.__write_timing_information("batch_put", lots_of_batch_puts)
    
    def test_delete_speed(self):
        objs = self.__create_objects(_SINGLE_LIST_LEN)
        for o in objs:
            self.store.put(o)
        def lots_of_deletes():
            for o in objs:
                self.store.delete(o)
        self.__write_timing_information("delete", lots_of_deletes)
    
    def test_batch_delete_speed(self):
        batches = [self.__create_objects(_BATCH_LIST_LEN) for i in range(_BATCH_LEN)]
        for objs in batches:
            self.store.batch_put(objs)
        def lots_of_batch_deletes():
            for objs in batches:
                self.store.batch_delete(objs)
        self.__write_timing_information("batch_delete", lots_of_batch_deletes)
    
    def test_get_speed(self):
        # pre-store
        objs = self.__create_objects(_SINGLE_LIST_LEN)
        for o in objs:
            self.store.put(o)
        
        # define gets
        getkeys = [{"zap": o.zap} for o in objs]
        def lots_of_gets():
            for getkey in getkeys:
                self.store.get(Foobar, getkey)
        self.__write_timing_information("get", lots_of_gets)
    
    def test_batch_get_speed(self):
        batches = [self.__create_objects(_BATCH_LIST_LEN) for i in range(_BATCH_LEN)]
        for objs in batches:
            self.store.batch_put(objs)
        batch_getkeys = [[{"zap": o.zap} for o in objs] for objs in batches]
        def lots_of_batch_gets():
            for getkeys in batch_getkeys:
                self.store.batch_get(Foobar, getkeys)
        self.__write_timing_information("batch_get", lots_of_batch_gets)
    
    def __write_timing_information(self, op, callback):
        start = time()
        try:
            callback()
        finally:
            delta = time() - start
            fd = _lazy_open_performance_file()
            message = "%s, %s, %s\n" % (self.__class__.__name__, op, delta)
            # sys.stderr.write(message)
            fd.write(message)
            fd.flush()


########################################################################

class ProcessMemoryStoreTestCase(PerformanceTestCaseMixin, TestCase):
    
    def setUp(self):
        from stockpyle.stores import ProcessMemoryStore
        self.store = ProcessMemoryStore()


class ProcessMemoryWithPolymorphismStoreTestCase(PerformanceTestCaseMixin, TestCase):
    
    def setUp(self):
        from stockpyle.stores import ProcessMemoryStore
        self.store = ProcessMemoryStore(polymorphic=True)


class ProcessMemoryStoreWithLifetimeCallbackTestCase(PerformanceTestCaseMixin, TestCase):
    
    def setUp(self):
        from stockpyle.stores import ProcessMemoryStore
        self.store = ProcessMemoryStore(lifetime_cb=lambda obj: _DUMMY_TIME)


########################################################################

class ThreadLocalStoreTestCase(PerformanceTestCaseMixin, TestCase):
    
    def setUp(self):
        from stockpyle.stores import ThreadLocalStore
        self.store = ThreadLocalStore()


class ThreadLocalWithPolymorphismStoreTestCase(PerformanceTestCaseMixin, TestCase):
    
    def setUp(self):
        from stockpyle.stores import ThreadLocalStore
        self.store = ThreadLocalStore(polymorphic=True)


class ThreadLocalStoreWithLifetimeCallbackTestCase(PerformanceTestCaseMixin, TestCase):
    
    def setUp(self):
        from stockpyle.stores import ThreadLocalStore
        self.store = ThreadLocalStore(lifetime_cb=lambda obj: _DUMMY_TIME)


########################################################################

if _HAS_MEMCACHED:


    class MemcacheStoreTestCase(PerformanceTestCaseMixin, TestCase):
    
        def setUp(self):
            from stockpyle.stores import MemcacheStore
            self.store = MemcacheStore(servers=[_MEMCACHED_HOST])


    class ShoveWithPolymorphismStoreTestCase(PerformanceTestCaseMixin, TestCase):
    
        def setUp(self):
            from stockpyle.stores import MemcacheStore
            self.store = MemcacheStore(servers=[_MEMCACHED_HOST], polymorphic=True)


    class MemcacheStoreWithLifetimeCallbackTestCase(PerformanceTestCaseMixin, TestCase):
    
        def setUp(self):
            from stockpyle.stores import MemcacheStore
            self.store = MemcacheStore(servers=[_MEMCACHED_HOST], lifetime_cb=lambda obj: _DUMMY_TIME)


########################################################################

if _HAS_SHOVE:


    class ShoveStoreTestCase(PerformanceTestCaseMixin, TestCase):
    
        def setUp(self):
            from stockpyle.stores import ShoveStore
            self.store = ShoveStore(shoveuri="simple://")


    class ShoveWithPolymorphismStoreTestCase(PerformanceTestCaseMixin, TestCase):
    
        def setUp(self):
            from stockpyle.stores import ShoveStore
            self.store = ShoveStore(shoveuri="simple://", polymorphic=True)


    class ShoveStoreWithLifetimeCallbackTestCase(PerformanceTestCaseMixin, TestCase):
    
        def setUp(self):
            from stockpyle.stores import ShoveStore
            self.store = ShoveStore(shoveuri="simple://", lifetime_cb=lambda obj: _DUMMY_TIME)


########################################################################

if _HAS_SQLALCHEMY:


    class SqlAlchemyWithSqliteStoreTestCase(PerformanceTestCaseMixin, TestCase):
    
        def setUp(self):
            # setup db file
            if os.path.exists(_PERF_SQLITE_FILENAME):
                os.remove(_PERF_SQLITE_FILENAME)
            ObjectBase.metadata.create_all(bind=create_engine("sqlite:///%s" % _PERF_SQLITE_FILENAME))
            
            # set up store
            from stockpyle.stores import SqlAlchemyStore
            engine = create_engine("sqlite:///%s" % _PERF_SQLITE_FILENAME)
            self.store = SqlAlchemyStore(engine=engine)
          
            # override classes to use SA-backed classes
            self.bazbot_klass = BazbotForSA
            self.foobar_klass = FoobarForSA
        
        def tearDown(self):
            # remove db file
            if os.path.exists(_PERF_SQLITE_FILENAME):
                os.remove(_PERF_SQLITE_FILENAME)
            