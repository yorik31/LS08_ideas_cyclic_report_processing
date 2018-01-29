# -*- coding: utf-8 -*-
# test routine
import os,sys, io
import imp
import glob
import numpy as np
import metadata_extraction
import main_infra
import log
from xml.dom import minidom
import time
import types
from osgeo import gdal
import correl_report as correl  #Internal Class
import image_processing as im_p #Internal Class 


#Load Lib ToCall runMedicisSpecificScript
#/usr/local/lib/python2.7/site-packages/run_medicis_module.py
from run_medicis_module import correl_image
from run_medicis_module import executeMedicis
from run_medicis_module import geocodedMedicsResults
from run_medicis_module import addDigitalElevationImage
from run_medicis_module import processStandardMedicisOutput
from run_medicis_module import updateMultitemporalMatFile

#Use global variables
from global_variables import *

import http_side #Internal Class 

global matlabProcessingDir
matlabProcessingDir='/home/saunier/INFRA/TOOLS/PERFORMANCE_EVALUATION_shell/geometricProcessing/point-m/'


global interest
interest='interbandRegistration'

global confidence
confidence = 0.95

global band_combination
band_combination = {}

ms=[[2,3],[3,4],
    [4,5],[5,6],
    [6,2],[10,11],
    [5,10]]

pan=[[8,3],[8,4],
     [8,5],[8,6],
     [8,2],[8,11],
     [8,10]]

band_combination["ms"] = ms
band_combination["pan"] = pan


global activityLabel
activityLabel='Landsat 08 Cyclic Report'



class interband:

    def __init__(self,band_type):
         self.band_type = band_type
         self.file_label = band_type+'_interbandRegistration' 
         self.mat_filename = ' '

         self.roi = ' '
         self.ref_channel = ''
         self.work_channel = ''
         self.refImage = ''
         self.workImage = ''
         self.main_wd = ''

    def set_ref_channel(self,band_twin):
         self.ref_channel=str(band_twin[0])   
         self.work_channel=str(band_twin[1])

    
    def search_image_twin(self,product):
         roi = self.roi
         ref_channel = self.ref_channel
         work_channel = self.work_channel
         self.refImage =glob.glob(os.path.join(os.path.join(product,roi,'*B'+ref_channel+'*.TIF')))[0]
         if os.path.exists(self.refImage):
               self.refImageTrue = True
               input_image = interband.refImage
               src_ds = gdal.Open(str(input_image)) #geotransform = src_ds.GetGeoTransform()
               self.ref_pixel_size = (src_ds.GetGeoTransform())[1]
               src_ds = None

         self.workImage=glob.glob(os.path.join(os.path.join(product,roi,'*B'+work_channel+'*.TIF')))[0]
         if os.path.exists(self.workImage):
               self.workImageTrue = True
               input_image = interband.workImage
               src_ds = gdal.Open(str(input_image))
               self.work_pixel_size = (src_ds.GetGeoTransform())[1]
               src_ds = None

         return (self.refImageTrue & self.workImageTrue)


    def get_output_filename(self,mtl,infra,ext):
#Return the path where is stored the mat / sta file in the Result Directory
         file_radical = mtl.landsat_scene_id 
         output_filename = file_radical+'_'+self.file_label+ext
         output_file = os.path.join(infra.result_location,
                                      interest,output_filename)           
         if os.path.exists(output_file):
             cmd = ' '.join(['rm -rf',output_file])
             log.info('[DEL] Remove mat File'+output_file)
#             os.system(cmd)
         return output_file




    def set_main_wd(self,infra,band_type):
         self.main_wd = os.path.join(infra.processing_location,interest,'wd_'+band_type) 
         return self.main_wd 

#Trigger_productSubview
# => Creation des sous produits en fonction des empruntes au sol definit dans la database de reference

