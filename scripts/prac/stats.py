'''
    author: Suhas Vittal
    date:   11 November 2024
'''

import math
import os
from copy import deepcopy

##########################################################
##########################################################

NCORE = 8
MPKI_MIN = 1.0

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
    MIXES.append([ w for w in workloads ])

##########################################################
##########################################################

def get_stats_from_file(f: str):
    with open(f, 'r') as reader:
        lines = reader.readlines()
    d = {}
    for line in lines:
        line = line.strip()
        if '=' in line:
            dat = line.split('=')
            dat[1] = dat[1][:dat[1].find('#')]
        else:
            dat = line.split(':')
        if len(dat) <= 1:
            continue
        for i in range(2):
            dat[i] = dat[i].strip()
        d[dat[0]] = dat[1]
    return d

##########################################################
##########################################################

# Collect single core IPC

SINGLE_CORE_IPC = {}

for f in os.listdir('out'):
    if 'SINGLE_CORE' not in f:
        continue
    bname = f.split('_')[0]
    d = get_stats_from_file(fr'out/{f}')
    SINGLE_CORE_IPC[bname] = float(d['CORE_00_IPC'])

##########################################################
##########################################################

def list_basic():
    stat_files = [ f for f in os.listdir('out') if f.endswith('.out') ]
    stat_files.sort()
    latex_list = []
    for f in stat_files:
        if 'BASE_' not in f:
            continue
        bname = f.split('_')[0]
        d = get_stats_from_file(fr'out/{f}')
        if 'CORE_00_MPKI' not in d:
            continue
        # Get basic info.
        mpki = NCORE / sum(1.0/float(d[f'CORE_0{i}_MPKI']) for i in range(NCORE))
        if mpki < MPKI_MIN:
            continue
        rbhr = float(d['num_read_row_hits'])/float(d['num_read_cmds'])
        acts_per_trefi = int(d['num_act_cmds'])/int(d['num_refab_cmds'])/32
        acts32 = (int(d['rows_ge_32_acts']) / 32) * (8192/int(d['num_refab_cmds']))
        acts64 = (int(d['rows_ge_64_acts']) / 32) * (8192/int(d['num_refab_cmds']))
        acts200 = (int(d['rows_ge_200_acts']) / 32) * (8192/int(d['num_refab_cmds']))
        latex_list.append((mpki,f'{bname:24} & {mpki:<12.1f} & {rbhr:<12.2f} & {acts_per_trefi:<12.1f} & {acts64:<12.1f} & {acts200:<12.1f}\t\\\\'))
    latex_list.sort(key=lambda x: x[0], reverse=True)
    for (_,s) in latex_list:
        print(s)


##########################################################
##########################################################

def dump_stats(policies: list[str], output_where='stdout'):
    stats = {}
    for p in policies:
        stats[p] = {
                'tot_files': 0,
                #
                'log_ipc': 0.0,
                'ipc_list': {},
                #
                'tot_mit': 0,
                'mit_list': {},
                #
                'tot_alerts': 0.0,
                'alerts_list': {},
                # 
                'log_ws': 0.0,
                'ws_list': {},
        }
    stat_files = [ f for f in os.listdir('out') if f.endswith('.out') ]
    for f in stat_files:
        fp = None
        # Identify policy that the file has data for
        for p in policies:
            if p in f:
                fp = p
                break
        if fp is None:
            continue
        # Get important stats of interest from file.
        bname = f.split('_')[0]
        print(f)
        d = get_stats_from_file(fr'out/{f}')
        if float(d['CORE_00_MPKI']) < MPKI_MIN:
            continue
        # Get stats
        hmipc = NCORE / sum(1.0 / float(d[f'CORE_0{i}_IPC']) for i in range(NCORE))
        ws = 0
        if 'mix' in bname:
            ii = int(bname[3:])
            mix = MIXES[ii-1]
            for (i,w) in enumerate(mix):
                ipc = float(d[f'CORE_0{i}_IPC'])
                ws += ipc/SINGLE_CORE_IPC[w]
        else:
            for i in range(NCORE):
                ipc = float(d[f'CORE_0{i}_IPC'])
                ws += ipc/SINGLE_CORE_IPC[bname]
        stats[fp]['tot_files'] += 1
        # IPC
        stats[fp]['log_ipc'] += math.log(hmipc)
        stats[fp]['ipc_list'][bname] = hmipc
        # Alerts
        stats[fp]['tot_alerts'] += int(d['num_alerts'])
        stats[fp]['alerts_list'][bname] = int(d['num_alerts'])
        # Mitigations
        stats[fp]['tot_mit'] += int(d['num_moat_mitigations'])
        stats[fp]['mit_list'][bname] = int(d['num_moat_mitigations'])
        # Weighted Speedup
        stats[fp]['log_ws'] += math.log(ws)
        stats[fp]['ws_list'][bname] = ws

    # Report stats
    base = policies[0]
    for p in policies:
        print(p)
        n = stats[p]['tot_files']
        stats[p]['ipc'] = math.exp( stats[p]['log_ipc'] / n )
        stats[p]['alerts'] = stats[p]['tot_alerts'] / n
        stats[p]['mit'] = stats[p]['tot_mit'] / n
        stats[p]['ws'] = math.exp( stats[p]['log_ws'] / n )

