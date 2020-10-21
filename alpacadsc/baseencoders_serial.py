#
#  Base encoder driver for digital setting circles using a serial connection
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

import time
import logging
import serial

from .baseencoders import EncodersBase


class EncodersSerial(EncodersBase):
    """ Base class for all DSC drivers using a serial port. """

    # set to false so scan for drivers will skip over this one
    # as it is also a subclass for EncodersBase but is not
    # a fully implemented driver
    _is_plugin = False

    def __init__(self, res_alt=4000, res_az=4000,
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
        self.serial = None

    def name(self):
        raise NotImplementedError

    def connect(self, port, speed=9600):
        """
        The driver should connect to the digital setting circles hardware
        when this method is called.

        :param port: Serial device to which digital setting circles is connected.
        :type action: str
        :param res_alt: Speed for serial connection.
        :type action: int
        :returns: True is successful.
        :rtype: bool

        """

        if self.serial is not None:
            logging.warning('AltAzEncoders: self.serial is not None and connecting!')

        logging.info(f'Connecting to f{self.name} style DSC '
                     f' on port {port} at speed {speed}.')

        self.port = port
        self.serial = serial.Serial(port, speed, timeout=5)

        # some arduino based dsc will need time as they reset when opened
        time.sleep(5)

        # set resolution
        self.set_encoder_resolution(self.res_alt, self.res_az)
        return True

    def disconnect(self):
        """
        Disconnect.

        :returns: True is successful.
        :rtype: bool

        """

        if self.serial is not None:
            self.serial.close()
        self.serial = None

    def get_encoder_resolution(self):
        """
        Read the encoders resolution from the digital setting circles hardware.

        :returns:
            (tuple)  The resolution of the altitude and azimuth encoders.

        """
        raise NotImplementedError

    def get_encoder_position(self):
        """
        Read the encoders resolution from the digital setting circles hardware.

        :returns:
            (ttuple)  The position of the altitude and azimuth encoders.

        """
        raise NotImplementedError

    def set_encoder_resolution(self, res_alt, res_az):
        """
        Read the encoders resolution from the digital setting circles hardware.

        :param res_alt: Resolution (steps/rev) of altitude encoder.
        :type action: int
        :param res_alt: Resolution (steps/rev) of azimuth encoder.
        :type action: int

        """
        raise NotImplementedError
