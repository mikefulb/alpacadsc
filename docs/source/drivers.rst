
********************
Writing A New Driver
********************

The :strong:`alpacadsc` package supports adding new drivers for digital setting
circles/encoders.  Currently any digital setting circles which use a serial
port interface and report the raw encoders counts should be able to made to
work.  Digital setting circles that work in celestial coordinates (RA/DEC)
will not work with the current alpacadsc implementation.

To add a new driver create a new source file with a name following the
pattern "encoders_altaz_<drivername>."  The package includes a reference
driver for encoders supporting the "Dave Ek" protocol as well as a simulator.
The "Dave Ek" driver would be a good starting point.  Simply copy the driver
source and then edit to change the various methods to use the protocol
commands for the encoders in question and parse the return values.  Also
change the name of the driver in the "name()" method to be a human readable
name for your new driver.

To test simply put the new source file in the :strong:`alpacadsc` package location.
When alpacadsc loads it will scan for modules following the pattern given
above for encoders driver plugin and detect it.  It will also be given
as an option on the configuration page.