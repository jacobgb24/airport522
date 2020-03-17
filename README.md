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

### Milestones
* 3/17/20 - Read the first live ICAO address and confirmed airplane with Flightradar24. 