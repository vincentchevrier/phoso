#! /usr/bin/python
from hashlib import sha1
import os
import os.path
import sys
import logging
import json
from json.decoder import JSONDecodeError
import copy

LOGGER = logging.getLogger(__name__)

def read_hash(path='~/.phoso/hashes.json'):
    # Read existing hashes from hash_list
    LOGGER.info('Reading %s', path)
    try:
        with open(path, 'r') as f:
            hashpairs = json.load(f)
    except (FileNotFoundError, JSONDecodeError):
        hashpairs = []

    return hashpairs


def write_hash(hashes, path='~/.phoso/hashes.json'):
    with open(path, 'w') as fobj:
        json.dump(hashes, fobj, indent=4)


def hash_tree(base_dir, fsize_max=500.*1e6, verbose=True, already_hashed=[]):
    """
    Given a base directory traverse the whole tree and calc all the sha1 hash

    Returns a list of hashes
    [[abspath, ctime, fsize, fhash]...]
    """
    report_every = 50
    count = 0
    hash_pairs = []
    abspaths = [x[0] for x in already_hashed]
    for d, subdirs, files in os.walk(base_dir):
        for fname in files:
            abspath = os.path.abspath(os.path.join(d, fname))
            ctime = os.path.getctime(abspath)
            fsize = os.path.getsize(abspath)
            fhash = None

            if abspath not in abspaths:
                if fsize < fsize_max:
                    with open(abspath, 'rb') as fobj:
                        fhash = sha1(fobj.read()).hexdigest()
                    if verbose:
                        if count % report_every == 0:
                            LOGGER.debug("Hashing file %s", count+1)
                else:
                    if verbose:
                        LOGGER.info(
                            'Skipped file %s due to size', abspath)

                hash_pairs.append((abspath, ctime, fsize, fhash))
                count += 1

    LOGGER.info("Hashed %s files", count)
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
    while i < len(sorted_hash):
        if sorted_hash[i][3] == sorted_hash[i-1][3]:
            duplicates.append(sorted_hash.pop(i))
        else:
            i += 1

    return sorted_hash, duplicates


def purge_duplicates(base_dir):
    """
    Delete all duplicates in the directory tree
    """
    hashes = hash_tree(base_dir)
    hashes, duplicates = extract_duplicates(hashes)

    for hash_tuple in duplicates:
        os.remove(hash_tuple[0])
    
    return hashes, duplicates


def common_hashes(source_hashes, destination_hashes):
    """
    Returns
    -------
    source_hashes: list
        list of hashes with hashes already in destination removed (modified in place)

    commons: list
        list of hashes popped from source because they were already in destination

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

# if __name__ == "__main__":



def cull(root:str, hash_list_path: str, dry_run:bool=False):
    '''
    Given root directory and a file containing a list of all hashes
    - recurse through the tree and create an updated list of file hashes
    - sort by ctime
    - tabulate all duplicates
    - delete all duplicates
    - write an updated hash_list

    Args:
        root: directory with files
        hash_list_path: path for hash list

    '''

    LOGGER.info('Hashing files')

    hashpairs = read_hash(hash_list_path)
    new_hashpairs = hash_tree(root, already_hashed=hashpairs)

    hashpairs = sorted(hashpairs + new_hashpairs, key=lambda x: x[0])

    hashpairs, duplicates = extract_duplicates(hashpairs)

    if not dry_run:
        for hash_tuple in duplicates:
            LOGGER.debug('Deleting duplicate file %s', hash_tuple[0])
            os.remove(hash_tuple[0])

    write_hash(hashpairs, hash_list_path)
    
    
