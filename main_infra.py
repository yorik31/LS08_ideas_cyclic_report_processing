# -*- coding: utf-8 -*-
# init class
import os, sys
import shutil
import numpy as np
from osgeo import gdal,gdalnumeric, ogr
from os import listdir
from osgeo import gdal
from gdalconst import *
import glob
from xml.dom import minidom
import re as r
import imp

import reference_data_management as ref
import log

from global_variables import *
metadata_extraction = imp.load_source('metadata_extraction',os.path.join(PY_CLASS,'metadata_extraction.py'))


#July, 13 Wednesday : S . Saunier
#   -- Main Infra   --
#      - Define main ressources for the processing
#      - Include basic Image function shared by all the processing
# 

#01/06/2017 - Add Function  "threshold_confidence_image" for masking confidence image
#             setting to '0' not Valid pixels, example Water Pixels


class mainInfra:
    def __init__(self):

        infra_dir = REFERENCE
        self.input_data_location = INPUT_DATA
        self.code_location = CODE
        self.matlab_processing = CODE_m
        self.processing_location = PROCESSING

        if os.path.exists(self.processing_location) is False:
             cmd=' '.join(['mkdir -v', self.processing_location])
             os.system(cmd)



        interest_list=['stabilityMonitoring','directLocation','interbandRegistration']

        for interest in interest_list:
           interest_dir=os.path.join(self.processing_location,interest,'done')
           if os.path.exists(interest_dir) is False :
              cmd=' '.join(['mkdir -vp', interest_dir])
              os.system(cmd)
              log.infog( ' -- Create '+interest+' and done directories  \n' )

           interest_dir=os.path.join(self.processing_location,interest,'input')
           if os.path.exists(interest_dir) is False :
              cmd=' '.join(['mkdir -vp', interest_dir])
              os.system(cmd)
              log.infog( ' -- Create '+interest+' and input directories  \n' )

           interest_dir=os.path.join(self.processing_location,interest,'wd')
           if os.path.exists(interest_dir) is False :
              cmd=' '.join(['mkdir -vp', interest_dir])
              os.system(cmd)
              log.infog( ' -- Create '+interest+' and input directories  \n' )

        self.result_location = RESULT
        if os.path.exists(self.result_location) is False:
             cmd=' '.join(['mkdir -v', self.result_location])
             os.system(cmd)

        for interest in interest_list:
           th_rep=os.path.join(self.result_location,interest)
           if os.path.exists(th_rep) is False:
              cmd=' '.join(['mkdir -v', th_rep])
              os.system(cmd)

        #RESULT
        self.result_radiometricStability = Radio_Txt_File(os.path.join(self.result_location,'stabilityMonitoring','radio_stability.txt'))

        #CONFIGURATION
        self.configuration = CONFIGURATION
        self.configuration_assessment_description=os.path.join(self.configuration,('assessmentControler.xml'))
        self.configuration_site_description_file=os.path.join(self.configuration,'desc_Site.xml')
        self.configuration_reference_description = os.path.join(self.configuration,'reference_data_description.xml')
        self.configuration_medicis = os.path.join(self.configuration,'Medicis_General_correl_tm.txt')
         

        #REFERENCE DATA
        self.reference_data_raster_file_location = os.path.join(infra_dir,'RASTER')
        self.reference_data_vector_file_location = os.path.join(infra_dir,'VECTOR')
        self.reference_data_dem_file_location = os.path.join(infra_dir,'DEM')
        self.reference_data_meteo_file_location = os.path.join(infra_dir,'METEO')

    def checkDirectoryPresence(self):
        print ' '
        print 'Landsat 8 Processing of Cyclic Report '
        print ' '

        log.infog( ' Check Directory Presence : \n' )
        if os.path.exists(self.input_data_location):
               log.info(' -- Input Data Location Directory exist')
        if os.path.exists(self.code_location):
               print ' -- Code Location Directory exist'
        else:
               log.err(' -- Code Location Directory is Missing \n')
        if os.path.exists(self.processing_location):
               print ' -- Processing Directory exist'
        else:
               log.err(' -- Processing Directory is Missing \n')
        if os.path.exists(self.result_location):
               print ' -- Result Directory exist'
        else:
               log.err(' -- Result Directory is Missing \n')
        if os.path.exists(self.configuration):
               print ' -- Configuration Directory exist'
        else:
               log.err(' -- Configuration Directory is Missing \n')

        if os.path.exists(self.reference_data_vector_file_location):
               print ' -- Vector - Shape File Directory exist'
        else:
               log.err(' -- Vector - Shape File is Missing \n')

        if os.path.exists(self.reference_data_raster_file_location):
               print ' -- Raster Reference Directory exist'
        else:
               log.err(' -- Raster Reference Directory is Missing \n')
        if os.path.exists(self.reference_data_dem_file_location):
               print ' -- DEM Reference Directory exist'
        else:
               log.err(' --  DEM Reference Directory is Missing \n')
        if os.path.exists(self.reference_data_meteo_file_location):
               print ' -- Meteo Files Directory exist \n'
        else:
               log.err(' -- Meteo Files is Missing \n')

    def makeProductSubview(self,metadata):
        #make product subview - needed for subsequent processing_location
        #  -- Create repository
        #  -- Copy files
        #  -- Crop data according to ROI
        #  -- Convert to TOA
        metadata.display_mtl_info()
        country_list=metadata.test_site
        site_list=metadata.test_site
        desc_site_xmldoc =minidom.parse(self.configuration_site_description_file)
        sites=desc_site_xmldoc.getElementsByTagName('site')
        #Loop on each site covered by the product
        #site_name corresponds to "site id" in the xml file, refer to configuration
        for k,site_chain in enumerate(site_list):
           country_name=site_chain.split(' ')[0]
           site_name=site_chain.split(' ')[1]
           site_interest = []
           for site in sites:
              site_name_att=site.getElementsByTagName('id')[0].childNodes[0].data
              if (site_name_att == site_name):
                 site_interest = site.getElementsByTagName('interest')
                 log.infog(' -- Site Interest Found ')
                 #Une fois que le site est trouver - loop on interest  
                 #Check if based on Assessment Manager Applicable to the input product
                 #Pour chaque interet - get processing parameters :
                 #                          -> list of image a traiter
                 #                          -> shape file for ROI to be croped
                 #En verifiant que l interet est couvert par le Manager 
                 for interest in metadata.interest[k].split():
                    xmldoc = minidom.parse(self.configuration_assessment_description)
                    missions=xmldoc.getElementsByTagName('mission')
                    for mission in missions :
                       sensor=mission.attributes["sensor"].value
                       plateform=mission.attributes["plateform"].value
                       if ( metadata.sensor == sensor ) and ( metadata.mission == plateform ):
                        # -- For interest Get Mission specific Processing paramters

                           print (' ')
                           log.info(' -- '+interest+' :')

                           interest_block = (mission.getElementsByTagName(interest))
                           band_list=(interest_block[0].getElementsByTagName('channel')[0]
                                                           .childNodes[0].data).split(' ')
         #  -- Create repository
                           outputrep=os.path.join(self.processing_location,interest,'input',metadata.landsat_scene_id)
                           if os.path.exists(outputrep) is False:
                              cmd = ' '.join(['mkdir -v',outputrep])
                              os.system(cmd)
         #  -- Copy initial info
                           inputrep=metadata.product_path
                           metadatafile_name=metadata.mtl_file_name
                           cmd = ' '.join(['cp',os.path.join(inputrep,metadatafile_name),outputrep])
                           os.system(cmd)

         #  -- Define the image_file_list
                           image_file_list = []
                           for rec in band_list:
                              reg=''.join(['*B',rec.replace(' ',''),'.TIF'])

                              image_file_list.append(glob.glob(os.path.join(inputrep,reg)))

