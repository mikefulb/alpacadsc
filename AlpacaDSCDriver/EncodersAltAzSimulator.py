#
#  Encoder driver for simulated setting circles
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

class EncodersAltAzSimulated:

    def __init__(self, res_alt=4000, res_az=4000, reverse_alt=False, reverse_az=False):

        self.res_az = res_az
        self.res_alt = res_alt
        self.reverse_az = reverse_az
        self.reverse_alt = reverse_alt

    def connect(self, port, speed=9600):
        return True

    def disconnect(self):
        return True

    def get_encoder_resolution(self):
        logging.debug(f'get_encoder_resolution:  alt_steps={self.res_alt}, az_steps={self.res_az}')
        return self.res_alt, self.res_az

    def get_encoder_position(self):
        alt_steps = 2000
        az_steps = 2000
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
