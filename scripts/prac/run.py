'''
    author: Suhas Vittal
    date:   11 November 2024
'''

from sys import argv

import os

EXEC_WHERE = argv[1]
EXEC_WHAT = argv[2]

# EXPERIMENT PARAMETERS
INST = 100_000_000
if EXEC_WHERE == 'ampere':
    TRACE_FOLDER = '/nethome/svittal8/research/c/TRACES'
else:
    TRACE_FOLDER = '/storage/coda1/p-mqureshi4/0/svittal8/research/c/TRACES'
if EXEC_WHERE == 'ampere':
    TRACES = [
        'blender_17.mtf.gz',
        'bwaves_17.mtf.gz',
        'cactuBSSN_17.mtf.gz',
        'fotonik3d_17.mtf.gz',
        'gcc_17.mtf.gz',
        'lbm_17.mtf.gz',
        'mcf_17.mtf.gz',
        'xz_17.mtf.gz'
    ]
else:
    TRACES = [f for f in os.listdir(TRACE_FOLDER) if f.endswith('.mtf.gz')]
# CONFIGS:
if EXEC_WHAT == 'sens_mopac_buf':
    configs = [ ('PRAC_MOPAC', f'buf{s}', f'prac/sens_mopac_buf/buf{s}.ini') for s in [5, 8, 16, 32, 64] ]

jobs = 0
for tr in TRACES:
    trpath = f'{TRACE_FOLDER}/{tr}'
    trname = tr.split('.')[0]
    if '_17' not in trname:
        continue
    print(trname)

    if EXEC_WHERE != 'pace':
        cmd = 'cd builds\n'
    for (build_dir, suffix, cfg) in configs:
        base_cmd = f'./{build_dir}/sim {trpath} -ratemode 8 -dramsim3cfg ../config_dramsim3/{cfg} -inst_limit {INST} -l3sizemb 8 -l3assoc 8'
        if EXEC_WHERE == 'pace':
            cmd = fr'ls . && cd builds && {base_cmd}'
            os.system(f'sbatch -N1 --ntasks-per-node=1 --mem-per-cpu=8G -t8:00:00 --account=gts-mqureshi4-rg -o out/{trname}_{build_dir}_{suffix}.out --wrap=\"{cmd}\"')
        else:
            cmd += f'{base_cmd} > ../out/{trname}_{build_dir}_{suffix}.out 2>&1 &\n'
        jobs += 1
    if EXEC_WHERE != 'pace':
        print(cmd)
        os.system(cmd)
print('jobs launched:', jobs)
