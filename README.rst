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

Contributing
------------

Contributions are always welcome. You may send patches directly (eg. ``git
send-email``), do a github pull request or just file an issue.

If you are doing code changes or additions please:

* respect the coding style (eg. PEP8),
* provide well-formed commit messages (see `this blog post
  <http://tbaggery.com/2008/04/19/a-note-about-git-commit-messages.html>`_.)
* add a Signed-off-by line (eg. ``git commit -s``)

License
-------

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.


.. [#os-indep] At the moment it is only developed and tested on linux
               hosts, but should also work on windows and other operating
               systems.

.. |BuildStatus| image:: https://travis-ci.org/kontron/robotframework-snmplibrary.png?branch=master
                 :target: https://travis-ci.org/kontron/robotframework-snmplibrary
.. |PyPiVersion| image:: https://badge.fury.io/py/robotframework-snmplibrary.svg
                 :target: http://badge.fury.io/py/robotframework-snmplibrary
