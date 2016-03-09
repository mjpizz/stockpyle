try:
    import sqlalchemy
    __HAVE_SA = True
except ImportError:
    import sys
    print >> sys.stderr, "WARNING: skipping optional SQLAlchemy tests, missing module 'SQLAlchemy' (http://pypi.python.org/pypi/SQLAlchemy)"
    __HAVE_SA = False


if __HAVE_SA:

    from unittest import TestCase
    from sqlalchemy import Column, create_engine
    from sqlalchemy.types import Integer, String
    from sqlalchemy.orm import sessionmaker
    from tests.helpers import CountingStoreWrapper
    from tests.fixture_store import StoreFixture, DeclarativeBase, Foobar
    from stockpyle._chained import ChainedStore
    from stockpyle._procmem import ProcessMemoryStore
    from stockpyle._sqlalchemy import SqlAlchemyStore, StockpyleSessionExtension
    from stockpyle.exceptions import NonUniqueKeyError
    
    
    class Bazbot(DeclarativeBase):

        __tablename__ = "bazbots"
    
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


    class SqlAlchemyStoreTestCase(StoreFixture, TestCase):
    
        store = property(lambda self: self.__store)
    
        def setUp(self):
            self.__engine = create_engine("sqlite:///:memory:")
            self.__store = SqlAlchemyStore(engine=self.__engine)
            DeclarativeBase.metadata.create_all(bind=self.__engine)
        
        def tearDown(self):
            DeclarativeBase.metadata.drop_all(bind=self.__engine)
        
        def test_instantiation_with_session_generates_deprecation_warning(self):
            session = sessionmaker(autoflush=True, bind=self.__engine)()
            self.assertRaises(DeprecationWarning, lambda: SqlAlchemyStore(session=session))
        
        def test_instantiation_with_uri_works(self):
            store = SqlAlchemyStore(uri="sqlite:///:memory:")
        
        def test_instantiation_with_nothing_is_okay_and_requires_objects_to_be_bound_to_engine(self):
            # create an engine-unbound SqlAlchemyStore
            store = SqlAlchemyStore()
            obj = Foobar(1,2,3)
            self.assertRaises(Exception, lambda: store.put(obj))
            DeclarativeBase.metadata.bind = self.__engine
            try:
                # now we should be able to put the object
                store.put(obj)
            finally:
                DeclarativeBase.metadata.bind = None
        
        def test_instantiation_with_connstring_and_engine_raises_error(self):
            engine = create_engine("sqlite:///:memory:")
            self.assertRaises(ValueError, lambda: SqlAlchemyStore(uri="sqlite:///:memory:", engine=engine))
        
        def test_ignores_non_sqlalchemy_mapped_objects(self):
            class NonMappedObj(object):
                __stockpyle_keys__ = ["mykey"]
                mykey = 123
            
            obj = NonMappedObj()
            self.__store.put(obj)
            
            self.__store.batch_put([obj])

            obj_r = self.__store.get(NonMappedObj, {"mykey": 123})
            self.assertEqual(obj_r, None)

            obj_list = self.__store.batch_get(NonMappedObj, [{"mykey": 123}])
            self.assertEqual(obj_list, [None])
            
            self.__store.batch_delete([obj])
        
        def test_external_session_must_merge_objects_retrieved_from_stockpyle(self):

            obj = Foobar(1,2,3)
            self.store.put(obj)
            
            # create an external session
            session = sessionmaker(autoflush=True, bind=self.__engine)()
            
            # change the object, we're going to save it to SA directly
            obj.foo = 999
        
            # try to add to SA session, should fail
            self.assertRaises(Exception, lambda: session.add(obj))
            
            # merge instead
            session.merge(obj)
            session.commit()
            
            # now that should be in SA with the new 999 value for obj.foo
            obj_r = session.query(Foobar).first()
            self.assertEqual(obj_r, obj)
            self.assertEqual(obj_r.foo, 999)

        def test_can_delete_retrieved_object_from_external_session(self):
        
            obj = Foobar(1,2,3)
            self.store.put(obj)
        
            # get using a sqlalchemy session
            session = sessionmaker(autoflush=True, bind=self.__engine)()
            obj_r = session.query(Foobar).first()
            self.assertEqual(obj_r, obj)
        
            # now delete the obj through the store
            self.store.delete(obj_r)
        
            # store should say empty
            obj_r = self.store.get(Foobar, {"foo": 1, "bar": 2})
            self.assertEqual(obj_r, None)
        
            # raw db request should say empty
            obj_r = session.query(Foobar).first()
            self.assertEqual(obj_r, None)
        
        def test_can_do_batch_delete_on_retrieved_objects_from_external_session(self):
        
            obj1 = Foobar(1,2,3)
            obj2 = Foobar(4,5,6)
        
            self.store.put(obj1)
            self.store.put(obj2)
        
            # get using a sqlalchemy session
            session = sessionmaker(autoflush=True, bind=self.__engine)()
            objs = session.query(Foobar).all()
            self.assertEqual(len(objs), 2)
        
            # verify we got the same objects out
            obj1_r, obj2_r = tuple(objs)
            self.assertEqual(obj1_r, obj1)
            self.assertEqual(obj2_r, obj2)
        
            # now delete them
            # session.expunge(obj1_r)
            # session.expunge(obj2_r)
            self.store.batch_delete([obj1_r, obj2_r])
        
            obj1_r, obj2_r = self.store.batch_get(Foobar, [
                {"foo": 1, "bar": 2}, #obj1
                {"foo": 4, "bar": 5}, #obj2
                ])
        
            self.assertEqual(obj1_r, None)
            self.assertEqual(obj2_r, None)

        def test_can_put_retrieved_object_from_external_session(self):
        
            obj = Foobar(1,2,3)
            self.store.put(obj)
        
            # get using a sqlalchemy session
            session = sessionmaker(autoflush=True, bind=self.__engine)()
            obj_r = session.query(Foobar).first()
            self.assertEqual(obj_r, obj)
        
            # now put the obj through the store
            self.store.put(obj_r)
        
            # store should give obj back
            obj_r = self.store.get(Foobar, {"foo": 1, "bar": 2})
            self.assertEqual(obj_r, obj)
        
            # raw db request should say the same
            obj_r = session.query(Foobar).first()
            self.assertEqual(obj_r, obj)

        def test_can_batch_put_retrieved_object_from_external_session(self):
        
            obj = Foobar(1,2,3)
            self.store.put(obj)
        
            # get using a sqlalchemy session
            session = sessionmaker(autoflush=True, bind=self.__engine)()
            obj_r = session.query(Foobar).first()
            self.assertEqual(obj_r, obj)
        
            # now put the obj through the store
            self.store.batch_put([obj_r])
        
            # store should give objs back
            obj_r = self.store.get(Foobar, {"foo": 1, "bar": 2})
            self.assertEqual(obj_r, obj)
        
            # raw db request should say the same
            obj_r = session.query(Foobar).first()
            self.assertEqual(obj_r, obj)
        
        def test_ignores_non_sqlalchemy_objects(self):
            
            class NonSaObject(object):
                __stockpyle_keys__ = ["key"]
                key = 1
            
            obj = NonSaObject()
            self.store.put(obj)
            self.assertEqual(None, self.store.get(NonSaObject, {"key": 1}))
            self.store.delete(obj)
            self.store.batch_put([obj])
            self.assertEqual([None], self.store.batch_get(NonSaObject, [{"key": 1}]))
            self.store.delete([obj])
            
            # when participating in a chain store, there are a few callbacks
            # (these are private API for now, but we need to test it)
            self.store._before_stockpyle_deserialize(obj)
    
        def test_closing_stockpyle_disallows_attribute_retrieval(self):
        
            obj = Foobar(1,2,3)
            self.store.put(obj)
            self.store.release()
            
            self.assertRaises(Exception, lambda: obj.foo)
            self.assertRaises(Exception, lambda: obj.bar)

    class ChainedStoreWithSqlAlchemyTestCase(TestCase):
    
        def setUp(self):
            self.__lm = CountingStoreWrapper(ProcessMemoryStore())
            self.__engine = create_engine("sqlite:///:memory:")
            self.__sa = CountingStoreWrapper(SqlAlchemyStore(engine=self.__engine))
            self.__store = ChainedStore([self.__lm, self.__sa])
            
            # create a special synchronizing session
            ext = StockpyleSessionExtension(self.__lm)
            self.__session = sessionmaker(autoflush=True, extension=ext, bind=self.__engine)()
            
            DeclarativeBase.metadata.create_all(bind=self.__engine)

        def tearDown(self):
            DeclarativeBase.metadata.drop_all(bind=self.__engine)
    
        def test_local_memory_updated_even_when_object_updated_outside_stockpyle(self):
        
            # create
            obj = Bazbot(1,2,3)
            
            # put in the store (sanity check)
            self.assertEqual(self.__sa.counts["put"], 0)
            self.__store.put(obj)
            self.assertEqual(self.__sa.counts["put"], 1)
            
            # retrieve from the store (sanity check)
            obj_r = self.__store.get(Bazbot, {"zap": 3})
            self.assertEqual(obj_r, obj)
        
            # ensure the get was done from localmem, not SA
            self.assertEqual(self.__lm.counts["get"], 1)
            self.assertEqual(self.__sa.counts["get"], 0)
        
            # now, update obj outside of stockpyle
            sa_obj = self.__session.query(Bazbot).filter_by(zap=3).first()
            sa_obj.bar = 555
            self.__session.add(sa_obj)
        
            # the commit should cause the cache to be updated
            self.assertEqual(self.__lm.counts["batch_put"], 0)
            print "about to commit..."
            self.__session.commit()
            print "committed..."
            self.assertEqual(self.__lm.counts["batch_put"], 1)
            self.assertEqual(self.__sa.counts["put"], 1)
            
            # we can retrieve this object now from the cache,
            # even though it was updated
            obj_r = self.__lm.get(Bazbot, {"zap": 3})
            self.assertEqual(obj_r, obj)
        
            # ensure we still haven't ever done a SA persistent get
            self.assertEqual(self.__sa.counts["get"], 0)

        def test_local_memory_deleted_even_when_object_deleted_outside_stockpyle(self):
        
            # create
            obj = Bazbot(1,2,3)
            
            # put in the store (sanity check)
            self.assertEqual(self.__sa.counts["put"], 0)
            self.__store.put(obj)
            self.assertEqual(self.__sa.counts["put"], 1)
            
            # retrieve from the store (sanity check)
            obj_r = self.__store.get(Bazbot, {"zap": 3})
            self.assertEqual(obj_r, obj)

            # ensure the get was done from localmem, not SA
            self.assertEqual(self.__lm.counts["get"], 1)
            self.assertEqual(self.__sa.counts["get"], 0)
        
            # now, delete obj outside of stockpyle
            sa_obj = self.__session.query(Bazbot).filter_by(zap=3).first()
            self.__session.delete(sa_obj)
        
            # the commit should cause the cache to be updated
            self.assertEqual(self.__lm.counts["batch_delete"], 0)
            print "about to commit..."
            self.__session.commit()
            print "committed..."
            self.assertEqual(self.__lm.counts["batch_delete"], 1)
            self.assertEqual(self.__sa.counts["put"], 1)
            
            # cache will not have this object anymore
            obj_r = self.__lm.get(Bazbot, {"zap": 3})
            self.assertEqual(obj_r, None)
            
            # ensure we try the persistence layer and get what we want
            # when using the writethru
            obj_r = self.__store.get(Bazbot, {"zap": 3})
            self.assertEqual(self.__lm.counts["get"], 3)
            self.assertEqual(self.__sa.counts["get"], 1)
            self.assertEqual(obj_r, None)
            
        def test_local_memory_updated_even_when_object_created_outside_stockpyle(self):
        
            # create
            obj = Bazbot(1,2,3)
            
            # save obj outside of stockpyle
            self.__session.add(obj)
            
            # the commit should cause the cache to be updated
            self.assertEqual(self.__lm.counts["batch_put"], 0)
            print "about to commit..."
            self.__session.commit()
            print "committed..."
            self.assertEqual(self.__lm.counts["batch_put"], 1)
            self.assertEqual(self.__sa.counts["put"], 0)
            
            # we can retrieve this object now from the cache,
            # even though it was created outside of stockpyle
            obj_r = self.__lm.get(Bazbot, {"zap": 3})
            self.assertEqual(obj_r, obj)
        
            # ensure we still haven't ever done a SA persistent get
            self.assertEqual(self.__sa.counts["get"], 0)
            
            # but the persistent get should also work
            obj_r = self.__sa.get(Bazbot, {"zap": 3})
            self.assertEqual(obj_r, obj)
        
        def test_queries_that_return_multiple_entities_throw_nonunique_error(self):
            barval = 2
            obj1 = Bazbot(1,barval,3)
            obj2 = Bazbot(1,barval,4)
            self.assertEqual(obj1.bar, 2)
            self.assertEqual(obj2.bar, 2)
            self.__sa.batch_put([obj1, obj2])
            self.assertRaises(NonUniqueKeyError, lambda: self.__sa.get(Bazbot, {"bar": barval}))
            
