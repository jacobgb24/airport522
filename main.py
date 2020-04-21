from radio import Radio, MockRadio
from gui import run_gui
from multiprocessing import Queue
import argparse
import utils
import time

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Runs Airport522, a ADS-B decoder")

    inp_parser = parser.add_argument_group('input settings')
    inp_parser.add_argument('-i', '--input', help="File to read messages from. Default is live from radio")
    inp_parser.add_argument('-r', '--repeat', help='Whether file input should repeat', action='store_true')
    inp_parser.add_argument('-d', '--delay', help='delay before starting/restarting input. Default is 1', type=int,
                            default=1)

    out_parser = parser.add_argument_group('Output settings')
    out_parser.add_argument('-o', '--output', help="File to write output to. Default is none (only support in cli mode",
                            type=argparse.FileType('w'))
    out_parser.add_argument('--output-invalid', action='store_true', help="Include invalid decoding in output")

    gui_parser = parser.add_argument_group('GUI settings')
    gui_parser.add_argument('-g', '--gui', help='launch dash GUI', action='store_true')
    gui_parser.add_argument('--debug', help='Put GUI in debug mode', action='store_true')

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

    msg_que = Queue()
    if args.input is not None:
        print(f"Using MockRadio with {args.input}")
        radio = MockRadio(msg_que, args.input, args.repeat, args.delay, args.delay)
    else:
        print('Setting up radio')
        radio = Radio(msg_que)
        print('Done')

    if args.gui:
        run_gui(radio, args.debug)
    else:
        while True:
            msgs = radio.get_all_queue()
            for m in msgs:
                if m.valid:
                    print(m)
                if args.output is not None and (m.valid or args.output_invalid):
                    args.output.write(f'{round(time.time())} {m.bin_msg}\n')
