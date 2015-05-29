SNMPLibrary for Robot Framework
===============================

|BuildStatus| |PyPiVersion|

Introduction
------------

SNMPLibrary is a `Robot Framework <http://robotframework.org>`__ test
library for testing SNMP. It is operating system independent [#os-indep]_.

The library provides the following features:

- get and set SNMP variables
- MIB handling (almost completely untested yet!)
- Receive and inspect SNMP traps
- SNMP v2c and v3 authentication

Installation
------------

The simplest method to install, is to use pip::

  pip install robotframework-snmplibrary

Documentation
-------------

The most up-to-date keyword documentation can be found at
http://kontron.github.io/robotframework-snmplibrary/SnmpLibrary.html

.. [#os-indep] At the moment it is only developed and tested on linux
               hosts, but should also work on windows and other operating
               systems.

.. |BuildStatus| image:: https://travis-ci.org/kontron/robotframework-aardvarklibrary.png?branch=master
                 :target: https://travis-ci.org/kontron/robotframework-aardvarklibrary
.. |PyPiVersion| image:: https://badge.fury.io/py/robotframework-snmplibrary.svg
                 :target: http://badge.fury.io/py/robotframework-snmplibrary
