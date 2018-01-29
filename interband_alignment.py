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

#pan=[[8,11]]

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
               input_image = self.refImage
               src_ds = gdal.Open(str(input_image)) #geotransform = src_ds.GetGeoTransform()
               self.ref_pixel_size = (src_ds.GetGeoTransform())[1]
               src_ds = None

         self.workImage=glob.glob(os.path.join(os.path.join(product,roi,'*B'+work_channel+'*.TIF')))[0]
         if os.path.exists(self.workImage):
               self.workImageTrue = True
               input_image = self.workImage
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
             os.system(cmd)
         return output_file




    def set_main_wd(self,infra,band_type):
         self.main_wd = os.path.join(infra.processing_location,interest,'wd_'+band_type) 
         return self.main_wd 


#Trigger_productSubview
# => Creation des sous produits en fonction des empruntes au sol definit dans la database de reference

def image_matching(mtl,infra,interband,cor):
         
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

         wd_name = (mtl.landsat_scene_id+'_'+os.path.basename(roi)+'_BD_REF'+ref_channel+'_BD_WORK'+work_channel)
         productWorkingDirectory=os.path.join(infra.processing_location,interest,'wd_'+band_type,wd_name)

         if os.path.exists(productWorkingDirectory) is False:
            cmd=' '.join(['mkdir -v',productWorkingDirectory])
            os.system(cmd) 
            print ('\n')

         else :
	    log.warn('-- Existing Product Working Directory / Remove Content')
	    cmd=' '.join(['rm -rf',os.path.join(productWorkingDirectory,'*')])
	    os.system(cmd)
            print ('\n')



         refimageName=refImage        
         inputImage=workImage
         grille=cor.grille
         paramMedicis=infra.configuration_medicis
 
         log.infog(" -- Execute Medicis ")
         executeMedicis(refImage,inputImage,cor.grille,paramMedicis)
         return productWorkingDirectory




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

def Mlab_run(mtl,mat_filename,productWorkingDirectory,pixelSpacing):

         
         medicisDirectory = productWorkingDirectory
         result_file = mat_filename
         log.infog(' -- Save in : ')
         log.infog(' --- '+result_file+' \n')
         matlabProcessingDir=infra.matlab_processing

         #processStandardMedicisOutput(pixelSpacing,medicisDirectory,
         #                            result_file,matlabProcessingDir,
         #                            activityLabel)
         
         rootdir='/home/saunier/Documents/MATLAB'
         updateMultitemporalMatFile(mtl, medicisDirectory,
	 		      result_file, matlabProcessingDir,
	 		      activityLabel, pixelSpacing, rootdir)


#         time.sleep(20)


def create_statistics_report(wd_list,output_sta_file) :

         dst_txt_file = output_sta_file
   #Fetch all WD and create txt_file
         res = [] 
         for wd in wd_list :
            gl = glob.glob(os.path.join(wd,'stat.txt'))
            cr = correl.correl_report(gl)
            ch_out = cr.parse_file()         
            if cr.exist :
                res.append(cr)

         res2 = sorted(res,key = lambda cr: cr.ref_band)  
         hd=res2[0].get_header() #header
         f = open(dst_txt_file,'w')
         f.write(hd+'\n')
         for rec in  res2   :
            print rec.export_record()
            f.write((rec.export_record()).replace('.',',')+'\n')
         f.close() 


         print "result_save_in "+dst_txt_file




def trigger_interband_processing(product,interband):

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
      interband.roi = roi
      roi_name=os.path.basename(roi).split('_')[1]
      print ' '
      print ' -------------------------'
      log.infog(' -- Processing of '+roi_name+'  : ')
      mtl = metadata_extraction.LandsatMTL(roi)
      mtl.set_test_site_information(infra.configuration_site_description_file)
      mtl.add_roi_name_information(roi_name)

#START Image Matching Loop
      wd_list = []
      for band_twin in band_combination[band_type]:

         interband.set_ref_channel(band_twin)
         test1=interband.search_image_twin(product)
         if test1 :
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


             band_type = interband.band_type
             roi = interband.roi
             ref_channel = interband.ref_channel
             work_channel = interband.work_channel
             wd_name = (mtl.landsat_scene_id+'_'+os.path.basename(roi)+'_BD_REF'+ref_channel+'_BD_WORK'+work_channel)
             productWorkingDirectory=os.path.join(infra.processing_location,interest,'wd_'+band_type,wd_name)
 
             cor = correl_image(os.path.join(productWorkingDirectory,'grille.hdf'))
             print cor.grille
             print interband.refImage
             productWorkingDirectory = image_matching(mtl,
                                                      infra,
                                                      interband,
                                                      cor)
         wd_list.append(productWorkingDirectory)
         cor = correl_image(os.path.join(productWorkingDirectory,'grille.hdf'))



