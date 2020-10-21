#
# Alpaca driver method implementations
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

from marshmallow import fields, Schema, ValidationError
from marshmallow.validate import Range


def field_right_ascension(*args, **kwargs):
    """ Fields descriptor for right ascension """
    return fields.Float(*args,
                        **kwargs,
                        validate=Range(min=0, min_inclusive=True,
                                       max=24, max_inclusive=False))


def field_declination(*args, **kwargs):
    """ Fields descriptor for declination """
    return fields.Float(*args,
                        **kwargs,
                        validate=Range(min=-90, min_inclusive=True,
                                       max=90, max_inclusive=True))


def field_longitude(*args, **kwargs):
    """ Fields descriptor for longitude """
    return fields.Float(*args,
                        **kwargs,
                        validate=Range(min=-180, min_inclusive=True,
                                       max=180, max_inclusive=True))


def field_latitude(*args, **kwargs):
    """ Fields descriptor for latitude """
    return fields.Float(*args,
                        **kwargs,
                        validate=Range(min=-90, min_inclusive=True,
                                       max=90, max_inclusive=True))


def _put_handler(arglist, form):
    """
    Create a handler dynamically for a field.

    Expects a dictionary containing of the form:

        {form_id: field}

    Where form_id is the field id in the form data and field is the
    the marshmallow field validator for that data.

    Returns a dict using the lower case version of form_id as the key
    and the value is the matching data from the form data.

    :param arglist: Dictionary containing descriptors of field
    :type arglist: dict
    :param form: Request form data
    :type form: dict
    :return: Dictionary containing values extracted from form data
    :rtype: dict

    """

    d = {}
    for key, field in arglist.items():
        d[key] = field(required=True, attribute=key.lower())

    d['ClientID'] = fields.Integer(required=True)
    d['ClientTransactionID'] = fields.Integer(required=True)

    schema = Schema.from_dict(d)
    result = None
    try:
        try_result = schema().load(form)
    except ValidationError:
        logging.error('_put_handler: failed to validate')
    except ValueError:
        logging.error('_put_handler: invalid values')
    else:
        result = {}
        for key in arglist:
            result[key.lower()] = try_result[key.lower()]

    return result


class AlpacaBaseService():
    """ Handle PUT REST API methods common to all Alpaca devices """

    def __init__(self, driver):
        self.driver = driver

    def connected(self, form):
        """
        Handle request to connect/disconnect the driver from hardware.

        :param form: PUT form data as a dict
        :type form: dict
        :return: Success code - True means success.
        :rtype: bool

        """

        value = _put_handler({'Connected': fields.Boolean}, form)
        if value is not None:
            if value['connected']:
                rc = self.driver.connect()
            else:
                rc = self.driver.disconnect()
            return rc
        else:
            return False


class AlpacaTelescopeService():
    """ Handle PUT REST API command for the Alpaca telescope driver. """

    def __init__(self, driver):
        self.driver = driver

    def siteelevation(self, form):
        """
        Handle request to set site elevation.

        :param form: PUT form data as a dict
        :type form: dict
        :return: Success code - True means success.
        :rtype: bool

        """

        value = _put_handler({'SiteElevation': fields.Float}, form)
        if value is not None:
            self.driver.sitelevation = value['siteelevation']
            return True
        else:
            return False

    def sitelatitude(self, form):
        """
        Handle request to set site latitude.

        :param form: PUT form data as a dict
        :type form: dict
        :return: Success code - True means success.
        :rtype: bool

        """

        value = _put_handler({'SiteLatitude': field_latitude}, form)
        if value is not None:
            self.driver.sitelatitude = value['sitelatitude']
            return True
        else:
            return False

    def sitelongitude(self, form):
        """
        Handle request to set site longitude.

        :param form: PUT form data as a dict
        :type form: dict
        :return: Success code - True means success.
        :rtype: bool

        """

        value = _put_handler({'SiteLongitude': field_longitude}, form)
        if value is not None:
            self.driver.sitelongitude = value['sitelongitude']
            return True
        else:
            return False

    def synctoaltaz(self, form):
        """
        Handle request to sync mount to an alt/az position.

        :param form: PUT form data as a dict
        :type form: dict
        :return: Success code - True means success.
        :rtype: bool

        """

        # FIXME Need to implement
        logging.warning('AlpacaTelescopeServer.synctoaltaz() not implemented!')
        return False

    def synctocoordinates(self, form):
        """
        Handle request to sync mount to a ra/dec position.

        :param form: PUT form data as a dict
        :type form: dict
        :return: Success code - True means success.
        :rtype: bool

        """

        value = _put_handler({'RightAscension': field_right_ascension,
                              'Declination': field_declination}, form)
        if value is not None:
            rc = self.driver.sync_to_coordinates(value['rightascension'],
                                                 value['declination'])
            return rc
        else:
            return False
