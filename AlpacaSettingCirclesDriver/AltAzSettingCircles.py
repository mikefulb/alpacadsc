#
# Device driver for Dave Ek's style setting circles
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


import logging
from astropy.coordinates import EarthLocation, AltAz, SkyCoord
from astropy.time import Time
from astropy import units as u
from AlpacaBaseDevice import AlpacaBaseDevice
from AlpacaBaseDevice import ALPACA_ALIGNMENT_ALTAZ
from AlpacaBaseDevice import ALPACA_ERROR_STRINGS
from AlpacaBaseDevice import ALPACA_ERROR_NOTIMPLEMENTED

class DaveEkSettingCircles(AlpacaBaseDevice):
    """
    Driver for Dave Ek's style setting circles
    """
    def __init__(self, encoders):
        """
        Initialize driver object.

        :param encoders: Encoder object used to communicate with encoders
        """
        super().__init__()

        self.driver_version = 0.1
        self.description = 'Dave Ek Setting Cirles'
        self.driverinfo = self.description + f' V. {self.driver_version}'
        self.name = 'DaveEkSettingCircles'
        self.supported_actions = []

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

        # these need to be handled dynamically
        self.azimuth = 0
        self.altitude = 0
        self.declination = 0
        self.rightascension = 0
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

        # used for setting circle transforms
        #self.earth_location =None

        # shouldnt hard code!
        self.earth_location = EarthLocation(lat='35d48m', lon='-78d48m', height=100*u.m)

        # FIXME encoders should be part of class??
        self.encoders = encoders

        self.enc_alt0 = None
        self.enc_az0 = None
        self.syncpos_alt = None
        self.syncpos_az = None



    # handle device specific actions or pass to base
    def get_action_handler(self, action):
        """
        Handle get actions.

        :param action: Action URI.
        :type action: str

        :returns:
          (dict) For requested action return dict with:

                'Value': return value for get request
                'ErrorNumber': error result for request
                'ErrorString': string corresponding to error number
        """
        #logging.debug(f'TestTelescopeDevice::get_action_handler(): action = {action}')
        resp = {}
        resp['ErrorNumber'] = 0
        resp['ErrorString'] = ''

        if action in ['alignmentmode', 'altitude', 'aperturearea',
                      'aperturediameter', 'athome',  'atpark',  'azimuth',
                      'canfindhome', 'canpark', 'canpulseguide',
                      'cansetdeclinationrate', 'cansetguiderates', 'cansetpark',
                      'cansetpierside', 'cansetrightascensionrate',
                      'cansettracking', 'canslew', 'canslewaltaz',
                      'canslewaltazasync', 'canslewasync', 'cansync',
                      'cansyncaltaz', 'doesrefraction',
                      'equatorialsystem', 'focallength',
                      'guideratedeclination', 'guideraterightascension',
                      'ispulseguiding', 'sideofpier',
                      'sideraltime', 'siteelavation', 'sitelatitude',
                      'sitelongitude', 'slewing', 'slewsettletime',
                      'targetdeclination', 'targetrightascension',
                      'tracking', 'trackingrate', 'trackingrates', 'utcdate',
                      'axisrates', 'canmoveaxis', 'destinationsideofpier']:
            #try:
            resp['Value'] = getattr(self, action)

                #resp['ErrorNumber'] = ALPACA_ERROR_NOTIMPLEMENTED
        elif action in ['rightascension', 'declination']:
            radec = self.get_current_radec()
            if radec is not None:
                if action == 'rightascension':
                    resp['Value'] = radec.ra.hour
                elif action == 'declination':
                    resp['Value'] = radec.dec.degree
            else:
                resp['Value'] = 0
        else:
            # try with any registered handlers
            base_resp = super().get_action_handler(action)
            resp['Value'] = base_resp['Value']
            resp['ErrorNumber'] = base_resp['ErrorNumber']
            #resp['ErrorNumber'] = ALPACA_ERROR_NOTIMPLEMENTED

        # fill in error string if required
        if resp['ErrorNumber'] != 0:
            resp['ErrorString'] = ALPACA_ERROR_STRINGS[resp['ErrorNumber']]
        else:
            logging.debug(f'return value for {action} = {resp["Value"]}')

        return resp

    def put_action_handler(self, action, forms):
        """
        Handle put actions.

        :param action: Action URI.
        :type action: str
        :param forms: Data for put action

        :returns:
          (dict) For requested action return dict with:

                'Value': return value for get request
                'ErrorNumber': error result for request
                'ErrorString': string corresponding to error number
        """
        #logging.debug(f'TestTelescopeDevice::put_action_handler(): action = {action}')
        resp = {}
        resp['ErrorNumber'] = 0
        resp['ErrorString'] = ''

        if action in ['declinationrate', 'doesrefraction',
                      'guideratedeclinatoin', 'guideraterightascension',
                      'rightascensionrate', 'sideofpier', 'slewsettletime',
                      'targetdeclination', 'targetrightascension',
                      'tracking', 'trackingrate', 'abortslew',
                      'findhome', 'moveaxis', 'park', 'pulseguide',
                      'setpark', 'slewtoaltaz', 'slewtoaltazasync',
                      'slewtocoordinates', 'slewtocoordinatesasync',
                      'slewtotarget', 'slewtotargetasync', 'synctotarget',
                      'unpark']:
            logging.error(f'Unimplemented telescope method {action} requested!')
            resp['ErrorNumber'] = ALPACA_ERROR_NOTIMPLEMENTED
        elif action == 'synctoaltaz':
            logging.error(f'Need to handle {action}!')
            resp['ErrorNumber'] = 0
        elif action == 'synctocoordinates':
            #logging.error(f'Need to handle {action}!')
            # RA in decimal hours
            sync_ra = float(forms['RightAscension'])
            # DEC in decimal degrees
            sync_dec = float(forms['Declination'])
            logging.debug(f'synctocoordinates: ra={sync_ra} dec={sync_dec}')
            rc = self.sync_to_coordinates(sync_ra, sync_dec)
            resp['ErrorNumber'] = rc
        elif action == 'siteelevation':
            logging.error(f'Need to handle {action}!')
            resp['ErrorNumber'] = 0
        elif action == 'sitelatitude':
            logging.error(f'Need to handle {action}!')
            resp['ErrorNumber'] = 0
        elif action == 'sitelongitude':
            logging.error(f'Need to handle {action}!')
            resp['ErrorNumber'] = 0
        elif action == 'utcdate':
            logging.error(f'Need to handle {action}!')
            resp['ErrorNumber'] = 0
        else:
            # try with any registered handlers
            base_resp = super().put_action_handler(action, forms)
            resp['ErrorNumber'] = base_resp['ErrorNumber']

        # fill in error string if required
        if resp['ErrorNumber'] != 0:
            resp['ErrorString'] = ALPACA_ERROR_STRINGS[resp['ErrorNumber']]

        return resp

    def connect(self):
        """
        Attempts to connect to device
        """
        logging.debug('TestTelescopeDevice:connect() called')
        self.connected = True

    def disconnect(self):
        """
        Disconnects from device
        """
        logging.debug('TestTelescopeDevice:disconnect() called')
        self.connected = False

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

        logging.info(f'off alt/az = {enc_alt_off} {enc_az_off} steps')

        enc_alt_off_deg = 360*enc_alt_off/enc_alt_res
        enc_az_off_deg = 360*enc_az_off/enc_az_res

        logging.info(f'off alt/az = {enc_alt_off_deg} {enc_az_off_deg} degrees')

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

        logging.info(f'cur alt/az = {cur_alt} {cur_az} steps')

        return cur_alt, cur_az

    def get_current_radec(self):
        """
        Returns current RA/DEC of where device is pointing.

        *note* Driver must be synchronized or value will be meaningless.

        :returns:
            (float, float) RA/DEC position or None if device is
                           not synchronized yet
        """
        if None in [self.enc_alt0, self.enc_az0, self.syncpos_alt, self.syncpos_az]:
            logging.error('get_current_radec: No transformation setup!')
            return None

        # get encoders
        enc_pos = self.encoders.get_encoder_position()
        if enc_pos is None:
            return -1

        enc_alt, enc_az = enc_pos

        sky_alt, sky_az = self.convert_encoder_position_to_altaz(enc_alt, enc_az)

        obs_time = Time.now()

        newaltaz = SkyCoord(alt=sky_alt*u.deg, az=sky_az*u.deg, obstime=obs_time,
                            frame = 'altaz', location=self.earth_location)

        cur_radec = newaltaz.transform_to('icrs')
        logging.info('current ra/dec = {cur_radec}')

        return cur_radec

    def sync_to_coordinates(self, ra, dec):
        """
        Synchronize device to RA/DEC position.

        :param ra: RA position
        :param dec: DEC position

        :returns:
            (int) Return code 0 = success -1 = failure
        """
        # find alt/az matching ra/dec and setup transfortmation from encoders
        # alt/az values from this

        logging.info(f'syncing ra:{ra} dec:{dec}')

        obs_time = Time.now()

        aa = AltAz(location=self.earth_location, obstime=obs_time)

        # convert RA to degrees
        radec = SkyCoord(ra*15, dec, unit='deg', frame='icrs')

        sync_altaz = radec.transform_to(aa)

        logging.info(f'sync alt/az = {sync_altaz.alt}/{sync_altaz.az}')

        # get encoders
        enc_pos = self.encoders.get_encoder_position()
        if enc_pos is None:
            return -1

        enc_alt, enc_az = enc_pos

        self.enc_alt0 = enc_alt
        self.enc_az0 = enc_az
        self.syncpos_alt = sync_altaz.alt.degree
        self.syncpos_az = sync_altaz.az.degree

        return 0

