
************
Introduction
************

.. highlight:: console

The Alpaca digital setting circles driver (:strong:`alpacadsc`) allows connecting
client software like planetariums to ALT/AZ mounted telescopes like
dobsonians with the appropriate hardware.  The software supports tracking
the position of the telescope as it is moved across the sky, allowing easy
acquisition of sky targets.

The basic theory of operation is for the user to locate a sky target such as
a bright star and center the telscope on the target.  Then using the
planetarium software the user send a "Sync" command to the driver with the
coordinates of the target.  In Cartes du Ciel, for example, the user would
right click on the target and select "Sync".  This tells the driver where
it is currently pointing in the sky.  Using the configured latitude and
longitude and the current time :strong:`alpacadsc` can then compute the altitude and
azimuth of the target.  From this it can then compute the altitude and azimuth
of the telescope from the changes in the encoder values.

This simple "1 star" synchronization works well over a small part of the sky
(say 30-50 degrees) as long as the telescope is fairly level.  If you find
the pointing of the scope is poor as you get farther from the original sync
target then simply sync on a new target closer to your desired desination
target.  This should improve the pointing accuracy.  Do this as necessary as
you move around the sky.

Before using :strong:`alpacadsc` it is necessary to configure a profile for your
telescope.  This an other usage details are covered in the :ref:`Usage`
section.


