#
# Utilty functions for test suite
#


from AlpacaDSCDriver import __version__ as AlpacaDSCDriver_Version
from AlpacaDSCDriver.AlpacaDeviceServer import AlpacaDeviceServer
from AlpacaDSCDriver.AltAzSettingCircles import AltAzSettingCircles,  PROFILE_BASENAME
from AlpacaDSCDriver.AltAzSettingCirclesProfile import AltAzSettingCirclesProfile as Profile
from AlpacaDSCDriver.Profiles import find_profiles, set_current_profile, get_current_profile


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
