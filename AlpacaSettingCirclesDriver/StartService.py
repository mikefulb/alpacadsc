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
import os
import sys

#sys.path.append('../AlpacaSettingCirclesDriver')

import time
import logging
import argparse

from datetime import datetime

from . import __version__ as version
from .AlpacaDeviceServer import AlpacaDeviceServer
from .AltAzSettingCircles import AltAzSettingCircles as TelescopeDevice


def parse_command_line():
    parser = argparse.ArgumentParser()
    parser.add_argument('--profile', type=str, help='Name of astro profile')
    parser.add_argument('--listprofiles', action='store_true', help='List known profiles')
    parser.add_argument('--debug', action='store_true', help='Set log level DEBUG')
    parser.add_argument('--simul', action='store_true', help='Run as simulation')

    args = parser.parse_args()
    logging.debug(f'cmd args = {args}')
    return args

def runapp(args):

    logging.info(f'AlpacaSettingCirclesDriver version {version} starting...')

    # create alpaca device object
    device = TelescopeDevice(args.profile)

    # start api server
    api_server = AlpacaDeviceServer(device)
    api_server.start()
    logging.info('Alpaca API server for encoders started')

    while True:
        time.sleep(1)

def main():
    # FIXME assumes tz is set properly in system?
    log_timestamp = datetime.now()
    logfilename = 'AlpacaSettingCirclesDriver'
    #logfilename += '-' + log_timestamp.strftime('%Y%m%d%H%M%S')
    logfilename += '.log'

#    FORMAT = '%(asctime)s %(levelname)-8s %(message)s'
    #LONG_FORMAT = '%(asctime)s.%(msecs)03d [%(filename)20s:%(lineno)3s - %(funcName)20s() ] %(levelname)-8s %(message)s'
    LONG_FORMAT = '%(asctime)s [%(filename)20s:%(lineno)3s - %(funcName)20s() ] %(levelname)-8s %(message)s'
    #SHORT_FORMAT = '%(asctime)s.%(msecs)03d %(levelname)-8s %(message)s'
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
        #formatter = logging.Formatter(LONG_FORMAT)
        formatter = logging.Formatter(SHORT_FORMAT)
        CH.setLevel(logging.DEBUG)
        CH.setFormatter(formatter)
    else:
        formatter = logging.Formatter(SHORT_FORMAT)
        CH.setLevel(logging.INFO)
        CH.setFormatter(formatter)

    LOG.addHandler(CH)

    runapp(cmd_args)

if __name__ == '__main__':
    main()