##########################################################
##########################################################
# NOTE -- functions below are part of the `print_stats` function.
    def get_rel(a,b):
        if a == 0 and b == 0:
            return 0
        elif a == 0:
            return 'inf'
        else:
            return b/a

##########################################################
##########################################################
    BAR = ''.join(['-' for _ in range(28*len(policies))])
    def print_stat(name: str, list_relative=True):
        print('\n\n\n')
        print(BAR)
        print(f'{"":<24}', ''.join(f'{p:<24}' for p in policies))
        print(BAR)
        print(f'GMEAN {name:<18}', end='')
        for p in policies:
            if list_relative:
                x = get_rel(stats[p][name], stats[base][name])
            else:
                x = stats[p][name]
            print(f'{x:<24.3f}', end='')
        print()
        print(BAR)

        stat_list = f'{name}_list'
        for b in stats[base][stat_list]:
            print(f'{b:<24}', end='')
            for p in policies:
                if list_relative:
                    x = get_rel(stats[p][stat_list][b], stats[base][stat_list][b])
                else:
                    x = stats[p][stat_list][b]
                print(f'{x:<24.3f}', end='')
            print()

##########################################################
##########################################################
    DELIM = ','
    FEXT = '.csv'
    def print_to_file(name, is_relative=True):
        wr = open(f'{output_where}.{name}{FEXT}', 'w')
        # Write header  
        wr.write('Workload')
        for p in policies:
            wr.write(f'{DELIM}{p}')
        # Do GMEAN
        wr.write('\nGMEAN')
        for p in policies:
            if is_relative:
                x = get_rel( stats[p][name], stats[base][name] )
                wr.write(f'{DELIM}{x:.3f}')
            else:
                x = stats[p][name]
                wr.write(f'{DELIM}{x}')
        # Each workload:
        stat_list = f'{name}_list'
        for b in stats[base][stat_list]:
            wr.write(f'\n{b}')
            for p in policies:
                if is_relative:
                    x = get_rel( stats[p][stat_list][b], stats[base][stat_list][b] )
                    wr.write(f'{DELIM}{x:.3f}')
                else:
                    x = stats[p][stat_list][b]
                    wr.write(f'{DELIM}{x}')
        wr.write('\n')
        wr.close()

##########################################################
##########################################################

    print_stat('ipc')
    print_stat('ws')
    if 'mit' in argv:
        print_stat('mit', False)
    if output_where != 'stdout':
        print_to_file('ipc')
        print_to_file('ws')
        if 'mit' in argv:
            print_to_file('mit', False)

##########################################################
##########################################################

from sys import argv

STAT_WHICH = argv[1]

##########################################################
##########################################################

if STAT_WHICH == 'basic':
    list_basic()

