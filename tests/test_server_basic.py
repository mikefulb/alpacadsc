#
# Test Alpaca REST API
#
import sys
import pytest
from pathlib import Path

# FIXME - better way to do this?  Want to be able to run the tests in a
#         checked out source tree
sys.path.append('..')

from AlpacaDSCDriver.AlpacaDeviceServer import AlpacaDeviceServer
from AlpacaDSCDriver.AltAzSettingCircles import AltAzSettingCircles, PROFILE_BASENAME
from AlpacaDSCDriver.Profiles import find_profiles, set_current_profile, get_current_profile
from AlpacaDSCDriver.AltAzSettingCirclesProfile import AltAzSettingCirclesProfile as Profile



# FIXME hard coded assumes running tests with 'tests' as cwd - is this OK?
templates_path = str(Path('../AlpacaDSCDriver/templates/').resolve())



ROOT_URI = '/'
ABOUT_URI = '/about'
GLOBAL_SETUP_URI = '/setup'
MONITOR_ENCODER_URL = '/encoders'
DRIVER_SETUP_URI = '/setup/v1/telescope/0/setup'

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
    fs.add_real_directory(templates_path)
    yield fs

def test_root(client):
    """ Test '/' - should redirect to '/setup/ """
    rv = client.get(ROOT_URI)
    assert b'You should be redirected automatically to target URL: <a href="/setup">/setup</a>' in rv.data

def test_global_setup(client):
    """ Test '/setup' - should return server info page """
    rv = client.get(GLOBAL_SETUP_URI)
    assert b'Alt/Az Setting Circles Alpaca Server Information' in rv.data

def test_driver_setup(client):
    """ Test '/setup/v1/telescope/0/setup' - should return driver setup page """
    rv = client.get(DRIVER_SETUP_URI)
    assert b'Alt/Az Setting Circles Driver Setup' in rv.data

def test_monitor_encoders(client):
    """ Test '/encoders' - should return monitor encoders page """
    rv = client.get(MONITOR_ENCODER_URL)
    assert b'Alt/Az Setting Circles Driver Monitor Encoders' in rv.data

def test_about(client):
    """ Test '/about' - should return about page """
    rv = client.get(ABOUT_URI)
    assert b'Alt/Az Setting Circles Alpaca - About' in rv.data

def test_new_profile(client, my_fs):
    """ Test creating a new profile """
    rv = client.post(DRIVER_SETUP_URI, data = dict(
            form_id='new_profile_form',
            new_profile_id='NewProfile'))

    assert b'Profile NewProfile created and set as current.' in rv.data

    config_path = Path.home() / '.config' / 'AlpacaDSCDriver' / 'NewProfile.yaml'
    assert config_path.exists()

    profiles = find_profiles(PROFILE_BASENAME)
    assert 'NewProfile.yaml' in profiles

    assert get_current_profile(PROFILE_BASENAME) == 'NewProfile'
    profile = Profile(PROFILE_BASENAME, 'NewProfile.yaml')
    profile.read()

    for k in ['location', 'encoders']:
        assert k in profile._to_dict()

    for k in ['altitude', 'longitude', 'latitude', 'obsname']:
        assert k in profile._to_dict()['location']

    for k in ['serial_speed', 'serial_port', 'driver', 'alt_reverse',
              'alt_resolution', 'az_reverse', 'az_resolution']:
        assert k in profile._to_dict()['encoders']
