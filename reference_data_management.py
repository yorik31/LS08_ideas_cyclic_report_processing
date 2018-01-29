# -*- coding: utf-8 -*-
# init class
import os, sys
import numpy as np
#from itertools import groupby
#from scipy.interpolate import InterpolatedUnivariateSpline
#import reflectanceProfile
#import observationPoint
import glob
from xml.dom import minidom
import log

class referenceData:

#
#
# description : xml file in configuration
# path : location where are stored shapefile
#

 def __init__(self, description_file,path):
        self.reference_data_path = path
        self.description_file = description_file

 def get_data_list(self,siteId,country,interest,ref_type):
        log.info(' -- For interest '+interest+' , selection of '+os.path.join(self.reference_data_path,country,siteId ))
        
        #Depending on site, interest select the needed data
        #Inputs:
        #	1.siteId
        #	2.country
        #	3.interest
        #	4.ref_type ,ref_type = ['vector, 'raster','dem']

        reference_file_list=[]
        #Access to xml file  
        xmldoc = minidom.parse(self.description_file)
        refs=xmldoc.getElementsByTagName('ref')
        for ref in refs :
           s = (ref.getElementsByTagName('siteId'))[0].childNodes[0].data
           c = (ref.getElementsByTagName('country'))[0].childNodes[0].data
           ref_t = (ref.getElementsByTagName('type'))[0].childNodes[0].data
           ct=ref.getElementsByTagName(interest).length
           if ((siteId ==s ) and (country == c) and ( ct > 0 ) and (ref_t == ref_type)) :
                 filename= (ref.getElementsByTagName('filename'))[0].childNodes[0].data
                 output_file=os.path.join(self.reference_data_path,c,s,'ROI',filename)
                 if os.path.isfile(output_file):
                     reference_file_list.append(output_file)
                     log.info( ' -- Check file presence => ok ')
                     print '\n'
                 else :
                     log.err( ' -- No '+ref_type+'reference file  \n ')
        return reference_file_list