elif STAT_WHICH == 'sens_mopac_buf':
    for nrh in [250, 500, 1000]:
        dump_stats(['BASE_',
                    'PRAC_ONLY_DELAY',
                    f'PRAC_MOPAC_buf5_nrh{nrh}',
                    f'PRAC_MOPAC_buf8_nrh{nrh}',
                    f'PRAC_MOPAC_buf16_nrh{nrh}',
                    f'PRAC_MOPAC_buf32_nrh{nrh}',
                    f'PRAC_MOPAC_buf64_nrh{nrh}'],
                   output_where=f'data/sens_mopac_buf_nrh{nrh}')
elif STAT_WHICH == 'sens_moat':
    dump_stats(['BASE_',
                'PRAC_ONLY_DELAY',
                'PRAC_MOAT_nrh1000',
                'PRAC_MOAT_nrh500',
                'PRAC_MOAT_nrh50',
                'PRAC_MOAT_nrh75',
                'PRAC_MOAT_nrh100',
                'PRAC_MOAT_nrh200',
                'PRAC_MOAT_nrh4000'], output_where='data/sens_moat')
elif STAT_WHICH == 'sens_pac_mopac_pr':
    dump_stats(['BASE_',
                'PRAC_ONLY_DELAY',
                'PRAC_PAC_pr2',
                'PRAC_PAC_pr4',
                'PRAC_PAC_pr8',
                'PRAC_PAC_pr16',
                'PRAC_MOPAC_pr2',
                'PRAC_MOPAC_pr4',
                'PRAC_MOPAC_pr8',
                'PRAC_MOPAC_pr16'], output_where='data/sens_pac_mopac_pr')
elif STAT_WHICH == 'sens_mopac_qth':
    dump_stats(['BASE_',
                'PRAC_ONLY_DELAY',
#               'PRAC_MOPAC_qth2',
#               'PRAC_MOPAC_qth4',
                'PRAC_MOPAC_qth8',
                'PRAC_MOPAC_qth16'], output_where='data/sens_mopac_qth')
elif STAT_WHICH == 'sens_mopac_df':
    for nrh in [250, 500, 1000]:
        dump_stats(['BASE_',
                    'PRAC_ONLY_DELAY',
#                   f'PRAC_MOPAC_df_0_1_nrh{nrh}',
#                   f'PRAC_MOPAC_df_1_1_nrh{nrh}',
#                   f'PRAC_MOPAC_df_2_1_nrh{nrh}'], output_where='data/sens_mopac_df_nrh{nrh}')
                    f'PRAC_MOPAC_df0_nrh{nrh}',
                    f'PRAC_MOPAC_df1_nrh{nrh}',
                    f'PRAC_MOPAC_df2_nrh{nrh}',
                    f'PRAC_MOPAC_df4_nrh{nrh}'], output_where=f'data/sens_mopac_df_nrh{nrh}')

##########################################################
##########################################################

elif STAT_WHICH == 'pac':
    dump_stats(['BASE_', 'PRAC_ONLY_DELAY',
                'PRAC_PAC_nrh125',
                'PRAC_PAC_nrh250',
                'PRAC_PAC_nrh500',
                'PRAC_PAC_nrh1000',
                'PRAC_PAC_nrh2000',
                'PRAC_PAC_nrh4000'], output_where='data/pac')
elif STAT_WHICH == 'mopac':
    dump_stats(['BASE_', 'PRAC_ONLY_DELAY',
                'MOPAC_nrh125',
                'MOPAC_nrh250',
                'MOPAC_nrh500',
                'MOPAC_nrh1000',
                'MOPAC_nrh2000',
                'MOPAC_nrh4000'], output_where='data/mopac')

##########################################################
##########################################################

elif STAT_WHICH == 'pac_rp':
    dump_stats(['BASE_', 'PRAC_ONLY_DELAY',
                'PRAC_PAC_RP_nrh250',
                'PRAC_PAC_RP_nrh500',
                'PRAC_PAC_RP_nrh1000'], output_where='data/pac_rp')
elif STAT_WHICH == 'mopac_rp':
    dump_stats(['BASE_', 'PRAC_ONLY_DELAY',
                'MOPAC_RP_nrh250',
                'MOPAC_RP_nrh500',
                'MOPAC_RP_nrh1000'], output_where='data/mopac_rp')
