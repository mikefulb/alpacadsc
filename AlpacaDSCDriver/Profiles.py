#
# General profile storage persistently for program options
#
# Copyright 2020 Michael Fulbright
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
import os
import logging
from dataclasses import dataclass
from pathlib import Path
import yaml


def get_base_config_dir():
    """
    Find base path for where to store config files depending on platform.

    :returns:
        (Path) Root path of where config files are stored
    :raises FileNotFoundError: If base path cannot be determined.
    """
    if os.name == 'nt':
        basedir = Path(os.path.expandvars('%APPDATA%'))
    elif os.name == 'posix':
        basedir = Path.home() / '.config'
    else:
        logging.error('Profile: Unable to determine OS for config_dir loc!')
        raise FileNotFoundError
    return basedir


def find_profiles(loc):
    """
    Return list of existing profiles in given location loc.  The location loc is
    relative to the base path for config files for the given platform.

    :param loc: Directory relative to base config path to search for profiles
    :type loc: str

    :note: Assumes profile configuration files end with '.yaml'

    :returns:
        (List[str]) List of profiles found or [] if none available.
    """
    config_path = get_base_config_dir() / loc
    config_files = config_path.glob('*.yaml')
    return sorted(x.name for x in config_files if x.name != 'current_profile.yaml')


def set_current_profile(loc, current_profile_name):
    """
    Write current_profile.yaml file with name of current profile.

    :param loc: Directory relative to base config path to search for profiles
    :type loc: str

    :param current_profile_name: Name of current active profile - do NOT include
                                 a '.yaml' extension on the profile name.
    :type current_profile_name: str

    :returns:
        (bool) Whether operation was successful or not

    """
    basedir = get_base_config_dir() / loc

    dataobj = {'current_profile' : current_profile_name}
    yaml_cur_file = basedir / 'current_profile.yaml'
    with yaml_cur_file.open('w') as yaml_f:
        yaml.dump(dataobj, stream=yaml_f, default_flow_style=False)

    return True


def get_current_profile(loc):
    """
    Read current_profile.yaml file to get name of current profile.

    :param loc: Directory relative to base config path to search for profiles
    :type loc: str

    :returns:
        (str) Name of currently active profile or None if none defined.

    """
    basedir = get_base_config_dir() / loc

    yaml_cur_file = basedir / 'current_profile.yaml'

    # see if file exists and if it doesn't then there is no current profile
    if not yaml_cur_file.exists():
        return None

    d = {}
    with yaml_cur_file.open('r') as yaml_f:
        d = yaml.safe_load(stream=yaml_f)

    return d.get('current_profile', None)


@dataclass
class ProfileSection(object):
    """
    A ProfileSection is a subtree member of a Profile and contains its own
    set of key/value pairs.  Multiple ProfileSection's can be added to a
    Profile to give parameters different namespaces in the Profile.'
    """

    def _property_keys(self):
        """
        Return a list of the property names in this ProfileSection.
        """
#        logging.info(f'{self.__class__.__name__}._property_keys()')
#        logging.info(f'{self.__dict__}')
#        for k, v in self.__dict__.items():
#            logging.info(f'   {k}   {v}')
        return sorted(x for x in self.__dict__ if x[0] != '_')

    def _to_dict(self):
        """
        Convert ProfileSection to a dictionary which can be used to
        produce a yaml output file.

        :returns:
            (dict) Dictionary representation of ProfileSection
        """
        #logging.info(f'class {self.__class__.__name__}.to_dict():')
        d = {}
        #logging.info(f' property_keys = {self._property_keys()}')
        #logging.info(f' dir(self) = {dir(self)}')
        for k in self._property_keys():
            #logging.info(f'   {k}  {self.__dict__[k]}')
            d[k] = self.__dict__[k]
        return d

    def _from_dict(self, d):
        """
        Initialize a ProfileSection from a dictionary.

        :param d: Dictionary to use to initialize object.
        :type d: dict
        """
        #logging.info(f'ProfileSection _from_dict {d}')
        for k, v in d.items():
            #logging.info(f' copying key {k} value = {v}')
            self.__dict__[k] = v
        #logging.info(f' final __dict__ = {self.__dict__}')

    def get(self, key, default=None):
        """
        Retrieve parameter from ProfileSection by key name.  Default value
        used if key not found in ProfileSection.

        :param key: Name of parameter to retrieve
        :type key: str
        :param default: Optional default value if key not present
        :returns:
            Parameter value or default value if not present.
        """
        try:
            val = self.__getattribute__(key)
        except AttributeError:
            val = default
        return val

    def __repr__(self):
        """
        Returns string representation of ProfileSection
        """
        s = f'{self.__class__.__name__}('
        ks = self.property_keys()
        i = 0
        #print(f'\n{ks}\n')
        for k in ks:
            if k == '_sectionname':
                continue
            s += f'{k}={self.__dict__[k]}'
            if i != len(ks) - 1:
                s += ', '
            i += 1
        s += ')'
        return s


