#
# store observatory profiles
#
from dataclasses import dataclass

from Profiles import Profile, ProfileSection

class DaveEkSettingCirclesProfile(Profile):

    @dataclass
    class Location(ProfileSection):
        _sectionname : str = 'location'
        #: Name of observing location
        obsname : str = None
        #: Latitude in degrees
        latitude : float = None
        #: Longitude in degrees
        longitude : float = None
        #: Altitude in meters
        altitude : float = None

    @dataclass
    class Encoders(ProfileSection):
        _sectionname : str = 'encoders'
        # serial port
        serial_port : str = None
        # speed
        serial_speed : int = 9600
        #: Alt axis resolution
        alt_resolution : int = None
        #: AZ axis resolution
        az_resolution : int = None
        #: Reverse ALT?
        alt_reverse : bool = False
        #: Reverse AZ?
        az_reverse : bool = False

    def __init__(self, reldir, name=None):
        super().__init__(reldir, name)

        self.add_section(self.Location)
        self.add_section(self.Encoders)

    def read(self):
        # load in profile
        super().read()

    def _data_complete(self):
        l = [self.location.obsname,
             self.location.latitude,
             self.location.longitude,
             self.location.altitudee]
        return (l.count(None) == 0)

    def __getattr__(self, attr):
        return super().__getattribute__(attr)

    def __setattr__(self, attr, value):
        super().__setattr__(attr, value)
