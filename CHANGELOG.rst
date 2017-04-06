0.3 2017-mm-dd
--------------
Added
-----

- Added descriptive exceptions.
- ``Gen`` object and ``gendata`` function for querying data about the Lawson environment.

Changed
-------

- Session objects will now accept ``kwargs`` and ignore ones they don't need.

0.2 2017-03-04
--------------
Added
-----

- Create connection using robo-login via SAML.

Changed
-------

- Refactor connections to use base class so you can choose/write the session object that fits your use case.
- Refactored API.

0.1 2016-09-30
--------------
Added
-----

- Initial concept (not released) creating connection via .NET SEC-API library.
