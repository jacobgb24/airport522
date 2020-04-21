# Airport522
An ADS-B decoder written for EC EN 522R at Brigham Young University.
Designed for the PlutoSDR.

The final presentation for this project can be viewed here - https://youtu.be/4Xr6dnybR_o.

## About ADS-B
ADS-B is the system used for aircraft to transmit information about themselves such as their ID, airspeed, heading, etc.
The protocol operates on the 1090MHz band and is fairly complicated.
Each bit is encoded in a rising/falling pattern of two values (high,low == 1 while low,high == 0).
Each bit takes 1 microsecond and each message has an 8 microsecond preamble.

Each message is 112 bits long with a 51 bit payload.
Payload content varies and depends on the type code.

## Resources / References
**Code**
* [pyModeS](https://github.com/junzis/pyModeS) - an ADS-B decoder (however, it's designed for rtlsdr not Pluto). Main
point of reference
* [dump1090 (PlutoSDR)](https://github.com/PlutoSDR/dump1090) - A fork of dump1090 (a popular C decoder) that uses
PlutoSDR. Useful when looking for PlutoSDR parameters
* [pyrtlsdr](https://github.com/roger-/pyrtlsdr) - python implementation for rtlsdr. Useful in combo with pyModeS for 
radio specific config.

**Documents**
* [mode-s.org](https://mode-s.org/decode/) - Information about high-level decoding of ADS-B packets. Does not go into
detail on how to get messages (e.g. getting hex from radio).
* [PyModeS Wiki](https://github.com/junzis/pyModeS/wiki) - Goes into more depth in some places than mode-s.org
* [PlutoSDR](https://wiki.analog.com/university/tools/pluto/users) - Pluto wiki. Not very helpful, but somewhat helped
with drivers
* [Stanford EE26N Class Assignment](https://web.stanford.edu/class/ee26n/Assignments/Assignment4.html) - 
has nice diagrams and overview of protocol.
* [World Aircraft Database](https://junzis.com/adb/data) - Database that maps ICAO -> model and operator.
This database was used and is necessary for the code to work (see aircraft.AircraftICAODB).


## Milestones
* 3/17/20 - Read the first live ICAO address and confirmed airplane with Flightradar24. 
* 3/19/20 - Decoded first `Aircraft Identification` message. Hello `UAL1798`!
* 4/3/20 - Read velocity data (TC=19)
* 4/4/20 - Saved first messages into file
* 4/4/20 - Read position data (TC=9-18)
* 4//20/20 - Displayed live data on GUI map

## Running the Code
* The code requires Python 3.5+ for type hints (built on 3.6.9)
* Download the [World Aircraft Database](https://junzis.com/adb/data) and place in the root directory
* An internet connection is required to get an IP address. Alternatively run with `-c` option
* `libiio` needs to be installed along with the Python package. By default the package installs to 
`/usr/lib/python3.6/site-packages` (though this may differ). Change the import in radio.py as needed.
* All other packages that are needed should be available through pip