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

from .baseencoders import EncodersBase


class EncodersAltAzSimulator(EncodersBase):

    def __init__(self, res_alt=4000, res_az=4000, *,
                 reverse_alt=False, reverse_az=False):
        """
        :param res_alt: Altitude encoder resolution, defaults to 4000
        :type res_alt: int, optional
        :param res_az: Azimuth encoder resolution, defaults to 4000
        :type res_az: int, optional
        :param reverse_alt: Reverse altitude axis, defaults to False
        :type reverse_alt: bool, optional
        :param reverse_az: Reverse azimuth axis, defaults to False
        :type reverse_az: bool, optional

        """
        self.res_az = res_az
        self.res_alt = res_alt
        self.reverse_az = reverse_az
        self.reverse_alt = reverse_alt

    def name(self):
        return "Simulator"

    def connect(self, port, speed=9600):
        """
        The driver should connect to the digital setting circles hardware
        when this method is called.

        Note: port and speed ignored in this simulator driver.

        :param port: Serial device to which digital setting circles is connected.
        :type action: str
        :param res_alt: Speed for serial connection.
        :type action: int
        :returns: (bool) True is successful.
        """
        return True

    def disconnect(self):
        return True

    def get_encoder_resolution(self):
        """
        Read the encoders resolution from the digital setting circles hardware.

        :returns:
            (ttuple)  The resolution of the altitude and azimuth encoders.

        """
        logging.debug(f'get_encoder_resolution:  alt_steps={self.res_alt}, '
                      f'az_steps={self.res_az}')
        return self.res_alt, self.res_az

    def get_encoder_position(self):
        """
        Read the encoders resolution from the digital setting circles hardware.

        :returns:
            (ttuple)  The position of the altitude and azimuth encoders.

        """
        alt_steps = 2000
        az_steps = 2000
        return alt_steps, az_steps

    def set_encoder_resolution(self, res_alt, res_az):
        """
        Read the encoders resolution from the digital setting circles hardware.

        :param res_alt: Resolution (steps/rev) of altitude encoder.
        :type action: int
        :param res_alt: Resolution (steps/rev) of azimuth encoder.
        :type action: int

        """
        self.res_alt = res_alt
        self.res_az = res_az
