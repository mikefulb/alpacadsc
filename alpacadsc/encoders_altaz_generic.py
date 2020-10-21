#
#  Encoder driver using generic setting circles commands for devices
#  like BBox, Intelliscope, NGCMax
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


class EncodersGeneric(EncodersSerial):

    _is_plugin = True

    def name(self):
        return "Generic"

    def get_encoder_resolution(self):
        """
        Read the encoders resolution from the digital setting circles hardware.

        :returns:
            (ttuple)  The resolution of the altitude and azimuth encoders.

        """
        if self.serial is None:
            logging.error('get_encoder_resolution: not connected!')
            return None

        self.serial.write(b'H\r\n')
        resp = self.serial.read_until(b'\r')
        logging.debug(f'get_encoder_resolution resp = {resp}')
        resp = resp.decode('utf-8').strip()

        fields = resp.split('\t')
        if len(fields) != 2:
            logging.error('get_encoder_resolution: unexpected response!')
            return None
        else:
            alt_steps = int(fields[0])
            az_steps = int(fields[1])
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

        logging.info('sending request')
        self.serial.write(b'Q\r\n')
        logging.info('request sent')
        resp = self.serial.read_until(b'\r')
        logging.debug(f'get_encoder_position resp = {resp}')
        resp = resp.decode('utf-8').strip()

        fields = resp.split('\t')
        if len(fields) != 2:
            logging.error('get_encoder_position: unexpected response!')
            return None
        else:
            alt_steps = int(fields[0])
            az_steps = int(fields[1])
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
        cmd = f'Z{res_alt:+d} {res_az:+d}\r\n'.encode('utf-8')
        logging.debug(f'set encoder resolution cmd is "{cmd}"')
        self.serial.write(cmd)
        resp = self.serial.read(1)
        logging.debug(f'set_encoder_position resp = {resp}')
        if resp == b'*':
            logging.debug('Set resolution succeeded')
            self.res_alt = res_alt
            self.res_az = res_az
            return True
        else:
            logging.error('Set resolution failed!')
            return False
