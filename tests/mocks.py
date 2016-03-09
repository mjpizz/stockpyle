import pickle
from datetime import datetime, timedelta

class MockMemcacheClient(object):
    """stubs out memcached calls with an in-memory compatible API"""
    
    def __init__(self):
        self.__map = {}
        self.__timeouts = {}
        self.flush_all()
    
    def get(self, key):
        now = datetime.today()
        if key in self.__timeouts:
            if now >= self.__timeouts[key]:
                del self.__timeouts[key]
                del self.__map[key]
                return None
        
        val = self.__map.get(key, None)
        if val:
            return pickle.loads(val)
        else:
            return None
    
    def set(self, key, value, time=None):
        
        # convert integer time into python time objects
        if time:
            if time < 60*60*24*30:
                delta = timedelta(seconds=time)
                time = datetime.today() + delta
            else:
                time = datetime.fromtimestamp(time)
            
        self.__map[key] = pickle.dumps(value)
        if time:
            self.__timeouts[key] = time
        return True
    
    def get_multi(self, keys):
        object_map = {}
        for k in keys:
            object_map[k] = self.get(k)
        return object_map
    
    def set_multi(self, obj_map, time=None):
        for key, obj in obj_map.iteritems():
            self.set(key, obj, time)
    
    def delete_multi(self, keys):
        for k in keys:
            self.delete(k)
        
    def delete(self, key):
        if key in self.__map:
            del self.__map[key]
            if key in self.__timeouts:
                del self.__timeouts[key]
            return True
        else:
            return False
    
    def flush_all(self):
        self.__map = {}
        self.__timeouts = {}
    
    def disconnect_all(self):
        pass
        
