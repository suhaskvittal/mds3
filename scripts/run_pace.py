import os
from sys import argv

ds3conf = argv[1]
builds = argv[2:]

TRACE_FOLDER = '/storage/coda1/p-mqureshi4/0/svittal8/research/c/TRACES'

TRACES = [f for f in os.listdir(TRACE_FOLDER) if f.endswith('.mtf.gz')]

INST = 100_000_000

jobs = 0
for tr in TRACES:
    tr_name = tr.split('.')[0]
    print(tr_name)
    for b in builds:
        cmd = fr'ls . && cd builds && ./{b}/sim {TRACE_FOLDER}/{tr} -ds3cfg ../ds3conf/{ds3conf} -inst {INST}'
        print(cmd)
        os.system(f'sbatch -N1 --ntasks-per-node=1 --mem-per-cpu=4G -t1:00:00 --account=gts-mqureshi4-rg -o out/{tr_name}_{b}.out --wrap=\"{cmd}\"')
    jobs += len(builds)
print('jobs launched:', jobs)

