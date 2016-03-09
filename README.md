Overview
===========

The central concept of stockpyle is the *Store* objects.  You can find a variety of these objects
in stockpyle.stores:

* ThreadLocalStore
* ProcessMemoryStore
* ChainedStore
* MemcacheStore - http://pypi.python.org/pypi/python-memcached
* ShoveStore - http://pypi.python.org/pypi/shove
* SqlAlchemyStore - http://pypi.python.org/pypi/SQLAlchemy
    
Stores can perform 6 operations on objects:

* put
* get
* delete
* batch_put
* batch_get
* batch_delete

Every stockpyle Store can handle any Python object that exposes the property *__stockpyle_keys__*.
This property lists the names of each attribute or attribute-tuple that `uniquely` identifies
that object.  Read the quickstart below for more details.

Quickstart
==========

Basics
------

The fastest way to get up and running is to create an in-memory Store::
    
    from stockpyle.stores import ProcessMemoryStore
    
    store = ProcessMemoryStore()

Now lets create a Python object that can be stored in stockpyle.  This object
has an attribute 'key' that identifies it uniquely::
    
    class Foo(object):
        
        __stockpyle_keys__ = ["key"]
        
        def __init__(self, key):
            self.key = key

We can now store a Foo object in our Store::
    
    f = Foo('my_unique_key_123')
    store.put(f)

And we can retrieve it from the Store::
    
    f = store.get(Foo, {'key': 'my_unique_key_123'})

We can also delete it from the Store::

    store.delete(f)

Manipulating batches of objects is also trivial::
    
    f1 = Foo('my_key_1')
    f2 = Foo('my_key_2')
    f3 = Foo('my_key_3')
    
    store.batch_put([f1, f2, f3])
    
    o1, o2, o3 = store.batch_get(Foo, [
        {'key': 'my_key_1'},
        {'key': 'my_key_2'},
        {'key': 'my_key_3'},
        ])
    
    assert((f1, f2, f3) == (o1, o2, o3))
    
    store.batch_delete([f1, f2, f3])

Note: if you do a *batch_get* and one of the keys is null, it still gets returned as None::
    
    o1, o2, o3 = store.batch_get(Foo, [
        {'key': 'my_key_1'},
        {'key': 'nonexistent_key'},
        {'key': 'my_key_3'},
        ])
    
    assert(o2 is None)

And that's basics of using stockpyle.  No matter what Store object
you use, you can use this API to store, retrieve, and delete objects.

Chained Storage (e.g. write-through caching)
--------------------------------------------

Persistent storage is often expensive to access, making caching a necessity.
However, maintaining cache consistency is difficult and error-prone.  The stockpyle
API provides a consistent way to perform this caching, using *ChainedStore*.

ChainedStore takes an ordered list of stores and treats them as a write-through
cache.  This example creates a write-through cache for SQLAlchemy-backed database objects::

    fast_cache = ProcessMemoryStore()
    dist_cache = MemcacheStore(servers=["localhost:11211"])
    persistent_store = SqlAlchemyStore(uri="sqlite:///data.sqlite")
    
    chained_store = ChainedStore([fast_cache, dist_cache, persistent_store])

In this example, the fast cache (in-memory) will always be attempted first for
retrievals.  The distributed cache (memcached) will be attempted second.  If these
stores fail to find the object, the database store (SQLAlchemy) will be queried for
the persistent object.

During puts, gets, and deletes, stockpyle will keep the upper layers (the caches)
populated with the latest data from lower layers (the persistent database).

Bugs
====

This is still an early-stage project.  Please file bugs on Google Code:

http://code.google.com/p/stockpyle/

Advanced
========

Alternate Keys
--------------

The __stockpyle_keys__ attribute can contain more than just one unique attribute.
It can also contain tuples of attribute names::
    
    class Foo(object):
        
        __stockpyle_keys__ = ["key", ("zap", "bar")]
        
        def __init__(self, key, zap, bar):
            self.key = key
            self.zap = zap
            self.bar = bar

Now, Foo is indexed by both 'key', *and* the combined attributes 'zap' and 'bar'::
    
    f = Foo(key=1, zap=2, bar=3)
    
    store.put(f)
    
    o1 = store.get(Foo, {'key': 1})
    o2 = store.get(Foo, {'zap': 2, 'bar': 3})
    
    assert(f == o1 == o2)

Cache Expiration
----------------

Some stockpyle stores support the concept of object expiration:

* ThreadLocalStore
* ProcessMemoryStore
* MemcachedStore
* ShoveStore

In all three stores, you can specify a "lifetime-callback", which takes
a Python object as an argument and returns a lifetime value for that object.

Lifetime can be expressed in 3 ways:

* integer number of seconds
* Python timedelta
* Python datetime (absolute expiration time)

This example allows Foo objects to live for 20 seconds, and Bar objects to
live for 5 minutes::

    def my_lifetime_cb(obj):
        
        if isinstance(obj, Foo):
            return 20
        
        elif isinstance(obj, Bar):
            return 5*60
    
    store = ProcessMemoryStore(lifetime_cb=my_lifetime_cb)

Note that you can specify different lifetime callbacks for each your stores.
For example, you may want to expire in-memory caches quickly to for more frequent
re-sync with the lower layers in a ChainedStore.

Polymorphic Storage
-------------------

Some stockpyle stores support the concept of storing objects in a way
that can be queried polymorphically:

