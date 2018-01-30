# -*- coding: utf-8 -*-
import os

#WINDOWS CONFIGURATION
#INFRA_HOME = 'C:\DATA\INFRA'
#INPUT_DATA = 'C:\DATA\INFRA\INPUT'
#CODE = 'C:\Users\saunier\PycharmProjects\LS08_ideas_cyclic_report_processing'
#HTTP_PAGES='/var/www/html/ls08_performance_report'
#PY_CLASS = 'C:\DEV\LIB\py_class'

#LINUX CONFIGURATION
INFRA_HOME = '/home/saunier/DEV/LS08_ideas_cyclic_report__processing'
INPUT_DATA = '/data1/LS8_OLI/'
CODE = '/home/saunier/DEV/LS08_ideas_cyclic_report__processing/CODE/LS08_ideas_cyclic_report_processing'
REFERENCE = '/home/saunier/INFRA/REFERENCE'
HTTP_PAGES='/var/www/html/ls08_performance_report'
PY_CLASS = '/home/saunier/INFRA/LIB/py_class'


CONFIGURATION = os.path.join(INFRA_HOME,'CONFIGURATION')
PROCESSING = os.path.join(INFRA_HOME,'PROCESSING')
REFERENCE = os.path.join(INFRA_HOME,'REFERENCE')
RESULT= os.path.join(INFRA_HOME,'RESULT')
CODE_m = os.path.join(CODE,'point-m')

#RADIOMETRY
RADIOMETRIC_STABILITY_RESULTS =  os.path.join(RESULT,'stabilityMonitoring')
RADIOMETRIC_STABILITY_RHO_RESULTS = os.path.join(RADIOMETRIC_STABILITY_RESULTS,'radio_stability_rho.txt')
RADIOMETRIC_STABILITY_RAD_RESULTS = os.path.join(RADIOMETRIC_STABILITY_RESULTS,'radio_stability_rad.txt')
#GEOMETRY
WD_INTERBAND_MS = os.path.join(PROCESSING,'interbandRegistration','wd_ms')
WD_INTERBAND_PAN = os.path.join(PROCESSING,'interbandRegistration','wd_pan')
if not os.path.exists(WD_INTERBAND_MS) :
   os.system(' '.join(['mkdir',WD_INTERBAND_MS ]))
if not os.path.exists(WD_INTERBAND_PAN) :
   os.system(' '.join(['mkdir',WD_INTERBAND_PAN ]))
FONT_PATH = os.path.join(CODE,'font')


