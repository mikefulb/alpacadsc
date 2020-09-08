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
        """
        Handler for endpoints - allows code reuse since all endpoints
        require similar handlers.
        """
        def __init__(self, outer, handler, method):
            """

            :param outer: Object for AlpacaDeviceServer this handler
                          is being created for.  Needed to access
                          server transaction ID so these can be
                          incremented each time an endpoint is handled.
            :type outer: AlpacaDeviceServer
            :param handler: Handler function.
            :param method: Method handled - 'GET' or 'PUT'
            :type method: str
            """
            self.outer = outer
            self.handler = handler
            self.method = method
            self.__name__ = __name__

        def __call__(self, *args, **kwargs):
            """
            Common handler code for all endpoints.
            """

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

        self.app.add_url_rule(_alpaca_url_base + '/<action>',
                              'GET_ACTION',
                              methods=['GET'],
                              view_func=self.EndpointHandler(self, self.device.get_action_handler, 'GET'))


        self.app.add_url_rule(_alpaca_url_base + '/<action>',
                              'PUT_ACTION',
                              methods=['PUT'],
                              view_func=self.EndpointHandler(self, self.device.put_action_handler, 'PUT'))

        self.server_transaction_id = 0

        # die if main dies
        self.daemon = True

    def run(self):
        """
        Starts the Alpaca Device Server in a thread.

        :return: None

        """
        self.app.run(host=self.host, port=self.port)