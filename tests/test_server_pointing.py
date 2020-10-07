#
# Test Encoders And Synchronization
#
#
# Invocation:  Run from the root directory of AlpacaDSCDriver git checkout:
#              python -m pytest -v tests/
#

import logging
import pytest
from ast import literal_eval
from lxml import html
from collections import namedtuple
from astropy.time import Time
from astropy import units as u
from astropy.coordinates import EarthLocation, SkyCoord

from AlpacaDSCDriver.AlpacaDeviceServer import AlpacaDeviceServer
from AlpacaDSCDriver.AltAzSettingCircles import AltAzSettingCircles

from utils import create_test_profile, REST_Handler

REST_API_URI = '/api/v1/telescope/0'
MONITOR_ENCODER_URL = '/encoders'


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


def test_encoders_endpoint(client, mocker):
    """
    Test '/encoders' endpoint and verify it displays the raw encoders count
    properly.

    """
    # create a profile
    create_test_profile()

    # create handler for sending REST requests
    rest = REST_Handler(client, REST_API_URI)

    # connect
    rv = rest.put('connected', data=dict(Connected=True))

    # confirm PUT worked
    rv = rest.get('connected')
    assert isinstance(rv.json['Value'], bool)
    assert rv.json['Value'] is True

    # test encoder page
    test_enc_alt = 1000
    test_enc_az = 2000
    mocker.patch(
        'AlpacaDSCDriver.EncodersAltAzSimulator.EncodersAltAzSimulator.get_encoder_position',
        return_value=(test_enc_alt, test_enc_az))

    rv = client.get(MONITOR_ENCODER_URL)
    assert b'Alt/Az Setting Circles Driver Monitor Encoders' in rv.data

    # parse encoder values from HTML
    root = html.fromstring(rv.data)
    element = root.get_element_by_id(('Connected'))
    connected = element.text == 'True'
    assert connected is True

    element = root.get_element_by_id(('ALTAZ_Counts'))
    enc_alt, enc_az = literal_eval((element.text))
    assert (enc_alt, enc_az) == (test_enc_alt, test_enc_az)