class Profile:

    """
    Stores program settings which can be saved persistently.  Supports
    ProfileSection's which allow a hierarchical namespace for parameters.
    """

    def __init__(self, reldir, name=None):
        """
        Set some defaults for program settings

        :param reldir: location relative to top of default config location
                 If None then will be relative to current working directory.
        :type reldir: str
        :param name: name of profile config file
        :type name: str


        Note: reldir = "hfdfocus/" and name = "C8F7.yaml" would create
        a file  <configbasedir>/hfdfocus/C8F7.yaml


        """
        self._config_reldir = reldir

        self._config_filename = name

        logging.debug(f'self._config_filname = {self._config_filename}')
        logging.debug(f'self._config_reldir = {self._config_reldir}')

        self.sections = {}

    def add_section(self, sectionclass):
        """
        Add a section to Profile.

        :param sectionclass: Section to be added.
        :type sectionclass: ProfileSection
        """
        self.sections[sectionclass._sectionname] = sectionclass
        self.__dict__[sectionclass._sectionname] = sectionclass()

    def _get_config_dir(self):
        """
        Find base path for where to store config files depending on platform.

        :returns:
            (Path) Root path of where config files are stored or None if location
            could not be determined for platform.
        """

        if self._config_reldir is None:
            return Path('.')

        return get_base_config_dir() / self._config_reldir

    def _get_config_filename(self):
        """
        Create full path to profile config file

        :returns:
            (Path) Full path to profile config file.
        """
        return Path(self._get_config_dir()) / self._config_filename

    def filename(self):
        """
        Return profile config filename.

        :returns:
            (Path) Profile filename
        """
        return self._get_config_filename()

    def write(self):
        """
        Write profile config file.

        :returns:
            (bool) Whether or not write succeeded.
        """
        # NOTE will overwrite existing without warning!
        logging.debug(f'Configuration files stored in {self._get_config_dir()}')

        # check if config directory exists
        if not self._get_config_dir().is_dir():
            if self._get_config_dir().exists():
                logging.error(f'write settings: config dir {self._get_config_dir()}' + \
                              ' already exists and is not a directory!')
                return False
            else:
                logging.info(f'write settings: creating config dir {self._get_config_dir()}')
                self._get_config_dir().mkdir(parents=True)

        logging.info(f'write() config filename: {self._get_config_filename()}')

        # to_dict() must be defined by child class
        # dataobj = {}
        # for k, v in self.sections.items():
        #     dataobj[k] = self.__dict__[k]._to_dict()
        dataobj = self._to_dict()

        with self._get_config_filename().open('w') as yaml_f:
            yaml.dump(dataobj, stream=yaml_f, default_flow_style=False)

        return True

    def read(self):
        """
        Read profile config file.

        :returns:
            (bool) Whether or not read succeeded.
        """
        with self._get_config_filename().open('r') as yaml_f:
            d = yaml.safe_load(stream=yaml_f)

        # from_dict() must be defined in child
        for k, v in d.items():
            self.__dict__[k] = self.sections[k]()
            self.__dict__[k]._from_dict(v)
        return True

    def _to_dict(self):
        dataobj = {}
        for k, v in self.sections.items():
            dataobj[k] = self.__dict__[k]._to_dict()
        return dataobj

    def __repr__(self):
        """
        Return string representation of Profile

        :returns:
            (str) String representation of Profile
        """
        s = f'{self.__class__.__name__}('
        ks = self.sections.keys()

        i = 0
        for k in ks:
            if k[0] == '_':
                continue
            s += f'{k}={self.__dict__[k]}'
            if i != len(ks) - 1:
                s += ', '
            i += 1
        s += ')'
        return s
