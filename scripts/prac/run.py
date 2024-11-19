'''
    author: Suhas Vittal
    date:   11 November 2024
'''

from sys import argv

import os

##################################################################
##################################################################

EXEC_WHERE = argv[1]
EXEC_WHAT = argv[2]
ONLY_MIXES = '--only-mixes' in argv

##################################################################
##################################################################

MIX_STRING =\
'''cactuBSSN-cam4-fotonik3d-mcf-parest-roms-xalancbmk-xz
cactuBSSN-lbm-mcf-omnetpp-parest-roms-xalancbmk-xz
bwaves-fotonik3d-lbm-mcf-parest-roms-xalancbmk-xz
bwaves-cactuBSSN-fotonik3d-lbm-omnetpp-parest-roms-xalancbmk
blender-bwaves-cam4-lbm-omnetpp-parest-roms-xz
blender-bwaves-cactuBSSN-cam4-fotonik3d-mcf-parest-roms'''

mix_lines = MIX_STRING.split('\n')
MIXES = []
for (i, line) in enumerate(mix_lines):
    workloads = line.split('-')
    MIXES.append([f'{w}_17.mtf.gz' for w in workloads])

##################################################################
##################################################################

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

##################################################################
##################################################################

if EXEC_WHAT == 'single_core':
    # Just run all applications in single core mode and give the result.
    for tr in TRACES:
        trpath = f'{TRACE_FOLDER}/{tr}'
        trname = tr.split('.')[0]
        print(trname)

        if EXEC_WHERE != 'pace':
            cmd = 'cd builds\n'
        base_cmd = f'./BASE/sim {trpath} -ratemode 1 -dramsim3cfg ../config_dramsim3/prac/baseline.ini -inst_limit {INST} -l3sizemb 8 -l3assoc 16'
        if EXEC_WHERE == 'pace':
            cmd = fr'ls . && cd builds && {base_cmd}'
            os.system(f'sbatch -N1 --ntasks-per-node=1 --mem-per-cpu=4G -t2:00:00 --account=gts-mqureshi4-rg -o out/{trname}_SINGLE_CORE.out --wrap=\"{cmd}\"')
        else:
            cmd += f'{base_cmd} > ../out/{trname}_SINGLE_CORE.out 2>&1 &\n'
        if EXEC_WHERE != 'pace':
            print(cmd)
            os.system(cmd)
    exit(1)

##################################################################
##################################################################

elif EXEC_WHAT == 'baseline':
    configs = [
                ('BASE', '', 'prac/baseline.ini'),
                ('PRAC_ONLY_DELAY', '', 'prac/baseline.ini'),
            ]

##################################################################
##################################################################

elif EXEC_WHAT == 'sens_mopac_buf':
    configs = []
    for nrh in [250, 500, 1000]:
        for s in [5,8,16,32,64]:
            configs.append(('PRAC_MOPAC', f'buf{s}_nrh{nrh}', f'prac/sens_mopac_buf/buf{s}_nrh{nrh}.ini'))
elif EXEC_WHAT == 'sens_moat':
    configs = [ ('PRAC_MOAT', f'nrh{nrh}', f'prac/sens_moat/nrh{nrh}.ini') for nrh in [50,75,100,200,500,1000,4000] ]
elif EXEC_WHAT == 'sens_pac_mopac_pr':
    configs = []
    for pr in [2,4]:
        for x in ['PRAC_PAC', 'PRAC_MOPAC']:
            configs.append( (x, f'pr{pr}', f'prac/sens_pac_mopac_pr/pr{pr}.ini') )
elif EXEC_WHAT == 'sens_mopac_qth':
    configs = [ ('PRAC_MOPAC', f'qth{qth}', f'prac/sens_mopac_qth/qth{qth}.ini') for qth in [2,4,8,16] ]
elif EXEC_WHAT == 'sens_mopac_df':
    configs = []
    for nrh in [250,500,1000]:
        for df in [0,1,2,4]:
            configs.append(('PRAC_MOPAC', f'df{df}_nrh{nrh}', f'prac/sens_mopac_df/df{df}_nrh{nrh}.ini'))

##################################################################
##################################################################

elif EXEC_WHAT == 'pac':
    configs = [ ('PRAC_PAC', f'nrh{nrh}', f'prac/pac/nrh{nrh}.ini') for nrh in [125,250,500,1000,2000,4000] ]
elif EXEC_WHAT == 'mopac':
    configs = [ ('PRAC_MOPAC', f'nrh{nrh}', f'prac/mopac/nrh{nrh}.ini') for nrh in [125,250,500,1000,2000,4000] ]

##################################################################
##################################################################

else:
    print('Unrecognized experiment:', EXEC_WHAT)
    exit(1)

##########################################################
##########################################################

jobs = 0
# Do ratemode=8
if not ONLY_MIXES:
    for tr in TRACES:
        trpath = f'{TRACE_FOLDER}/{tr}'
        trname = tr.split('.')[0]
        print(trname)

        if EXEC_WHERE != 'pace':
            cmd = 'cd builds\n'
        for (build_dir, suffix, cfg) in configs:
            base_cmd = f'./{build_dir}/sim {trpath} -ratemode 8 -dramsim3cfg ../config_dramsim3/{cfg} -inst_limit {INST} -l3sizemb 8 -l3assoc 16'
            if EXEC_WHERE == 'pace':
                cmd = fr'ls . && cd builds && {base_cmd}'
                os.system(f'sbatch -N1 --ntasks-per-node=1 --mem-per-cpu=8G -t8:00:00 --account=gts-mqureshi4-rg -o out/{trname}_{build_dir}_{suffix}.out --wrap=\"{cmd}\"')
            else:
                cmd += f'{base_cmd} > ../out/{trname}_{build_dir}_{suffix}.out 2>&1 &\n'
            jobs += 1
        if EXEC_WHERE != 'pace':
            print(cmd)
            os.system(cmd)
# Do MIXES
for (i,MIX) in enumerate(MIXES):
    trace_line = ' '.join([ f'{TRACE_FOLDER}/{tr}' for tr in MIX ])
    print(f'Mix {i}')

    if EXEC_WHERE != 'pace':
        cmd = 'cd builds\n'
    for (build_dir, suffix, cfg) in configs:
        base_cmd = f'./{build_dir}/sim {trace_line} -dramsim3cfg ../config_dramsim3/{cfg} -inst_limit {INST} -l3sizemb 8 -l3assoc 16'
        if EXEC_WHERE == 'pace':
            cmd = fr'ls . && cd builds && {base_cmd}'
            os.system(f'sbatch -N1 --ntasks-per-node=1 --mem-per-cpu=8G -t8:00:00 --account=gts-mqureshi4-rg -o out/mix{i+1}_{build_dir}_{suffix}.out --wrap=\"{cmd}\"')
        else:
            cmd += f'{base_cmd} > ../out/mix{i+1}_{build_dir}_{suffix}.out 2>&1 &\n'
        jobs += 1
    if EXEC_WHERE != 'pace':
        print(cmd)
        os.system(cmd)
print('jobs launched:', jobs)

##########################################################
##########################################################

