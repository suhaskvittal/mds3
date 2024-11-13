'''
    author: Suhas Vittal
    date:   11 November 2024
'''

import math
import os
from copy import deepcopy

NCORE = 8

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

policies = [
# BASELINES
        'BASE_',
        'PRAC_ONLY_DELAY',
# MOAT
        'PRAC_MOAT_ath16',
        'PRAC_MOAT_ath20',
        'PRAC_MOAT_ath24',
        'PRAC_MOAT_ath28',
        'PRAC_MOAT_ath32',
        'PRAC_MOAT_ath64',
        'PRAC_MOAT_ath128',
        ]
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
    print(f)
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
#   if bname in ['add', 'copy', 'scale', 'bfs', 'sssp', 'tc', 'bfs', 'cc', 'pr', 'bc']:
#       continue
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

BAR = ''.join(['-' for _ in range(32*len(policies))])

'''-------------------------------------------
   PRINT OUT STATS
-------------------------------------------'''

def get_rel(a, b):
    if a == 0 and b == 0:
        return 0
    elif a == 0:
        return 'inf'
    else:
        return b/a

def print_stat(name: str, list_relative=True):
    print('\n\n\n')
    print(BAR)
    print(f'{"":<24}', ''.join(f'{p:<24}' for p in policies))
    print(BAR)
    print(f'GMEAN {name:<18}', end='')
    for p in policies:
        if list_relative:
            rel = get_rel(stats[p][name], stats[base][name])
        else:
            rel = stats[p][name]
        print(f'{rel:<24.3f}', end='')
    print()
    print(BAR)

    stat_list = f'{name}_list'
    for b in stats[base][stat_list]:
        print(f'{b:<24}', end='')
        for p in policies:
            if list_relative:
                rel = get_rel(stats[p][stat_list][b], stats[base][stat_list][b])
            else:
                rel = stats[p][stat_list][b]
            print(f'{rel:<24.3f}', end='')
        print()

print_stat('ipc')
#print_stat('alerts', False)
