#
# Test Flask App Basic Functionality
#
#
# Invocation:  Run from the root directory of AlpacaDSCDriver git checkout:
#              python -m pytest -v tests/
#
#import sys
import pytest
from pathlib import Path

# FIXME - better way to do this?  Want to be able to run the tests in a
#         checked out source tree
#sys.path.append('..')

from AlpacaDSCDriver.AlpacaDeviceServer import AlpacaDeviceServer
from AlpacaDSCDriver.AltAzSettingCircles import AltAzSettingCircles, PROFILE_BASENAME
from AlpacaDSCDriver.Profiles import find_profiles, set_current_profile, get_current_profile
from AlpacaDSCDriver.AltAzSettingCirclesProfile import AltAzSettingCirclesProfile as Profile

# assume templates are in AlpacaDSCDriver module
# import a module and find __file__
import AlpacaDSCDriver.StartService
templates_path = Path(AlpacaDSCDriver.StartService.__file__).resolve().parent

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

    #print(api_server.app.config)

    with api_server.app.test_client() as client:
        yield client

    # do cleanup here
    pass

@pytest.fixture
def my_fs(fs):
    fs.add_real_directory(templates_path)
    yield fs

#
# Test Endpoints
#
# This section will go through and exercise the main endpoints of the
# Alpaca driver web page.  These tests verify the pages load and contain
# a string which is expected but do not test the functionality or
# integrity of the entire page that loads.
#
# These tests will verify the URL rules were setup properly for the
# Flask app and that the templates were located and rendered.
#
def test_root(client):
    """ Test '/' - should redirect to '/setup/ """
    rv = client.get(ROOT_URI)
    assert b'You should be redirected automatically ' \
           b'to target URL: <a href="/setup">/setup</a>' in rv.data

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

#
# Test Web Site Profile Functionality
#
# This section will test that the '/setup' POST endpoint functionality
# for profile manipulation work.  All created profile files will be
# on a pyfakefs filesystem but the AlpacaDSDDriver templates and
# static content are punched through to the real filesystem so the
# pages will still render properly.
#

# Test: New Profile POST
#
# Test consists of:
#
#  - Using POST to simulate the request when the 'New Profile' button
#     is pressed on the driver setup page.
#  - Verify the profile file is created in the fake filesystem
#  - Verify the new profile shows up via the find_profiles() API call
#  - Verify the current profile is set to the new profile using the
#     get_current_profile() API call
#  - Load the new profile and verify it has the correct entries
def test_new_profile(client, my_fs, name='NewProfile'):
    """ Test creating a new profile """
    rv = client.post(DRIVER_SETUP_URI, data=dict(
                     form_id='new_profile_form',
                     new_profile_id=name))

    assert b'Profile ' + name.encode('utf-8') + \
           b' created and set as current.' in rv.data

    config_path = Path.home() / '.config' / 'AlpacaDSCDriver' / f'{name}.yaml'
    assert config_path.exists()

    profiles = find_profiles(PROFILE_BASENAME)
    assert f'{name}.yaml' in profiles

    assert get_current_profile(PROFILE_BASENAME) == name
    profile = Profile(PROFILE_BASENAME, f'{name}.yaml')
    profile.read()

    for k in ['location', 'encoders']:
        assert k in profile._to_dict()

    for k in ['altitude', 'longitude', 'latitude', 'obsname']:
        assert k in profile._to_dict()['location']

    for k in ['serial_speed', 'serial_port', 'driver', 'alt_reverse',
              'alt_resolution', 'az_reverse', 'az_resolution']:
        assert k in profile._to_dict()['encoders']

#
# Test: Change Profile Page Render/Select Profile POST
#
# Test consists of:
#  - Create 2 new profiles - Test1 and Test2
#  - Verify Test2 is current profile
#  - Request change profile page and verify
#  - Call selected profile POST to switch profile to Test1
#  - Verify Test1 is current profile
def test_change_select_profile(client, my_fs):
    test_new_profile(client, my_fs, name='Test1')
    test_new_profile(client, my_fs, name='Test2')
    assert get_current_profile(PROFILE_BASENAME) == 'Test2'

    rv = client.post(DRIVER_SETUP_URI, data=dict(
                     form_id='change_profile_form'))

    assert b'Select the new profile from the options below' in rv.data
    assert b'id="Test1" name="profile_choice" value="Test1"' in rv.data
    assert b'id="Test2" name="profile_choice" value="Test2"' in rv.data

    rv = client.post(DRIVER_SETUP_URI, data=dict(
                     form_id='selected_profile_form',
                     profile_choice='Test1'))

    assert b'The profile Test1 is now the current profile.' in rv.data

    assert get_current_profile(PROFILE_BASENAME) == 'Test1'

#
# Test: Change Encoder Settings
#
# Test consists of:
#  - Create new profiles Test1
#  - Change encoder values via POST
#  - Load driver setup page and verify new encoder values
def test_change_encoder_settings(client, my_fs):
    test_new_profile(client, my_fs, name='Test1')

    encoder_dict = dict(encoder_driver='DaveEk',
                        serial_port='/dev/ttyUSB0',
                        serial_speed=9600,
                        alt_resolution=10000,
                        az_resolution=8000,
                        alt_reverse=False,
                        az_reverse=True)

    form_dict = dict(form_id='encoder_modify_form', profile_id='Test1')
    post_dict = {**encoder_dict, **form_dict}
    rv = client.post(DRIVER_SETUP_URI, data=post_dict)

    assert b'Profile Test1 updated.' in rv.data

    profile = Profile(PROFILE_BASENAME, 'Test1.yaml')
    profile.read()

    # compare read dict to requested dict
    # have to change 'driver' key to 'encoder_driver' (if it exists)
    # due to difference in how these are defined in profile class
    # and HTML form
    new_encoder_dict = profile._to_dict()['encoders']
    assert 'driver' in new_encoder_dict
    new_encoder_dict['encoder_driver'] = new_encoder_dict['driver']
    del new_encoder_dict['driver']

    assert new_encoder_dict == encoder_dict

#
# Test: Change Location Settings
#
# Test consists of:
#  - Create new profiles Test1
#  - Change location values via POST
#  - Load driver setup page and verify new location values
def test_change_location_settings(client, my_fs):
    test_new_profile(client, my_fs, name='Test1')

    location_dict = dict(name='Observatory',
                         longitude=123.0,
                         latitude=20.0,
                         altitude=1000.0)
    form_dict = dict(form_id='location_modify_form', profile_id='Test1')
    post_dict = {**location_dict, **form_dict}
    rv = client.post(DRIVER_SETUP_URI, data=post_dict)

    assert b'Profile Test1 updated.' in rv.data

    profile = Profile(PROFILE_BASENAME, 'Test1.yaml')
    profile.read()

    # compare read dict to requested dict
    # have to change 'obsname' key to 'name' (if it exists)
    # due to difference in how these are defined in profile class
    # and HTML form
    new_location_dict = profile._to_dict()['location']
    assert 'obsname' in new_location_dict
    new_location_dict['name'] = new_location_dict['obsname']
    del new_location_dict['obsname']
    assert new_location_dict == location_dict
