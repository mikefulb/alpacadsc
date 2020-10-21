#
# Flask-restx resource classes
#
# General profile storage persistently for program options
#
# Copyright 2020 Michael Fulbright
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

import logging
from pathlib import Path

import serial.tools.list_ports as list_serial_ports

from flask import render_template, make_response, request
from flask_restx import Resource

from .profiles import find_profiles, set_current_profile
from .profiles import get_current_profile, Profile
from .alpaca_models import PROFILE_BASENAME


def render_response(template, **kwargs):
    output = render_template(template, **kwargs)
    headers = {'Content-Type': 'text/html'}
    return make_response(output, 200, headers)


class About(Resource):
    """ Handle rendering the /about endpoint. """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.driver = kwargs['driver']

    def get(self):
        """
        Handle "/about" endpoint with info about the driver.

        :returns:
          (str) Rendered Flask template HTML output.
        """

        return render_response('about.html', driver=self.driver)


class MonitorEncoders(Resource):
    """ Handle rednering the /encoders endpoint. """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.driver = kwargs['driver']

    def get(self):
        """
        Handle reading encoders positions requests (/encoders endpoint).

        :returns:
          (str) Rendered Flask template HTML output.
        """

        # see if encoders configured?
        if self.driver.encoders is None:
            logging.error('Encoders not configured.'
                          'Unable to read encoder position!')
        elif not self.driver.connected:
            logging.error('Not connected to encoders.'
                          'Unable to read encoder position!')

        return render_response('report_encoders.html', driver=self.driver)


class GlobalSetup(Resource):
    """ Handle /setup GET request. """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.driver = kwargs['driver']
        self.server_ip = kwargs['server_ip']
        self.server_port = kwargs['server_port']

    def get(self):
        """
        Handle get global setup requests.

        This returns a info page on the driver.

        :returns:
          (str)  Rendered template output for /setup endpoint.
        """

        return render_response('global_setup_base.html',
                               server_ip=self.server_ip,
                               server_port=self.server_port,
                               driver=self.driver)


