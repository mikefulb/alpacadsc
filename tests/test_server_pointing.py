#
# Test Encoders And Synchronization
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
from astropy.time import Time
from astropy import units as u
from astropy.coordinates import EarthLocation, SkyCoord

from consts import REST_API_URI

# we must import pytest fixtures client and my_fs for the test cases
# below to run properly.  Pytest will inject them into the argument
# list for the test cases.  It is normal for a python linter to
# report they are unused.
from utils import create_test_profile, REST_Handler, client, my_fs
from utils import mock_encoder_and_read_values


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
    values = mock_encoder_and_read_values(client, mocker, test_enc_alt, test_enc_az)
    assert (values.enc_alt, values.enc_az) == (test_enc_alt, test_enc_az)


def test_encoders_sync(client, mocker):
    """
    Test synchronizing driver and alt/az and ra/dec mapping for
    different encoder positions relative to original.
    """

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

    # test encoder page with a selected encoder alt/az raw counts
    test_enc_alt = 1000
    test_enc_az = 1000

    values = mock_encoder_and_read_values(client, mocker, test_enc_alt, test_enc_az)
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

    # test if close enough to true values
    values = mock_encoder_and_read_values(client, mocker, sync_enc_alt, sync_enc_az)

    assert abs(values.sky_alt - sync_sky_alt) < TEST_EPSILON
    assert abs(values.sky_az - sync_sky_az) < TEST_EPSILON
    assert abs(values.ra_deg - cur_radec.ra.deg) < TEST_EPSILON
    assert abs(values.dec_deg - cur_radec.dec.deg) < TEST_EPSILON

    # now move the mount in raw alt/az counts and read change in pos
    delta_enc_alt = 1000
    delta_enc_az = 1000
    values = mock_encoder_and_read_values(client, mocker,
                                          sync_enc_alt+delta_enc_alt,
                                          sync_enc_az+delta_enc_az)

    # compute expected change in sky alt/az in degrees by scaling raw
    # counts using resolution of encoders from test profile
    alt_res = test_profile.encoders.alt_resolution
    az_res = test_profile.encoders.alt_resolution
    delta_sky_alt = 360.0*delta_enc_alt/alt_res
    delta_sky_az = 360.0*delta_enc_az/az_res
    pred_sky_alt = sync_sky_alt + delta_sky_alt
    pred_sky_az = sync_sky_az + delta_sky_az

    # compare predicted to actual read values
    assert abs(values.sky_alt - pred_sky_alt) < TEST_EPSILON
    assert abs(values.sky_az - pred_sky_az) < TEST_EPSILON

    # calculate the ra/dec corresponding to the new alt/az
    obs_time = Time.now()
    pred_altaz = SkyCoord(alt=pred_sky_alt*u.deg, az=pred_sky_az*u.deg,
                          obstime=obs_time, frame='altaz', location=location)
    pred_radec = pred_altaz.transform_to('icrs')
    assert abs(values.ra_deg - pred_radec.ra.deg) < TEST_EPSILON
    assert abs(values.dec_deg - pred_radec.dec.deg) < TEST_EPSILON
