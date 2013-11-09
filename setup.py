import setuptools


setuptools.setup(
    name="Mongothon",
    version="0.5.4",
    author="Tom Leach",
    author_email="tom@leach.it",
    description="A MongoDB object-document mapping layer for Python",
    license="BSD",
    keywords="mongo mongodb database pymongo odm validation",
    url="http://github.com/tleach/mongothon",
    packages=["mongothon"],
    long_description="Mongothon is a MongoDB object-document mapping " +
                     "API for Python, loosely based on the awesome " +
                     "mongoose.js library.",
    install_requires=['pymongo', 'inflection'],
    tests_require=['mock', 'nose']
    )
