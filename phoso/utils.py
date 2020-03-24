import io
import logging
import os
import re
import shutil
import subprocess
from subprocess import PIPE
import sys
from datetime import datetime

# -------- convenience methods -------------

def purge_string(s):
    allowed = '.0123456789-ABCDEFGHIJKLMNOPQRSTUVWXYZ_abcdefghijklmnopqrstuvwxyz'
    if s:
        return ''.join([x for x in s if x in allowed])
    else:
        return ''


def cmd_exiftool(tag, fname, command):
    sp = subprocess.run([command,'-s','-S',f'-{tag}',fname], stdout=PIPE, stderr=PIPE)
    out = sp.stdout.decode().strip()
    err_val = sp.stderr.decode().strip()
    if err_val:
        msg = '{}: EXIF failed with error: {}'.format(fname, err_val)
        logging.debug(msg)
        raise ValueError(msg)
    return out


def cmd_exif(tag, fname, command="/opt/bin/exif"):
    # out = subprocess.check_output([command,'-m','-t',tag,fname]).decode().strip()
    sp = subprocess.run([command,'-m','-t',tag,fname], stdout=PIPE, stderr=PIPE)
    out = sp.stdout.decode().strip()
    err_val = sp.stderr.decode().strip()
    if err_val:
        msg = '{}: EXIF failed with error: {}'.format(fname, err_val)
        logging.debug(msg)
        raise ValueError(msg)
    return out

def del_dirs(src_dir,force=False, match=None):
    for dirpath, _, _ in os.walk(src_dir, topdown=False):  # Listing the files
        if dirpath == src_dir:
            break
        try:
            if match:
                if os.path.basename(dirpath) == match:
                    shutil.rmtree(dirpath)
                    logging.info('match-rmtree: {}'.format(dirpath))
            elif force==True:
                shutil.rmtree(dirpath)
                logging.info('force-rmtree: {}'.format(dirpath))
            else:
                os.rmdir(dirpath)
                logging.info('rmdir: {}'.format(dirpath))
        except OSError as ex:
            sys.stderr.write(str(ex))
            
def general_case_exif(src_file, exif_path, ignore_exif=False):
    # use file time stamp if no valid EXIF dataa
    date = None
    date_fail = False
    if ignore_exif:
        date = datetime.fromtimestamp(os.path.getmtime(src_file))
        model = None

    else:
        # look for date in EXIF data
        if 'exiftool' in exif_path:
            # use exiftool syntax (windows)
            date_tags = ['DateTimeCreated', 'DateTimeOriginal', 'CreateDate']
            exif_function = cmd_exiftool
        else:
            # assume standard linux exif
            date_tags = ['Date and Time (Original)', 'Date and Time (Digitized)', 'Date and Time']
            exif_function = cmd_exif

        for tag in date_tags:
            try:
                date_str = exif_function(tag, src_file, exif_path)
                date = datetime.strptime(date_str,"%Y:%m:%d %H:%M:%S")
                break
            except:
                pass

        if date is None:
            date = datetime.fromtimestamp(os.path.getmtime(src_file))
            date_fail = True
            

        # look for model in EXIF data
        try:
            model = exif_function('Model', src_file, exif_path)
        except:
            model = None
            
    return date, model, date_fail

def move_to_hold(src_dir, hold_dir, fpath):
    new_fpath = os.path.join(hold_dir, os.path.relpath(fpath, src_dir))
    new_dir = os.path.dirname(new_fpath)
    if not os.path.isdir(new_dir):
        os.makedirs(new_dir)
    shutil.move(fpath, new_fpath)
    return new_fpath        

def match_files(src_dir, includes, excludes=[], ignore_case=True):

    # find files that have the specified extensions
    matched_files = []

    # check if file system is case sensitive
    case_sensitive_os = True
    if os.path.normcase('A') == os.path.normcase('a'):
        case_sensitive_os = False

    # compile regular expressions
    if case_sensitive_os or ignore_case:
        r_ins = [re.compile(i, re.IGNORECASE) for i in includes]
        r_exs = [re.compile(x, re.IGNORECASE) for x in excludes]
    else:
        r_ins = [re.compile(i) for i in includes]
        r_exs = [re.compile(x) for x in excludes]

    # recurvsively search directory
    for root, dirnames, filenames in os.walk(src_dir):
        for f in filenames:
            exclude = False            
            # Break loop if regex_exlude matches
            for r_ex in r_exs:
                if r_ex.match():
                    exclude = True
                    break
            if exclude:
                break

            # Keep file and break if regex_include matches
            for r_in in r_ins:
                if r_in.match(f):
                    matched_files.append(os.path.join(root, f))
                    break

    # Linux thumbnails are generated with @ in the filename
    matched_files = [x for x in matched_files if "@" not in x]

    return matched_files


def rename_file(src_file, date, model):
    basename, ext = os.path.splitext(os.path.basename(src_file))
    if model is None:
        model = basename    
    fname = '{}_{}{}'.format(
                date.strftime('%Y-%m-%d_%H%M%S'), model, ext)
    return fname