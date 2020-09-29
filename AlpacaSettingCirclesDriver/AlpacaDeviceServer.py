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
#
import json
import logging
from threading import Thread

from flask import Flask, Response, request, redirect, render_template

_alpaca_url_base = '/v1/telescope/0'


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

            if isinstance(handler_resp, str):
                return Response(handler_resp, status=200, headers={})
            else:

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

        get_func = self.EndpointHandler(self, self.device.get_action_handler, 'GET')
        self.app.add_url_rule('/api' + _alpaca_url_base + '/<action>',
                              'GET_ACTION',
                              methods=['GET'],
                              view_func=get_func)

        put_func = self.EndpointHandler(self, self.device.put_action_handler, 'PUT')
        self.app.add_url_rule('/api' + _alpaca_url_base + '/<action>',
                              'PUT_ACTION',
                              methods=['PUT'],
                              view_func=put_func)

        # Alpaca defines a global parameters setup for the device at '/setup'
        global_get_func = self.EndpointHandler(self, self.get_global_setup_handler, 'GET')
        self.app.add_url_rule('/setup',
                              'GET_GLOBAL_SETUP',
                              methods=['GET'],
                              view_func=global_get_func)

        # for convenience redirect '/' to setup page
        self.app.add_url_rule('/', 'ROOT_REDIRECT', methods=['GET'],
                              view_func=self.redirect_root)

        # Specific setup for the actual device at '/setup' + _alpaca_url_base + '/setup'
        logging.info(f"adding endpoint {'/setup' + _alpaca_url_base + '/setup'}")
        setup_func = self.EndpointHandler(self, self.device.get_device_setup_handler, 'GET')
        self.app.add_url_rule('/setup' + _alpaca_url_base + '/setup',
                              'GET_DEVICE_SETUP',
                              methods=['GET'],
                              view_func=setup_func)

        self.app.add_url_rule('/setup' + _alpaca_url_base + '/setup',
                              'POST_DEVICE_SETUP',
                              methods=['POST'],
                              view_func=self.device.post_device_setup_handler)

        self.server_transaction_id = 0

        # die if main dies
        self.daemon = True

    def redirect_root(self):
        """Redirect root to setup page for convenience to user"""
        return redirect('/setup')

    # handle device specific setup
    def get_global_setup_handler(self):
        """
        Handle get global setup requests.

        This returns a info page on the driver.

        :returns:
          (dict) For requested setup return dict with:

                'Value': return value for get request
                'ErrorNumber': error result for request
                'ErrorString': string corresponding to error number
        """
        return render_template('global_setup_base.html', server=self,
                               device=self.device)


    def run(self):
        """
        Starts the Alpaca Device Server in a thread.

        :return: None

        """
        self.app.run(host=self.host, port=self.port)