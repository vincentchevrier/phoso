#! /usr/bin/python
from hashlib import sha1
import os
import os.path
import sys
import logging

logging.basicConfig(format='%(asctime)s %(message)s', filename='cull.info.log', level=logging.INFO)


root = '/share/photo_archive'
hashpairs = []
hash_list = 'hash_list.txt'

def read_hash_old(hash_list):
    # Read existing hashes from hash_list
    sys.stdout.write('Reading %s, ' %hash_list)
    with open(hash_list,'r') as f:
        for line in f.readlines():
            t,p,h = line.strip().split('\t')
            hashpairs.append((float(t),p,h))
    sys.stdout.write('%s hashes found.\n' %len(hashpairs))
    return hashpairs

def read_hash(hash_list, hashpairs=[]):
    # Read existing hashes from hash_list
    sys.stdout.write('Reading %s, ' %hash_list)
    with open(hash_list,'r') as f:
        for line in f.readlines():
            p,t,s,h = line.strip().split('\t')
            hashpairs.append((p,float(t),int(s),h))
    sys.stdout.write('%s hashes found.\n' %len(hashpairs))
    return hashpairs


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

