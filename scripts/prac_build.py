'''
    author: Suhas Vittal
    date:   11 November 2024
'''

import os
from sys import argv

EXEC_WHERE = 'ampere'
if len(argv) > 1:
    EXEC_WHERE = argv[1]

'''
Generates build directories for ddr6prac
'''

COMMON_OPTS = '-DCMAKE_BUILD_TYPE=Release'

BUILDS = [
    ('BASE', 0),
    ('PRAC_ONLY_DELAY', 1),
    ('PRAC_MOAT', 2),
    ('PRAC_PAC', 3),
    ('PRAC_MOPAC', 4)
]

# PACE -- load relevant modules
if EXEC_WHERE == 'pace':
    os.system('module load cmake')
# Build directories.
os.system('rm -rf builds ; mkdir builds')
for (b, pracnum) in BUILDS:
    cmd =\
fr'''cd builds ; mkdir {b} && cd {b}
cmake ../.. {COMMON_OPTS} -DUSE_PRAC={pracnum}
make -j8
  '''
    print(cmd)
    os.system(cmd)
