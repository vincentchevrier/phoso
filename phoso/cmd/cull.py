import argparse
import logging
import os
import sys
from datetime import datetime

from ..cull import cull

def main():

    # setup command line parsing
    parser = argparse.ArgumentParser(formatter_class=argparse.RawTextHelpFormatter,
                                     description='Cull a directory of all duplicates using a hash list')
    parser.add_argument('root', type=str,
                        help='root directory (searched recursively)')
    parser.add_argument('hash_list', type=str, help='Path to hash_list')

    # parse command line arguments
    args = parser.parse_args()

    # SETUP LOGGING
    
    logging.basicConfig(level=os.environ.get("LOGLEVEL", "DEBUG"))
    # now = datetime.now().strftime('%Y%m%d-%H%M%S')
    # log_file = "log_debug_{}.log".format(now)
    # logging.basicConfig(filename=os.path.join('.', log_file),
    #                     level=logging.DEBUG, format='%(asctime)s %(message)s')

    # # setup logging from stderr
    # error_log_file = "log_error_{}.log".format(now)
    # fo = open(os.path.join('.', error_log_file), 'w')
    # sys.stderr = fo

    cull(args.root, args.hash_list)


if __name__ == '__main__':
    main()
