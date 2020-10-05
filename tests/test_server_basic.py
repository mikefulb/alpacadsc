#
# Test Alpaca REST API
#
import sys
import pytest

# FIXME - better way to do this?  Want to be able to run the tests in a
#         checked out source tree
sys.path.append('..')

from AlpacaDSCDriver.AlpacaDeviceServer import AlpacaDeviceServer
from AlpacaDSCDriver.AltAzSettingCircles import AltAzSettingCircles

# create global variable for server instance
# FIXME This doesn't seem right - do I need a simulator for the device instead?
api_server = AlpacaDeviceServer(AltAzSettingCircles())


@pytest.fixture
def client():
    global api_server

    with api_server.app.test_client() as client:
        yield client

    # do cleanup here
    pass


def test_root(client):
    """ Test '/' - should redirect to '/setup/ """
    rv = client.get('/')
    assert b'You should be redirected automatically to target URL: <a href="/setup">/setup</a>' in rv.data

def test_global_setup(client):
    """ Test '/setup' - should return server info page """
    rv = client.get('/setup')
    assert b'Alt/Az Setting Circles Alpaca Server Information' in rv.data

def test_driver_setup(client):
    """ Test '/setup/v1/telescope/0/setup' - should return driver setup page """
    rv = client.get('/setup/v1/telescope/0/setup')
    assert b'Alt/Az Setting Circles Driver Setup' in rv.data

def test_monitor_encoders(client):
    """ Test '/encoders' - should return monitor encoders page """
    rv = client.get('/encoders')
    assert b'Alt/Az Setting Circles Driver Monitor Encoders' in rv.data

def test_about(client):
    """ Test '/encoders' - should return monitor encoders page """
    rv = client.get('/about')
    assert b'Alt/Az Setting Circles Alpaca - About' in rv.data


