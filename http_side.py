# -*- coding: utf-8 -*-
# init class
import os, sys
import shutil
from os import listdir
from osgeo import gdal
import glob
import re as r
import imp
import log
from global_variables import *
metadata_extraction = imp.load_source('metadata_extraction',os.path.join(PY_CLASS,'metadata_extraction.py'))


#September, 05 Wednesday : S . Saunier
#   -- Http side   --


class performance_report:
    def __init__(self,product):

        mtl = metadata_extraction.LandsatMTL(product)
        scene_id = mtl.landsat_scene_id
        obs_date = (mtl.observation_date)
	year_month =  obs_date.split('-')[0]+obs_date.split('-')[1]

        self.main = os.path.join(HTTP_PAGES,year_month)
        self.ql_location = os.path.join(HTTP_PAGES,year_month,scene_id,'QL')
        self.md_location = os.path.join(HTTP_PAGES,year_month,scene_id)

        self.interband_report_location_pan = os.path.join(HTTP_PAGES,year_month,scene_id,'interbandRegistration_PAN')
        self.interband_report_location_ms = os.path.join(HTTP_PAGES,year_month,scene_id,'interbandRegistration_MS')
        self.geolocation_report_location = os.path.join(HTTP_PAGES,year_month,scene_id,'directLocation')
        self.stability_monitoring_report_location = os.path.join(HTTP_PAGES,year_month,scene_id,'stabilityMonitoring')

        if os.path.exists(self.ql_location) is False:
             cmd=' '.join(['mkdir -pv', self.ql_location])
             os.system(cmd)

        if os.path.exists(self.interband_report_location_pan) is False:
             cmd=' '.join(['mkdir -pv', self.interband_report_location_pan])
             os.system(cmd)

        if os.path.exists(self.interband_report_location_ms) is False:
             cmd=' '.join(['mkdir -pv', self.interband_report_location_ms])
             os.system(cmd)

        if os.path.exists(self.geolocation_report_location) is False:
             cmd=' '.join(['mkdir -pv', self.geolocation_report_location])
             os.system(cmd)

        if os.path.exists(self.stability_monitoring_report_location) is False:
             cmd=' '.join(['mkdir -pv', self.stability_monitoring_report_location])
             os.system(cmd)


    def  updateContent(self,src,interest,bandType):

#Manage output when Interband registration
         if interest == 'interbandRegistration' :
             if bandType == 'ms':
                dst = self.interband_report_location_ms
                roi = ((os.path.basename(src)).split('_'))[2]                
                ref_ch = ((os.path.basename(src)).split('_'))[4] 
                work_ch = ((os.path.basename(src)).split('_'))[-1] 
             if bandType == 'pan':
                dst = self.interband_report_location_pan
                roi = ((os.path.basename(src)).split('_'))[2]                
                ref_ch = 'REF8'
                work_ch = ((os.path.basename(src)).split('_'))[-1]  
             dst_rep = 'roi_'+roi+'_'+ref_ch+'_'+work_ch
#Prepare output directory
             if not os.path.exists( os.path.join(dst,dst_rep) ):
                log.infog('-- Create Output Directory on http')
                cmd = ' '.join(['mkdir -v ', os.path.join(dst,dst_rep) ])
                os.system(cmd)

#Copy PNG files              
             cmd = ' '.join(['cp -r ',os.path.join(src,'*.png'),  os.path.join(dst,dst_rep) ])
             os.system(cmd)
#Copy JPG files              
             cmd = ' '.join(['cp -r ',os.path.join(src,'*Radial_Error_QL.jpg'),  os.path.join(dst,dst_rep) ])
             os.system(cmd)
#Prepare Files (gdal warp) 
             src_file = glob.glob(os.path.join(src,'*confidence_binaryMask_*rescale.tif'))[0]
             dst_file =  os.path.join(dst,dst_rep,'dc-confidence_mask.png')               
             cmd = ' '.join(['gdal_translate -ot Byte -scale 0 1 0 255',src_file,dst_file,'-of PNG'])
             os.system(cmd)
#Copy Results
             print cmd

