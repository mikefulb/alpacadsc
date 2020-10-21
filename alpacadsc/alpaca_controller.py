#
# Handlers for Alpaca REST API endpoints
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
from flask import request, redirect
from flask_restx import Resource

from .alpaca_service import AlpacaBaseService, AlpacaTelescopeService

# error codes from https://ascom-standards.org/Help/Developer/html/T_ASCOM_ErrorCodes.htm
ALPACA_ERROR_NOTIMPLEMENTED = 0x80040400
ALPACA_ERROR_INVALIDOPERATION = 0x8004040B
ALPACA_ERROR_NOTCONNECTED = 0x80040407
ALPACA_ERROR_UNSPECIFIEDERRROR = 0x800404FF
ALPACA_ERROR_INVALIDVALUE = 0x80040401

ALPACA_ERROR_STRINGS = {
                         ALPACA_ERROR_NOTIMPLEMENTED: 'Method not implemented',
                         ALPACA_ERROR_INVALIDOPERATION: 'Invalid operation requested',
                         ALPACA_ERROR_NOTCONNECTED: 'Not connected',
                         ALPACA_ERROR_UNSPECIFIEDERRROR: 'Unspecified error',
                         ALPACA_ERROR_INVALIDVALUE: 'Invalid value'
                       }

# alignment modes
ALPACA_ALIGNMENT_ALTAZ = 0
ALPACA_ALIGNMENT_POLAR = 1
ALPACA_ALIGNMENT_GERMANPOLAR = 2

class AlpacaBase(Resource):
    """
    Handle common Alpaca REST APIs for all device types.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.driver = kwargs['driver']
        self.base_service = AlpacaBaseService(self.driver)

    def get(self, action):
        resp = {'ErrorNumber': 0, 'ErrorString': '', 'Value': ''}

        try:
            resp['Value'] = getattr(self.driver, action)
        except AttributeError:
            resp['ErrorNumber'] = ALPACA_ERROR_NOTIMPLEMENTED
            resp['ErrorString'] = ALPACA_ERROR_STRINGS[resp['ErrorNumber']]

        return resp

    def put(self, action):
        resp = {'ErrorNumber': 0, 'ErrorString': ''}

        logging.debug(f'AlpacaBase:put() {action} {request.form}')

        try:
            method = getattr(self.base_service, action)
        except AttributeError:
            resp['ErrorNumber'] = ALPACA_ERROR_NOTIMPLEMENTED
            resp['ErrorString'] = ALPACA_ERROR_STRINGS[resp['ErrorNumber']]
        else:
            if callable(method):
                if not method(request.form):
                    resp['ErrorNumber'] = ALPACA_ERROR_UNSPECIFIEDERRROR
                    resp['ErrorString'] = ALPACA_ERROR_STRINGS[resp['ErrorNumber']]
            else:
                resp['ErrorNumber'] = ALPACA_ERROR_NOTIMPLEMENTED
                resp['ErrorString'] = ALPACA_ERROR_STRINGS[resp['ErrorNumber']]

        return resp

class AlpacaTelescope(AlpacaBase):
    """
    Handle common Alpaca REST APIs for all device types.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.driver = kwargs['driver']
        self.service = AlpacaTelescopeService(self.driver)

    def get(self, action):
        resp = {'ErrorNumber': 0, 'ErrorString': '', 'Value': ''}

        # FIXME Should we add check for a ClientID and ClientTransactionID?

        try:
            resp['Value'] = getattr(self.driver, action)
        except AttributeError:
            resp = super().get(action)

        return resp

    def put(self, action):
        resp = {'ErrorNumber': 0, 'ErrorString': ''}

        logging.debug(f'AlpacaTelescope:put() {action} {request.form}')

        try:
            method = getattr(self.service, action)
        except AttributeError:
            return super().put(action)
        else:
            if callable(method):
                if not method(request.form):
                    resp['ErrorNumber'] = ALPACA_ERROR_UNSPECIFIEDERRROR
                    resp['ErrorString'] = ALPACA_ERROR_STRINGS[resp['ErrorNumber']]
            else:
                resp['ErrorNumber'] = ALPACA_ERROR_NOTIMPLEMENTED
                resp['ErrorString'] = ALPACA_ERROR_STRINGS[resp['ErrorNumber']]

        return resp
