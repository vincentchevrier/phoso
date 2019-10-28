import argparse
import logging
import os
import sys
from datetime import datetime

from ..sort import sortphotos
from ..utils import del_dirs

def main():

    # setup command line parsing
    parser = argparse.ArgumentParser(formatter_class=argparse.RawTextHelpFormatter,
                                     description='Sort files (primarily photos) into folders by date\nusing EXIF data if possible and file creation date if not')
    parser.add_argument('src_dir', type=str,
                        help='source directory (searched recursively)')
    parser.add_argument('dest_dir', type=str, help='destination directory')
    parser.add_argument('--hold-dir', type=str, default='/share/homes/admin/hold',
                        help='holding directory for identical files, recreates the dir structure')
    parser.add_argument('-m', '--move', action='store_true',
                        help='move files instead of copy')
    parser.add_argument('-d', '--delete-dir', action='store_true',
                        help='Remove all empty directories from src_dir')
    parser.add_argument('-f', '--force-delete-dir', action='store_true',
                        help='Remove all directories from src_dir, even if not empty')
    parser.add_argument('-s', '--sort', type=str, default='%Y/%m',
                        help="choose destination folder structure using datetime format \n\
https://docs.python.org/2/library/datetime.html#strftime-and-strptime-behavior. \n\
Use forward slashes / to indicate subdirectory(ies) (independent of your OS convention). \n\
The default is '%%Y/%%m', which separates by year then month (e.g., 2012/11).")
    parser.add_argument('--keep-duplicates', action='store_true',
                        help='If file is a duplicate keep it anyway (after renaming).')
    parser.add_argument('--extensions', type=str, nargs='+',
                        default=['jpg', 'jpeg', 'tiff', 'arw', 'avi',
                                 'mov', 'mp4', 'mts', 'mkv', 'rw2', 'png', '3gp'],
                        help='file types to sort')
    parser.add_argument('--ignore-exif', action='store_true',
                        help='always use file time stamp even if EXIF data exists')
    parser.add_argument('--keep-filenames', action='store_true',
                        help='Do not rename the files. Default behavior is to rename the files, e.g. 2014-09-04_FinePix_1.jpg')
    parser.add_argument('--exif-path', type=str, default='/opt/bin/exif',
                        help='path to use for the terminal exif command, defaults to /opt/bin/exif')

    # parse command line arguments
    args = parser.parse_args()

    # SETUP LOGGING
    now = datetime.now().strftime('%Y%m%d-%H%M%S')
    log_file = "log_debug_{}.log".format(now)
    logging.basicConfig(filename=os.path.join('.', log_file),
                        level=logging.DEBUG, format='%(asctime)s %(message)s')

    # setup logging from stderr
    error_log_file = "log_error_{}.log".format(now)
    fo = open(os.path.join('.', error_log_file), 'w')
    sys.stderr = fo

    sortphotos(args.src_dir, args.dest_dir, args.extensions, args.sort,
               args.move, not args.keep_duplicates, args.ignore_exif, rename=not args.keep_filenames, exif_path=args.exif_path, hold_dir=args.hold_dir)

    # If requested, remove all empty directories from source
    if args.delete_dir or args.force_delete_dir:
        # First delete the annoying thumbnail folders
        # del_dirs(args.src_dir, match='.@__thumb')
        # delete the rest
        del_dirs(args.src_dir, force=args.force_delete_dir)


if __name__ == '__main__':
    main()
