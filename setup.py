import setuptools


setuptools.setup(
    name="Mongothon",
    version="0.7.1",
    author="Tom Leach",
    author_email="tom@gc.io",
    description="A MongoDB object-document mapping layer for Python",
    license="BSD",
    keywords="mongo mongodb database pymongo odm validation",
    url="http://github.com/gamechanger/mongothon",
    packages=["mongothon"],
    long_description="Mongothon is a MongoDB object-document mapping " +
                     "API for Python, loosely based on the awesome " +
                     "mongoose.js library.",
    install_requires=['pymongo>=2.5.0', 'inflection==0.2.0', 'schemer==0.2.0'],
    tests_require=['mock', 'nose']
    )
