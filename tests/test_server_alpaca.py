#
# Test Alpaca REST API
#
#
# Invocation:  Run from the root directory of AlpacaDSCDriver git checkout:
#              python -m pytest -v tests/
#

import pytest
from AlpacaDSCDriver import __version__ as AlpacaDSCDriver_Version
from AlpacaDSCDriver.AlpacaDeviceServer import AlpacaDeviceServer
from AlpacaDSCDriver.AltAzSettingCircles import AltAzSettingCircles

from consts import REST_API_URI
from utils import create_test_profile, REST_Handler


@pytest.fixture
def client():
    api_server = AlpacaDeviceServer(AltAzSettingCircles())

    # push context so GET/POST will work
    api_server.app.app_context().push()

    with api_server.app.test_client() as client:
        yield client

    # do cleanup here
    pass


@pytest.fixture
def my_fs(fs):
    yield fs


def test_rest_get_basic(client):
    """
    Test Alpaca GET API common to all drivers.
    """

    # get a driver object and compare attributes to those
    # returned by a REST API call
    altaz_driver = AltAzSettingCircles()

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

    # interface version
    rv = rest.get('interfaceversion')
    assert altaz_driver.interface_version == rv.json['Value']

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
