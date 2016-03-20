import os
try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

setup(
    name="stockpyle",
    packages=["stockpyle", "stockpyle.ext"],
    version="0.1.8",
    license="BSD",
    author="Matt Pizzimenti",
    author_email="mjpizz+stockpyle@gmail.com",
    url="https://github.com/mjpizz/stockpyle",
    install_requires=["SQLAlchemy>=1.0.11", "shove>=0.6.6", "python-memcached>=1.57"],
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
    # Note that pypi does not support markdown yet
    # https://bitbucket.org/pypa/pypi/issues/148/support-markdown-for-readmes
)
