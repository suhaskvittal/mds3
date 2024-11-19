import os
import time

CONFIGS = [
    'baseline',
    'sens_mopac_buf',
    'sens_moat_ath',
    'sens_pac_mopac_pr',
    'pac',
    'mopac'
]

for c in CONFIGS:
    os.system(f'python scripts/prac/run.py pace {c}')
    time.sleep(45)  # Wait 5 minutes to avoid QoS violation
