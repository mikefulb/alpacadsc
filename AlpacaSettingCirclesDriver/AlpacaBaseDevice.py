#
# Alpaca Base Device Driver Class
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

# error codes from https://ascom-standards.org/Help/Developer/html/T_ASCOM_ErrorCodes.htm
ALPACA_ERROR_NOTIMPLEMENTED = 0x80040400
ALPACA_ERROR_INVALIDOPERATION = 0x8004040B
ALPACA_ERROR_NOTCONNECTED = 0x80040407
ALPACA_ERROR_UNSPECIFIEDERRROR = 0x800404FF
ALPACA_ERROR_INVALIDVALUE = 0x80040401

ALPACA_ERROR_STRINGS = {
                         ALPACA_ERROR_NOTIMPLEMENTED : 'Method not implemented',
                         ALPACA_ERROR_INVALIDOPERATION : 'Invalid operation requested',
                         ALPACA_ERROR_NOTCONNECTED : 'Not connected',
                         ALPACA_ERROR_UNSPECIFIEDERRROR : 'Unspecified error',
                         ALPACA_ERROR_INVALIDVALUE : 'Invalid value'
                       }

# alignment modes
ALPACA_ALIGNMENT_ALTAZ = 0
ALPACA_ALIGNMENT_POLAR = 1
ALPACA_ALIGNMENT_GERMANPOLAR = 2

class AlpacaBaseDevice:

    def __init__(self):
        self.interface_version = 0

        # internal state variables
        self.connected = False

        # these are descriptive of driver and should be overridden
        # by class instance
        self.driver_version = 1.0
        self.description = 'AlpacaDevice'
        self.driverinfo = self.description + f' V. {self.driver_version}'
        self.name = 'AlpacaDevice'
        self.supported_actions = []

    def common_get_action_handler(self, action):
        """
        Handle get actions common to all devices.

        :param action: Action URI.
        :type action: str

        :returns:
          (dict) For requested action return dict with:

                'Value': return value for get request
                'ErrorNumber': error result for request
                'ErrorString': string corresponding to error number
        """
        resp = {}
        resp['ErrorNumber'] = 0
        resp['ErrorString'] = ''

        if action == 'connected':
            resp['Value'] = self.connected
        elif action == 'description':
            resp['Value'] = self.description
        elif action == 'driverinfo':
            resp['Value'] = self.driverinfo
        elif action == 'driverversion':
            resp['Value'] = self.driverversion
        elif action == 'interfaceversion':
            resp['Value'] = self.interface_version
        elif action == 'name':
            resp['Value'] = self.name
        elif action == 'supportedactions':
            if len(self.supported_actions) > 0:
                resp['Value'] = self.supported_actions
            else:
                resp['Value'] = []
                resp['ErrorNumber'] = ALPACA_ERROR_NOTIMPLEMENTED
        else:
            # try with any registered handlers
            #if self.custom_get_handler is not None:
            #    resp = self.custom_get_handler()
            resp['ErrorNumber'] = ALPACA_ERROR_NOTIMPLEMENTED

        # fill in error string if required
        if resp['ErrorNumber'] != 0:
            resp['ErrorString'] = ALPACA_ERROR_STRINGS[resp['ErrorNumber']]

        return resp

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
        # try base actions
        common_resp = self.common_get_action_handler(action)

        return common_resp

    def common_put_action_handler(self, action, forms):
        """
        Handle put actions common to all devices.

        :param action: Action URI.
        :type action: str
        :param forms: Data for put action

        :returns:
          (dict) For requested action return dict with:

                'Value': return value for get request
                'ErrorNumber': error result for request
                'ErrorString': string corresponding to error number
        """
        resp = {}
        resp['ErrorNumber'] = 0
        resp['ErrorString'] = ''

        if action == 'connected':
            try:
                state_string = forms['Connected']
            except KeyError:
                logging.error(f'missing value for Connected')
                resp['ErrorNumber'] = ALPACA_ERROR_INVALIDVALUE
            else:
                if state_string not in ['True', 'true', 'False', 'false']:
                    logging.error(f'invalid value for Connected: {state_string}')
                    resp['ErrorNumber'] = ALPACA_ERROR_INVALIDVALUE
                else:
                    state = state_string in ['true', 'True']
                    #logging.debug(f'connected state {state} requested')
                    if state:
                        self.connect()
                    else:
                        self.disconnect()
        else:
            resp['ErrorNumber'] = ALPACA_ERROR_NOTIMPLEMENTED

        # fill in error string if required
        if resp['ErrorNumber'] != 0:
            resp['ErrorString'] = ALPACA_ERROR_STRINGS[resp['ErrorNumber']]

        return resp

    def put_action_handler(self, action, forms):
        """
        Handle put actions common to all devices.

        :param action: Action URI.
        :type action: str
        :param forms: Data for put action

        :returns:
          (dict) For requested action return dict with:

                'Value': return value for get request
                'ErrorNumber': error result for request
                'ErrorString': string corresponding to error number
        """
        common_resp = self.common_put_action_handler(action, forms)

        return common_resp
