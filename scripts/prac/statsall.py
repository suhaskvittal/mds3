import os

CONFIGS = [
    'sens_mopac_buf',
    'sens_moat',
    'sens_mopac_df',
    'pac',
    'mopac',
    'pac_rp',
    'mopac_rp'
]

for c in CONFIGS:
    print(c, '---------------------------------------')
    os.system(f'python scripts/prac/stats.py {c}')
