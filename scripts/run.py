import os
from sys import argv

common_suffix= argv[1]
ds3conf = argv[2]
builds = argv[3:]

TRACE_FOLDER = '~/research/c/TRACES'

TRACES = [ 
#   'bc', 
#   'bfs',
#   'blender_17',
    'bwaves_17',
    'cactuBSSN_17',
#   'cc',
    'fotonik3d_17',
#   'gcc_17',
#   'lbm_17',
#   'mcf_17',
#   'sssp',
#   'tc',
    'xz_17'
]

INST = 30_000_000

jobs = 0
for tr in TRACES:
    cmd = f'cd builds\n'
    for b in builds:
        cmd += f'./{b}/sim {TRACE_FOLDER}/{tr}.mtf.gz -ds3cfg ../ds3conf/{ds3conf} -inst {INST} > ../out/{tr}_{b}_{common_suffix}.out 2>&1 &\n'
    print(cmd)
    os.system(cmd)
    jobs += len(builds)
print('jobs launched:', jobs)
