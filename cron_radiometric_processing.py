# -*- coding: utf-8 -*-
# test routine
# -*- coding: utf-8 -*-
import os,sys, io
import time
import glob
import imp
from global_variables import *
metadata_extraction = imp.load_source('metadata_extraction',os.path.join(PY_CLASS,'metadata_extraction.py'))
import main_infra
import radiometric_calibration as rad
import log
import Image
from global_variables import *
#from itertools import groupby

#Trigger_radio_processing - in radiometric calibration stability
#Si produit present dans calibration stability
#1. Convertion en RADIANCE et en Top of Atmosphere
#2. Traitement statistique 
#3. Mise a jour du fichier de resultats

#20/12/2016 - Re package for uk.


def trigger_radio_processing(product):

    global PROCESSING_STATUS
    PROCESSING_STATUS='PASSED' #to be pass in this interface (as parameter)

    infra=main_infra.mainInfra()
    stat_table = []
    stat_table_sort = []
    roi_list=[rec for rec in glob.glob(os.path.join(product,'ROI*'))]

    for roi in roi_list:
        log.infog(' -- Processing of '+roi+'  : ')
        mtl = metadata_extraction.LandsatMTL(roi)
        mtl.set_test_site_information(infra.configuration_site_description_file)
        log.info(' -- Convert to RAD / TOA')
        mtl.display_mtl_info()
        
        r=rad.radiometric_calibration(product,mtl)
        log.info(' -- Extract / store statistics ')
        mtl.update_image_file_list()

        image_file_list=mtl.rhotoa_image_list        
        output_txt_file= RADIOMETRIC_STABILITY_RHO_RESULTS

#infra.result_radiometricStability
        roi_id=os.path.basename(roi)
        gainList = [ str(rec) for rec in  mtl.rescaling_gain]
        #print mtl.band_sequence
        for image_file in image_file_list:
            a = None
            a = Image.Statistics(image_file,roi_id)
            r = a.get_statistics()
            stat_table.append(r)

    stat_table_sort = sorted(stat_table, key=lambda x : x[1]) #sort by  band_number
    infra.update_text_file(mtl,stat_table_sort)

    #input_product=product
    #output_rep=os.path.join(product,'../../done')
    #cmd = ' '.join(['mv',input_product,output_rep])
    #print cmd
    #os.system(cmd)

if __name__ == '__main__':
    infra=main_infra.mainInfra()
    infra.checkDirectoryPresence()
    interest='stabilityMonitoring'
    path_to_product=os.path.join(infra.processing_location,interest,'input','*')
    product_list=glob.glob(path_to_product)
    
    if len(product_list) > 0 :
       for product in product_list:
          print product
          trigger_radio_processing(product)
	  if PROCESSING_STATUS == 'PASSED':
          #si succes alors on efface le produit
            done_repo = os.path.join(infra.processing_location,
                                      interest,'done')
            out = os.path.join(done_repo,os.path.basename(product))
            log.warn(' -- '+out)
            if (os.path.exists(out)):
                   cmd=' '.join(['rm -rf ',out])
                   os.system(cmd)
                   log.warn(' -- Remove past product in done : ')
                   log.warn(' -- '+os.path.basename(product)+' ')
                   log.warn(' -- '+done_repo)

	    log.info(' -- Move product to done ')
#            cmd=' '.join(['mv ',product,done_repo])
#            os.system(cmd)
    else :
       log.info(' -- No product to be processed ')
       log.info(' - End of radio_processing')
