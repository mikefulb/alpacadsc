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
#
import os
import sys
import logging
import serial.tools.list_ports as list_serial_ports
from astropy.coordinates import EarthLocation, AltAz, SkyCoord
from astropy.time import Time
from astropy import units as u
from .AlpacaBaseDevice import AlpacaBaseDevice
from .AlpacaBaseDevice import ALPACA_ALIGNMENT_ALTAZ
from .AlpacaBaseDevice import ALPACA_ERROR_STRINGS
from .AlpacaBaseDevice import ALPACA_ERROR_NOTIMPLEMENTED
from .Profiles import find_profiles, set_current_profile, get_current_profile
from .AltAzSettingCirclesProfile import AltAzSettingCirclesProfile as Profile
from .EncodersAltAzDaveEk import EncodersAltAzDaveEk
#from EncodersAltAzSimulator import EncodersAltAzSimulated

from flask import request, render_template, Response

# base name used for profile storage
PROFILE_BASENAME = "AlpacaSettingCirclesDriver"

class AltAzSettingCircles(AlpacaBaseDevice):
    """
    Driver for Alt/Az setting circles
    """
    def __init__(self, use_profile=None):
        """
        Initialize driver object.
        """
        super().__init__()

        # driver info
        self.driver_version = 0.1
        self.description = 'Alt/Az Setting Cirles'
        self.driverinfo = self.description + f' V. {self.driver_version}'
        self.name = 'AltAzSettingCircles'
        #self.supported_actions = [] # FIXME NOT NEEDED?

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

        self.enc_alt0 = None
        self.enc_az0 = None
        self.syncpos_alt = None
        self.syncpos_az = None

    def load_profile(self, try_profile=None):
        # load profile
        # if profile was specified then try using it
        # FIXME maybe need way to suggest a profile from command line?
#        if use_profile is not None:
#            try_profile = use_profile

        # if no suggestion for profile try to find last one used
        if try_profile is None:
            try_profile = get_current_profile(PROFILE_BASENAME)
            if try_profile is not None:
                logging.info(f'Using current profile {try_profile}')

        if try_profile is None:
            # FIXME probably shouldnt exit from init() - return exception?
            logging.error('Must specify a valid profile')
            return None, None

        logging.info(f'load_profile: try_profile = {try_profile}')

        profile = Profile(PROFILE_BASENAME, try_profile + '.yaml')
        profile.read()

        return profile, try_profile

    def load_current_profile(self):
        profile, profile_name = self.load_profile()
        logging.info(f'load_current_profile: {profile} {profile_name}')

        if profile is None or profile_name is None:
            logging.error('load_current_profile: Failed to load profile!')
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
        self.profile = None
        self.profile_name = None

    def load_encoders(self, encoders_profile):
        """
        Load encoders and connect.

        :param encoders_profile: Dictionary containing encoder parameters

        :returns: True on success, False if fails.
        """

        # FIXME hard coded mapping for now need to perhaps make a way to
        #       dynamically build list of available encoder drivers
        encoder_drv = encoders_profile.get('driver')
        logging.info(f'encoder_drv = {encoder_drv}')
        if encoder_drv is None:
            logging.error('No encoder driver specified - cannot load encoder driver')
            # FIXME Raise exception?
            return False

        if encoder_drv == 'DaveEk':
            self.encoders = EncodersAltAzDaveEk(res_alt=encoders_profile.alt_resolution,
                                     res_az=encoders_profile.az_resolution,
                                     reverse_alt=encoders_profile.alt_reverse,
                                     reverse_az=encoders_profile.az_reverse)
            self.encoders.connect(encoders_profile.serial_port,
                             speed=encoders_profile.serial_speed)
        else:
            logging.error(f'Unknown encoder driver {encoder_drv} requested!')
            self.encoders = None
            # FIXME Raise exception?
            return False
