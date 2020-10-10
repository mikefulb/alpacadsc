
*****
Usage
*****

.. highlight:: console

Installation
............
The Alpaca Digital Setting Circles Driver (ADSCD) can be installed from source.
It supports setup.py so the package can be installed using the command:

::

    python3 setup.py install

Alternately a distribution package can be created with:

::

    python3 setup.py bdist_wheel

The resulting package can be installed with:

::

    python3 -m pip install <bdist_file>

where `<bdist_file>` will be the newly created package in the "dist/" folder.

Other options available are:

 - Rebuilding the documentation into the directory docs/build/html.

   ::

     python3 setup.py build_sphinx

 - Run several tests on the code base.

   ::

     python3 setup.py test`

Starting The Alpaca Service
...........................
You will need to start the Alpaca service which will
allow software to connect with your setting circles.  The command to do this
on Linux is:

::

    alpacadsc

and on Windows would be:

::

    alpacadsc.exe

You can also start the service by invoking the module via python:

::

    python -m alpacadsc.startservice

The service will start and by default listens to the port 8000 on the local host.

.. warning::

    The service will run a web server on your system that will listen for
    incoming connections from Alpaca clients.  It should only
    listen for connections from your local computer.  At this point `alpacdsc`
    is still in development and such the test server built into Flask is being
    used.  You will see a warning when you start the service that says this.
    The intention long term is to move off the internal Flask server.

Command Line Options
""""""""""""""""""""

The service accepts several command line options:

.. program:: alpacadsc

.. option:: --port port

   Sets the port that the Alpaca service will listen to for client connections.
   The default value is 8000.

.. option:: --profile PROFILE

   Use the configuration profile :strong:`PROFILE`.  If none is supplied then
   the last profile used will be loaded.

.. option:: --listprofiles

   List all profiles which are currently defined.

.. option:: --debug

   Show additional debugging information in log file.

Log File Output
"""""""""""""""

A log file will be created in the directory from which the service was started
and has a filename of the format `alpacadsc-<dateime>.log` where
`datetime` is a timestamp of when the service was started.  This file can be
helpful when trying to track down problems or reporting an issue you may encounter.

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

or:

    http://localhost:8000/setup


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
Optionally the `--profile` command line option can be used to specify the profile
to be used.  To get a list of available profiles use the `--listprofiles` command
line option.

Profiles are stored as YAML formatted files.  The location of the profile
files depends on the platform:

======= ================================
Linux   $(HOME)/.config/alpacadsc
Windows %APPDATA%/alpacadsc
======= ================================

If you want to backup your settings or move them to another computer you can
copy the profiles stored here.  The current profile name is stored in the file
"current_profile.yaml".

The location configuration in the YAML file are stored in an array called
"location" with the following keys:

============= ======================== =============
Key                  Data Type            Notes
============= ======================== =============
  obsname          String               Human readable name of location
  longitude        Float                Longitude as decimal degrees
  latitude         Float                Latitude as decimal degrees
  altitude         Float                Altitude in meters
============= ======================== =============

An example is:

.. code-block:: yaml

    location:
        obsname: Observatory
        longitude: 100.0
        latitude: 30.0
        altitude: 450.0

The encoder configuration in the YAML file are stored in an array called
"encoders" with the following keys:

=============== =========== ====================================================
Key             Data Type   Notes
=============== =========== ====================================================
driver          String      Name of driver - currently "DaveEk" is only allowed
serial_port     String      Serial port device name
serial_speed    Integer     Serial port speed
alt_resolution  Integer     Tics per revolution for alt encoder
az_resolution   Integer     Tics per revolution for alt encoder
alt_reverse     Boolean     If true then reverse alt axes
az_reverse      Boolean     If true then reverse alt axes
=============== =========== ====================================================

An example is:

.. code-block:: yaml

    encoders:
      alt_resolution: 4000
      alt_reverse: false
      az_resolution: 4000
      az_reverse: false
      driver: DaveEk
      serial_port: /dev/ttyUSB1
      serial_speed: 9600


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

Using With Planetarium Software
...............................

First start the Alpaca DSC driver service as shown in the section
:ref:`Starting The Alpaca Service`.

Then use your software to connect to the service.  The software must support
Alpaca to work with this driver.  You will want to configure the server IP
as 127.0.0.1 or "localhost" and the server port as 8000.

Once connected to the Alpaca DSC driver service the driver will still need to
be synchronized with the sky before it can report the position of the telescope.
This is done by finding a star in your planetarium program and then manually
pushing the telescope so the same star is centered in the eyepiece.  Now use
the "Sync" command in your program to tell the driver to sync on the current
position.  This will let the driver know the current telescope position and
from then on the driver will report the ALT/AZ and RA/DEC values as the telescope
is moved around.

For best results choose a star to synchronize on which is close to the area of
the sky you will be observing.  If you move to another part of the sky then
you can synchronize on a new star in that region.  The sync operation will
override the previous one.

The synchronization with the sky is lost when the driver exits.

Debugging Encoders
..................
There is a debugging web page generated by the driver which reports the
current encoder raw counts if the driver is connected.  If the driver has been
synchronized with a star then it will also report the current ALT/AZ and RA/DEC
position.


