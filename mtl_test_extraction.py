# -*- coding: utf-8 -*-
import os
import sys
from xml.dom import minidom
from osgeo import gdal
from osgeo import osr
from osgeo import gdal
import glob
from gdalconst import *
import numpy as np
import imp
from global_variables import *
metadata_extraction = imp.load_source('metadata_extraction',os.path.join(PY_CLASS,'metadata_extraction.py'))

def main(argv):

    image = argv
    mtl = metadata_extraction.LandsatMTL(product)
    configuration_site_description_file=os.path.join(CONFIGURATION,'desc_Site.xml')

    mtl.set_test_site_information(configuration_site_description_file)
    mtl.display_mtl_info()

    print mtl.radiance_image_list
    



if __name__ == '__main__':

     product = '/home/saunier/DEV/LS08_ideas_cyclic_report__processing/PROCESSING/stabilityMonitoring/input/LC81810402017309MTI00/ROI_Libya4_half'
     'LC81810402018008MTI00/ROI_Libya4_half'
     product = os.path.join(PROCESSING,'LC81810402018008MTI00','ROI_Libya4_half')
     #product = os.path.join(PROCESSING,'LC81810402017309MTI00','ROI_Libya4_half')

     print product
     main(product)
