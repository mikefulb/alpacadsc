#
#  Encoder driver for Dave Ek's style setting circles
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
import serial


class EncodersAltAzDaveEk:

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

    def disconnect(self):
        if self.serial is not None:
            self.serial.close()
        self.serial = None

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
