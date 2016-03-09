from stockpyle._base import BaseDictionaryStore


class ShoveStore(BaseDictionaryStore):
    """Represents a store that places all objects in a Shove (see http://pypi.python.org/pypi/shove)"""
        
    def __init__(self, shove=None, shoveuri=None, polymorphic=False, lifetime_cb=None):
        # TODO: deprecate 'shoveuri' in favor of 'uri'
        if shove is not None and shoveuri is not None:
            raise ValueError("you can only provide either a Shove object or a Shove URI, not both")
        elif shove is not None:
            self.__shove = shove
        elif shoveuri is not None:
            from shove import Shove
            self.__shove = Shove(shoveuri)
        else:
            raise ValueError("you must provide either a Shove object or a Shove URI to create a ShoveStore")
        super(ShoveStore, self).__init__(dictionary=self.__shove, polymorphic=polymorphic, lifetime_cb=lifetime_cb)
