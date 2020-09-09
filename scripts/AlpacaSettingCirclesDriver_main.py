# AlpacaSettingCirclesDriver_main.py
#
# Main script which starts the Alpaca service listens for REST API calls
# and also handles the web dashboard.
#
# Author: Michael Fulbright <mike.fulbright@pobox.com>
#
# Copyright 2020
#
import os
import sys

sys.path.append('../AlpacaSettingCirclesDriver')

import time
import logging
import argparse

from datetime import datetime

from AlpacaDeviceServer import AlpacaDeviceServer
from AltAzSettingCircles import AltAzSettingCircles as TelescopeDevice


def parse_command_line():
    parser = argparse.ArgumentParser()
    parser.add_argument('--profile', type=str, help='Name of astro profile')
    parser.add_argument('--listprofiles', action='store_true', help='List known profiles')
    parser.add_argument('--debug', action='store_true', help='Set log level DEBUG')
    parser.add_argument('--simul', action='store_true', help='Run as simulation')

    args = parser.parse_args()
    logging.debug(f'cmd args = {args}')
    return args

def main(args):

#    # list profiles if requested
#    if args.listprofiles:
#        profiles = find_profiles(PROFILE_BASENAME)
#        if len(profiles) > 0:
#            logging.info('Available profiles:')
#            for p in profiles:
#                logging.info(f'    {p}')
#            logging.info('Current profile is:')
#            logging.info(f'    {get_current_profile(PROFILE_BASENAME)}')
#        else:
#            logging.info('No profiles available')
#        sys.exit(0)
#
#    # load profile
#    if args.profile is None:
#        # see if current profile set
#        profile_name = get_current_profile(PROFILE_BASENAME)
#        if profile_name is None:
#            logging.error('Must specify a profile with --profile')
#            sys.exit(1)
#        logging.info(f'Using current profile {profile_name}')
#    else:
#        profile_name = args.profile
#    profile = Profile(PROFILE_BASENAME, profile_name + '.yaml')
#    profile.read()
#    print(profile)
#
#    # set as current
#    set_current_profile(PROFILE_BASENAME, profile_name)

#    logging.info(f'Loaded profile {args.profile} from {profile.filename()}:')
#    logging.info(f'Location:')
#    logging.info(f'   Name: {profile.location.obsname}')
#    logging.info(f'   Lat : {profile.location.latitude}')
#    logging.info(f'   Lon : {profile.location.longitude}')
#    logging.info(f'   Alt : {profile.location.altitude} meters')
#    logging.info(f'Encoders:')
#    logging.info(f'   Serial Port   : {profile.encoders.serial_port}')
#    logging.info(f'   Serial Speed  : {profile.encoders.serial_speed}')
#    logging.info(f'   ALT resolution: {profile.encoders.alt_resolution}')
#    logging.info(f'   AZ  resolution: {profile.encoders.az_resolution}')
#    logging.info(f'   Reverse ALT   : {profile.encoders.alt_reverse}')
#    logging.info(f'   Reverse AZ    : {profile.encoders.az_reverse}')



    # create alpaca device object
    device = TelescopeDevice(args.profile)

    # start api server
    api_server = AlpacaDeviceServer(device)
    api_server.start()
    logging.info('Alpaca API server for encoders started')

    # start web server
#    status_dict = {}
#    status_dict['profile'] = profile
#    status_dict['encoders'] = encoders
#    http_server = WebMonitor(status_dict)
#    http_server.start()
#    logging.info(f'Status web server started on port {http_server.port}')


    while True:
        time.sleep(1)
        #print(encoders.get_encoder_resolution())
#        enc_pos = encoders.get_encoder_position()
#        if enc_pos is not None:
#            alt, az = enc_pos
#            logging.info(f'alt={alt} az={az}')
#        else:
#            logging.error('could not read pos')



    # start up bottle
if __name__ == '__main__':

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

    main(cmd_args)