def image_matching(mtl,infra,interband):
         
         refImage = interband.refImage
         workImage = interband.workImage

         if workImage is None :
            print ('missing product')
            return

         if refImage is None :
            print ('missing product')
            return


         band_type = interband.band_type
         roi = interband.roi
         ref_channel = interband.ref_channel
         work_channel = interband.work_channel
         print str(ref_channel)

         wd_name = (mtl.landsat_scene_id+'_'+os.path.basename(roi)+'_BD_REF'+ref_channel+'_BD_WORK'+work_channel)
         productWorkingDirectory=os.path.join(infra.processing_location,interest,'wd_'+band_type,wd_name)

         if os.path.exists(productWorkingDirectory) is False:
            cmd=' '.join(['mkdir -v',productWorkingDirectory])
            os.system(cmd) 
            print ('\n')

         else :
	    log.warn('-- Existing Product Working Directory / Remove Content')
	    cmd=' '.join(['rm -rf',os.path.join(productWorkingDirectory,'*')])
	    #os.system(cmd)
            print ('\n')



         refimageName=refImage        
         inputImage=workImage
         grille=os.path.join(productWorkingDirectory,"grille")
         paramMedicis=infra.configuration_medicis
 
         log.infog(" -- Execute Medicis ")
         #executeMedicis(refImage,inputImage,grille,paramMedicis)
         return productWorkingDirectory,grille




def assessmentManager_get_band_list(infra,metadata):

   xmldoc = minidom.parse(infra.configuration_assessment_description)
   missions=xmldoc.getElementsByTagName('mission')
   for mission in missions :
      sensor=mission.attributes["sensor"].value
      plateform=mission.attributes["plateform"].value
      if ( metadata.sensor == sensor ) and ( metadata.mission == plateform ):
     # -- For interest Get Mission specific Processing paramters
         print interest
         interest_block = (mission.getElementsByTagName(interest))
         band_list=(interest_block[0].getElementsByTagName('channel')[0]
                                                           .childNodes[0].data).split(' ')
   return band_list
#Trigger_directLocation_processing - in radiometric calibration stability
#Si produit present dans calibration stability
#1. Convertion en RADIANCE et en Top of Atmosphere
#2. Traitement statistique 
#3. Mise a jour du fichier de resultats








def trigger_productSubview():

   infra=main_infra.mainInfra()
   infra.checkDirectoryPresence()
   product_id='LC81810402013218LGN00'
   product=os.path.join(infra.input_data_location,product_id)
   mtl = metadata_extraction.LandsatMTL(product)
   mtl.get_test_site_information(infra.configuration_site_description_file)
   infra.makeProductSubview(mtl)


#Trigger_radio_processing - in radiometric calibration stability
#Si produit present dans calibration stability
#1. Convertion en RADIANCE et en Top of Atmosphere
#2. Traitement statistique 
#3. Mise a jour du fichier de resultats

def trigger_radio_processing():
   infra=main_infra.mainInfra()
   product_id='LC81810402013218LGN00'
#Hypothese : nous sommes dans le repertoire stabilityMonitoring
   interest='stabilityMonitoring'
   product_list=[rec for rec in glob.glob(os.path.join(infra.processing_location,interest,'input',product_id,'ROI*'))]
   for product in product_list:
      log.infog(' -- Processing of '+product+'  : ')
      mtl = metadata_extraction.LandsatMTL(product)
      log.info(' -- Convert to RAD / TOA')
      #r=rad.radiometric_calibration(product,mtl)
      log.info(' -- Extract / store statistics ')
      mtl.update_image_file_list()
      #mtl.display_mtl_info()
      image_file_list=mtl.rhotoa_image_list
      output_txt_file=infra.result_radiometricStability
      roi_id=os.path.basename(product)
      gainList = [ str(rec) for rec in  mtl.rescaling_gain]
      #print mtl.band_sequence
      extract_reflectance_in_roy.reduction_on_roi(mtl,image_file_list,output_txt_file,roi_id)
      print '\n'
      print output_txt_file
      #Move Product From input to done
   input_product=os.path.join(infra.processing_location,interest,'input',product_id)
   output_rep=os.path.join(infra.processing_location,interest,'done')
   cmd = ' '.join(['mv',input_product,output_rep])
   os.system(cmd)



