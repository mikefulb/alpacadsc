.. sectnum::

==============================================================
Design Specification For Alpaca Digital Setting Circles Driver
==============================================================

Author: Michael Fulbright

Contact: mike.fulbright@pobox.com

Status: Initial draft

Date: 2020-09-04

---------------
Introduction
---------------

.......
Purpose
.......
The main purpose of this document is to outline the requirements of
the Alpaca Digital Setting Circles Driver (hereafter "DSC driver").  This
specification will cover the user experience as well as address some details
of the technical implementation.

The digital setting circles (DSC) is a device which interfaces which each moveable
axis of a telescope and tracking change sin position.  The most common use is on
a dobsonian telescope which has altitude (ALT) and azimuth (AZ) axes.  The ALT
axis moves from the horizon to straight overhead (the zenith), while the AZ
axis corresponds to the distance from North around the horizon.  These together
allow the specification of any point in the sky.

By reading the changes in the ALT and AZ position of the telescope a program
can track the telescope and determine where it is pointing in the night sky.
A planetarium program can be used which also has a database of sky objects and
so the telescope position can be plotted against the known objects.  This allows
user ("observer") to find objects by moving the telescope until it is at the desired
object.

.....
Scope
.....
The DSC Driver will allow users to:

- connect to a DSC using an application which supports Alpaca
- edit the configuration of the DSC (serial port, encoder resolution, etc)
- edit the geographical location where the observer is location
- synchronize the telescope location via a planetarium program
- once synchronized the user can get locate objects using the planetarium program

...................
Technical Ovewview
...................

~~~~~~~~~~~~~~~~~~~
Supported Platforms
~~~~~~~~~~~~~~~~~~~
The DSC driver will support Windows and Linux targets initially.  In theory the
driver should work on any platform which supports Python 3.

~~~~~~~~~~~~~~~~~~~~~~~~
Communication Interfaces
~~~~~~~~~~~~~~~~~~~~~~~~
The DSC driver will listen on a TCP port for REST API requests which are how an
Alpaca driver communicates with clients.

The DSC driver will also communicate with the DSC device.  This is normally
a serial interface such as RS232 or a USB<->RS232 adapter.  Wireless operation
using a serial stream via Bluetooth or WiFi is also possible.

~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Assumptions and Dependencies
~~~~~~~~~~~~~~~~~~~~~~~~~~~~
The DSC driver uses Python 3.7 and depends on <insert python web framework>
web framework to implement the REST API server needed for Alpaca.  The *pyserial*
module is used for commincating with serial devices.

Currently the driver assumes an ALT/AZ arrangement for the telescope.  It would
be possible to support a RA/DEC arrangement (like a German Equatorial Mount (GEM)),
but this is beyond the scope of the current implementation.

................
Requirements
................

~~~~~~~~~
Functions
~~~~~~~~~

'''''''''''''''''''''''
Alpaca Telescope Driver
'''''''''''''''''''''''
The Alpaca driver listens on a TCP socket for REST API requests from clients. There
are several classes of devices supported by Alpaca such as cameras, telescope,
filter wheels, etc.  The DSC Driver is a telescope device.  The entire API for a
telescope device is not implemented however, as this is not required for a DSC device.

The entire Alpaca API for a telescope device is NOT implemented, but only those
sufficient to get a planetarium program working.  The program *Cartes du Ciel*
was used for testing - other programs may require additional API components to
be implemented.

The following Alpaca API interfaces are implemented:

