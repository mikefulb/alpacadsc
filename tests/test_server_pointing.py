#
# Test Encoders And Synchronization
#
#
# Invocation:  Run from the root directory of AlpacaDSCDriver git checkout:
#              python -m pytest -v tests/
#

import pytest
import logging

logging.basicConfig(level=logging.DEBUG)
mylogger = logging.getLogger()

from AlpacaDSCDriver import __version__ as AlpacaDSCDriver_Version
from AlpacaDSCDriver.AlpacaDeviceServer import AlpacaDeviceServer
from AlpacaDSCDriver.AltAzSettingCircles import AltAzSettingCircles,  PROFILE_BASENAME
from AlpacaDSCDriver.AltAzSettingCirclesProfile import AltAzSettingCirclesProfile as Profile
from AlpacaDSCDriver.Profiles import find_profiles, set_current_profile, get_current_profile

REST_API_URI = '/api/v1/telescope/0'
ENCODERS_URI = '/encoders'

@pytest.fixture
def client():
    api_server = AlpacaDeviceServer(AltAzSettingCircles())

    # push context so GET/POST will work
    api_server.app.app_context().push()

    #print(api_server.app.config)

    with api_server.app.test_client() as client:
        yield client

    # do cleanup here
    pass

@pytest.fixture
def my_fs(fs):
    yield fs


# create a test profile
def _create_test_profile(name='Test'):
    profile = Profile(PROFILE_BASENAME, f'{name}.yaml')
    profile.location.longitude = 135.0
    profile.location.latitude = 45.0
    profile.location.altitude = 100.0
    profile.location.obsname = 'Test Location'
    profile.encoders.driver = 'Simulator'
    profile.encoders.serial_port = '/dev/ttyUSB0'
    profile.encoders.serial_speed = 9600
    profile.encoders.alt_resolution = 10000
    profile.encoders.az_resolution = 10000
    profile.encoders.alt_reverse = False
    profile.encoders.az_reverse = False
    profile.write()

    set_current_profile(PROFILE_BASENAME, name)

    return profile



#
# Test '/encoders' endpoint
#
def test_encoders_endpoint(client):

    # get a driver object and compare attributes to those
    # returned by a REST API call
    altaz_driver = AltAzSettingCircles()

    trans_id = 0
    get_dict = dict(ClientID=1,
                    ClientTransactionID=trans_id)

    # description
    rv = client.get(REST_API_URI + '/description', query_string=get_dict)
    assert altaz_driver.description == rv.json['Value']

    get_dict['ClientTransactionID'] += 1

    # name
    rv = client.get(REST_API_URI + '/name', query_string=get_dict)
    assert altaz_driver.name == rv.json['Value']

    get_dict['ClientTransactionID'] += 1

    # driverinfo
    rv = client.get(REST_API_URI + '/driverinfo', query_string=get_dict)
    assert altaz_driver.driverinfo == rv.json['Value']

    get_dict['ClientTransactionID'] += 1

    # driver version
    rv = client.get(REST_API_URI + '/driverversion', query_string=get_dict)
    assert f'{AlpacaDSCDriver_Version}' == rv.json['Value']

    get_dict['ClientTransactionID'] += 1

    # interface version
    rv = client.get(REST_API_URI + '/interfaceversion', query_string=get_dict)
    assert altaz_driver.interface_version == rv.json['Value']

    get_dict['ClientTransactionID'] += 1

    # connected
    rv = client.get(REST_API_URI + '/connected', query_string=get_dict)
    assert rv.status_code == 200
    assert isinstance(rv.json['Value'], bool)





#
# Test connected PUT call
#
def test_rest_connected(client, my_fs):


    # create a profile
    _create_test_profile()

    trans_id = 0

    # get current state
    get_dict = dict(ClientID=1,
                    ClientTransactionID=trans_id)
    trans_id += 1
    rv = client.get(REST_API_URI + '/connected', query_string=get_dict)
    assert rv.status_code == 200
    assert rv.json['ErrorNumber'] == 0
    assert isinstance(rv.json['Value'], bool)
    assert rv.json['Value'] is False

    # connect
    put_dict = dict(Connected=True,
                    ClientID=1,
                    ClientTransactionID=trans_id)
    trans_id += 1

    # connect
    headers = {'content-type': 'application/x-www-form-urlencoded'}
    rv = client.put(REST_API_URI + '/connected', data=put_dict,
                    headers=headers)
    assert rv.status_code == 200
    assert rv.json['ErrorNumber'] == 0

    # confirm PUT worked
    get_dict = dict(ClientID=1,
                    ClientTransactionID=trans_id)
    trans_id += 1
    rv = client.get(REST_API_URI + '/connected', query_string=get_dict)
    assert rv.status_code == 200
    assert rv.json['ErrorNumber'] == 0
    assert isinstance(rv.json['Value'], bool)
    assert rv.json['Value'] is True

    # disconnect
    put_dict = dict(Connected=False,
                    ClientID=1,
                    ClientTransactionID=trans_id)
    trans_id += 1

    # connect
    headers = {'content-type': 'application/x-www-form-urlencoded'}
    rv = client.put(REST_API_URI + '/connected', data=put_dict,
                    headers=headers)
    assert rv.status_code == 200
    assert rv.json['ErrorNumber'] == 0

    # confirm PUT worked
    get_dict = dict(ClientID=1,
                    ClientTransactionID=trans_id)
    trans_id += 1
    rv = client.get(REST_API_URI + '/connected', query_string=get_dict)
    assert rv.status_code == 200
    assert rv.json['ErrorNumber'] == 0
    assert isinstance(rv.json['Value'], bool)
    assert rv.json['Value'] == False
