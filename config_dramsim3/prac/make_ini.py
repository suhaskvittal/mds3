'''
    author: Suhas Vittal
    date:   14 November 2024
'''

import math

##################################################################
##################################################################

ABO_LEVEL = 1

tABO = 180
tRC = 52
tRFM = 350
tREFW = 32*1e6
tRFC = 450

tA2A = tABO + (tRC+tRFM)*ABO_LEVEL
M = 3+ABO_LEVEL
tMAX = tREFW - 8192*tRFC

##################################################################
##################################################################

def N_RH(ath):
    n = tMAX / (ath*tRC + tA2A/ABO_LEVEL)
    return math.ceil(ath + math.log(n)/math.log(M/3) + M)

##################################################################
##################################################################

def search_for_ath(n_rh: int):
    prev_ath = n_rh
    while True:
        new_n_rh = N_RH(prev_ath-1)
        if new_n_rh < n_rh:
            return prev_ath
        else:
            prev_ath -= 1

def get_pac_ath(ath: int, p: int):
    ath_ = math.floor(ath/p)
    while True:
        pr = math.lgamma(ath+1) - math.lgamma(ath_+1) - math.lgamma(ath-ath_+1)
        pr += ath_ * math.log(1/p)
        pr += (ath-ath_) * math.log(1-1/p)
        pr = math.e**pr
        if pr < 1e-9:
            return ath_
        ath_ -= 1

##################################################################
##################################################################

POL_BASELINE = 0
POL_PAC_OR_MOPAC = 1

def write_ini_file(output_file: str, ath: int,\
        # Optionals:
        pac_prob=8,
        mopac_buf_size=5,
        mopac_abo_updates=5,
        mopac_ref_updates=1,
        mopac_drain_freq=1
):
    content =\
f'''
[dram_structure]
protocol = DDR5
bankgroups = 8
banks_per_group = 4
rows = 65536
columns = 2048
device_width = 4
BL = 16

[system]
channel_size = 16384
channels = 2
bus_width = 32
address_mapping = rohirababgchlo
mop_size = 4
queue_structure = PER_BANK
refresh_policy = RANK_LEVEL_STAGGERED
row_buf_policy = OPEN_PAGE
cmd_queue_size = 32
trans_queue_size = 128

MoatATH = {ath}
PacProb = {pac_prob}
MopacBufSize = {mopac_buf_size}
MopacABOUpdates = {mopac_abo_updates}
MopacREFUpdates = {mopac_ref_updates}
MopacDrainFrequency = {mopac_drain_freq}

[timing]
tCK = 0.416
AL = 0
CL = 28
CWL = 26
tRCD = 33
tRFC = 984
tRFCsb = 456
tRFCb = 528
tREFI = 9390
tREFIsb = 1170
tREFIb = 4680
tRRD_S = 8
tRRD_L = 12
tWTR_S = 6
tWTR_L = 24
tFAW = 32
tWR = 24
tRTP = 12
tCCD_S = 8
tCCD_L = 12
tCKE = 8
tCKESR = 13
tXS = 984
tXP = 18
tRTRS = 2

tRP = 33
tRAS = 76
tRP2 = 86
tRAS2 = 38

[rfm]
rfm_mode = 0
raaimt = 16
raammt = 48
rfm_raa_decrement = 16
ref_raa_decrement = 16
tRFM = 840

[alert]
alert_mode = 1
refchunks = 8192
tABO = 432 # 180 ns
ABO_delay_acts = 1

[power] 
VDD = 1.2
IDD0 = 57
IPP0 = 3.0
IDD2P = 25
IDD2N = 37
IDD3P = 43
IDD3N = 52
IDD4W = 150
IDD4R = 168
IDD5AB = 250
IDD6x = 30

[other]
epoch_period = 100000000
output_level = 1
output_prefix = DDR5_baseline
'''
    with open(output_file, 'w') as wr:
        wr.write(content)

##################################################################
##################################################################

# Baseline Config
write_ini_file('config_dramsim3/prac/baseline.ini', 128,8,5,5,1)

##################################################################
##################################################################

# Sensitivity on MOPAC Buffer Size
mopac_sens_ath = get_pac_ath(search_for_ath(500), 8)
for mopac_buf_size in [5, 8, 16, 32, 64]:
    for mopac_ref_updates in [0,1,2]:
        write_ini_file(f'config_dramsim3/prac/sens_mopac_buf/buf{mopac_buf_size}_ref{mopac_ref_updates}.ini',\
                            mopac_sens_ath,
                            mopac_buf_size=mopac_buf_size,
                            mopac_ref_updates=mopac_ref_updates)

# Sensitivity on MOAT ATH
for ath in [16, 20, 24, 28, 32, 64, 128, 256]:
    write_ini_file(f'config_dramsim3/prac/sens_moat_ath/ath{ath}.ini', ath)

# Sensitivity on PAC + MOPAC probability
for pr in [2,4,8,16]:
    ath = get_pac_ath(search_for_ath(500), pr)
    if ath < 1.0:
        print('[ PAC + MOPAC sens on `pr` ] Negative ATH for pr={pr}')
        continue
    write_ini_file(f'config_dramsim3/prac/sens_pac_mopac_pr/pr{pr}.ini')

##################################################################
##################################################################

# PAC with N_RH = 125, 250, 500, 1000, 2000
for nrh in [125, 250, 500, 1000, 2000]:
    pr = 2 * (nrh//125)
    ath = get_pac_ath(search_for_ath(nrh), pr)
    write_ini_file(f'config_dramsim3/prac/pac/nrh{nrh}.ini', ath, pac_prob=pr)

##################################################################
##################################################################

for nrh in [125, 250, 500, 1000, 2000]:
    pr = 2 * (nrh//125)
    ath = get_pac_ath(search_for_ath(nrh), pr)

    if nrh <= 500:
        mopac_ref_updates = 2
        mopac_drain_freq = 1
    else nrh == 1000:
        mopac_ref_updates = 1
        mopac_drain_freq = nrh//1000
    write_ini_file(f'config_dramsim3/prac/mopac/nrh{nrh}.ini',\
            ath,
            pac_prob=pr,
            mopac_buf_size=16,
            mopac_abo_updates=5,
            mopac_ref_updates=mopac_ref_updates,
            mopac_drain_freq=mopac_drain_freq)

##################################################################
##################################################################