def test_thresholdImage() :
    infra=main_infra.mainInfra()
    infra.checkDirectoryPresence()
    #trigger_productSubview()
    
    #trigger_radio_processing()
    cor_product = os.path.join(infra.processing_location,
                 'interbandRegistration',
                  'wd_pan',
                  'LC81960302017110MTI00_ROI_prism_roi_BD_REF8_BD_WORK10')
    
    
    land_sea_mask = os.path.join(infra.processing_location,
                               'interbandRegistration','input',
                               'LC81960302017110MTI00',
                               'ROI_prism_roi','land_sea_mask.tif')
    cor_conf_image = os.path.join(cor_product,'LC81960302017110MTI00_B10_dc-confidence.TIF')
    dst_file_name = os.path.join(cor_product,'LC81960302017110MTI00_B10_dc-displacement.TIF')

    infra.threshold_confidence_image(land_sea_mask,cor_conf_image,dst_file_name)
#threshold_displacement_image(self,cor_conf_image,d_image):
    dx_image = os.path.join(cor_product,'LC81960302017110MTI00_B10_dx-displacement.TIF')

    #infra.threshold_displacement_image(cor_conf_image,dx_image)

#07 / 09 / 2017 -  Amelioration des chaines de performances 'Test . py'
#Travailler sur test.py afin de lire les stats de chaque traitement et ensuite les stocker dans un fichier texte global a la racine


def create_statistics_report(wd_list,output_sta_file) :

   dst_txt_file = output_sta_file
   #Fetch all WD
   res = [] 
   for wd in wd_list :

          gl = glob.glob(os.path.join(wd,'stat.txt'))
          cr = correl.correl_report(gl)
          ch_out = cr.parse_file()
          if cr.exist :
              res.append(cr)
          #Add
   res2 = sorted(res,key = lambda cr: cr.ref_band)  
   hd=res2[0].get_header() #header
   f = open(dst_txt_file,'w')
   f.write(hd+'\n')
   for rec in  res2   :
       f.write((rec.export_record()).replace('.',',')+'\n')
   f.close() 
   print "result_save_in "+dst_txt_file
   return 



def trigger_interband_processing_with_ms(product,interband):

#Recall Object
   infra=main_infra.mainInfra()
   mtl = metadata_extraction.LandsatMTL(product)
   scene_id = mtl.landsat_scene_id

   mtl.set_test_site_information(infra.configuration_site_description_file)
   country_name=((mtl.test_site[0]).split())[0]
   site_name=((mtl.test_site[0]).split())[1]
   repo_ref=os.path.join(infra.reference_data_raster_file_location,country_name,site_name,'ROI');
#Access to assessment manager ? 
   band_list=assessmentManager_get_band_list(infra,mtl)   
#   mtl=None ? cette commande
   roi_list=[rec for rec in glob.glob(os.path.join(product,'ROI*'))]
#http class : interface with web server 
   http = http_side.performance_report(product)

   band_type = interband.band_type
   interband.set_main_wd(infra,band_type)

#-- MLAB output file initialisation
   file_label = interband.file_label
   ext = '.mat'
   result_mat_file= interband.get_output_filename(mtl,infra,ext)

#-- Summary Statistisque file_label - same level of mat file but
#   just list results in a CSV.
   ext = '.txt'
   result_sta_file= interband.get_output_filename(mtl,infra,ext)

  

#-- Loop on all image roi, perform correlation and statistics
   for roi in roi_list:
      print 'roi '+roi
      interband.roi = roi
      roi_name=os.path.basename(roi).split('_')[1]
      print ' '
      log.infog(' -------------------------')
      log.infog(' -- Processing of '+roi_name+' -- ')
      log.infog(' -------------------------')

      mtl = metadata_extraction.LandsatMTL(roi)
      mtl.set_test_site_information(infra.configuration_site_description_file)
      mtl.add_roi_name_information(roi_name)

