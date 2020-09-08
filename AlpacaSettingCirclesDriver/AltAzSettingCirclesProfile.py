#
# Store configuration profile for Dave Ek's style setting circles
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
from dataclasses import dataclass

from Profiles import Profile, ProfileSection

class AltAzSettingCirclesProfile(Profile):

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
