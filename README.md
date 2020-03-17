# Airport522
An ADS-B decoder written for EC EN 522R at Brigham Young University.
Designed for the PlutoSDR.

**VERY** Work in Progress as it stands

## About ADS-B
ADS-B is the system used for aircraft to transmit information about themselves such as their ID, airspeed, heading, etc.
The protocol operates on the 1090MHz band and is fairly complicated.
As an example a single bit is represented by two data point: high,low == 1 while low,high == 0.
Each datapoint is 0.5 microseconds.
Each message is 112 bits long, though some data takes two messages.

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
* [PlutoSDR](https://wiki.analog.com/university/tools/pluto/users) - Pluto wiki. Not very helpful, but somewhat helped
with drivers


## Milestones
* 3/17/20 - Read the first live ICAO address and confirmed airplane with Flightradar24. 