#GEOCODING
         log.infog(" -- Geocoded Medicis Results")
         inputImage = interband.workImage
         refimageName = interband.workImage  #?

#Size of input Full Image (correlation undersampled input images ...)
      
         src_filename = inputImage
         src_ds = gdal.Open(str(src_filename))
         image_width = src_ds.RasterXSize
         image_length = src_ds.RasterYSize
         src_ds = None

         cor.geocoded(inputImage,refimageName,productWorkingDirectory)
         if (cor.geocoded_valid) :
             dx = cor.dx
             dy = cor.dy
             dc = cor.dc
             mask =  cor.mask
         else :
            log.warning(" --  [ERROR ] No Correlation Results in ")          
            log.warning(" --  [ERROR ] No Correlation Results in ")          
            return


#FILTERING : IF MASK AVAILABLE - APPLIED
         log.infog(" -- Mask Confidence Image with land_sea mask \n")
         land_sea_mask  = os.path.join(product,roi,'land_sea_mask.tif') 
     
         if os.path.exists(land_sea_mask):
             log.infog(" --- Land Sea Mask Exist : "+land_sea_mask)
             input_image = dc
             mask = land_sea_mask
             log.infog(" --- Applied Land Sea Mask to confidence image")
             list_image = []
             list_image.append(input_image)
             im_st = im_p.image(list_image)
             im_st.maskImage(mask,productWorkingDirectory)
             log.info(" -- Create "+im_st.masked_image+' \n')
             cmd = ' '.join(['mv', im_st.masked_image,dc])
             os.system(cmd)
             im_st = None


#FILTERING : APPLIED CONFIDENCE THRESHOLD ON DC - can applied to DX,DY,DC
         list_image = []
         list_image.append(dc)
         im_st = im_p.image(list_image)
         im_st.histerysisThreshold(confidence,productWorkingDirectory)
         dc = im_st.masked_image
         dc_mask = im_st.mask_image #BINARY MASK
         im_st = None

#UPDATE DC / DC MASK WITH 3 SIGMA THRESHOLD ON DX , DY
         im_st = im_p.image([dc,dc_mask])

         n_value = 3          #SIGMA VALUE
         threshold = confidence     #CONFIDENCE VALUE - 
         log.infog(" --- Applied Sigma Threshold to DX ")
         DX_proc_flag = im_st.sigma_threshold(dx,n_value,confidence)
         log.infog(" --- Applied Sigma Threshold to DY ")
         DY_proc_flag = im_st.sigma_threshold(dy,n_value,confidence)
         dc = im_st.masked_image
         dc_mask = im_st.mask_image #BINARY MASK
         cmd = ' '.join(['mv', im_st.masked_image,cor.dc]) #Ecrase DC - original in "OLD"
         os.system(cmd) 
         im_st = None

	 print "Exit Processing if cannot applied 3 sigma threshold "

         if ((not DX_proc_flag) or (not DY_proc_flag)) :
            log.err(" -- Correlation is NOT successfull")
	    log.err(" --             After 3 Sigma threshold ")
	    log.err(" --             There is no sufficient point above the confidence threshold ")
            log.err(" --             Processing Abort and record not added to the m lab structure ")
         
	    return
	


#APPLIED DC BINARY MASK TO DX, DY
         mask = dc_mask
         list_image = []
         list_image.append(dx)
         im_st = im_p.image(list_image)
         im_st.maskImage(mask,productWorkingDirectory)
         log.info(" -- Create "+im_st.masked_image+' \n')
         dx = im_st.masked_image
         im_st = None

         list_image = []
         list_image.append(dy)
         im_st = im_p.image(list_image)
         im_st.maskImage(mask,productWorkingDirectory)
         log.info(" -- Create "+im_st.masked_image+' \n')
         dy = im_st.masked_image
         im_st = None

         log.infog(" -- Mask :"+dc_mask)
         log.infog(" -- DX   :"+dx)
         log.infog(" -- DY   :"+dy)
         log.infog(" -- DC   :"+dc+'\n')