* ThreadLocalStore
* ProcessMemoryStore
* MemcachedStore
* ShoveStore

By default, objects are not stored polymorphically in these stores because
it duplicates the locations that a single object is stored.  However, you may
want to be able to query subclasses out of a cache::

    class Automobile(object):
        
        __stockpyle_keys__ = ["license_plate"]
        
        def __init__(self, license_plate):
            self.license_plate = license_plate
    
    class Car(Automobile):
        pass
    
    
    class Truck(Automobile):
        pass

If you create a store that supports polymorphic queries::
    
    store = ProcessMemoryStore(polymorphic=True)

Then you can store a Car::
    
    car = Car(license_plate="1234 XYZ")
    store.put()

And retrieve it as either a Car or an automobile::
    
    car = store.get(Car, {'license_plate': '1234 XYZ'})
    automobile = store.get(Automobile, {'license_plate': '1234 XYZ'})
    
    assert(car == automobile)

Note that there is a tradeoff in storage duplication when doing this.  Every Car
object is indexed as a Car and as an Automobile (2 locations in storage).

Memcache Integration
--------------------

In order to enable MemcacheStore, you will need to install the python-memcached module:

http://pypi.python.org/pypi/python-memcached

The MemcacheStore supports polymorphic storage and object expiration.  The native memcache API is used to support
object expiration and batched operations.

Shove Integration
-----------------

In order to enable ShoveStore, you will need to install the shove module:

http://pypi.python.org/pypi/shove

The Shove API provides a very broad array of storage backends with a dictionary-style interface,
which work well in stockpyle. This example uses the shove backend for Amazon S3::
    
    from stockpyle.stores import ShoveStore
    
    s3_store = ShoveStore(shoveuri="s3://s3key:s3secret@your_s3_bucket_name")

ShoveStores support polymorphic storage and object expiration.  Every object stored in the Shove is stored at
a human-readable key, as a tuple of (obj, expiredate).

SQLAlchemy Integration
----------------------

In order to enable SqlAlchemyStore, you will need to install the SQLAlchemy module:

http://pypi.python.org/pypi/SQLAlchemy

Typically, in SQLAlchemy you will use a session to store and retrieve your mapped objects::

    # create the object
    obj = MyMappedObject(foobar=123)
    
    # store it
    session.save(obj)
    session.commit()
    
    # retrieve it
    obj_retrieved = session.query(MyMappedObject).filter(MyMappedObject.foobar == 123).first()

You can do the same thing through a SqlAlchemyStore::
    
    # create the store
    store = SqlAlchemyStore(uri="sqlite:///data.sqlite")
    
    # create the object
    obj = MyMappedObject(foobar=123)
    
    # store it
    store.put(obj)
    
    # retrieve it
    obj_retrieved = store.get(MyMappedObject, {'foobar': 123})

Now you can put this SqlAlchemyStore in a ChainedStore for write-through caching::
    
    # use MemcacheStore as a cache layer
    mc = MemcacheStore(servers=["localhost:11211"])
    sa = SqlAlchemyStore(uri="sqlite:///data.sqlite")
    store = ChainedStore([mc, sa])
    
    # store it, which causes the object to be written-through
    # the MemcacheStore
    store.put(obj)
    
    # retrieve it, except this time it comes from
    # the MemcacheStore instead of the database
    obj_retrieved = store.get(MyMappedObject, {'id': obj.id})

*What if you want to access the SQLAlchemy session directly?*  This is a common
case, since obviously stockpyle does not provide the rich querying API that
SQLAlchemy has.  To ensure that your stockpyle cache does not get out of sync
with queries done in your own SQLAlchemy sessions, simply add a
StockpyleSessionExtension to your session object::
    
    from sqlalchemy.orm import sessionmaker
    from stockpyle.stores import MemcacheStore
    from stockpyle.ext.sqlalchemy import StockpyleSessionExtension

    mc = MemcacheStore(servers=["localhost:11211"])
    ext = StockpyleSessionExtension(store=mc)
    my_session = sessionmaker(extension=ext)

Now, whenever *my_session* performs an insert, update, or delete on an object,
it will also perform the corresponding puts and deletes in the MemcacheStore.

Objects that you get from SqlAlchemyStore are bound to the internal session
object on that store.  Keep this in mind when you are using your own session,
since you will have to *merge()* the stockpyle-retrieved object into your session::
    
    # get an object from SqlAlchemyStore
    obj = sa_store.get(MyMappedObject, {'id': 'foobar123'})
    
    # change some information
    obj.name = "bleh"
    
    # if you want to use this object in your SQLAlchemy
    # session, you must merge the object first since the
    # object is currently bound to the internal session
    # inside the SqlAlchemyStore
    my_session.merge(obj)
    my_session.commit()
    
Caveats:

* SqlAlchemyStores are *not* threadsafe (at least, at the moment)

Defining a custom Store
-----------------------
Although stockpile contains most of the stores you will need to support
any storage backend (especially through Shove integration), you may
want to implement your own Store.  The stockpyle library provides two base
classes to define your own Stores:

* BaseStore (for implementing your own store from scratch)
* BaseDictionaryStore (for implementing your own store that has a dictionary-style interface)

To make your own store, simply create a subclass of either of these stores and implement
the 6 storage methods (put, get, delete, batch_put, batch_get, batch_delete).

Please browse the source code for detailed examples of how to implement your own store.
