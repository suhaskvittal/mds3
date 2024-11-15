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

def dump_stats(policies: list[str], output_where='stdout'):
    stats = {}
    for p in policies:
        stats[p] = {
                'tot_files': 0,
                'log_ipc': 1.0,
                'ipc_list': {},
                'tot_alerts': 0.0,
                'alerts_list': {}
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
        if bname in ['add', 'copy', 'scale', 'bfs', 'sssp', 'tc', 'bfs', 'cc', 'pr', 'bc']:
            continue
        print(f, bname)
        d = get_stats_from_file(fr'out/{f}')
        if float(d['CORE_00_MPKI']) < 1.0:
            continue
        gmlogipc = 1.0
        for i in range(NCORE):
            gmlogipc += math.log( float(d[f'CORE_0{i}_IPC']) )
        gmipc = math.e**(gmlogipc/NCORE)
        stats[fp]['log_ipc'] += gmlogipc/NCORE
        stats[fp]['tot_files'] += 1
        stats[fp]['ipc_list'][bname] = gmipc
        stats[fp]['tot_alerts'] += int(d['num_alerts'])
        stats[fp]['alerts_list'][bname] = int(d['num_alerts'])
    # Report stats
    base = policies[0]
    for p in policies:
        stats[p]['ipc'] = math.e**( stats[p]['log_ipc'] / stats[p]['tot_files'] )
        stats[p]['alerts'] = stats[p]['tot_alerts'] / stats[p]['tot_files']

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
    def print_to_file(name):
        wr = open(f'{output_where}.{name}{FEXT}', 'w')
        # Write header  
        wr.write('Workload')
        for p in policies:
            wr.write(f'{DELIM}{p}')
        '''
        IPC -------------------------------
        '''
        # Do GMEAN
        wr.write('\nGMEAN')
        for p in policies:
            x = get_rel( stats[p][name], stats[base][name] )
            wr.write(f'{DELIM}{x:.3f}')
        # Each workload:
        stat_list = f'{name}_list'
        for b in stats[base][stat_list]:
            wr.write(f'\n{b}')
            for p in policies:
                x = get_rel( stats[p][stat_list][b], stats[base][stat_list][b] )
                wr.write(f'{DELIM}{x:.3f}')
        wr.write('\n')
        wr.close()

##########################################################
##########################################################

    print_stat('ipc')
    if output_where != 'stdout':
        print_to_file('ipc')

##########################################################
##########################################################

from sys import argv

STAT_WHICH = argv[1]

##########################################################
##########################################################

if STAT_WHICH == 'mopac_buf_sens':
    for r in [0,1,2]:
        dump_stats(['BASE_',
                    'PRAC_ONLY_DELAY',
                    f'PRAC_MOPAC_buf5_ref{r}',
                    f'PRAC_MOPAC_buf8_ref{r}',
                    f'PRAC_MOPAC_buf16_ref{r}',
                    f'PRAC_MOPAC_buf32_ref{r}',
                    f'PRAC_MOPAC_buf64_ref{r}'],
                   output_where=f'data/mopac_buf_sens_ref{r}')
elif STAT_WHICH == 'moat_ath_sens':
    dump_stats(['BASE_',
                'PRAC_ONLY_DELAY',
                'MOAT_ath16',
                'MOAT_ath20',
                'MOAT_ath24',
                'MOAT_ath28',
                'MOAT_ath32',
                'MOAT_ath64',
                'MOAT_ath128',
                'MOAT_ath256'], output_where='data/moat_ath_sens')

##########################################################
##########################################################

elif STAT_WHICH == 'pac':
    dump_stats(['BASE_', 'PRAC_ONLY_DELAY',
                'PAC_nrh125',
                'PAC_nrh250',
                'PAC_nrh500',
                'PAC_nrh1000',
                'PAC_nrh2000'], output_where='data/pac')
elif STAT_WHICH == 'mopac':
    dump_stats(['BASE_', 'PRAC_ONLY_DELAY',
                'MOPAC_nrh125',
                'MOPAC_nrh250',
                'MOPAC_nrh500',
                'MOPAC_nrh1000',
                'MOPAC_nrh2000'], output_where='data/mopac')

##########################################################
##########################################################

