'''
    author: Suhas Vittal
    date:   11 November 2024
'''

import os
from sys import argv

##################################################################
##################################################################

EXEC_WHERE = 'ampere'
if len(argv) > 1:
    EXEC_WHERE = argv[1]

##################################################################
##################################################################

COMMON_OPTS = '-DCMAKE_BUILD_TYPE=Release'

BUILDS = [
    ('BASE', 0),
    ('PRAC_ONLY_DELAY', 1),
    ('PRAC_MOAT', 2),
    ('PRAC_PAC', 3),
    ('PRAC_MOPAC', 4),
    ('PRAC_PAC_RP', 3),
    ('PRAC_MOPAC_RP', 4)
]

##################################################################
##################################################################

# PACE -- load relevant modules
if EXEC_WHERE == 'pace':
    os.system('module load cmake')
# Build directories.
os.system('rm -rf builds ; mkdir builds')
for (b, pracnum) in BUILDS:
    extra_opts = ''
    if 'RP' in b:
        extra_opts = '-DROWPRESS=ON'
    cmd =\
fr'''cd builds ; mkdir {b} && cd {b}
cmake ../.. {COMMON_OPTS} -DUSE_PRAC={pracnum} {extra_opts}
make -j8
  '''
    print(cmd)
    os.system(cmd)

##################################################################
##################################################################
