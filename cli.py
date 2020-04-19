from message import Message
from radio import Radio
import argparse
import utils


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Runs Airport522, a ADS-B decoder")
    parser.add_argument('-i', '--input', help="File to read messages from. Default is live from radio", type=argparse.FileType('r'))
    parser.add_argument('-o', '--output', help="File to write output to. Default is none", type=argparse.FileType('w'))
    parser.add_argument('--output-invalid', action='store_true', help="Include invalid decoding in output")
    parser.add_argument('-c', '--custom-coords', default=None,
                        help="Custom coordinates to use for reference. Format as `lat,lon`. "
                             "Default is based on IP address. Need ~300km accuracy")
    args = parser.parse_args()

    if args.custom_coords is not None:
        lat, lon = args.custom_coords.strip().split(',')
        utils.REF_LAT, utils.REF_LON = float(lat), float(lon)
    else:
        utils.set_loc_ip()
    print(f'Using reference coordinates of: {utils.REF_LAT}, {utils.REF_LON}')

    if args.input is not None:
        for m in args.input:
            if not m.startswith('#'):
                print(Message(m.strip()))
    else:
        print('Setting up radio')
        radio = Radio()
        print('Done')
        while True:
            msgs = radio.recv()
            for m in msgs:
                if m.valid:
                    print(m)
                if args.output is not None and (m.valid or args.output_invalid):
                    args.output.write(f'{m.bin_msg}\n')