# -- Append Mask if exists
                           msk_file_name = 'land_sea_mask.tif'
                           mask_image = os.path.join(inputrep,msk_file_name)
                           if os.path.exists(mask_image) :
                               image_file_list.append(glob.glob(mask_image))
                               log.info(' --- mask Image :'+mask_image )

                           for rec in image_file_list :
                               log.info(' --- Image List record :'+str(rec) )  

# -- For each interest, site Crop Data According to roi defined by shapefile
                           country=country_name
                           vector=self.reference_data_vector_file_location        
                           ref_type='vector'
                           
# -- Print self.configuration_reference_description
# -- Print  self.reference_data_vector_file_location

                           ref_1 = ref.referenceData(self.configuration_reference_description,
                                  self.reference_data_vector_file_location)
             
                           reference_file_list=ref_1.get_data_list(site_name,country,interest,'vector')
                           if reference_file_list :
                              for ref_file in reference_file_list:
                                 log.info(' --- Reference File : '+os.path.basename(ref_file).split('.')[0])
                                 #Fabrique repertoire ROi_[nom du site]                     
                                 roi_rep=os.path.join(outputrep,
                                         ''.join(['ROI_',os.path.basename(ref_file).split('.')[0]])
                                         )                                          
                                 if os.path.exists(roi_rep) is False:
                                    cmd = ' '.join(['mkdir -v',roi_rep])
                                    os.system(cmd)