#Manage output when Direct Location
         if interest == 'directLocation' :
             dst = self.geolocation_report_location
             print 'DST : '+dst
                
             if bandType == 'ms':
                  roi = ((os.path.basename(src)).split('_'))[2]                
                  ref_ch = ((os.path.basename(src)).split('_'))[4] 
                  work_ch = ((os.path.basename(src)).split('_'))[-1] 
             if bandType == 'pan':
                  roi = ((os.path.basename(src)).split('_'))[2]                
                  ref_ch = 'REF8'
                  work_ch = ((os.path.basename(src)).split('_'))[-1]  
             dst_rep = 'roi_'+roi+'_'+ref_ch+'_'+work_ch
#Prepare output directory
             if not os.path.exists( os.path.join(dst,dst_rep) ):
                 log.infog('-- Create Output Directory on http')
                 cmd = ' '.join(['mkdir -v ', os.path.join(dst,dst_rep) ])
                 os.system(cmd)

#Copy PNG files              
             cmd = ' '.join(['cp -r ',os.path.join(src,'*.png'),  os.path.join(dst,dst_rep) ])
             os.system(cmd)
#Copy JPG files              
             cmd = ' '.join(['cp -r ',os.path.join(src,'*Radial_Error_QL.jpg'),  os.path.join(dst,dst_rep) ])
             os.system(cmd)
#Prepare Files (gdal warp) 
             src_file = glob.glob(os.path.join(src,'*confidence_binaryMask_*rescale.tif'))[0]
             dst_file =  os.path.join(dst,dst_rep,'dc-confidence_mask.png')               
             cmd = ' '.join(['gdal_translate -ot Byte -scale 0 1 0 255',src_file,dst_file,'-of PNG'])
             os.system(cmd)
#Copy Results

#Manage output when Stability Monitoring

         if interest == 'stabilityMonitoring' :
                dst = self.stability_monitoring_report_location


#CP MAT FILE TO SERVER DIRECTORY
    def  updateContentWith_FILE(self,src,dst_file_name,interest,bandType):


         if interest == 'directLocation' :
             dst =  self.geolocation_report_location
             roi = os.path.basename(
                     (os.path.dirname(src))).split('_')[2]                
             roi_rep = 'roi_'+roi
             ref_ch = 'REF8'
             work_ch = '8'
             dst_rep = 'roi_'+roi+'_'+ref_ch+'_'+work_ch
             dst_file = os.path.join(dst,dst_rep,dst_file_name)

	 if interest == 'interbandRegistration' :
             if bandType == 'ms':
                 dst =  self.interband_report_location_ms

             if bandType == 'pan':
                 dst =  self.interband_report_location_pan

             dst_file = os.path.join(dst,dst_file_name)
         print "DST : "+dst_file
#Check Input / Output         
         if not os.path.exists(src) :
            log.err(' -- [ERROR   ] File Source Missing')
            log.err(' -- [ERROR   ] '+src)
            return False
            
         if os.path.exists(dst_file):
            log.warn(' -- [WARN    ] File Exist in the server')
            log.info(' -- [WARN    ] '+dst_file)
            cmd = ' '.join(['rm -rf',dst_file])
            os.system(cmd)

         if os.path.exists(os.path.join(src)):             
             cmd = ' '.join(['cp -r ',os.path.join(src),  dst_file ])
             os.system(cmd)
             log.info(' -- [COPY    ] : '+src)
             log.info(' -- [COPY    ] to : '+dst_file+'\n')

             return True

    def  updateWithDirectLocationMATFile(self,result_mat_file):
         if not os.path.exists(result_mat_file) :
             log.error(' -- [ERR    ] Mat file is missing '+'\n')
             return False
         else :
             cmd = ' '.join(['cp -r ',result_mat_file,self.main])
             os.system(cmd)
             return True


    def  updateContentWitQL(self,productWorkingDirectory,interest,bandType,ql_name):
#IF QL Available COPY
         if interest == 'directLocation' :
                dst = self.geolocation_report_location

         if interest == 'stabilityMonitoring' :
                dst = self.stability_monitoring_report_location

         if interest == 'interbandRegistration' :
             if bandType == 'ms':
                dst = self.interband_report_location_ms
             if bandType == 'pan':
                dst = self.interband_report_location_pan
             dst_rep = dst

#Copy PNG files              

             cmd = ' '.join(['cp -r ',ql_name, dst ])
             os.system(cmd)

