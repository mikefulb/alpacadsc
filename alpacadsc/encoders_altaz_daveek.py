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

from .baseencoders_serial import EncodersSerial


class EncodersDaveEk(EncodersSerial):

    _is_plugin = True

    def name(self):
        return "DaveEk"

    def get_encoder_resolution(self):
        """
        Read the encoders resolution from the digital setting circles hardware.

        :returns:
            (tuple)  The resolution of the altitude and azimuth encoders.

        """
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
            logging.debug(f'get_encoder_resolution:  alt_res={alt_steps}, '
                          f'az_res={az_steps}')
            return alt_steps, az_steps

    def get_encoder_position(self):
        """
        Read the encoders resolution from the digital setting circles hardware.

        :returns:
            (ttuple)  The position of the altitude and azimuth encoders.

        """
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
            logging.debug(f'get_encoder_position:  alt_steps={alt_steps}, '
                          f'az_steps={az_steps}')
            return alt_steps, az_steps

    def set_encoder_resolution(self, res_alt, res_az):
        """
        Read the encoders resolution from the digital setting circles hardware.

        :param res_alt: Resolution (steps/rev) of altitude encoder.
        :type action: int
        :param res_alt: Resolution (steps/rev) of azimuth encoder.
        :type action: int

        """
        logging.debug('set_encoder_resolution:  setting resolution to '
                      f'res_alt={res_alt}, '
                      f'res_az={res_az}')
        enc_res_alt = int.to_bytes(res_alt, 2, 'little')
        enc_res_az = int.to_bytes(res_az, 2, 'little')

        logging.debug(f'set_encoder_resolution:  enc_res_alt={enc_res_alt}, '
                      f'enc_res_az={enc_res_az}')
        self.serial.write(b'z')
        self.serial.write(enc_res_alt)
        self.serial.write(enc_res_az)

        self.res_alt = res_alt
        self.res_az = res_az