#Copy le fichier mtl_file_name
                                 metadatafile_name=metadata.mtl_file_name
                                 if os.path.exists(os.path.join(inputrep,metadatafile_name)) : 
                                    cmd = ' '.join(['cp',os.path.join(inputrep,metadatafile_name),roi_rep])
                                    os.system(cmd)
#Copy le fichier mtl_file_name

                                 #Pour chaque REF FILE Decoupe suivant la definition de la roi
                                 
                                 crop_on_roi_gdal_warp(image_file_list,roi_rep,ref_file)
                                 log.info(' --- End crop' )
                              

                           else :
                                 log.info(' -- Site not appropriate for this interest, no reference found ')
                           #Reset la list des fichiers images 
                           image_file_list=[]
        print ('\n')
        log.infog(' - End of makeProductSubview \n')

    def update_text_file (self,mtl,record_list):
        a=self.result_radiometricStability
        a.add_to_text_file(mtl,record_list)



# threshold_confidence : Allow to applied land_sea_mask to cor_conf_image
#                        In cor_conf_image all Water Pixels as flag in the mask
#                        are set to 0 Value   
#                        Additionnal DC Mask is output 
#                                  0 - Below confidence threshold ( <=)
#                                  1 - Above confidence threshold ( > )
#                        [dst_file_name] Name of the new DC Image
#                         
    def threshold_confidence_image(self,land_sea_mask,cor_conf_image,dst_file_name):


        confidence_threshold = 0.8

        log.infog(' - Start mask  the confidence image with land sea mask \n')
#Name of Rescaled Land Sea Mask
        input_file = land_sea_mask
        land_sea_mask_rad = os.path.basename(input_file).split('.')[0]
        land_sea_mask_path = os.path.dirname(input_file)
        land_sea_mask_rescale = os.path.join(land_sea_mask_path,land_sea_mask_rad+'_rescale.tif')
        land_sea_tmp = os.path.join(land_sea_mask_path,land_sea_mask_rad+'_tmp.tif')
        if os.path.exists(land_sea_mask_rescale):
             os.remove(glob.glob(land_sea_mask_rescale)[0])

#save input cor_conf_image to old 
        cor_conf_image_old = cor_conf_image.replace('.TIF','_OLD.TIF')
        shutil.copy(cor_conf_image,cor_conf_image_old)

