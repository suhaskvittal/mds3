import os
import time

CONFIGS = [
    'baseline',
    'sens_moat',
    'pac',
    'mopac',
    'sens_mopac_buf',
    'sens_mopac_df',
    'pac_rp',
    'mopac_rp',
]

for c in CONFIGS:
    os.system(f'python scripts/prac/run.py pace {c}')
    time.sleep(180)  # Wait 5 minutes to avoid QoS violation
