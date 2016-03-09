from stockpyle._base import BaseStore
try:
    import google.appengine
    from google.appengine.ext import db
    __HAS_APPENGINE = True
except ImportError, e:
    __HAS_APPENGINE = False


class AppEngineStore(object):
    """represents a storage container on the Google App Engine DataStore"""
        
    def put(self, obj):
        if isinstance(obj, db.Model):
            db.put(obj)
        
    def batch_put(self, objs):
        ds_objs = [o for o in objs if isinstance(o, db.Model)]
        db.put(ds_objs)
    
    def delete(self, obj):
        if isinstance(obj, db.Model):
            db.delete(obj)
    
    def batch_delete(self, objs):
        ds_objs = [o for o in objs if isinstance(o, db.Model)]
        db.delete(ds_objs)
    
    def get(self, klass, key):
        if issubclass(klass, db.Model):
            query = db.Query(klass)
            for k,v in key.iteritems():
                query.filter("%s=" % k, v)
            return query.get()
    
    def batch_get(self, klass, keys):
        # TODO: is there a more efficient way?
        return [self.get(klass, k) for k in keys]
            