#    if args.simul:
#        encoders = EncodersAltAzSimulated(res_alt=profile.encoders.alt_resolution,
#                             res_az=profile.encoders.az_resolution,
#                             reverse_alt=profile.encoders.alt_reverse,
#                             reverse_az=profile.encoders.az_reverse)
#    else:


        logging.info(f'Connected to encoders on port {encoders_profile.serial_port}')
        return True

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

        if action in ['alignmentmode', 'aperturearea', #'altitude',
                      'aperturediameter', 'athome',  'atpark', # 'azimuth',
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
        elif action in ['altitude', 'azimuth']:
            altaz = self.get_current_altaz()
            if altaz is not None:
                cur_alt, cur_az = altaz
                if action == 'altitude':
                    resp['Value'] = cur_alt
                elif action == 'azimuth':
                    resp['Value'] = cur_az
            else:
                resp['Value'] = 0
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

    # handle device specific setup
    def get_device_setup_handler(self):
        """
        Handle get setup requests.

        :param setup: Setup URI.
        :type setup: str

        :returns:
          (dict) For requested setup return dict with:

                'Value': return value for get request
                'ErrorNumber': error result for request
                'ErrorString': string corresponding to error number
        """

        # determine if driver is connected or not
        if not self.connected:
            # load current profile for purposes of editting
            profile, profile_name = self.load_profile()
        else:
            profile = self.profile
            profile_name = self.profile_name

        try:
            available_ports = sorted([d.device for d in list_serial_ports.comports()])
        except:
            logging.error('Unable to determine available ports', exc_info=True)
            available_ports = []

        output = render_template('device_setup_base.html', driver=self,
                                 profile=profile,
                                 profile_name=profile_name,
                                 profile_list=find_profiles(PROFILE_BASENAME),
                                 available_ports=available_ports)

        return output

    def post_device_setup_handler(self):
        logging.info(f'post_device_setup_handler request.form={request.form}')

        # do not accept changes while connected
        if self.connected:
            logging.error('post_device_setup_handler: request while connected!')
            return render_template('modify_profile.html',
                                   body_html='post_device_setup_handler: '
                                             'Cannot send setup post requests '
                                             'while device is connected!'
                                             '<br><p><a href="setup">'
                                             'Return to setup page</a>')

        # identify which form this is from
        form_id = request.form.get('form_id')
        logging.info(f'form_id = {form_id}')

        # handle selection of new current profile
        if form_id == 'selected_profile_form':
            new_profile = request.form.get('profile_choice')
            set_current_profile(PROFILE_BASENAME, new_profile)
            return render_template('modify_profile.html',
                                   body_html=f'The profile {new_profile} is now '
                                   'the current profile.<br><p><a href="setup">'
                                   'Return to setup page</a>')

        # handle change current profile request
        if form_id == 'change_profile_form':
            raw_profile_list=find_profiles(PROFILE_BASENAME)
            profile_list = []
            for p in raw_profile_list:
                base = os.path.basename(p)
                fname, ext = os.path.splitext(base)
                profile_list.append(fname)
            return render_template('change_profile.html',
                                   current_profile=get_current_profile(PROFILE_BASENAME),
                                   profile_list=profile_list)

        # handle new profile request
        if form_id == 'new_profile_form':
            new_profile_id = request.form.get('new_profile_id')
            if new_profile_id is None or len(new_profile_id) < 1:
                logging.error('post_device_setup_handler: invalid new_profile_id!')
                return render_template('modify_profile.html',
                                       body_html='post_device_setup_handler: '
                                                 'invalid new profile id !<br><p><a href="setup">'
                                                 'Return to setup page</a>')

            new_profile = profile = Profile(PROFILE_BASENAME,
                                            new_profile_id+ '.yaml')
            new_profile.write()
            set_current_profile(PROFILE_BASENAME, new_profile_id)

            return render_template('new_profile.html',
                                    body_html=f'Profile {new_profile_id} created and set as '
                                              'current.<br><p><a href="setup">'
                                              'Return to setup page</a>')

        # handle forms modifying an existing profile

        profile_id = request.form.get('profile_id')
        logging.info(f'profile_id = {profile_id}')

        profile = None
        if profile_id is not None:
            profile, profile_name = self.load_profile(profile_id)
            logging.info(f'{profile} {profile_name}')

        if profile is None:
            logging.error('post_device_setup_handler: unknown profile_id!')
            return render_template('modify_profile.html',
                                   body_html='post_device_setup_handler: '
                                   'unknown profile id !<br><p><a href="setup">'
                                   'Return to setup page</a>')

        logging.info(f'post_device_setup_handler: profile = {profile}')

        if form_id == 'encoder_modify_form':
            encoder_driver = request.form.get('encoder_driver')
            serial_port = request.form.get('serial_port')
            serial_speed = request.form.get('serial_speed')
            alt_resolution = request.form.get('alt_resolution')
            az_resolution = request.form.get('az_resolution')
            alt_reverse =  request.form.get('alt_reverse', 'false') != 'false'
            az_reverse = request.form.get('az_reverse', 'false') != 'false'

            logging.info(f'{encoder_driver} {serial_port} {serial_speed} '
                         f'{alt_resolution} {az_resolution} '
                         f'{alt_reverse} {az_reverse}')

            if None in [encoder_driver, serial_port, serial_speed,
                        alt_resolution, az_resolution, alt_reverse,
                        az_reverse]:
                logging.error('post_device_setup_handler: Encoder missing required fields!')
                return render_template('modify_profile.html',
                                       body_html='post_device_setup_handler: Encoder missing '
                                                 'required fields!<br><p><a href="setup">'
                                                 'Return to setup page</a>')

            error_resp = ''

            if encoder_driver not in ['DaveEk']:
                error_resp += f'<br>Driver {encoder_driver} is not valid.<br>'
                error_resp += 'Valid choice is "DaveEk"'

            try:
                alt_resolution_value = int(alt_resolution)
                az_resolution_value = int(az_resolution)
                serial_speed_value = int(serial_speed)
            except:
                error_resp += '<br>Error - alt_resolution, az_resolution and '
                error_resp += 'serial_speed require integer values!'

            if len(error_resp) > 0:
                logging.error('post_device_setup_handler: {error_resp}')
                error_resp += '<br><p><a href="setup">Return to setup page</a>'
                return render_template('modify_profile.html', body_html=error_resp)

            profile.encoders.driver = encoder_driver
            profile.encoders.serial_port = serial_port
            profile.encoders.serial_speed = serial_speed_value
            profile.encoders.alt_resolution = alt_resolution_value
            profile.encoders.az_resolution = az_resolution_value
            profile.encoders.alt_reverse = alt_reverse
            profile.encoders.az_reverse = az_reverse
            logging.info(f'profile before write: {profile}')

            profile.write()
        if form_id == 'location_modify_form':
            obsname = request.form.get('name')
            lat = request.form.get('latitude')
            lon = request.form.get('longitude')
            alt = request.form.get('altitude')

            logging.info(f'{obsname} {lat} {lon} {alt}')

            if None in [obsname, lat, lon, alt]:
                logging.error('post_device_setup_handler: Location missing required fields!')
                return render_template('modify_profile.html',
                                       body_html='post_device_setup_handler: Location missing '
                                                 'required fields!<br><p><a href="setup">'
                                                 'Return to setup page</a>')
            error_resp = ''

            try:
                lat_value = float(lat)
                lon_value = float(lon)
                alt_value = float(alt)
            except:
                error_resp += '<br>Error - latitude, longitude and '
                error_resp += 'altitude require float values!'

            if len(error_resp) > 0:
                logging.error(f'post_device_setup_handler: {error_resp}')
                error_resp += '<br><p><a href="setup">Return to setup page</a>'
                return render_template('modify_profile.html', body_html=error_resp)

            profile.location.obsname = obsname
            profile.location.longitude = lat_value
            profile.location.latitude = lon_value
            profile.location.altitude = alt_value

            logging.info(f'profile before write: {profile}')

            profile.write()

        elif form_id == 'location_modify_form':
            encoder_driver = request.form.get('encoder_driver')
            serial_port = request.form.get('serial_port')
            serial_speed = request.form.get('serial_speed')
            alt_resolution = request.form.get('alt_resolution')
            az_resolution = request.form.get('az_resolution')
            alt_reverse =  request.form.get('alt_reverse', 'false') != 'false'
            az_reverse = request.form.get('az_reverse', 'false') != 'false'

            logging.info(f'{encoder_driver} {serial_port} {serial_speed} '
                         f'{alt_resolution} {az_resolution} '
                         f'{alt_reverse} {az_reverse}')

            if None in [encoder_driver, serial_port, serial_speed,
                        alt_resolution, az_resolution, alt_reverse,
                        az_reverse]:
                logging.error('post_device_setup_handler: Missing required fields!')
                return render_template('modify_profile.html',
                                       body_html='post_device_setup_handler: Missing '
                                                 'required fields!<br><p><a href="setup">'
                                                 'Return to setup page</a>')

            error_resp = ''

            if encoder_driver not in ['DaveEk']:
                error_resp += f'<br>Driver {encoder_driver} is not valid.<br>'
                error_resp += 'Valid choice is "DaveEk"'

            try:
                alt_resolution_value = int(alt_resolution)
                az_resolution_value = int(az_resolution)
                serial_speed_value = int(serial_speed)
            except:
                error_resp += '<br>Error - alt_resolution, az_resolution and '
                error_resp += 'serial_speed require integer values!'

            if len(error_resp) > 0:
                logging.error('post_device_setup_handler: {error_resp}')
                error_resp += '<br><a href="setup">Return to setup page</a>'
#                return Response(f'{error_resp}',  status=200, headers={})
                return render_template('modify_profile.html', body_html=error_resp)

            profile.encoders.encoder_driver = encoder_driver
            profile.encoders.serial_port = serial_port
            profile.encoders.serial_speed = serial_speed_value
            profile.encoders.alt_resolution = alt_resolution_value
            profile.encoders.az_resolution = az_resolution_value
            profile.encoders.alt_reverse = alt_reverse
            profile.encoders.az_reverse = az_reverse
            logging.info(f'profile before write: {profile}')

            profile.write()
        else:
            logging.error('post_device_setup_handler: unknown form_id!')
#            return Response(f'post_device_setup_handler: unknown form_id! '
#                     f'called with form = {request.form}'
#                     f'<br><a href="setup">Return to setup page</a>',
#                     status=200, headers={})

            render_template('modify_profile.html',
                            body_html=f'post_device_setup_handler: unknown form_id! '
                            f'called with form = {request.form}'
                            f'<br><a href="setup">Return to setup page</a>')



#        return Response(f'Profile {profile_id} updated.<br><a href="setup">'
#                        f'Return to setup page</a>', status=200, headers={})
        return render_template('modify_profile.html',
                               body_html = f'Profile {profile_id} updated.<br> '
                                           f'<p><a href="setup">'
                                           f'Return to setup page</a>')
    # FIXME connect/disconnect does not distiguish between clients - is this
    #       even addressed by the Alpaca standard?  Need to investigate.
    def connect(self):
        """
        Attempts to connect to device
        """
        logging.debug('TestTelescopeDevice:connect() called')

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

        print('self.encoders = ', self.encoders)
        return True

    def disconnect(self):
        """
        Disconnects from device
        """
        logging.info('TestTelescopeDevice:disconnect() called')

        if not self.connected:
            logging.error('disconnect called but not connected!')
            return False

        # disconnect from encoders
        self.encoders.disconnect()

        # clear out profile
        self.unload_current_profile()

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

