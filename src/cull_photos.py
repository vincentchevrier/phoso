#! /usr/bin/python
from hashlib import sha1
import os
import os.path
import sys
import logging
import json

logging.basicConfig(format='%(asctime)s %(message)s', filename='cull.info.log', level=logging.INFO)


root = '/share/photo_archive'
hashpairs = []
hash_list = 'hash_list.txt'


def read_hash(path='~/.phoso/hashes.json'):
    # Read existing hashes from hash_list
    sys.stdout.write('Reading %s, ' %hash_list)
    with open(path, 'r') as f:
        hashpairs = json.load(f)

    return hashpairs

def write_hash(hashes, path='~/.phoso/hashes.json'):
    with open(path, 'w') as fobj:
        json.dump(fobj, hashes)


def hash_tree(base_dir, fsize_max=500.*1e6, verbose=True):
    """
    Given a base directory traverse the whole tree and calc the sha1 hash

    Returns a list of hashes
    [[abspath, ctime, fsize, fhash]...]
    """
    report_every = 50
    count = 0
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
            i++

    return sorted_hash, duplicates


def purge_duplicates(base_dir):
    """
    Delete all duplicates in the directory tree
    """
    hashes = hash_tree(base_dir)
    hashes, duplicates = extract_duplicates(hashes)

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


def main():
    hash_tree

if __name__ == "__main__":


logging.info('Hashing files')
if True:
    hashpairs = read_hash(hash_list)
    # Hash all new paths and write as you go
    abspaths = [x[1] for x in hashpairs]
    sys.stdout.write('Hashing files\n')
    cnt = 0
    cnt_old = 0
    cnt_new = 0
    freq = 50
    cnt_max = 1000000
    stop_hashing = False
    fsize_max = 20*1e6 # 20 MB
    with open(hash_list,'w') as f:
        for d, subdirs, files in os.walk(root):
            for fname in files:
                cnt += 1
                abspath = os.path.abspath(os.path.join(d,fname))
                if abspath not in abspaths:
                    ctime = os.path.getctime(abspath)
                    fsize = os.path.getsize(abspath)
                    fhash = None
                    if fsize < fsize_max:
                        fhash = sha1(open(abspath,'rb').read()).hexdigest()
                    f.write('%s\t%s\t%s\t%s\n' %(abspath, ctime, fsize, fhash))
                    #hashpairs.append((ctime, abspath, fhash))
                    cnt_new += 1
                else:
                    cnt_old += 1

                if cnt%freq == 0:
                    sys.stdout.write('\r%7d: %7d old, %7d new.' %(cnt, cnt_old, cnt_new))
                    sys.stdout.flush()
                if cnt >= cnt_max:
                    stop_hashing = True

                if stop_hashing:
                    break
            if stop_hashing:
                break

    sys.stdout.write('\n%s files hashed, %s old, %s new.\n'%(cnt, cnt_old, cnt_new))
    logging.info('%s files hashed, %s old, %s new.'%(cnt, cnt_old, cnt_new))

hashpairs = read_hash(hash_list)
hashpairs = sorted(hashpairs, key=lambda x:x[1])

# Look for duplicates and create list of duplicates called dupe
n=len(hashpairs)
dupes=[]
sys.stdout.write('\nComparing for duplicates\n')
logging.info('Comparing for duplicates')
freq = 50
for i,(p1,t1,s1,h1) in enumerate(hashpairs):
    if i%freq == 0:
        sys.stdout.write('\r%d' %i)
    for j in xrange(i+1,n):
        p2,t2,s2,h2 = hashpairs[j]
        if h1 is None:
            if s1 == s2:
                dupes.append(j)
        else:        
            if h2 == h1:
                dupes.append(j)

# Set commands removes duplicates identified multiple times
dupes = sorted(list(set(dupes)),reverse=True)

# Delete all the duplicates and pop them from the hashlist
sys.stdout.write('\nDeleting duplicates\n')
logging.info('Deleting duplicates')
#answer = raw_input('Are you sure you want to delete %s duplicates? (y/n)\n' %len(dupes))
#if answer == 'y':
if True:
    cnt = 1
    for i in dupes:
        t,p,h = hashpairs.pop(i)
        sys.stdout.write('\r%i'%cnt)
        sys.stdout.flush()
        #os.remove(p)
	if i%100==0:
            logging.info('Deleting %s: %s' %(cnt,p))
        cnt += 1

sys.stdout.write('\n\n')

# Write new hashlist to disk
with open('hash_list.txt','w') as f:
    for tup in hashpairs:
        f.write('%s\t%s\t%s\n' %tup)