#COMPUTE DX²+ DY² - RADIAL ERROR
         list_image = [dx,dy]
         
         dst_file_name = os.path.join(productWorkingDirectory,scene_id+
                                      '_B'+interband.ref_channel+
                                      '_B'+interband.work_channel+
                                      '_radialError_'+
                                       str(np.int(confidence*100))+'.tif',)
         im_st = im_p.image(list_image)
         if (im_st.computeRadialError(dst_file_name)):
            cor.radial_error = dst_file_name
            cor.radial_error_valid = True
         im_st = None

#STATISTICS DX

#STATISTICS DY

#STATISTICS DC

#--  QL Radial Error - Overlayed Image Band with B1 B2 B3 Image
#Rescale QL Radial Error to size of B1 , B2 , B3 
         list_image = [interband.workImage]
         im1 = cor.radial_error
         dst_filename = im1.replace('.tif','_rescale.tif')
         im_st = im_p.image(list_image)
         im_st.rescaleImage(im1,dst_filename)   
         cor.radial_error_rescaled = dst_filename

         im1 = dc_mask
         dst_filename = im1.replace('.TIF','_rescale.tif')

         im_st.rescaleImage(im1,dst_filename)   #Geometric Rescaling
         cor.dc_mask_rescaled = dst_filename

         im_st = None

#BURN TIF IMAGES WITH RADIAL ERRORS
         #Convert each image to 8 Bits
         list_image = []
	 list_image.append(glob.glob(os.path.join(product,roi,'*B2.TIF'))[0]) # QL Generation
	 list_image.append(glob.glob(os.path.join(product,roi,'*B3.TIF'))[0]) # QL Generation
	 list_image.append(glob.glob(os.path.join(product,roi,'*B4.TIF'))[0]) # QL Generation
         im_st = im_p.image(list_image)
         dst_repo = productWorkingDirectory
         output_list = im_st.byte_rescaling(dst_repo )
         im_st = None

         #Burn each one tif images
         list_image = output_list
         output_list = []

         for image in list_image:
              output_list.append(image.replace('.tif','_burn.tif'))

         im_st = im_p.image(list_image)
         im_filename = cor.radial_error_rescaled #Radial Error Value map to QL 
         mask_filename = cor.dc_mask_rescaled    #DC Mask to select pixel
         im_st.burn_image(output_list,im_filename,mask_filename)
         im_st = None

         #Create the quick look 
         image_data_list = output_list
         ql_name = os.path.join(productWorkingDirectory,scene_id+
                                      '_B'+interband.ref_channel+
                                      '_B'+interband.work_channel+
                                      '_Radial_Error_QL.jpg')
	  
	 outputdir =  productWorkingDirectory
	 quick_look_resolution = 30
	 im_st = im_p.image(image_data_list) # Create Object instance
	 im_st.createimageQuicklook(ql_name,outputdir,quick_look_resolution)




#-- MLAB Production

         #result file is matlab file (.mat)

         pixelSpacing=interband.ref_pixel_size  #Pixel spacing of the orginal Image

         #[NFO]       Mlab_run - attente des fichiers dx,dy,dc normés
         #            M=dir([obj.repName filesep '*_dx-displacement.TIF']); 
         #            M=dir([obj.repName filesep '*_dy-displacement.TIF']);            
         #            M=dir([obj.repName filesep '*_dc-confidence.TIF']);  

         Mlab_run(mtl,
                  result_mat_file,
                  productWorkingDirectory,
                  pixelSpacing)
         
         ##TEMPS MININIMUM A 30 BIEN ATTENDRE LA FIN DE TRAITEMENT
         print (' ')
         log.warn('TIME SLEEP ACTIVIATED - 30 s - Wait end of M LAB PROCESSING')
         log.warn('TIME SLEEP ACTIVIATED - 30 s - Important to let Completion')
         log.warn('TIME SLEEP ACTIVIATED - 30 s - of the mat file ')
         print (' ')

         time.sleep(30)

#--- 2. Repatriate BD2 BD3 BD4 Images
#--- 3. Open Images and Burn Values
#--- 4. Create QL

#-- CP to the HTTP
         src_directory = productWorkingDirectory
#-- Copy MLAB Results   (PNG) to repository
#-- Copy DC  mask image (PNG)to http repository
#-- Copy Radial Error  image (JPG)to http repository

         http.updateContent(productWorkingDirectory,interest,band_type)

