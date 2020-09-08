#
# Alpaca Server In Thread Using Flask
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

import json
import logging
from threading import Thread

from flask import Flask, request

_alpaca_url_base = '/api/v1/telescope/0'




class AlpacaDeviceServer(Thread):
    """
    AlpacaDeviceServer class creates a Flask app in a thread that
    handles all REST API calls from an Alpaca client.
    """

    class EndpointHandler:

        def __init__(self, outer, handler, method):
            self.outer = outer
            self.handler = handler
            self.method = method
            self.__name__ = __name__

        def __call__(self, *args, **kwargs):

            print(args)
            print(kwargs)

            resp = {}
            try:
                resp['ClientTransactionID'] = request.query['ClientTransactionID']
            except:
                logging.warning('request missing client id!')

            resp['ServerTransactionID'] = self.outer.server_transaction_id
            self.outer.server_transaction_id += 1

            if self.method == 'PUT':
                kwargs['forms'] = request.form

            handler_resp = self.handler(*args, **kwargs)

            resp['ErrorNumber'] = handler_resp['ErrorNumber']
            resp['ErrorString'] = handler_resp['ErrorString']

            if self.method == 'GET':
                resp['Value'] = handler_resp['Value']

            return json.dumps(resp), 200, {'Content-Type' : 'application/json'}

    def __init__(self, device, host='localhost', port=8000):
        """
        Initialize AlpacaDeviceServer.  Accepts a AlpacaBaseDevice
        object which does the real work.  This class services the
        Alpaca REST API requests.


        :param device: AlpacaBaseDevice object for actual device driver
        :type device: AlpacaBaseDevice
        :param host: Address to bind to - defaults to localhost
        :type host: str
        :param port: Port to bind to - defaults to 8000
        :type port: int

        """
        super().__init__()

        self.device = device
        self.host = host
        self.port = port
        self.app = Flask(__name__)

#        self.app.add_url_rule(_alpaca_url_base + '/<action>', methods=['GET'],
#                              view_func=self.core_get_action_handler)

        self.app.add_url_rule(_alpaca_url_base + '/<action>',
                              'GET_ACTION',
                              methods=['GET'],
                              view_func=self.EndpointHandler(self, self.device.get_action_handler, 'GET'))

#        self.app.add_url_rule(_alpaca_url_base + '/<action>',
#                              'PUT_ACTION',
#                              methods=['PUT'],
#                              view_func=self.core_put_action_handler)

        self.app.add_url_rule(_alpaca_url_base + '/<action>',
                              'PUT_ACTION',
                              methods=['PUT'],
                              view_func=self.EndpointHandler(self, self.device.put_action_handler, 'PUT'))

        self.server_transaction_id = 0

        # die if main dies
        self.daemon = True


    #
    # FIXME: Should somehow combine action and setup handlers into sharing more
    #        code as currently they are almost identical!
    #


    def core_get_action_handler(self, action):
        """
        Endpoint for all GET actions for Alpaca server.

        This function is a wrapper that handles the request and passes it
        to the actual device driver to handle.

        :param action: Alpaca REST action requested
        :type action: str

        """
        #logging.debug(f'core_get_action_handler(): action = {action}')

        # methods common to all devices
#        logging.debug('get request:')
#        for k, v in request.query.items():
#            logging.debug(f'   {k} : {v}')

        resp = {}
        try:
            resp['ClientTransactionID'] = request.query['ClientTransactionID']
        except:
            logging.warning('request missing client id!')

        resp['ServerTransactionID'] = self.server_transaction_id
        self.server_transaction_id += 1

        action_resp = self.device.get_action_handler(action)

        resp['ErrorNumber'] = action_resp['ErrorNumber']
        resp['ErrorString'] = action_resp['ErrorString']
        resp['Value'] = action_resp['Value']

        return json.dumps(resp), 200, {'Content-Type' : 'application/json'}

    def core_put_action_handler(self, action):
        """
        Endpoint for all PUT actions for Alpaca server.

        This function is a wrapper that handles the request and passes it
        to the actual device driver to handle.

        :param action: Alpaca REST action requested
        :type action: str

        """
        #logging.debug(f'core_put_action_handler(): action = {action}')

        # methods common to all devices
#        logging.debug('put request:')
#        for k, v in request.query.items():
#            logging.debug(f'   {k} : {v}')

        resp = {}
        try:
            resp['ClientTransactionID'] = request.form['ClientTransactionID']
        except:
            logging.warning('request missing client id!')

        resp['ServerTransactionID'] = self.server_transaction_id
        self.server_transaction_id += 1
        resp['ErrorNumber'] = 0
        resp['ErrorString'] = ''

        action_resp = self.device.put_action_handler(action, request.form)

        resp['ErrorNumber'] = action_resp['ErrorNumber']
        resp['ErrorString'] = action_resp['ErrorString']

        return json.dumps(resp), 200, {'Content-Type' : 'application/json'}

    def run(self):
        """
        Starts the Alpaca Device Server in a thread.

        :return: None

        """
        self.app.run(host=self.host, port=self.port)