from datetime import datetime, timedelta
from stockpyle._helpers import KeyValueHelper

    
class BaseStore(object):
    """represents a standard storage container"""
        
    def put(self, obj):
        raise NotImplementedError()
        
    def batch_put(self, objs):
        raise NotImplementedError()
    
    def delete(self, obj):
        raise NotImplementedError()
    
    def batch_delete(self, objs):
        raise NotImplementedError()
    
    def get(self, klass, key):
        raise NotImplementedError()
    
    def batch_get(self, klass, keys):
        raise NotImplementedError()
    
    def release(self):
        raise NotImplementedError()


class BaseDictionaryStore(BaseStore):
    """Base class for all dictionary-like stores.  Optional capabilities include
    polymorphic stores and object expiration times."""
        
    def __init__(self, dictionary, polymorphic=False, lifetime_cb=None):
        """create a new BaseDictionaryStore that stores data in the given
        dictionary or dictionary-like object.  Options:
        
        polymorphic: set this to true to replicate stored objects
                     under their base classes' __stockpyle_keys__
                     so that they can be queried via the base class
                     as well
        
        lifetime_cb: this callback takes an object and returns an absolute
                     expiration time as a datetime, or a relative expiration
                     as a timedelta or integer number of seconds
        """
        super(BaseDictionaryStore, self).__init__()
        self.__keyvalue_helper = KeyValueHelper(verbose=True, polymorphic=polymorphic)
        self.__dictionary = dictionary
        if lifetime_cb:
            self.__lifetime_cb = lifetime_cb
        else:
            self.__lifetime_cb = lambda obj: None
        
    def put(self, obj):
        """stores the given object, indexed by its __stockpyle_keys__ and with
        and expiration date determined by the lifetime_cb in the constructor"""
        # get the lifetime as a datetime
        lifetime = self.__lifetime_cb(obj)
        if lifetime and not isinstance(lifetime, datetime):
            if isinstance(lifetime, timedelta):
                lifetime = datetime.today() + lifetime
            elif isinstance(lifetime, int) or isinstance(lifetime, float):
                lifetime = datetime.today() + timedelta(seconds=int(lifetime))
        
        for k in self.__keyvalue_helper.generate_all_lookup_keys(obj):
            self.__dictionary[k] = (obj, lifetime)

    def batch_put(self, objs):
        """puts a list of objects into the dictionary store"""
        for obj in objs:
            self.put(obj)
    
    def delete(self, obj):
        """deletes an object from the dictionary store"""
        cachekeys = self.__keyvalue_helper.generate_all_lookup_keys(obj)
        for k in cachekeys:
            if k in self.__dictionary:
                del self.__dictionary[k]
    
    def batch_delete(self, objs):
        """deletes a list of objects from the dictionary store"""
        for o in objs:
            self.delete(o)
    
    def get(self, klass, key):
        """retrieves an object of the given class, under the given 'key' (a dictionary of key/value pairs)
        Expiration is checked before returning the object.  If the object has expired,
        this method will delete the object from the dictionary store."""
        cachekey = self.__keyvalue_helper.generate_lookup_key(klass, key)
        result = self.__dictionary.get(cachekey, None)
        if result:
            (obj, lifetime) = result
            if lifetime:
                if datetime.today() <= lifetime:
                    return obj
                else:
                    # expired
                    self.delete(obj)
                    return None
            else:
                # no lifetime, we don't have to worry about expiration
                return obj
        else:
            return None
    
    def batch_get(self, klass, keys):
        """returns a list of objects of the given class, under the given 'keys'
        (dictionaries of key/value pairs)"""
        return [self.get(klass, k) for k in keys]
    
    def release(self):
        """by default, release is a no-op for dictionary stores"""
        pass
        