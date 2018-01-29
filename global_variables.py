# -*- coding: utf-8 -*-
import os

INFRA_HOME = 'C:\DATA\INFRA'
INPUT_DATA = 'C:\DATA\INFRA\INPUT'
CODE = 'C:\Users\saunier\PycharmProjects\LS08_ideas_cyclic_report_processing'
#CODE_m = '/home/saunier/DEV/LS08_ideas_cyclic_report__processing/CODE/point-m'
RESULT = '/home/saunier/DEV/LS08_ideas_cyclic_report__processing/RESULT'
CONFIGURATION = 'C:\DATA\INFRA\CONFIGURATION'
PROCESSING = 'C:\DATA\INFRA\PROCESSING'
REFERENCE = 'C:\DATA\INFRA\REFERENCE'
RESULT= os.path.join(INFRA_HOME,'RESULT')
RADIOMETRIC_STABILITY_RESULTS =  os.path.join(RESULT,'stabilityMonitoring')
RADIOMETRIC_STABILITY_RHO_RESULTS = os.path.join(RADIOMETRIC_STABILITY_RESULTS,'radio_stability_rho.txt')
RADIOMETRIC_STABILITY_RAD_RESULTS = os.path.join(RADIOMETRIC_STABILITY_RESULTS,'radio_stability_rad.txt')
#HTTP_PAGES='/var/www/html/ls08_performance_report'
PY_CLASS = 'C:\DEV\LIB\py_class'
WD_INTERBAND_MS = os.path.join(PROCESSING,'interbandRegistration','wd_ms')
WD_INTERBAND_PAN = os.path.join(PROCESSING,'interbandRegistration','wd_pan')
if not os.path.exists(WD_INTERBAND_MS) :
   os.system(' '.join(['mkdir',WD_INTERBAND_MS ]))
if not os.path.exists(WD_INTERBAND_PAN) :
   os.system(' '.join(['mkdir',WD_INTERBAND_PAN ]))
FONT_PATH = os.path.join(CODE,'font')


