from stockpyle._base import BaseDictionaryStore


class ProcessMemoryStore(BaseDictionaryStore):
    """Represents an in-process memory store"""
        
    def __init__(self, polymorphic=False, lifetime_cb=None):
        self.__dictionary = {}
        super(ProcessMemoryStore, self).__init__(dictionary=self.__dictionary, polymorphic=polymorphic, lifetime_cb=lifetime_cb)