#Remove the hdf file as output from medicis
         hdf_grille = os.path.join(productWorkingDirectory,'grille.hdf')
         if os.path.exists(hdf_grille):
            cmd = ' '.join(['rm -f ',hdf_grille])
            os.system(cmd)

#[END] of processing the band twin LOOP
      log.infog(" - End Loop on WD LIST \n")

#Generate A single stat/csv for all Report WD in this processing
      log.infog(" - [STA File] Create STA File : "+result_sta_file)     
      create_statistics_report(wd_list,result_sta_file)

#PARTIE EXPORT SUR HTTP A SEPARER DE CETTE FONCTION


      print ( ' ')
      log.infog(" - Populate HTTP \n")

# POPULATE HTTP WITH ALL RESULTS :
#--  MAT FILE :
      dst_file_name = ''.join([mtl.landsat_scene_id,'_','roi_',roi_name,'_inter_',band_type,'.mat'])
      if not (http.updateContentWith_FILE(result_mat_file,dst_file_name,interest,band_type)):
#          log.info(" -- [MAT File] Copy From : "+result_mat_file)
#          log.info(" -- [MAT File] to   : "+dst_file_name)
#      else :
          log.err(" -- [ERROR   ] Input / Output MAT FILE Missing+'\n' ")

#--  STA FILE :
      dst_file_name = ''.join([mtl.landsat_scene_id,'_','roi_',roi_name,'_inter_',band_type,'.txt'])
      if not (http.updateContentWith_FILE(result_sta_file,dst_file_name,interest,band_type)):
#          log.info(" -- [MAT File] Copy From : "+result_sta_file)
#          log.info(" -- [MAT File] to   : "+dst_file_name)
#      else :
          log.err(" - [ERROR   ] Input / Output TXT-STA FILE Missing+'\n' ")


#--  QL
      listql=[]
      listql.append(glob.glob(os.path.join(product,roi,'*B2.TIF'))[0]) # QL Generation
      listql.append(glob.glob(os.path.join(product,roi,'*B3.TIF'))[0]) # QL Generation
      listql.append(glob.glob(os.path.join(product,roi,'*B4.TIF'))[0]) # QL Generation

      image_data_list = listql
      ql_file_name = ''.join([mtl.landsat_scene_id,'_','roi_',roi_name,'_bd234.jpg'])
      ql_name = os.path.join(interband.main_wd,ql_file_name)
      log.info(" -- [QL      ] Create ROI QL : "+ql_name)
      
      dst_dir = productWorkingDirectory
      quick_look_resolution = 30
      outputdir = interband.main_wd
      im_st = im_p.image(listql) # Create Object instance
      im_st.createimageQuicklook(ql_name,outputdir,quick_look_resolution)
      http.updateContentWitQL(infra,interest,band_type,ql_name)



      #End of processing each ROI
      log.infog(" - [PROC     ] End ")


if __name__ == '__main__':



    if len(sys.argv) == 2 :

    #The block below is not Valid  - Enter Valid atest block
        print sys.argv[1]
        product = glob.glob(sys.argv[1])
        print product
        if len(product) == 0 :
           log.err('-- Invalid Product')

        else :
           product = os.path.abspath(product[0])
           log.infog(" -- Interband Registration with product : "+product+"\n")
           infra=main_infra.mainInfra()
           band_type = 'pan'
           interband = interband(band_type);
           trigger_interband_processing(product,interband)


    else:

        infra=main_infra.mainInfra()
        infra.checkDirectoryPresence()
        path_to_product=os.path.join(infra.processing_location,interest,'input','*')
        product_list=glob.glob(path_to_product)


        if len(product_list) > 0 :
            for product in product_list:

#                band_type = 'ms'
#                interband = interband(band_type);
#                trigger_interband_processing_with_ms(product,interband)
#                trigger_interband_processing_with_panchro(product)
                band_type = 'pan'
                interband1 = interband(band_type)
                trigger_interband_processing(product,interband1)

                band_type = 'ms'
                interband2 = interband(band_type)
                trigger_interband_processing(product,interband2)


                log.infog(" --- Move Input Products to Done")  
                input_product=product
                DONE=os.path.join(infra.processing_location,interest,'done')
                cmd = ' '.join(['mv',input_product,DONE])
                os.system(cmd)

        else :
             log.info(' -- No product to be processed ')
    
    log.info(' - End of geometric processing')
