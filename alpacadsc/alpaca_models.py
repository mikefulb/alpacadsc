#
# Alpaca driver data model
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

import logging
import importlib
import inspect
import pkgutil
from collections import namedtuple

from astropy.coordinates import EarthLocation, AltAz, SkyCoord
from astropy.time import Time
from astropy import units as u

# import so we can walk all encoder plugins distributed with package
import alpacadsc

# get version
from . import __version__ as ALPACADSC_VERSION

from .baseencoders import EncodersBase
from .profiles import set_current_profile, get_current_profile
from .altaz_dsc_profile import AltAzSettingCirclesProfile as Profile
from .alpaca_controller import ALPACA_ALIGNMENT_ALTAZ


# define named tuple for representing loaded encoders plugins
Plugin = namedtuple('Plugin', ['name', 'moduleref', 'classref'])

# base name used for profile storage
PROFILE_BASENAME = "alpacadsc"


class AlpacaBaseModel:
    def __init__(self):
        self.connected = False
        self.interfaceversion = 0


class AlpacaAltAzTelescopeModel(AlpacaBaseModel):
    """
    Driver for Alt/Az setting circles
    """

    def __init__(self, use_profile=None):

        super().__init__()

        # driver info
        self.driverversion = ALPACADSC_VERSION
        self.description = 'Alt/Az Setting Circles'
        self.driverinfo = self.description + f' V. {self.driverversion}'
        self.name = 'AltAzSettingCircles'
        # self.supported_actions = [] # FIXME NOT NEEDED?

        # configuration profile
        self.profile = None

        # alt/az
        self.alignmentmode = ALPACA_ALIGNMENT_ALTAZ
        self.aperturearea = 0
        self.aperturediameter = 0
        self.canfindhome = False
        self.canpark = False
        self.canpulseguide = False
        self.cansetpark = False
        self.cansetpierside = False
        self.cansetrightascensionrate = False
        self.cansettracking = False
        self.canslew = False
        self.canslewaltaz = False
        self.canslewaltazasync = False
        self.canslewasync = False
        self.cansync = True
        self.cansyncaltaz = True
        self.doesrefraction = False
        self.equatorialsystem = 'J2000'
        self.focallength = 0
        self.guideratedeclination = 0.0
        self.guideraterightascension = 0.0
        self.siteelevation = 0
        self.sitelatitude = 0
        self.sitelongitude = 0
        self.slewsettletime = 0
        self.axisrates = []
        self.canmoveaxis = False

        self.sideofpier = 0
        self.sideraltime = 0
        self.slewing = False
        self.isslewing = False
        self.ispulseguiding = False
        self.athome = False
        self.atpark = False
        self.targetdeclination = 0
        self.targetrightascension = 0
        self.tracking = False
        self.trackingrate = 0.0
        self.utcdate = 0
        self.destinationsideofpier = 0

        self.encoders = None

        self.enc_alt0 = None
        self.enc_az0 = None
        self.syncpos_alt = None
        self.syncpos_az = None

        self.find_encoders_plugins()

        for p in self.encoders_plugins:
            logging.info(f'Loaded encoder plugin {p.name}: {p.classref}.')

    def __getattr__(self, attr):
        """
        Implement __getattr__ to generate 'alitude', 'azimuth',
        'right_ascension' and 'declination' attributes on the fly using
        the latest telescope synchronizaiton.

        """

        if attr in ['altitude', 'azimuth']:
            altaz = self.get_current_altaz()
            if altaz is not None:
                cur_alt, cur_az = altaz
                if attr == 'altitude':
                    return cur_alt
                elif attr == 'azimuth':
                    return cur_az
            else:
                raise ValueError
        elif attr in ['rightascension', 'declination']:
            radec = self.get_current_radec()
            if radec is not None:
                if attr == 'rightascension':
                    return radec.ra.hour
                elif attr == 'declination':
                    return radec.dec.degree
            else:
                raise ValueError
        else:
            return super().__getattribute__(attr)

    def find_encoders_plugins(self):
        """
        Searches for encoders drivers.

        Drivers will have a name in the format "encoders_<drivername>"
        and are located in the alpacadsc package, an example being
        "encoders_altaz_simulator"

        The path containing the alpacadsc package is scanned for
        modules matching this pattern.  Then for each module it
        is inspected to determine if it is an encoder driver.  The
        signature for this is if the module contains a class that
        is derived from the EncodersBase class.

        The result will be to add an attribute to the object called
        "encoders_plugins" which is a list of Plugins namedtuples which
        contains the human readable name of the driver as well as
        a reference to the important module and the class containing
        the encoders driver.
        """

        self.encoders_plugins = []

        plugins = {
            name: importlib.import_module(f'alpacadsc.{name}')
            for finder, name, ipkg
            in pkgutil.iter_modules(alpacadsc.__path__)
            if name.startswith('encoders_')}

        for k, v in plugins.items():
            for _, c in inspect.getmembers(v, inspect.isclass):
                if issubclass(c, EncodersBase) and c is not EncodersBase:
                    self.encoders_plugins.append(Plugin(c().name(), v, c))

    def load_profile(self, try_profile=None):
        """
        Load a configuration profile.  Will load the current active profile
        or if a profile name is provided it will be attempted first.

        :param try_profile: Optional profile name (without '.yaml' extension), defaults to None
        :type try_profile: str
        :return: Tuple with loaded Profile object and name of profile loaded
        :rtype: tuple of (Profile, str)

        """

        # load profile
        # if profile was specified then try using it
        # if no suggestion for profile try to find last one used
        if try_profile is None:
            try_profile = get_current_profile(PROFILE_BASENAME)
            if try_profile is not None:
                logging.info(f'Using current profile {try_profile}')

        if try_profile is None:
            logging.error('Must specify a valid profile')
            return None, None

        logging.debug(f'load_profile: try_profile = {try_profile}')

        profile = Profile(PROFILE_BASENAME, try_profile + '.yaml')
        profile.read()

        return profile, try_profile

    def load_current_profile(self):
        """
        Attempts to load the current active profile.

        :return: Success code - True for success
        :rtype: bool

        """

        profile, profile_name = self.load_profile()
        logging.info(f'load_current_profile: {profile} {profile_name}')

        if profile is None or profile_name is None:
            logging.error('load_current_profile: Failed to load profile!')
            return False

        # validate location values
        error_list = []
        if not isinstance(profile.location.latitude, float):
            error_list.append('Latitude must be a float')
        if not isinstance(profile.location.longitude, float):
            error_list.append('Longitude must be a float')
        if not isinstance(profile.location.altitude, float):
            error_list.append('Altitude must be a float')

        if len(error_list) > 0:
            logging.error(f'Error with profile {profile_name}: {error_list}')
            return False

        self.profile = profile
        self.profile_name = profile_name
        logging.info(f'Loaded profile {self.profile_name} = {self.profile}')

        # set as current
        set_current_profile(PROFILE_BASENAME, self.profile_name)

        # set location
        self.earth_location = EarthLocation(lat=self.profile.location.latitude,
                                            lon=self.profile.location.longitude,
                                            height=self.profile.location.altitude*u.m)

        return True

    def unload_current_profile(self):
        """
        Clear any profile information from object.
        """
        self.profile = None
        self.profile_name = None

    def load_encoders(self, encoders_profile):
        """
        Load encoders and connect.

        :param encoders_profile: Dictionary containing encoder parameters

        :returns: True on success, False if fails.
        :rtype: bool
        """

        # FIXME hard coded mapping for now need to perhaps make a way to
        #       dynamically build list of available encoder drivers
        encoder_drv = encoders_profile.get('driver')
        logging.debug(f'encoder_drv = {encoder_drv}')
        if encoder_drv is None:
            logging.error('No encoder driver specified - cannot load encoder driver')
            # FIXME Raise exception?
            return False

        # scan encoders pluins for driver matching requested
        encoder_class = None
        for n, m, c in self.encoders_plugins:
            logging.debug(f'scanning encoders plugin {n} matching {encoder_drv}.')
            if n == encoder_drv:
                logging.info(f'Loading encoders driver {n}.')
                encoder_class = c
                break
        else:
            logging.error(f'Requested encoders driver {encoder_drv} '
                          f'could not be found!.')
            self.encoders = None
            return False

        self.encoders = encoder_class(
                                res_alt=encoders_profile.alt_resolution,
                                res_az=encoders_profile.az_resolution,
                                reverse_alt=encoders_profile.alt_reverse,
                                reverse_az=encoders_profile.az_reverse)
        if not self.encoders.connect(encoders_profile.serial_port,
                                     speed=encoders_profile.serial_speed):
            self.encoders = None
            logging.info('Failed to connect to encoders on port '
                         f'{encoders_profile.serial_port}')
            return False

        logging.info(f'Connected to encoders.')
        return True

    # FIXME connect/disconnect does not distiguish between clients - is this
    #       even addressed by the Alpaca standard?  Need to investigate.
    def connect(self):
        """
        Attempts to connect to device

        :return: Success code - True means success.
        :rtype: bool
        """

        # load operating profile
        if not self.load_current_profile():
            logging.error('Unable to load profile - cannot connect!')
            # FIXME Raise exception?
            return False

        # load encoders
        if not self.load_encoders(self.profile.encoders):
            logging.error('Unable to load encoders driver - cannot connect!')
            # FIXME Raise exception?
            return False

        self.connected = True
        return True

    def disconnect(self):
        """
        Disconnects from device

        :return: Success code - True means success.
        :rtype: bool
        """

        if not self.connected:
            logging.error('disconnect called but not connected!')
            return False

        # disconnect from encoders
        self.encoders.disconnect()

        # clear out profile
        self.unload_current_profile()

        self.connected = False
        return True

    def convert_encoder_position_to_altaz(self, enc_alt, enc_az):
        """
        Converts from raw encoder values to sky alt/az values.

        *note* Driver must be synchronized or value will be meaningless.

        :param enc_alt: Raw encoder alitude value
        :param enc_az: Raw encoder azimuth value

        :returns:
            (float, float) Sky altitude/azimuth positions or None if device is
                           not synchronized yet
        """
        if None in [self.enc_alt0, self.enc_az0, self.syncpos_alt, self.syncpos_az]:
            logging.error('convert_encoder_position_to_altaz: No transformation setup!')
            return None

        enc_alt_res = self.encoders.res_alt
        enc_az_res = self.encoders.res_az

        enc_alt_off = enc_alt - self.enc_alt0
        enc_az_off = enc_az - self.enc_az0

        logging.debug(f'off alt/az = {enc_alt_off} {enc_az_off} steps')

        enc_alt_off_deg = 360*enc_alt_off/enc_alt_res
        enc_az_off_deg = 360*enc_az_off/enc_az_res

        logging.debug(f'off alt/az = {enc_alt_off_deg} {enc_az_off_deg} degrees')

        if self.encoders.reverse_alt:
            alt_mult = -1
        else:
            alt_mult = 1

        if self.encoders.reverse_az:
            az_mult = -1
        else:
            az_mult = 1

        cur_alt = self.syncpos_alt + alt_mult*enc_alt_off_deg

        if cur_alt > 90:
            logging.warning(f'get_current_radec: cur_alt = {cur_alt} > 90 deg so clipping!')
            cur_alt = 90
        elif cur_alt < -90:
            logging.warning(f'get_current_radec: cur_alt = {cur_alt} < -90 deg so clipping!')
            cur_alt = -90

        cur_az = self.syncpos_az + az_mult*enc_az_off_deg

        logging.debug(f'cur alt/az = {cur_alt} {cur_az} steps')

        return cur_alt, cur_az

    def get_current_altaz(self):
        """
        Returns current RA/ALT/AZ of where device is pointing.

        *note* Driver must be synchronized or value will be meaningless.

        :returns:
            (float, float) RA/DEC position or None if device is
                           not synchronized yet
        """
        if None in [self.enc_alt0, self.enc_az0, self.syncpos_alt, self.syncpos_az]:
            logging.error('get_current_altaz: No transformation setup!')
            return None

        # get encoders
        enc_pos = self.encoders.get_encoder_position()
        if enc_pos is None:
            logging.error('get_current_altaz: Unable to read encoder position!')
            return None

        enc_alt, enc_az = enc_pos

        skyaltaz = self.convert_encoder_position_to_altaz(enc_alt, enc_az)

        if skyaltaz is None:
            logging.error('get_current_altaz: Unable to convert encoder position!')
            return None

        logging.debug('current alt/az = {skyaltaz}')
        return skyaltaz

    def get_current_radec(self):
        """
        Returns current RA/DEC of where device is pointing.

        *note* Driver must be synchronized or value will be meaningless.

        :returns:
            (float, float) RA/DEC position or None if device is
                           not synchronized yet
        """

        altaz = self.get_current_altaz()
        if not altaz:
            logging.error('get_current_radec: Unable to get alt/az position!')
            return None

        sky_alt, sky_az = altaz

        # create SkyCoord and convert to RA/DEC
        obs_time = Time.now()

        newaltaz = SkyCoord(alt=sky_alt*u.deg, az=sky_az*u.deg, obstime=obs_time,
                            frame='altaz', location=self.earth_location)

        cur_radec = newaltaz.transform_to('icrs')
        logging.debug('current ra/dec = {cur_radec}')

        return cur_radec

    def sync_to_coordinates(self, ra, dec):
        """
        Synchronize device to RA/DEC position.

        :param ra: RA position in decimal hours
        :param dec: DEC position in decimal degrees

        :returns:
            (bool) Return code True = success False = failure
        """

        # find alt/az matching ra/dec and setup transfortmation from encoders
        # alt/az values from this
        logging.debug(f'syncing ra:{ra} dec:{dec}')

        obs_time = Time.now()

        aa = AltAz(location=self.earth_location, obstime=obs_time)

        # convert RA to degrees
        radec = SkyCoord(ra*15, dec, unit='deg', frame='icrs')

        sync_altaz = radec.transform_to(aa)

        logging.debug(f'sync alt/az = {sync_altaz.alt}/{sync_altaz.az}')

        # get encoders
        enc_pos = self.encoders.get_encoder_position()
        logging.debug(f'enc_pos ALT/AZ = {enc_pos}')

        if enc_pos is None:
            return False

        enc_alt, enc_az = enc_pos

        self.enc_alt0 = enc_alt
        self.enc_az0 = enc_az
        self.syncpos_alt = sync_altaz.alt.degree
        self.syncpos_az = sync_altaz.az.degree

        return True