def test_encoders_sync(client, mocker):
    """
    Test synchronizing driver and alt/az and ra/dec mapping for
    different encoder positions relative to original.
    """

    def mock_encoder_and_read_values(client, mock_alt, mock_az):
        mocker.patch(
            'AlpacaDSCDriver.EncodersAltAzSimulator.EncodersAltAzSimulator.get_encoder_position',
            return_value=(mock_alt, mock_az))

        rv = client.get(MONITOR_ENCODER_URL)
        assert b'Alt/Az Setting Circles Driver Monitor Encoders' in rv.data

        # parse encoder values from HTML
        root = html.fromstring(rv.data)
        element = root.get_element_by_id(('Connected'))
        connected = element.text == 'True'
        assert connected is True

        element = root.get_element_by_id(('ALTAZ_Counts'))
        enc_alt, enc_az = literal_eval((element.text))

        element = root.get_element_by_id(('ALTAZ_Degrees'))
        try:
            sky_alt, sky_az = literal_eval((element.text))
        except TypeError:
            sky_alt, sky_az = None, None

        element = root.get_element_by_id(('RADEC_Degrees'))
        try:
            ra_deg, dec_deg = literal_eval((element.text))
        except TypeError:
            ra_deg, dec_deg = None, None

        tup = namedtuple('EncoderReadValues', ['enc_alt', 'enc_az',
                         'sky_alt', 'sky_az', 'ra_deg', 'dec_deg'])
        return tup(enc_alt, enc_az, sky_alt, sky_az, ra_deg, dec_deg)

    # how close must float value be to be considered the same
    TEST_EPSILON = 0.1

    # create a profile
    test_profile = create_test_profile()

    # setup earth location
    location = EarthLocation(lat=test_profile.location.latitude,
                             lon=test_profile.location.longitude,
                             height=test_profile.location.altitude*u.m)

    # create handler for sending REST requests
    rest = REST_Handler(client, REST_API_URI)

    # connect
    rv = rest.put('connected', data=dict(Connected=True))

    # confirm PUT worked
    rv = rest.get('connected')
    assert isinstance(rv.json['Value'], bool)
    assert rv.json['Value'] is True

    # test encoder page
    test_enc_alt = 1000
    test_enc_az = 1000
    # mocker.patch(
    #     'AlpacaDSCDriver.EncodersAltAzSimulator.EncodersAltAzSimulator.get_encoder_position',
    #     return_value=(test_enc_alt, test_enc_az))

    # rv = client.get(MONITOR_ENCODER_URL)
    # assert b'Alt/Az Setting Circles Driver Monitor Encoders' in rv.data

    # # parse encoder values from HTML
    # root = html.fromstring(rv.data)
    # element = root.get_element_by_id(('Connected'))
    # connected = element.text == 'True'
    # assert connected is True

    # element = root.get_element_by_id(('ALTAZ_Counts'))
    # enc_alt, enc_az = literal_eval((element.text))

    values = mock_encoder_and_read_values(client, test_enc_alt, test_enc_az)
    assert (values.enc_alt, values.enc_az) == (test_enc_alt, test_enc_az)

    #
    # given profile lat/lon and current time pick raw counts for encoders
    # and actual alt/az values in sky.   Using time and location convert actual
    # alt/az to ra/dec to send for synchronize command
    #
    sync_enc_alt = 1000
    sync_enc_az = 1000
    sync_sky_alt = 45.0
    sync_sky_az = 90.0
    mocker.patch(
        'AlpacaDSCDriver.EncodersAltAzSimulator.EncodersAltAzSimulator.get_encoder_position',
        return_value=(sync_enc_alt, sync_enc_az))

    # get ra/dec for sky alt/az chosen
    # create SkyCoord and convert to RA/DEC
    obs_time = Time.now()

    cur_altaz = SkyCoord(alt=sync_sky_alt*u.deg, az=sync_sky_az*u.deg,
                         obstime=obs_time, frame='altaz', location=location)
    cur_radec = cur_altaz.transform_to('icrs')

    # sync
    # we have RA/DEC in decimal degrees, sync expects RA as decimal hours
    # and DEC as decimal degrees so need to convert RA
    rv = rest.put('synctocoordinates', data=dict(RightAscension=cur_radec.ra.hour,
                                                 Declination=cur_radec.dec.degree))

    # # read RA/DEC and ALT/AZ from monitor page
    # rv = client.get(MONITOR_ENCODER_URL)
    # assert b'Alt/Az Setting Circles Driver Monitor Encoders' in rv.data

    # # parse encoder values from HTML
    # root = html.fromstring(rv.data)
    # element = root.get_element_by_id(('Connected'))
    # connected = element.text == 'True'
    # assert connected is True

    # element = root.get_element_by_id(('ALTAZ_Degrees'))
    # act_sky_alt, act_sky_az = literal_eval((element.text))

    # element = root.get_element_by_id(('RADEC_Degrees'))
    # act_ra_deg, act_dec_deg = literal_eval((element.text))

    # test if close enough to true values
    values = mock_encoder_and_read_values(client, sync_enc_alt, sync_enc_az)

    assert abs(values.sky_alt - sync_sky_alt) < TEST_EPSILON
    assert abs(values.sky_az - sync_sky_az) < TEST_EPSILON
    assert abs(values.ra_deg - cur_radec.ra.deg) < TEST_EPSILON
    assert abs(values.dec_deg - cur_radec.dec.deg) < TEST_EPSILON

    # now move the mount in alt/az counts
    delta_alt = 1000
    delta_az = 1000
    mocker.patch(
        'AlpacaDSCDriver.EncodersAltAzSimulator.EncodersAltAzSimulator.get_encoder_position',
        return_value=(sync_enc_alt+delta_alt, sync_enc_az+delta_az))

    # read RA/DEC and ALT/AZ from monitor page
    rv = client.get(MONITOR_ENCODER_URL)
    assert b'Alt/Az Setting Circles Driver Monitor Encoders' in rv.data

    # parse encoder values from HTML
    root = html.fromstring(rv.data)
    element = root.get_element_by_id(('Connected'))
    connected = element.text == 'True'
    assert connected is True

    element = root.get_element_by_id(('ALTAZ_Degrees'))
    act_sky_alt, act_sky_az = literal_eval((element.text))
    print(act_sky_alt, act_sky_az)

    new_alt = (sync_sky_alt+360.0*delta_alt/test_profile.encoders.alt_resolution)
    new_az = (sync_sky_az+360.0*delta_az/test_profile.encoders.az_resolution)
    print(new_alt, new_az)
    assert abs(act_sky_alt - new_alt) < TEST_EPSILON
    assert abs(act_sky_az - new_az) < TEST_EPSILON

    element = root.get_element_by_id(('RADEC_Degrees'))
    act_ra_deg, act_dec_deg = literal_eval((element.text))


