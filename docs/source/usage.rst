
*****
Usage
*****

Author: Michael Fulbright

Contact: mike.fulbright@pobox.com

Date: 2020-09-29

Installation
............
The Alpaca Digital Setting Circles Driver (ADSCD) can be installed from source.
It supports setup.py so the package can be installed using the command:

python setup.py install

Alternately a distribution package can be created with:

python setup.py bdist_wheel

The resulting package can be installed with:

pip install <bdist_file>

where <bdist_file> will be the newly created package in the 'dist/' folder.

Starting The Alpaca Service
...........................
You will need to start the Alpaca service which will
allow software to connect with your setting circles.  The command to do this is:

python -m AlpacaSettingCirclesDriver.StartService

The service will start and by default listens to the port 8000 on the local host.


Configuration
.............
Before connecting to the Alpaca service you will need to configure a profile for your
equipment.

.. note::
    You cannot configure the Alpaca server if a program is currently connected
    to the service so be sure to disconnect all clients before attempting
    configuration.


The configuration page is available by connecting a browser to:

http://localhost:8000/setup/v1/telescope/0/setup

As a convenience if you connect to:

http://localhost:8000

a link will be provided to get to the actual configuration page.


Profiles
""""""""
The first step is to create a new profile for your equipment.  This is done using
the "Create New Profile" button.  Fill in the box next to the button with the
name of the new profile and click the button.  If successful a new page will load
confirming the new profile has been created.  Use the link to return to the
configuration page.

When a new profile is created the current profile used for the service will
be set to the new profile.  If you want to change the current profile to a
previously created profile use the "Change Profile" button.  A new page will
load showing all the available profiles with a checkbox next to each one.
Select the checkbox for the profile you want to switch to and then click
the "Change Profile" button.

The current profile will automatically be loaded whenever the service is started.

Profiles are stored as YAML formatted files.  Under Linux they are stored
in "$(HOME)/.config/AlpacaSettingCirclesDriver" and under Windows in
"%APPDATA%/AlpacaSettingCirclesDriver".  If you want to backup your settings
or move them to another computer you can copy the profiles stored here.  The
current profile name is stored in the file "current_profile.yaml".



Location
""""""""
The observing location needs to be set for each profile.  This consists of
the name of the location (a string) as well as the latitude, longitude and
altitude (meters).  Specify the latitude and longitude as decimal degrees and
use a negative longitude for Western latitudes.

For example, if the location is latitude equal to 36d40m20s North and longitude was
30d30m10s West, first convert the sexagesimal degrees to decimal degrees yielding
36.67222 North, 30.502778 W.  Since the longitude is a Western one then convert
it to a negative value so you would use "36.67222" for the latitude and
"-30.502778" as the longitude.

There are websites that can convert sexagesimal degrees to decimal degrees as
well as many calculators have a function to perform this conversion.

Once these settings are entered use the "Save Changes" button to make them
permanent.  The button only saves the location settings.

""""""""
Encoders
""""""""
The encoders used by the digital setting circles (DSC) also need to be configured.

Currently the Alpaca service only supports DSC which use the "Dave Eks" protocol
so the "Driver" should be set to "DaveEk".

The serial port should be configured to match the port the DSC is connected to -
there will be some suggested ports based on the available ports on the computer.

The serial speed must match that of the DSC - 9600 is typical.

The resolution of the encoders on the altitude and azimuth axes must also be
specified.  Common values are 4000, 8000 or 10000.  If this value is wrong
then the service will not properly track the scope as it is moved.

Finally two checkboxes are available to tell the service the altitude and/or
azimuth encoder outputs need to be reversed.  If you move the scope one way
and it moves the opposite direction in your software connected to the service
then try reversing the axis.

Once these settings are entered use the "Save Changes" button to make them
permanent.  The button only saves the encoder settings.
