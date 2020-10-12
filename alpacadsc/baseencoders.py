#
#  Encoder driver class definition
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


from abc import ABCMeta, abstractmethod

class EncodersBase(metaclass=ABCMeta):
    """ Base class for all encoder drivers. """

    @abstractmethod
    def __init__(self):
        pass

    @abstractmethod
    def name(self):
        """
        Returns the human readable name for this driver.

        """
        pass

    @abstractmethod
    def connect(self):
        """
        The driver should connect to the digital setting circles hardware
        when this method is called.
        """
        pass

    @abstractmethod
    def disconnect(self):
        """
        The driver should disconnect to the digital setting circles hardware
        when this method is called.
        """
        pass

    @abstractmethod
    def get_encoder_resolution(self):
        """
        Read the encoders resolution from the digital setting circles hardware.

        :returns:
            (ttuple)  The resolution of the altitude and azimuth encoders.

        """
        pass

    @abstractmethod
    def get_encoder_position(self):
        """
        Read the encoders resolution from the digital setting circles hardware.

        :returns:
            (ttuple)  The position of the altitude and azimuth encoders.

        """
        pass

    @abstractmethod
    def set_encoder_resolution(self, res_alt, res_az):
        """
        Read the encoders resolution from the digital setting circles hardware.

        :param res_alt: Resolution (steps/rev) of altitude encoder.
        :type action: int
        :param res_alt: Resolution (steps/rev) of azimuth encoder.
        :type action: int

        """
        pass


class A(EncodersBase):
    def __init__(self):
        pass
