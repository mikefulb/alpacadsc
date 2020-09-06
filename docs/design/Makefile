# Minimal makefile for RST documentation
#

# You can set these variables from the command line.
RSTOPTS    =
RSTCMD     = rst2html4.py
SOURCEDIR  = source
BUILDDIR   = build
RSTSRC     = AlpacaSettingCirclesDriver.rst
OUTHTML    = $(RSTSRC:.rst=.html)


%.html: %.rst
	$(RSTCMD) $< > $@


#AlpacaSettingCircleDriver.html: AlpacaSettingCircleDriver.rst
#	$(RSTCMD) $< >@

.PHONY: docs

# Put it first so that "make" without argument is like "make help".
docs: $(OUTHTML)
