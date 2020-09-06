# test alpaca server template
import json
import time
import logging
import argparse
import serial

from datetime import datetime
from threading import Thread, Lock

from astropy.coordinates import EarthLocation, AltAz, SkyCoord
from astropy.time import Time
from astropy import units as u

from bottle import Bottle, template
from bottle import request, response
from bottle import post, get, put, route, delete

_alpaca_url_base = '/api/v1/telescope/0'

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
ALPCA_ALIGNMENT_ALTAZ = 0
ALPCA_ALIGNMENT_POLAR = 1
ALPCA_ALIGNMENT_GERMANPOLAR = 2


class AlpacaDeviceServer(Thread):
    def __init__(self, device, host='localhost', port=8000):
        super().__init__()

        self.device = device
        self.host = host
        self.port = port
        self.app = Bottle()
        self.app.route(_alpaca_url_base + '/<action>', method='GET',
                       callback=self.core_get_action_handler)
        self.app.route(_alpaca_url_base + '/<action>', method='PUT',
                       callback=self.core_put_action_handler)
        self.server_transaction_id = 0

        # die if main dies
        self.daemon = True

   # @route(_alpaca_url_base + '/<action>', method='GET')
    def core_get_action_handler(self, action):
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

        response.headers['Content-Type'] = 'application/json'
        return json.dumps(resp)

    def core_put_action_handler(self, action):
        #logging.debug(f'core_put_action_handler(): action = {action}')

        # methods common to all devices
#        logging.debug('put request:')
#        for k, v in request.query.items():
#            logging.debug(f'   {k} : {v}')

        resp = {}
        try:
            resp['ClientTransactionID'] = request.forms['ClientTransactionID']
        except:
            logging.warning('request missing client id!')

        resp['ServerTransactionID'] = self.server_transaction_id
        self.server_transaction_id += 1
        resp['ErrorNumber'] = 0
        resp['ErrorString'] = ''

        action_resp = self.device.put_action_handler(action, request.forms)

        resp['ErrorNumber'] = action_resp['ErrorNumber']
        resp['ErrorString'] = action_resp['ErrorString']

        response.headers['Content-Type'] = 'application/json'
        return json.dumps(resp)

    def run(self):
        self.app.run(host=self.host, port=self.port, debug=True, quiet=True)


class AlpacaDeviceBase:

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
        # for requested action return dict with:
        #  'Value': return value for get request
        #  'ErrorNumber': error result for request
        #  'ErrorString': string corresponding to error number
        #
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
        # try base actions
        common_resp = self.common_get_action_handler(action)

        return common_resp

    def common_put_action_handler(self, action, forms):
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
        # try base actions
        common_resp = self.common_put_action_handler(action, forms)

        return common_resp