======================== === === =====================================================
Name                     GET SET Notes
======================== === === =====================================================
alignmentmode            YES NO  Returns ALPCA_ALIGNMENT_ALTAZ
altitude                 YES NO  Need to implement SET
aperturearea             YES NO  Need to implement SET
aperturediameter         YES NO  Need to implement SET
athome                   YES NO  Returns FALSE
atpark                   YES NO  Retursn FALSE
axisrates                YES NO  Returns empty list
azimuth                  YES NO
canfindhome              YES NO  Returns FALSE
canmoveaxis              YES NO  Returns FALSE
canpark                  YES NO  Returns FALSE
canpulseguide            YES NO  Returns FALSE
cansetdeclinationrate    YES NO  Returns FALSE
cansetguiderates         YES NO  Returns FALSE
cansetpark               YES NO  Returns FALSE
cansetpierside           YES NO  Returns FALSE
cansetrightascensionrate YES NO  Returns FALSE
cansettracking           YES NO  Returns FALSE
canslew                  YES NO  Returns FALSE
canslewaltaz             YES NO  Returns FALSE
canslewaltazasync        YES NO  Returns FALSE
canslewasync             YES NO  Returns FALSE
cansync                  YES NO  Returns TRUE
cansyncaltaz             YES NO  Returns FALSE
connected                YES NO
declination              YES NO
description              YES NO
destinationsideofpier
doesrefraction           YES NO  Returns FALSE
driverinfo               YES NO
equatorialsystem         YES NO  Returns FALSE
focallength              YES YES
interfaceversion         YES NO
ispulseguiding           YES NO  Returns FALSE
rightascension           YES NO
sideofpier               YES NO  Returns 0
sideraltime              YES NO
siteelavation            YES NO  Need to implement SET
sitelatitudev            YES NO  Need to implement SET
sitelongitude            YES NO  Need to implement SET
slewing                  YES NO  Returns FALSE
supportedactions         YES NO
synctocoordinates        NO  YES
targetdeclination        YES NO
targetrightascension     YES NO
tracking                 YES NO
trackingrate             YES NO
trackingrates            YES NO
utcdate                  YES NO
======================== === === =====================================================

'''''''''''''''''''''''''
Interface to DSC Encoders
'''''''''''''''''''''''''
The DSC driver also maintains communication with the encoders of the DSC device. This
gives the position of the ALT and AZ axes of the telescope.  The DSC is polled
at regular intervals for its current position and the driver then recomputers
the sky position that the telescope is currently pointed.  This computation depends
upon the user first performing a *synchronize* (or *sync*) operation which involves
pointing the telescope at a known star or sky objects and telling the planetarium
program to synchronize the mount.  The DSC driver uses the raw ALT/AZ encoder
positions and the RA/DEC coordinates of the target chosen in the sky for syncing
and computes a mapping from raw encoder position to sky position.

'''''''''''''''''''''''
Encoder Synchronization
'''''''''''''''''''''''
The DSC encoders report back the change in the position of each axis since the
DSC was powered on.  The changes are relative to the original position.  In order
to map these values to the position of the telescope in the sky the user must synchronize
the DSC encoders.  The process is as follows:

- User points the telescope to a star or sky object in the planetarium catalog.
- Once the object is centered in the field of view (FOV) of the telescope the
  planetarium program is told to "sync" the position of the telescope.
- The DSC driver receives the sync request and records the raw DSC encoder values.
- Using the encoder resolution for each axis the raw encoder values are converted
  to degrees.
- Using the geographic location of the observer site and the current time the
  current position of the object in the sky (ALT/AZ) is computed.
- A linear mapping between the raw encoder values and the actual ALT/AZ position
  is computed and applied to future value read from the DSC device.
- It is assumed the dobsonian base is level for this simple synchronization to work.

This simple mapping works well within the vicinity of the object chosen for
synchronization but will become more inaccurate as the observing position is
farther and farther from the synchronization position.  The easy remedy is to
chose a new synchronization point when moving to a new area of the sky.

'''''''''''''''''
Observing Profile
'''''''''''''''''
A profile is stored for each observing configuration which contains the following
information:

- location
    * location name
    * latitude (decimal degrees)
    * longitude (decimal degrees)
    * altiude (meters)
- DSC configuration
    * serial port for DSC
    * communcation speed
    * ALT/AZ encoder resolution
    * Whether ALT and/or AZ direction is reversed
- equipment information
    * aperture of telescope
    * focal length of telescope

This profile is stored as a YACC file under a system configuration directory
which depends on the system platform.  For Linux is it stored in the
".config/AlpacaSettingCirclesDriver" directory in the user's home directory.
In Windows it is stored in the directory "%APPDATA"/AlpacaSettingCirclesDriver".

'''''''''''''
Web dashboard
'''''''''''''
The DSC driver also has a built in web server which is used to monitor the
current status of the DSC driver as well as config the driver.  The status
page displays the following information:

- current raw encoder counts
- current sky position as ALT/AZ (if synchronized)
- current sky position as RA/DEC (if synchronized)
- whether the mount is tracking (for dobsonians on an equatorial platform - not
  currently implemented)
- current observational profile

A button exists that will lead to an alternate web page allows configuring the
observating profile mentioned in the previous section "Observing Profile".  The
user can also create a new profile, load an existing profile, or save the
current profile under a new name.








