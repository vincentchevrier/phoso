#! /usr/bin/python
from hashlib import sha1
import os
import os.path
import sys
import logging
import json

from os.path import expanduser
home = expanduser("~")

def read_hash(path=os.path.join(home, '.phoso/hashes.json')):
    # Read existing hashes from hash_list
    sys.stdout.write('Reading %s, ' %hash_list)
    with open(path, 'r') as f:
        hashpairs = json.load(f)

    return hashpairs


def write_hash(hashes, path=os.path.join(home, '.phoso/hashes.json')):
    with open(path, 'w') as fobj:
        json.dump(hashes, fobj)


def hash_tree(base_dir, fsize_max=500.*1e6, verbose=True):
    """
    Given a base directory traverse the whole tree and calc the sha1 hash

    Returns a list of hashes
    [[abspath, ctime, fsize, fhash]...]
    """
    report_every = 50
    count = 1
    hash_pairs = []
    for d, subdirs, files in os.walk(base_dir):
        for fname in files:
            abspath = os.path.abspath(os.path.join(d,fname))
            ctime = os.path.getctime(abspath)
            fsize = os.path.getsize(abspath)
            fhash = None

            if fsize < fsize_max:
                with open(abspath, 'rb') as fobj:
                    fhash = sha1(fobj.read()).hexdigest()
                if verbose:
                    if count%report_every == 0:
                        sys.stdout.write("\rHashed {} files".format(count))
            else:
                if verbose:
                    sys.stdout.write('\nSkipped file {} due to size'.format(abspath))

            hash_pairs.append((abspath, ctime, fsize, fhash))
    sys.stdout.write('\n')
    return hash_pairs


def extract_duplicates(hash_pairs):
    """
    Given a list of hash_pairs 

    Parameters
    ----------
    hash_pairs: list
    
    Returns
    -------
    sorted_hash: list
        unique hash_pairs
    duplicates: list
        hashed removed from the original hash_pairs list
    """
    sorted_hash = sorted(hash_pairs, key=lambda x: x[3])
    duplicates = []
    i = 1
    while i<len(sorted_hash):
        if sorted_hash[i][3] == sorted_hash[i-1][3]:
            duplicates.append(sorted_hash.pop(i))
        else:
            i += 1

    return sorted_hash, duplicates


def purge_duplicates(base_dir, dry_run=False):
    """
    Delete all duplicates in the directory tree
    """
    hashes = hash_tree(base_dir)
    hashes, duplicates = extract_duplicates(hashes)

    if dry_run:
        for hash_tuple in hashes:
            sys.stdout.write("os.remove({})".format(hash_tuple[0]))

    else:
        for hash_tuple in hashes:
            os.remove(hash_tuple[0])


def common_hashes(source_hashes, destination_hashes):
    """
    Returns
    -------
    source_hashes: list
        list of hashes with hashes already in destination removed (modified in place)

    commons: list
        list of hashes popped from source because they were already in destionation

    """
    destination_h = [x[3] for x in destination_hashes]
    commons = []

    n_source = len(source_hashes)
    for i in range(n_source):
        # go reverse
        i_source = n_source - i - 1
        if source_hashes[i_source][3] in destination_h:
            commons.append(source_hashes.pop(i_source))

    return source_hashes, commons




