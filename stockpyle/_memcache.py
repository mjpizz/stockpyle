import time
from datetime import datetime, timedelta
from stockpyle._base import BaseStore
from stockpyle._helpers import KeyValueHelper


class MemcacheStore(BaseStore):
    
    def __init__(self, client=None, servers=None, polymorphic=False, lifetime_cb=None, prefix="stockpyle"):
        super(MemcacheStore, self).__init__()
        
        # set up the lifetime callback and key/value generator
        self.__keyvalue_helper = KeyValueHelper(verbose=False, polymorphic=polymorphic, prefix=prefix)
        if lifetime_cb:
            self.__lifetime_cb = lifetime_cb
        else:
            self.__lifetime_cb = lambda obj: None
        
        # get/create the memcache client object
        if client and servers:
            raise ValueError("cannot give both a client and a list of servers, only one is allowed")
            
        if client:
            self.__client = client
        elif servers:
            import memcache
            self.__client = memcache.Client(servers)
        else:
            raise ValueError("you must specify either a client or a list of servers for memcache")
    
    def __get_memcache_compatible_lifetime(self, obj):
        """returns the lifetime for an object as an integer time since
        the epoch, or as a delta number of seconds (according to the memcache API
        limitation that deltas must be < 60*60*24*30 seconds)"""
        
        # get default lifetime
        lifetime = self.__lifetime_cb(obj)
        if lifetime is None:
            return 0
            
        else:
            # TODO: memoize this block of code for speed
            # ensure that lifetime is in unixtime or seconds
            if isinstance(lifetime, datetime):
            
                # unixtime
                return time.mktime(lifetime.timetuple())
            
            else:
                # timedelta
                if isinstance(lifetime, timedelta):
                    # convert to integer seconds
                    lifetime = int(86400*lifetime.days + lifetime.seconds + lifetime.microseconds/1000000.0)

                if isinstance(lifetime, int):
                    # check delta expiration against memcache API limitation
                    if lifetime >= 60*60*24*30:
                        raise ValueError("delta expiration must be less than 60*60*24*30 seconds (memcache API limitation)")
                else:
                    raise ValueError("lifetime must be an integer, datetime, or timedelta (got %s)" % lifetime.__class__)
                
                # everything checked out ok
                return lifetime
    
    def put(self, obj):
        lifetime = self.__get_memcache_compatible_lifetime(obj)
        object_map = {}
        for k in self.__keyvalue_helper.generate_all_lookup_keys(obj):
            object_map[k] = obj
        self.__client.set_multi(object_map, lifetime)
        
    def batch_put(self, objs):
        
        # group puts by lifetime
        lifetime_lookup = {}
        for obj in objs:
            lifetime = self.__get_memcache_compatible_lifetime(obj)
            if lifetime not in lifetime_lookup:
                lifetime_lookup[lifetime] = []
            lifetime_lookup[lifetime].append(obj)
        
        # for each lifetime, do a set_multi to drop those objects into memcache
        # with that same expiration time
        for lifetime in lifetime_lookup:
            objs_with_same_lifetime = lifetime_lookup[lifetime]
            object_map = {}
            for obj in objs_with_same_lifetime:
                for k in self.__keyvalue_helper.generate_all_lookup_keys(obj):
                    object_map[k] = obj
            self.__client.set_multi(object_map, lifetime)
    
    def delete(self, obj):
        cachekeys = self.__keyvalue_helper.generate_all_lookup_keys(obj)
        self.__client.delete_multi(cachekeys)
    
    def batch_delete(self, objs):
        cachekeys = []
        for obj in objs:
            cachekeys += self.__keyvalue_helper.generate_all_lookup_keys(obj)
        self.__client.delete_multi(cachekeys)
    
    def get(self, klass, key):
        cachekey = self.__keyvalue_helper.generate_lookup_key(klass, key)
        return self.__client.get(cachekey)
    
    def batch_get(self, klass, keys):
        cachekeys = [self.__keyvalue_helper.generate_lookup_key(klass, key) for key in keys]
        object_map = self.__client.get_multi(cachekeys)
        return [object_map.get(k, None) for k in cachekeys]
    
    def release(self):
        self.__client.disconnect_all()
        