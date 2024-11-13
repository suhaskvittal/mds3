import math
import os
from copy import deepcopy

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
            dat = line.split('\t')
        if len(dat) <= 1:
            continue
        for i in range(2):
            dat[i] = dat[i].strip()
        d[dat[0]] = dat[1]
    return d

from sys import argv

baseline = argv[1]  # Baseline config
cfg = argv[2]  # Compare against

base_stats = { 
              'tot_files': 0, 
              'log_ipc': 1.0,
              'ipc_list': {}
              }
cfg_stats = deepcopy(base_stats)

stat_files = [ f for f in os.listdir('out') if f.endswith('.out') ]
for f in stat_files:
    if baseline not in f and cfg not in f:
        continue
    bname = f.split('_')[0]
    d = get_stats_from_file(fr'out/{f}')
    gmlogipc = 1.0
    for i in range(4):
        gmlogipc += math.log( float(d[f'CORE_{i}_IPC']) )
    gmipc = math.e**(gmlogipc*0.25)
    print(bname, gmipc)
    if baseline in f:
        sd = base_stats
    else:
        sd = cfg_stats
    sd['log_ipc'] += gmlogipc*0.25
    sd['tot_files'] += 1
    sd['ipc_list'][bname] = gmipc

for sd in [base_stats, cfg_stats]:
    sd['ipc'] = math.e**(sd['log_ipc'] / sd['tot_files'])
print('RESULTS---------------------------\n')
print('GEOMEAN\t', cfg_stats['ipc']/base_stats['ipc'])
for b in base_stats['ipc_list']:
    print(f'\t{b}\t', cfg_stats['ipc_list'][b]/base_stats['ipc_list'][b])
