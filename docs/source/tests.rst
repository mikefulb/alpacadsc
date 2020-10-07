Tests
=====

Test cases
----------

The test cases can be executed using the command:

   python setup.py test

test_server_basic
'''''''''''''''''

Tests various HTTP endpoints served by the driver work properl including
pages supporting the configuration of the driver.

.. automodule:: tests.test_server_basic
   :members:

test_server_alpaca
''''''''''''''''''

Tests basic Alpaca REST API calls.

.. automodule:: tests.test_server_alpaca
   :members:

test_server_pointing
''''''''''''''''''''

Tests reading encoders value and that syncronizing the driver and moving
scope to a new position tracks in ALT/AZ and RA/DEC properly.

.. automodule:: tests.test_server_pointing
   :members:

utils module
------------

.. automodule:: tests.utils
   :members:

