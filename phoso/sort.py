#!/usr/bin/env python
# encoding: utf-8
"""
sortphotos.py
"""

import filecmp
import fnmatch
import io
import logging
import os
import re
import shutil
import subprocess
import sys
from datetime import datetime
from typing import Callable
from .utils import (del_dirs, general_case_exif, match_files, move_to_hold,
                    purge_string, rename_file)


def sortphotos(src_dir: str, dest_dir: str, extensions: list, sort_format: str, move_files: bool, remove_duplicates: bool,
               ignore_exif: bool, rename: Callable[[str, object, str],None], exif_path: str = '/opt/bin/exif', hold_dir: str = None):
    '''

    Args:
        src_dir: source directory (will be recursively traversed)
        dest_dir: destination directory
        extensions: list of extensions for file matching (do not include a period)
        sort_format: Format to use for the directory structure. Fed to `datetime.strftime`. For example: '%Y/%m'
        move_files: True: the files are moved, False the files are copied
        remove_duplicates: True: redundant files are deleted, False redundant files are kept and renamed. File comparisons are done with `filecmp.cmp`
        ignore_exif: True: Do not attempt to use exif information of file. False: use exif information for camera model and datetime
        rename: Function for renaming files. Arguments given to the function are the source file, the datetime, and the camera model
        exif_path: path to the local exif program. Defaults to '/opt/bin/exif'. Will be called using subprocess
        hold_dir: default None. If not none, should be a directory path where identical files are moved to instead of deleted


    '''
    # some error checking
    if not os.path.exists(src_dir):
        raise Exception('Source directory does not exist')
    if not os.path.exists(dest_dir):
        raise Exception('Destination directory does not exist')

    matched_files = match_files(src_dir, [f'.*\.{ext}' for ext in extensions])

    # setup a progress bar
    num_files = len(matched_files)
    idx = 0

    # RE of special cases
    r_wp_mp4 = re.compile(r'.*WP_([0-9]{8})_[0-9]{3}\.mp4')
    r_gen_vid = re.compile(r'.*(VID|TRIM)_([0-9]{8}_[0-9]{6})\.(mp4|mkv|3gp)')
    r_gen_img = re.compile(r'.*IMG_([0-9]{8}_[0-9]{6})\.(jpg|JPG)')
    r_gen_mp4 = re.compile(
        r'.*([12][890][0-9]{6}_[012][0-9][0-6][0-9][0-6][0-9])\.mp4')
    r_gen_rw2 = re.compile(r'.+\.rw2')

    for src_file in matched_files:

        # update progress bar
        numdots = int(20.0*(idx+1)/num_files)
        sys.stdout.write('\r')
        sys.stdout.write('[%-20s] %d of %d ' % ('='*numdots, idx+1, num_files))
        sys.stdout.flush()

        idx += 1
        date_fail = False
        date = None

        # Special cases
        src_basename = os.path.basename(src_file)
        if r_wp_mp4.match(src_basename):
            mo = r_wp_mp4.match(src_basename)
            date = datetime.strptime(mo.groups()[0], '%Y%m%d')
            model = 'WP'
        elif r_gen_vid.match(src_basename):
            mo = r_gen_vid.match(src_basename)
            date = datetime.strptime(mo.groups()[1], '%Y%m%d_%H%M%S')
            model = 'video'
        elif r_gen_img.match(src_basename):
            date, model, date_fail = general_case_exif(
                src_file, exif_path, ignore_exif=ignore_exif)
            if model is None or date_fail:
                mo = r_gen_img.match(src_basename)
                date = datetime.strptime(mo.groups()[0], '%Y%m%d_%H%M%S')
                model = 'img' if model is None else model
        elif r_gen_mp4.match(src_basename):
            mo = r_gen_mp4.match(src_basename)
            date = datetime.strptime(mo.groups()[0], '%Y%m%d_%H%M%S')
            model = 'video'
        elif r_gen_rw2.match(src_basename):
            mo = r_gen_rw2.match(src_basename)
            date = date = datetime.fromtimestamp(os.path.getmtime(src_file))
            model = 'raw'

        # General case
        else:
            date, model, date_fail = general_case_exif(
                src_file, exif_path, ignore_exif=ignore_exif)

        # create folder structure
        dir_structure = date.strftime(sort_format)
        dirs = dir_structure.split('/')
        dest_file = dest_dir
        for thedir in dirs:
            dest_file = os.path.join(dest_file, thedir)
            if not os.path.exists(dest_file):
                os.makedirs(dest_file)

        # setup destination file
        found_model = model
        if rename and not date_fail:
            new_fname = rename_file(src_file, date, model)
            dest_file = os.path.join(dest_file, new_fname)
        else:
            dest_file = os.path.join(dest_file, os.path.basename(src_file))
        root, ext = os.path.splitext(dest_file)
        # force extension to be lower case
        ext = ext.lower()

        # check for collisions
        append = 1
        file_is_identical = False

        while True:
            if os.path.isfile(dest_file):  # check for existing name
                # check for identical files
                if remove_duplicates and filecmp.cmp(src_file, dest_file):
                    file_is_identical = True
                    break

                else:  # name is same, but file is different
                    dest_file = root + '_' + str(append) + ext
                    append += 1

            else:
                break

        # finally move or copy the file
        if move_files:
            if file_is_identical:
                if hold_dir is not None:
                    hold_file = move_to_hold(src_dir, hold_dir, src_file)
                    logging.info('{}, {}, hold moved as it is identical, {}, {}'.format(
                        src_file, hold_file, date, found_model))
                else:
                    logging.info('{}, {}, not moved as it is identical, {}, {}'.format(
                        src_file, dest_file, date, found_model))
                continue  # if file is same, we just ignore it

            else:
                logging.info('{}, {}, moved to, {}, {}'.format(
                    src_file, dest_file, date, found_model))
                shutil.move(src_file, dest_file)
        else:
            if file_is_identical:
                logging.info('{}, {}, not copied as it is identical, {}, {}'.format(
                    src_file, dest_file, date, found_model))
                # if file is same, we just ignore it (for copy option)
                continue
            else:
                logging.info('{}, {}, copied, {}, {}'.format(
                    src_file, dest_file, date, found_model))
                shutil.copy2(src_file, dest_file)

    # Print a newline to move below the progress bar
    print()
