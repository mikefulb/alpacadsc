#
# Test Alpaca REST API
#
#
# Invocation:  Run from the root directory of alpacadsc git checkout:
#              python -m pytest -v tests/
#
# To see logging output up to a certain log level add the options:
#              "-v -o log_cli=true --log-cli-level=DEBUG"
#
# Copyright 2020 Michael Fulbright
#
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
from alpacadsc import __version__ as AlpacaDSCDriver_Version
from alpacadsc.alpaca_models import AlpacaAltAzTelescopeModel

from consts import REST_API_URI

# we must import pytest fixtures client and my_fs for the test cases
# below to run properly.  Pytest will inject them into the argument
# list for the test cases.  It is normal for a python linter to
# report they are unused.
from utils import create_test_profile, REST_Handler, client, my_fs


def test_rest_get_basic(client):
    """
    Test Alpaca GET API common to all drivers.
    """

    # get a driver object and compare attributes to those
    # returned by a REST API call
    altaz_driver = AlpacaAltAzTelescopeModel()

    # create handler for sending REST requests
    rest = REST_Handler(client, REST_API_URI)

    # description
    rv = rest.get('description')
    assert altaz_driver.description == rv.json['Value']

    # name
    rv = rest.get('name')
    assert altaz_driver.name == rv.json['Value']

    # driverinfo
    rv = rest.get('driverinfo')
    assert altaz_driver.driverinfo == rv.json['Value']

    # driver version
    rv = rest.get('driverversion')
    assert f'{AlpacaDSCDriver_Version}' == rv.json['Value']
    assert f'{altaz_driver.driverversion}' == rv.json['Value']

    # interface version
    rv = rest.get('interfaceversion')
    assert altaz_driver.interfaceversion == rv.json['Value']

    # connected
    rv = rest.get('connected')
    assert isinstance(rv.json['Value'], bool)


def test_rest_connected(client, my_fs):
    """
    Test connecting to the driver.
    """
    # create a profile
    create_test_profile()

    # create handler for sending REST requests
    rest = REST_Handler(client, REST_API_URI)

    # get current connected state, should be False
    rv = rest.get('connected')
    assert isinstance(rv.json['Value'], bool)
    assert rv.json['Value'] is False

    # connect
    rv = rest.put('connected', data=dict(Connected=True))

    # confirm PUT worked
    rv = rest.get('connected')
    assert isinstance(rv.json['Value'], bool)
    assert rv.json['Value'] is True

    # disconnect
    rv = rest.put('connected', data=dict(Connected=False))

    # confirm PUT worked
    rv = rest.get('connected')
    assert isinstance(rv.json['Value'], bool)
    assert rv.json['Value'] is False
