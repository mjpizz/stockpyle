import sys

__CAPABLE = True
_MEMCACHED_HOST = "localhost:9876"
_SQLITE_FILENAME = "test_sqlalchemy_multiproc.sqlite"

# check for presence of python-memcached module
if __CAPABLE:
    try:
        import memcache
    except ImportError:
        import sys
        print >> sys.stderr, "WARNING: skipping optional test_sqlalchemy_multiproc, missing module 'python-memcached' (http://pypi.python.org/pypi/python-memcached)"
        __CAPABLE = False

# check for presence of sqlalchemy module
if __CAPABLE:
    try:
        import sqlalchemy
    except ImportError:
        import sys
        print >> sys.stderr, "WARNING: skipping optional test_sqlalchemy_multiproc, missing module 'SQLAlchemy' (http://pypi.python.org/pypi/SQLAlchemy)"
        __CAPABLE = False

# check for presence of pyprocessing module
if __CAPABLE:
    try:
        import processing
    except ImportError:
        import sys
        print >> sys.stderr, "WARNING: skipping optional test_sqlalchemy_multiproc, missing module 'processing' (http://pypi.python.org/pypi/processing)"
        __CAPABLE = False

# check for memcache daemon running on the system
if __CAPABLE:
    import memcache
    if not memcache.Client([_MEMCACHED_HOST]).get_stats():
        __CAPABLE = False
        print >> sys.stderr, "WARNING: memcache daemon is not running on '%s', skipping test_sqlalchemy_multiproc.  You should be able to start it with the shell command 'memcached -p 9876'" % _MEMCACHED_HOST

# if we are capable of running the test, do it now
if __CAPABLE:

    from unittest import TestCase
    import os
    import pickle
    from processing import Process
    import memcache
    from sqlalchemy import Column, create_engine
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy.types import Integer, String
    from sqlalchemy.ext.declarative import declarative_base
    from tests.helpers import CountingStoreWrapper
    from stockpyle.stores import SqlAlchemyStore, MemcacheStore, ChainedStore
    

    DeclarativeBase = declarative_base()


    class MultiprocBazbot(DeclarativeBase):

        __tablename__ = "multiproc_bazbots"

        zap = Column(Integer, primary_key=True)
        foo = Column(Integer)
        bar = Column(Integer)
        bleh = Column(String, default="bleh")

        __stockpyle_keys__ = [("foo", "bar"), ("bar", "zap"), "zap"]

        def __init__(self, foo, bar, zap):
            self.foo = foo
            self.bar = bar
            self.zap = zap

        def __eq__(self, other):
            return other and (other.foo, other.bar == self.foo, self.bar)


    class SqlAlchemyMultiprocTestCase(TestCase):
        
        def setUp(self):
        
            # setup db file
            memcache.Client([_MEMCACHED_HOST]).flush_all()
            if os.path.exists(_SQLITE_FILENAME):
                os.remove(_SQLITE_FILENAME)
            DeclarativeBase.metadata.create_all(bind=create_engine("sqlite:///%s" % _SQLITE_FILENAME))
            
        def tearDown(self):
            
            os.remove(_SQLITE_FILENAME)
            memcache.Client([_MEMCACHED_HOST]).flush_all()
        
        def test_possible_to_share_sqlalchemy_objects_across_process_boundaries_with_memcache(self):
            
            # write to the memcache in another process
            def write_to_cache():
                # create storage for subprocess
                mc = MemcacheStore(servers=[_MEMCACHED_HOST])
                sa = SqlAlchemyStore(uri="sqlite:///%s" % _SQLITE_FILENAME)
                ch = ChainedStore([mc, sa])
            
                # store a MultiprocBazbot object for retrieval in the main process
                bb = MultiprocBazbot(1, 2, 999)
                ch.put(bb)
        
            p = Process(target=write_to_cache)
            p.start()
            p.join()
        
            # create storage in the main process
            mc = MemcacheStore(servers=[_MEMCACHED_HOST])
            sa = SqlAlchemyStore(uri="sqlite:///%s" % _SQLITE_FILENAME)
            ch = ChainedStore([mc, sa])
        
            # FIXME: these unit tests should be valid, but for some reason running the Shove unit tests beforehand interacts with this
            # # accessing the MemcacheStore directly will not work
            # # since the ChainedStore is the only thing that can
            # # conceptually link it to the SqlAlchemyStore
            # bb_mc = mc.get(MultiprocBazbot, {"zap": 999})
            # self.assert_(isinstance(bb_mc, MultiprocBazbot))
            # self.assertRaises(Exception, lambda: bb_mc.zap)
            # self.assertRaises(Exception, lambda: bb_mc.foo)
            # self.assertRaises(Exception, lambda: bb_mc.bar)
            # self.assertRaises(Exception, lambda: bb_mc.bleh)
        
            # accessing the ChainedStore will work since it allows
            # the SqlAlchemyStore to execute its merge callbacks
            bb = ch.get(MultiprocBazbot, {"zap": 999})
            self.assert_(bb)
            self.assert_(isinstance(bb, MultiprocBazbot))
            self.assertEqual(bb.zap, 999)
            self.assertEqual(bb.foo, 1)
            self.assertEqual(bb.bar, 2)
            self.assertEqual(bb.bleh, "bleh")
            