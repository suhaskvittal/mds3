'''
    author: Suhas Vittal
    date:   13 November 2024
'''

import math

ABO_LEVEL = 1

tABO = 180
tRC = 52
tRFM = 350
tREFW = 32*1e6
tRFC = 450

tA2A = tABO + (tRC+tRFM)*ABO_LEVEL
M = 3+ABO_LEVEL
tMAX = tREFW - 8192*tRFC

def N_RH(ath):
    n = tMAX / (ath*tRC + tA2A/ABO_LEVEL)
    return math.ceil(ath + math.log(n)/math.log(M/3) + M)

from sys import argv

if argv[1] == '-nrh':
    nrh = int(argv[2])
    p = int(argv[3])
    USE_NORMAL = '-normal' in argv
    # Search for ath.
    prev_ath = nrh
    while True:
        new_nrh = N_RH(prev_ath-1)
        if new_nrh < nrh:
            break
        else:
            prev_ath -= 1
    # Found ATH for MOAT, now need ATH*
    ath = prev_ath
    # ATH*:
    if USE_NORMAL:
        ath_mean = ath / p
        ath_std = math.sqrt(ath * (1/p) * (1-1/p))
        ath_ = math.floor(ath_mean - 6*ath_std)
    else:
        ath_ = math.floor(ath/p)
        while True:
            pr = math.lgamma(ath+1) - math.lgamma(ath_+1) - math.lgamma(ath-ath_+1)
            pr += ath_ * math.log(1/p)
            pr += (ath-ath_) * math.log(1-1/p)
            pr = math.e**pr
            if pr < 1e-9:
                break
            ath_ -= 1
    print(ath, ath_)
else:
    ath = int(argv[2])
    print(N_RH(ath))