#cor_conf_image
        src_ds = gdal.Open(str(cor_conf_image))
        geotransform = src_ds.GetGeoTransform()
        print '-- Origin = (', geotransform[0], ',', geotransform[3], ')'
        print '-- Input Pixel Size = (', geotransform[1], ',', geotransform[5], ')'

        msk_ds = gdal.Open(str(land_sea_mask))
        dc_array = src_ds.GetRasterBand(1).ReadAsArray()
        msk_array = msk_ds.GetRasterBand(1).ReadAsArray()

        nb_line = dc_array.shape[0]
        nb_col = dc_array.shape[1]

#Rescale land sea mask to confidence image scale
        cmd = ' '.join(['gdal_translate -of GTiff','-strict -tr ',str(geotransform[1]),' ', \
                        str(geotransform[1]),
#                        '-outsize ',str(nb_line),' ',str(nb_col),
                        ' -r nearest',
                        land_sea_mask,land_sea_tmp])
        os.system(cmd)
        cmd = ' '.join(['gdal_translate -of GTiff','-strict ',
                        '-outsize ',str(nb_col),' ',str(nb_line),
                        ' -r nearest',
                        land_sea_tmp,land_sea_mask_rescale])
        os.system(cmd)



#Applied Land Sea Mask to Correlation Confidence Image
        msk_ds = gdal.Open(str(land_sea_mask_rescale))
        msk_array = msk_ds.GetRasterBand(1).ReadAsArray()

        nb_line_1 = msk_array.shape[0]
        nb_col_2 = msk_array.shape[1]
        if (nb_line_1 != nb_line ) :
            log.warn('-- The image size of Mask and Confidence Different \n')
            log.warn(' '.join(['-- Masque          line_nbr x col_nbr : ',str(nb_line_1),'X',str(nb_col_2) ,' \n']))
            log.warn(' '.join(['-- Confident Image line_nbr x col_nbr : ',str(nb_line),'X',str(nb_col) ,' ',' \n']))

            return False

        m1 = dc_array
        m1[msk_array == 0] = 0

        tmp_ds = gdal.GetDriverByName('MEM').CreateCopy('', src_ds, 0)
        tmp_ds.GetRasterBand(1).WriteArray(m1, 0, 0)
#Write output
        gdal.GetDriverByName('GTiff').CreateCopy(dst_file_name, tmp_ds, 0)

        tmp_ds = None

        log.infog(' - End   -> Mask  the confidence image with land sea mask \n')
        log.infog(' - Start -> Create Mask of the confidence image \n')

#Create MASK of DC 0 below threshold and 1 above threshold        
        m2 = dc_array
        m2[ m1 <= confidence_threshold ] = 0
        m2[ m1 > confidence_threshold ] = 1

        tmp_ds = gdal.GetDriverByName('MEM').CreateCopy('', src_ds, 0)
        tmp_ds.GetRasterBand(1).WriteArray(m2, 0, 0)
        #Write output
        dst2_file_name = dst_file_name.replace('.TIF',''.join(['_mask_',str(np.int(confidence_threshold*100)),'.TIF']))
        gdal.GetDriverByName('GTiff').CreateCopy(dst2_file_name, tmp_ds, 0)


        src_ds = None
        msk_ds = None
        tmp_ds = None
	  
        log.infog(' -- Create : '+ dst2_file_name+'\n')
        log.infog(' - End -> Create Mask of the confidence image \n')

        return  dst_file_name,dst2_file_name


    def threshold_displacement_image(self,cor_conf_image,d_image):


        #[cor_conf_image] Input confidence Image
        #[d_image] DC, DX or DY Image.
        #Applied Confidence Image to  d_image
        #Threshold is 0.8 :
        conf_threshold = 0.8
        log.infog(' - Start threshold_displacement_image \n')

#save input cor_conf_image to old 
        d_image_old = d_image.replace('.TIF','_OLD.TIF')
        shutil.copy(d_image,d_image_old)
#Define destination file
        dst_file_name = d_image
