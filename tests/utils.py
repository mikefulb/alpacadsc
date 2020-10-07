#
# Utilty functions for test suite
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

from collections import namedtuple
from lxml import html
from ast import literal_eval

from AlpacaDSCDriver import __version__ as AlpacaDSCDriver_Version
from AlpacaDSCDriver.AlpacaDeviceServer import AlpacaDeviceServer
from AlpacaDSCDriver.AltAzSettingCircles import AltAzSettingCircles,  PROFILE_BASENAME
from AlpacaDSCDriver.AltAzSettingCirclesProfile import AltAzSettingCirclesProfile as Profile
from AlpacaDSCDriver.Profiles import find_profiles, set_current_profile, get_current_profile

from consts import *

# create a test profile
def create_test_profile(name='Test'):
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

def mock_encoder_and_read_values(client, mocker, mock_alt, mock_az):
    """

    :param client: Flask test client object created with test_client()
    :type client: FlaskClient
    :param mock_alt: Encoder altitude raw counts to be mocked
    :type mock_alt: int
    :param mock_az: Encoder azimuth raw counts to be mocked
    :type mock_az: int
    :return: Named tuple containing read values.
    :rtype: namedtuple('EncoderReadValues')

    Fields of the namedtupled returned are:
        - enc_alt : Altitude encoder raw counts
        - enc_az : Altitude encoder raw counts
        - sky_alt : Actual altitude in degrees (if synced)
        - sky_az : Actual azimuth in degrees (if synced)
        - ra_deg : Actual RA in degrees (if synced)
        - dec_deg : Actual DEC in degrees (if synced)

    """
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


class REST_Handler:
    def __init__(self, client, base_uri):
        self.client = client
        self.base_uri = base_uri
        self.client_id = 1
        self.transaction_id = 1

    def get(self, action, data=None):
        """
        data can be dict() which will be added as query string for GET action.
        """
        rv = self.client.get(self.base_uri + '/' + action,
                             query_string=data)
        assert rv.status_code == 200
        assert rv.json['ErrorNumber'] == 0
        return rv

    def put(self, action, data=None):
        """
        data can be dict() which will be added as data for PUT action.
        """
        headers = {'content-type': 'application/x-www-form-urlencoded'}
        rv = self.client.put(self.base_uri + '/' + action,
                             headers=headers,
                             data=data)
        assert rv.status_code == 200
        assert rv.json['ErrorNumber'] == 0
        return rv