class DeviceSetup(Resource):
    """ Handle device setup page requests. """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.driver = kwargs['driver']

    def get(self):
        """
        Handle device setup GET requests.

        :returns:
          (str) Rendered Flask template HTML output.
        """

        # determine if driver is connected or not
        if not self.driver.connected:
            # load current profile for purposes of editting
            profile, profile_name = self.driver.load_profile()
        else:
            profile = self.driver.profile
            profile_name = self.driver.profile_name

        try:
            available_ports = sorted([d.device for d in list_serial_ports.comports()])
        except:
            logging.error('Unable to determine available ports', exc_info=True)
            available_ports = []

        return render_response('device_setup_base.html', driver=self.driver,
                               encoder_plugins=[n for n, m, c in self.driver.encoders_plugins],
                               profile=profile,
                               profile_name=profile_name,
                               profile_list=find_profiles(PROFILE_BASENAME),
                               available_ports=available_ports)

    def post(self):
        """
        Handle device setup POST (form) requests.

        :returns:
          (str) Rendered Flask template HTML output.

        Multiple forms on the device setup pages come to this endpoint.
        The source is differentiated by a hidden variable "form_id" contained
        in each form.  This value is used to route the response to the
        appropriate form data handler.
        """

        # identify which form this is from
        form_id = request.form.get('form_id')

        # FIXME Find a better way to route to the appropriate handler
        #       based on the form_id.  Big 'if ladder' is not ideal.

        # handle selection of new current profile
        if form_id == 'connect_driver_form' or form_id == 'disconnect_driver_form':
            return self.connect_disconnect_handler(form_id)

        # do not accept changes while connected
        if self.driver.connected:
            logging.error('request while connected!')
            return render_response('modify_profile.html',
                                   body_html='Cannot send setup post requests '
                                   'while device is connected!')

        # handle creating new or changing current profile
        if form_id == 'selected_profile_form':
            return self.selected_profile_handler()
        elif form_id == 'change_profile_form':
            return self.change_profile_handler()
        elif form_id == 'new_profile_form':
            return self.new_profile_handler()

        # handle forms modifying an existing profile
        profile_id = request.form.get('profile_id')

        profile = None
        if profile_id is not None:
            profile, profile_name = self.driver.load_profile(profile_id)

        if profile is None:
            logging.error('unknown profile_id!')
            return render_response(
                            'modify_profile.html',
                            body_html='unknown profile id!')

        if form_id == 'encoder_modify_form':
            resp = self.encoder_modify_handler(profile)
            if resp is not None:
                return resp
        elif form_id == 'location_modify_form':
            resp = self.location_modify_handler(profile)
            if resp is not None:
                return resp
        else:
            return self.unknown_form_handler()

        return render_response('modify_profile.html',
                               body_html=f'Profile {profile_id} updated.')

    def unknown_form_handler(self):
        """
        Handle rendering output when unknown form_id is received.

        :return: Rendered output from handling request.
        :rtype: str
        """

        logging.error('punknown form_id!')
        return render_response('modify_profile.html',
                               body_html=f'unknown form_id! '
                               f'called with form = {request.form}')

    def connect_disconnect_handler(self, form_id):
        """

        :param form_id: id of form to be handled - should be 'connect_driver_form'
                        or 'disconnect_driver_form'
        :type form_id: str
        :return: Rendered output from handling request.
        :rtype: str

        """

        if form_id == 'disconnect_driver_form':
            action = 'Disconnect'
            res = self.driver.disconnect()
        elif form_id == 'connect_driver_form':
            action = 'Connect'
            if self.driver.connected:
                # if already connected just skip and succeed
                logging.debug('Already connected so skipping /setup '
                              'connection request.')
                res = True
            else:
                res = self.driver.connect()
        else:
            return render_response('modify_profile.html',
                                   body_html=f'unknown form_id! '
                                   f'called with form = {request.form}')

        res_str = 'succeeded' if res else 'failed'

        logging.debug(f'{action} action via /setup request {res_str}')
        body = f'{action} action {res_str}.'
        return render_response('connect.html', body_html=body)

    def selected_profile_handler(self):
        """
        Handle selection of new active profile.

        :return: Rendered output from handling request.
        :rtype: str
        """

        new_profile = request.form.get('profile_choice')
        set_current_profile(PROFILE_BASENAME, new_profile)
        return render_response(
                        'modify_profile.html',
                        body_html=f'The profile {new_profile} is now '
                        'the current profile.')

    def change_profile_handler(self):
        """
        Handle request to change active profile.

        :return: Rendered output from handling request.
        :rtype: str
        """

        profile_list = [Path(x).stem for x in find_profiles(PROFILE_BASENAME)]
        return render_response(
                        'change_profile.html',
                        current_profile=get_current_profile(PROFILE_BASENAME),
                        profile_list=profile_list)

    def new_profile_handler(self):
        """
        Handle request to create a new profile.

        :return: Rendered output from handling request.
        :rtype: str
        """

        new_profile_id = request.form.get('new_profile_id')
        if new_profile_id is None or len(new_profile_id) < 1:
            logging.error('invalid new_profile_id!')
            return render_response('modify_profile.html',
                                   body_html='invalid new profile id!')

        new_profile = Profile(PROFILE_BASENAME, new_profile_id + '.yaml')
        new_profile.write()
        set_current_profile(PROFILE_BASENAME, new_profile_id)

        return render_response(
            'new_profile.html',
            body_html=f'Profile {new_profile_id} created and set as current.')

    def encoder_modify_handler(self, profile):
        """
        Handle request to modify profile parameters for encoders.

        :return: Rendered output from handling request.
        :rtype: str
        """

        encoder_driver = request.form.get('encoder_driver')
        serial_port = request.form.get('serial_port')
        serial_speed = request.form.get('serial_speed')
        alt_resolution = request.form.get('alt_resolution')
        az_resolution = request.form.get('az_resolution')
        alt_reverse = request.form.get('alt_reverse', 'false').lower() != 'false'
        az_reverse = request.form.get('az_reverse', 'false').lower() != 'false'

        logging.debug(f'{encoder_driver} {serial_port} {serial_speed} '
                      f'{alt_resolution} {az_resolution} '
                      f'{alt_reverse} {az_reverse}')

        if None in [encoder_driver, serial_port, serial_speed,
                    alt_resolution, az_resolution, alt_reverse,
                    az_reverse]:
            logging.error('Encoder missing required fields!')
            return render_response('modify_profile.html',
                                   body_html='Encoder missing required fields!')

        error_resp = ''

        encoders_plugin_names = [n for n, m, c in self.driver.encoders_plugins]
        if encoder_driver not in encoders_plugin_names:
            error_resp += f'<br>Driver {encoder_driver} is not valid.<br>'
            error_resp += f'Valid choices are {" ".join( encoders_plugin_names)}.'

        try:
            alt_resolution_value = int(alt_resolution)
            az_resolution_value = int(az_resolution)
            serial_speed_value = int(serial_speed)
        except:
            error_resp += '<br>Error - alt_resolution, az_resolution and '
            error_resp += 'serial_speed require integer values!'

        if len(error_resp) > 0:
            logging.error(f'{error_resp}')
            return render_response('modify_profile.html', body_html=error_resp)

        profile.encoders.driver = encoder_driver
        profile.encoders.serial_port = serial_port
        profile.encoders.serial_speed = serial_speed_value
        profile.encoders.alt_resolution = alt_resolution_value
        profile.encoders.az_resolution = az_resolution_value
        profile.encoders.alt_reverse = alt_reverse
        profile.encoders.az_reverse = az_reverse

        profile.write()

        return None

    def location_modify_handler(self, profile):
        """
        Handle request to modify profile parameters for location.

        :return: Rendered output from handling request.
        :rtype: str
        """

        obsname = request.form.get('name')
        lat = request.form.get('latitude')
        lon = request.form.get('longitude')
        alt = request.form.get('altitude')

        if None in [obsname, lat, lon, alt]:
            logging.error('Location missing required fields!')
            return render_response(
                    'modify_profile.html',
                    body_html='post_device_setup_handler: Location missing'
                    ' required fields!')

        error_resp = ''

        try:
            lat_value = float(lat)
            lon_value = float(lon)
            alt_value = float(alt)
        except ValueError:
            error_resp += '<br>Error - latitude, longitude and '
            error_resp += 'altitude require float values!'

        if len(error_resp) > 0:
            logging.error(f'{error_resp}')
            return render_response('modify_profile.html', body_html=error_resp)

        profile.location.obsname = obsname
        profile.location.longitude = lon_value
        profile.location.latitude = lat_value
        profile.location.altitude = alt_value

        profile.write()

        return None
