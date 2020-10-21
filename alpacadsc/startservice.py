#
# Main script which starts the Alpaca service listens for REST API calls
# and also handles the web dashboard.
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
import argparse
from datetime import datetime

from flask import Flask, redirect
from flask_restx import Api

from . import __version__ as version
from .alpaca_controller import AlpacaTelescope
from .alpaca_models import AlpacaAltAzTelescopeModel as TelescopeModel
from .setup_controller import About, MonitorEncoders, GlobalSetup, DeviceSetup


def parse_command_line():
    parser = argparse.ArgumentParser()
    parser.add_argument('--profile', type=str, help='Name of astro profile')
    parser.add_argument('--listprofiles', action='store_true',
                        help='List known profiles')
    parser.add_argument('--port', type=int, default=8000,
                        help='TCP Port Alpaca server will listen on.')
    parser.add_argument('--debug', action='store_true',
                        help='Set log level DEBUG')
    parser.add_argument('--simul', action='store_true',
                        help='Run as simulation')

    args = parser.parse_args()
    logging.debug(f'cmd args = {args}')
    return args

def redirect_root():
    """Redirect root to setup page for convenience to user"""
    print("HERE")
    return redirect('/setup')

def create_app(port=8000):
    """
    Create Flask app object.

    :param port: TCP port for service to use.
    :type port: int
    :return: Flask app object
    :rtype: Flask()

    """

    app = Flask(__name__)

    # we need to add redirect for '/' to '/setup' before
    # connecting api to app or else the rule for '/' inserted
    # by the api creation will override.
    app.add_url_rule('/', 'ROOT_REDIRECT', methods=['GET'],
                    view_func=redirect_root)

    api = Api(app, doc='/apidoc/')

    driver = TelescopeModel()

    api.add_resource(AlpacaTelescope, '/api/v1/telescope/0/<string:action>',
                      endpoint='Alpaca',
                      resource_class_kwargs={'driver': driver})

    api.add_resource(About, '/about', endpoint='About',
                      resource_class_kwargs={'driver': driver})

    api.add_resource(MonitorEncoders, '/encoders', endpoint='Encoders',
                      resource_class_kwargs={'driver': driver})

    api.add_resource(GlobalSetup, '/setup', endpoint='GlobalSetup',
                      resource_class_kwargs={'driver': driver,
                                            'server_ip': '127.0.0.1',
                                            'server_port': port})

    api.add_resource(DeviceSetup, '/setup/v1/telescope/0/setup',
                      endpoint='DeviceSetup',
                      resource_class_kwargs={'driver': driver})

    return app


def run_app(args):

    logging.info(f'Alpaca DSC Driver version {version} starting...')

    app = create_app(args.port)

    app.run(host='127.0.0.1', port=args.port, debug=True)


def main():
    # FIXME assumes tz is set properly in system?
    logfilename = 'alpacadsc'
#    logfilename += '-' + datetime.now().strftime('%Y%m%d%H%M%S')
    logfilename += '.log'

    LONG_FORMAT = '%(asctime)s [%(filename)20s:%(lineno)3s - ' + \
                  '%(funcName)20s() ] %(levelname)-8s %(message)s'
    SHORT_FORMAT = '%(asctime)s %(levelname)-8s %(message)s'
    logging.basicConfig(filename=logfilename,
                        filemode='a',
                        level=logging.DEBUG,
                        format=LONG_FORMAT,
                        datefmt='%Y-%m-%d %H:%M:%S')

    # add to screen as well
    LOG = logging.getLogger()
    CH = logging.StreamHandler()

    cmd_args = parse_command_line()

    if cmd_args.debug:
        # formatter = logging.Formatter(LONG_FORMAT)
        formatter = logging.Formatter(SHORT_FORMAT)
        CH.setLevel(logging.DEBUG)
        CH.setFormatter(formatter)
    else:
        formatter = logging.Formatter(SHORT_FORMAT)
        CH.setLevel(logging.INFO)
        CH.setFormatter(formatter)

    LOG.addHandler(CH)

    run_app(cmd_args)


if __name__ == '__main__':
    main()