#cor_conf_image
        src_ds = gdal.Open(str(d_image))
        geotransform = src_ds.GetGeoTransform()
        print '-- Origin = (', geotransform[0], ',', geotransform[3], ')'
        print '-- Input Pixel Size = (', geotransform[1], ',', geotransform[5], ')'

        conf_ds = gdal.Open(str(cor_conf_image))
        dc_array = conf_ds.GetRasterBand(1).ReadAsArray()
        d_array = src_ds.GetRasterBand(1).ReadAsArray()

        nb_line = dc_array.shape[0]
        nb_col = dc_array.shape[1]

        m1 = d_array
        m1[dc_array <= conf_threshold] = 10

        tmp_ds = gdal.GetDriverByName('MEM').CreateCopy('', src_ds, 0)
        tmp_ds.GetRasterBand(1).WriteArray(m1, 0, 0)
#Write output
        gdal.GetDriverByName('GTiff').CreateCopy(dst_file_name, tmp_ds, 0)

        src_ds = None
        conf_ds = None
        tmp_ds = None



        log.infog(' -- Create : '+ dst_file_name+'\n')

        log.infog(' -- Create : '+ dst_file_name+'\n')

        log.infog(' - End threshold_confidence_image \n')




    def create_rgb_image(DX,DY,DC,image_rgb):

        log.infog(' - Create RGB Image  \n')




        log.infog(' - End of Create RGB Image  \n')





class Radio_Txt_File:

    def __init__(self,name):
        self.filename=name
        self.init_text_file_header()

    def init_text_file_header(self):
        txtfile_name = self.filename
        if not os.path.isfile(txtfile_name):
            log.info(' -- Radiometric stability result file does not exist, create header ')
            ch = ' '.join(['File_Id', 'Band_Id','ROI_name','Pixel_number'
                       'rho_min', 'rho_max', 'rho_sum','rho_mean', 'rho_std',
                       'Observation_Date', 'Observation_Time',
                       'Doy ', 'SZA', 'SAA', 'Rescaling_Gain', 'Rescaling_Offset',
                       'Minimum_Radiance', 'Maximum_Radiance'
                       ])
            txtfile = open(txtfile_name, 'a')  # Append to txt file
            txtfile.write(ch + '\n')
            txtfile.close()

    def add_to_text_file(self,mtl,stat_list):

        txtfile_name = self.filename
        txtfile = open(txtfile_name, 'a')  # Append to txt file

        #Metadata
        #''Rescaling_Gain'' \
        #''Rescaling_Offset'\
        #'Minimum_Radiance'\
        #'Maximum_Radiance'
        #Statistics

        for record in stat_list:
            ch=''
            for el in record:
                ch+= str(el)+' '
            band_id = int(record[1])
            ch_m = mtl.get_band_info(band_id)
            txtfile.write(' '.join([ch,ch_m,'\n']))
        txtfile.close()
        print ' --- Save Statistics in :  '
        print '                         '+txtfile_name

#Functions for class main Infra
#      1. crop_on_roi(image_list,output_repository,shape_uri)

def crop_on_roi_gdal_warp(image_list,output_repository,shape_uri):

   
   for image in image_list:
      
      if len(image)>0:
         print 'Crop :'+ image[0]

         image=image[0]
         print image
         log.info( ' --- Process Image : '+os.path.basename(image))
         src_ds=gdal.Open(image,GA_ReadOnly)
         format = 'GTiff'
         geotransform=src_ds.GetGeoTransform()
         im=None
         pixel_size=geotransform[1]
         dst_filename = os.path.join(output_repository,os.path.basename(image))
         cmd=' '.join(['gdalwarp -q -crop_to_cutline -cutline',shape_uri,
                    ' -tap -tr',str(pixel_size),str(pixel_size),'-r near',
                     '-overwrite',image,dst_filename])
         os.system(cmd)
         log.info( ' --- Creation of : '+dst_filename+'\n')                 

