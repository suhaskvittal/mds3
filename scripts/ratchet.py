'''
    author: Suhas Vittal
    date:   13 November 2024
'''

import math

ABO_LEVEL = 1

tABO = 180
tRC = 52
tRFM = 350

t_alert_to_alert = tABO + (tRC+tRFM)*ABO_LEVEL

