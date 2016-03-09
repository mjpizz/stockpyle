import threading
from stockpyle._base import BaseStore
from stockpyle.exceptions import NonUniqueKeyError
try:
    import sqlalchemy
    __HAS_SQLALCHEMY = True
except ImportError:
    __HAS_SQLALCHEMY = False
    

if __HAS_SQLALCHEMY:

    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker, EXT_CONTINUE, SessionExtension, scoped_session
    from sqlalchemy.exceptions import InvalidRequestError


    # SQLAlchemy is installed
    class StockpyleSessionExtension(SessionExtension):
        """If you have your own sessions, you can add this extension
        to force that session to synchronize objects with the given store"""
        
        def __init__(self, store):
            self.__store = store
            self.__operation_for_instance = {}
        
        def after_flush(self, session, flush_context):
            
            # deleted items must be deleted from the store
            for o in session.deleted:
                self.__operation_for_instance[o] = "delete"
            
            # new items must be put to the store
            for o in session.new:
                self.__operation_for_instance[o] = "put"
            
            # dirty items must be put to the store as well
            for o in session.dirty:
                self.__operation_for_instance[o] = "put"
                
            return EXT_CONTINUE
        
        def after_commit(self, session):
            
            # group operations by deletes/puts
            operation_map = {}
            for obj, operation in self.__operation_for_instance.iteritems():
                if operation not in operation_map:
                    operation_map[operation] = []
                operation_map[operation].append(obj)
            
            # do a batch delete for all deletes
            if "delete" in operation_map:
                self.__store.batch_delete(operation_map["delete"])
            
            # do a batch put for all puts
            if "put" in operation_map:
                self.__store.batch_put(operation_map["put"])
            
            # clear the operation cache, we're done
            self.__operation_for_instance = {}
            
            return EXT_CONTINUE
            
            
else:
    
    
    # SQLAlchemy is not installed
    class StockpyleSessionExtension(object):
        
        def __init__(self):
            raise StandardError("cannot use StockpyleSessionExtension without the SQLAlchemy module")


def _is_sqlalchemy_class(klass):
    """returns true if the given class is managed by SQLAlchemy"""
    # TODO: better way?
    return hasattr(klass, "_sa_class_manager")

def _is_sqlalchemy_object(obj):
    """returns true if the given object is managed by SQLAlchemy"""
    # TODO: better way?
    return hasattr(obj, "_sa_instance_state")


class SqlAlchemyStore(BaseStore):
    """Represents a storage target that can store any SQLAlchemy-mapped object.
    Non-SQLAlchemy objects will be ignored by this store."""
    
    def __init__(self, uri=None, engine=None, **kwargs):
        """Create a new SqlAlchemyStore.  When given a connection string (uri)
        or SQLAlchemy Engine (engine), this Store will create it's own internal
        SQLAlchemy Session to manage objects.  If you do not provide a URI or
        Engine, your mapped object metadata must be bound to their own engines.
        """

        super(SqlAlchemyStore, self).__init__()
        
        # get the session
        if "session" in kwargs:
            # we no longer allow initialization with a pre-existing session object, there
            # are too many issues with this approach at the moment
            raise DeprecationWarning("cannot instantiate a SqlAlchemyStore with a pre-existing session object")
        else:
            # no session, we have to make one
            # first we need to get the engine
            
            if uri and engine:
                # can't give two ways to get an engine
                raise ValueError("you can only provide either a connection string URI or an engine, not both")
                
            elif uri:
                # we have a uri to create an engine
                engine = create_engine(uri)
            
            if engine:
                # we have an engine, we can create the bound session now
                self.__session = scoped_session(sessionmaker(autoflush=True, bind=engine))
            
            else:
                # no engine or URI was specified, create an unbound session
                # (mapped object metadata will need to be bound to an engine in this case)
                self.__session = scoped_session(sessionmaker(autoflush=True))
    
    def put(self, obj):
        # only store SA objects
        if _is_sqlalchemy_object(obj):
            self._sa_put(obj)
        
    def batch_put(self, objs):
        # only store SA objects
        sa_objs = [o for o in objs if _is_sqlalchemy_object(o)]
        if sa_objs:
            self._sa_batch_put(sa_objs)
    
    def delete(self, obj):
        # only delete SA objects
        if _is_sqlalchemy_object(obj):
            self._sa_delete(obj)
    
    def batch_delete(self, objs):
        # only delete SA objects
        sa_objs = [o for o in objs if _is_sqlalchemy_object(o)]
        if sa_objs:
            self._sa_batch_delete(sa_objs)
    
    def get(self, klass, key):
        # only attempt to query SQAlchemy objects
        if _is_sqlalchemy_class(klass):
            return self._sa_get(klass, key)
        else:
            return None
    
    def batch_get(self, klass, keys):
        # only attempt to query SQAlchemy objects
        if _is_sqlalchemy_class(klass):
            return self._sa_batch_get(klass, keys)
        else:
            return [None for k in keys]
    
    def release(self):
        self.__session.close()
    
    def _sa_put(self, obj):
        try:
            self.__session.add(obj)
            self.__session.commit()
        except InvalidRequestError:
            # this is likely due to mismatched session attachment, do the more expensive 'merge' operation
            try:
                self.__session.merge(obj)
                self.__session.commit()
            except:
                self.__session.rollback()
                raise
        except:
            self.__session.rollback()
            raise

    def _sa_batch_put(self, objs):
    
        # commit the session
        try:
            self.__session.add_all(objs)
            self.__session.commit()
        except InvalidRequestError:
            # this is likely due to mismatched session attachment, do the more expensive 'merge' operation
            try:
                for obj in objs:
                    self.__session.merge(obj)
                self.__session.commit()
            except:
                self.__session.rollback()
                raise
        except:
            self.__session.rollback()
            raise
    
    def _sa_delete(self, obj):
        try:
            self.__session.delete(obj)
            self.__session.commit()
        except InvalidRequestError:
            # this is likely due to mismatched session attachment, do the more expensive 'merge' operation
            try:
                obj = self.__session.merge(obj)
                self.__session.delete(obj)
                self.__session.commit()
            except:
                self.__session.rollback()
                raise
        except:
            self.__session.rollback()
            raise
    
    def _sa_batch_delete(self, objs):

        # TODO: is there a bulk_delete in SA?
        try:
            for obj in objs:
                self.__session.delete(obj)
            self.__session.commit()
        except InvalidRequestError:
            # this is likely due to mismatched session attachment, do the more expensive 'merge' operation
            try:
                for obj in objs:
                    obj = self.__session.merge(obj)
                    self.__session.delete(obj)
                self.__session.commit()
            except:
                self.__session.rollback()
                raise
        except:
            self.__session.rollback()
            raise
    
    def _sa_get(self, klass, key):
        objs = self.__session.query(klass).filter_by(**key)[0:2]
        if objs:
            if len(objs) == 2:
                raise NonUniqueKeyError(klass, key)
            else:
                return objs[0]
        else:
            return None
    
    def _sa_batch_get(self, klass, keys):
        # FIXME: this is very inefficient, need to read up on the SA API a bit more
        return [self.get(klass, k) for k in keys]
        
    def _before_stockpyle_deserialize(self, obj):
        """this callback is used by ChainedStore to post-process any
        object that was deserialized out of another Store. As documented
        in the SQLAlchemy API, we should use the merge() operation with
        dont_load=True for handling deserialized SA objects"""
        
        # only merge SA objects
        if _is_sqlalchemy_object(obj):
            self.__session.merge(obj, dont_load=True)
        