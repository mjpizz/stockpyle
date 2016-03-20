import os
from distutils.core import setup
from distutils.extension import Extension

from setuptools import setup

# try:
#     from Cython.Distutils import build_ext
#     
#     cmdclass = {"build_ext": build_ext}
#     ext_modules = [Extension("stockpyle._speedups", ["stockpyle/_speedups.pyx"])]
# 
# except ImportError:
#     print "*** skipping Cython compilation, using built-in C files"
#     cmdclass = {}
#     ext_modules = [Extension("stockpyle._speedups", ["stockpyle/_speedups.c"])]

setup(
    name="stockpyle",
    packages=["stockpyle", "stockpyle.ext"],
    version="0.1.4",
    license="BSD",
    author="Matt Pizzimenti",
    author_email="mjpizz+stockpyle@gmail.com",
    url="http://pypi.python.org/pypi/stockpyle/",
    install_requires=[ 'SQLAlchemy>=1.0.11', 'shove>=0.6.6', 'python-memcached>=1.57', ],
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Programming Language :: Python",
        "License :: OSI Approved :: BSD License",
        "Intended Audience :: Developers",
        "Operating System :: OS Independent",
        "Natural Language :: English",
        "Topic :: Software Development",
        "Topic :: System :: Distributed Computing",
        "Topic :: Software Development :: Object Brokering",
        "Topic :: Database :: Front-Ends",
    ],
    description="stockpyle allows the creation of write-through storage for object caching and persistence",
    long_description=open(os.path.join(os.path.dirname(__file__), "README.md")).read(),
    # zip_safe=False,
    # cmdclass=cmdclass,
    # ext_modules=ext_modules,
    )