class TestTelescopeDevice(AlpacaDeviceBase):
    def __init__(self, encoders):
        super().__init__()

        self.driver_version = 0.1
        self.description = 'Test Telescope Device'
        self.driverinfo = self.description + f' V. {self.driver_version}'
        self.name = 'TestTelescopeDevice'
        self.supported_actions = []

        # alt/az
        self.alignmentmode = ALPCA_ALIGNMENT_ALTAZ
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

        # used for setting circle transforms
        #self.earth_location =None

        # shouldnt hard code!
        self.earth_location = EarthLocation(lat='35d48m', lon='-78d48m', height=100*u.m)

        # FIXME encoders should be part of class??
        self.encoders = encoders

        self.enc_alt0 = None
        self.enc_az0 = None
        self.syncpos_alt = None
        self.syncpos_az = None



    # handle device specific actions or pass to base
    def get_action_handler(self, action):
        #logging.debug(f'TestTelescopeDevice::get_action_handler(): action = {action}')
        resp = {}
        resp['ErrorNumber'] = 0
        resp['ErrorString'] = ''

        if action in ['alignmentmode', 'altitude', 'aperturearea',
                      'aperturediameter', 'athome',  'atpark',  'azimuth',
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
        logging.debug(f'TestTelescopeDevice::put_action_handler(): action = {action}')
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

    def connect(self):
        logging.debug('TestTelescopeDevice:connect() called')
        self.connected = True

    def disconnect(self):
        logging.debug('TestTelescopeDevice:disconnect() called')
        self.connected = False

    def convert_encoder_position_to_altaz(self, enc_alt, enc_az):

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

    def get_current_radec(self):
        if None in [self.enc_alt0, self.enc_az0, self.syncpos_alt, self.syncpos_az]:
            logging.error('get_current_radec: No transformation setup!')
            return None

        # get encoders
        enc_pos = self.encoders.get_encoder_position()
        if enc_pos is None:
            return -1

        enc_alt, enc_az = enc_pos

        sky_alt, sky_az = self.convert_encoder_position_to_altaz(enc_alt, enc_az)

        obs_time = Time.now()

        newaltaz = SkyCoord(alt=sky_alt*u.deg, az=sky_az*u.deg, obstime=obs_time,
                            frame = 'altaz', location=self.earth_location)

        cur_radec = newaltaz.transform_to('icrs')
        logging.info('current ra/dec = {cur_radec}')

        return cur_radec

    def sync_to_coordinates(self, ra, dec):
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



class AltAzEncoders:

    def __init__(self, res_alt=4000, res_az=4000, reverse_alt=False, reverse_az=False):

        self.res_az = res_az
        self.res_alt = res_alt
        self.reverse_az = reverse_az
        self.reverse_alt = reverse_alt
        self.serial = None

    def connect(self, port, speed=9600):
        if self.serial is not None:
            logging.warning('AltAzEncoders: self.serial is not None and connecting!')
        self.port = port
        self.serial = serial.Serial(port, speed, timeout=5)
        #time.sleep(5)
        #self.get_encoder_resolution()
        logging.warning('Not setting encoder resolution - doesnt work yet!')
        #self.set_encoder_resolution(self.steps_alt, self.steps_az)

    def get_encoder_resolution(self):
        if self.serial is None:
            logging.error('get_encoder_resolution: not connected!')
            return None

        self.serial.write(b'h')
        resp = self.serial.read(4)
        logging.debug(f'get_encoder_resolution resp = {resp}')

        if len(resp) != 4:
            logging.error(f'get_encoder_resolution: expected 4 bytes got {len(resp)}')
        else:
            alt_steps = int.from_bytes(resp[0:2], 'little')
            az_steps = int.from_bytes(resp[2:4], 'little')
            logging.debug(f'get_encoder_resolution:  alt_steps={alt_steps}, az_steps={az_steps}')

    def get_encoder_position(self):
        if self.serial is None:
            logging.error('get_encoder_position: not connected!')
            return None

        self.serial.write(b'y')
        resp = self.serial.read(4)
        logging.debug(f'get_encoder_position resp = {resp}')

        if len(resp) != 4:
            logging.error(f'get_encoder_position: expected 4 bytes got {len(resp)}')
            return None
        else:
            alt_steps = int.from_bytes(resp[0:2], 'little')
            az_steps = int.from_bytes(resp[2:4], 'little')
            #logging.debug(f'get_encoder_position:  alt_steps={alt_steps}, az_steps={az_steps}')
            return alt_steps, az_steps

#    def set_encoder_resolution(self, steps_alt, steps_az):
#        if self.serial is None:
#            logging.error('set_encoder_resolution: not connected!')
#            return None
#
#        enc_alt_steps = int.to_bytes(steps_alt, 2, 'little')
#        enc_az_steps = int.to_bytes(steps_az, 2, 'little')
#
#        logging.debug(f'set_encoder_resolution:  enc_alt_steps={enc_alt_steps}, enc_az_steps={enc_az_steps}')
#        self.serial.write(b'z')
#        self.serial.write(enc_alt_steps)
#        self.serial.write(enc_az_steps)
#
#        self.steps_alt = steps_alt
#        self.steps_az = steps_az




def parse_command_line():
    parser = argparse.ArgumentParser()
#    parser.add_argument('--listprofiles', action='store_true', help='List astroprofiles available')
#    parser.add_argument('--profile', type=str, help='Name of astro profile')
#    parser.add_argument('--seqtemplate', type=str, help='Name of sequence template to use')
#    parser.add_argument('--project', type=str, help='Name of project to observe')
#    parser.add_argument('--slewzenith', action='store_true', help='Slew to near zenith first')
#    parser.add_argument('--blindsolve', action='store_true', help='Start with blind solve')
#    parser.add_argument('--runsimul', action='store_true', help='Run simulation')

    parser.add_argument('--debug', action='store_true', help='Set log level DEBUG')

    args = parser.parse_args()
    logging.debug(f'cmd args = {args}')
    return args

def main(args):

    encoders = AltAzEncoders()
    encoders.connect('COM24')

    # create alpaca device object
    device = TestTelescopeDevice(encoders)

    # start api server
    api_server = AlpacaDeviceServer(device)
    api_server.start()
    logging.info('Alpaca API server started')


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
    logfilename = 'test_alpaca_server'
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