#START Image Matching Loop
      wd_list = []
      for band_twin in band_combination[band_type]:
         interband.set_ref_channel(band_twin)
          
         test1=interband.search_image_twin(product)

	 if (interband.ref_channel == '8') : #Et mission Landsat alors rescaling a 30 m

             if  interband.ref_pixel_size == 15 :
                 log.infog(' -- Input Image scale is '+str(interband.ref_pixel_size)+' m --')
                 log.infog(' -- Input Image is rescaled '+str(interband.work_pixel_size)+' m --')
                 px_size = str(interband.work_pixel_size)
                 i_file = interband.refImage
                 o_file = interband.refImage.replace('B8.TIF','B8_30.TIF')
                 if not os.path.exists(o_file) : 
                     cmd = ' '.join(['gdalwarp -tr ', px_size,px_size, i_file, o_file])                 
                     os.system(cmd)
                 interband.refImage = o_file
             src_ds = None

if __name__ == '__main__':



    if len(sys.argv) == 2 :

    #The block below is not Valid  - Enter Valid atest block
        product = glob.glob(sys.argv[1])
        if len(product) == 0 :
           log.err('-- Invalid Product')

        else :
           product = os.path.abspath(product[0])
           log.infog(" -- Interband Registration with product : "+product+"\n")
           infra=main_infra.mainInfra()
           band_type = 'ms'
           interband = interband(band_type);

           trigger_interband_processing_with_ms(product,interband)
#           trigger_interband_processing_with_panchro(product)


    else:

        infra=main_infra.mainInfra()
        infra.checkDirectoryPresence()
        path_to_product=os.path.join(infra.processing_location,interest,'input','*')
        product_list=glob.glob(path_to_product)

        print "----------------------------------------------------"
        print "-- For trigger_interband_processing_with_panchro  --"
        print "-- Verified Landsat Panchro band has been created --"
        print "        gdalwarp -tr 30 30     i_file o_file        "
        print "-- with o_file : LC8xxxxxxyyyydoySSS00_B8_30.TIF    " 
        print "----------------------------------------------------"

        if len(product_list) > 0 :
            for product in product_list:

#                band_type = 'ms'
#                interband = interband(band_type);
#                trigger_interband_processing_with_ms(product,interband)
#                trigger_interband_processing_with_panchro(product)
                band_type = 'pan'
                interband = interband(band_type)
                trigger_interband_processing_with_ms(product,interband)


                log.infog(" --- Move Input Products to Done")  
                input_product=product
                DONE=os.path.join(infra.processing_location,interest,'done')
                cmd = ' '.join(['mv',input_product,DONE])
#                os.system(cmd)

        else :
             log.info(' -- No product to be processed ')
    
    log.info(' - End of geometric processing')




#Si radiometric calibration :

#make product suget_test_sitebview
#Copy mtl,
#Crop des images suivant ROI disponnibles (country/siteLabel)

#Convertion en toa
#Statistics

#r=radiometric_calibration(product) #convertion to toa

#

#shape_file

# Extraction des mtl
# Input  : Repertoire Landsat 8
# Output : Fichier MTL


# Extraction des rois en fonction de la zone


#def main(argv):

    #product_path = argv
    #product_list = build_product_list(product_path)
    #for product in product_list :

        #print "Processing of "+product
        #r=rad.radiometric_calibration(product)
        #r.product.display_mtl_info()


#if __name__ == '__main__':
    #if len(sys.argv) > 1:
        #main(sys.argv[1])
    #else:
        #print "Un Seul parametre attendu"
        #print "Parametre d entree: Chemin vers repertoire du produit"
        #print "le contener des produits ESA se termine par .TIFF "
        #product_path='C:/DATA/LANDSAT/Landsat-Time-Series-Lybia/TM_L1T_USGS'
        #main(product_path)
