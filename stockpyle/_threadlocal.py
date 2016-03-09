import threading
from stockpyle._base import BaseDictionaryStore


class _ThreadlocalDict(object):
    
    def __init__(self):
        self.__threadlocal = threading.local()
    
    def __get_threadlocal_dict(self):
        if not hasattr(self.__threadlocal, "dictionary"):
            self.__threadlocal.dictionary = {}
        return self.__threadlocal.dictionary
    
    def __getattr__(self, name):
        d = self.__get_threadlocal_dict()
        return getattr(d, name)
    
    def __getitem__(self, key):
        d = self.__get_threadlocal_dict()
        return d[key]
        
    def __setitem__(self, key, value):
        d = self.__get_threadlocal_dict()
        d[key] = value
    
    def __delitem__(self, key):
        d = self.__get_threadlocal_dict()
        del d[key]
    
    def __contains__(self, item):
        d = self.__get_threadlocal_dict()
        return bool(item in d)


class ThreadLocalStore(BaseDictionaryStore):
    """Represents threadlocal memory store.  This cache-like store
    will only be available within the current thread of execution.
    All objects will be lost after the thread completes.  This is good
    for web applications that serve each request in a thread - all storage
    retrievals can happen in-memory during the request, but nothing would last
    beyond the request in a ThreadLocalStore."""
        
    def __init__(self, polymorphic=False, lifetime_cb=None):
        super(ThreadLocalStore, self).__init__(dictionary=_ThreadlocalDict(), polymorphic=polymorphic, lifetime_cb=lifetime_cb)
