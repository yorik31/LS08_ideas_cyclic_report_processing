# -*- coding: utf-8 -*-
import os,sys
import imp
import glob
import imp
import numpy as np
from osgeo import gdal
from global_variables import *
metadata_extraction = imp.load_source('metadata_extraction',os.path.join(PY_CLASS,'metadata_extraction.py'))
import main_infra
import radiometric_calibration as rad
import log


#July, 13 Wednesday : S . Saunier
#   -- Cron Data Import --
#      - inspect if data in INPUT DATA
#      -Import data
#      -Applied pre processing
#      -

#20/12/2016 - Re package for uk - Add Error Management
#19/05/2017 - Extract Landsat Sea Mask as preprocessing : get_qa_land_sea_mask





def get_qa_land_sea_mask(mtl,dst_filename):

#        image = mtl.dn_image_list[0]
        bqa_image = mtl.bqa_filename
#IndexError: listindexoutofrange
    #Create Output dataset
   #Read BQA Image

        src_ds = gdal.Open(str(bqa_image))
        bqa_array = src_ds.GetRasterBand(1).ReadAsArray()
# Create Empty Matrix
        nb_line = bqa_array.shape[0]
        nb_col = bqa_array.shape[1]
        m1 = np.zeros((nb_line, nb_col), dtype='uint8')

# 1 ) To indicate Land
# 0 ) To indicate Sea
        m1[ (bqa_array > 1) & (bqa_array < 20512)] = 1
        tmp_ds = gdal.GetDriverByName('MEM').CreateCopy('', src_ds, 0)
        tmp_ds.GetRasterBand(1).WriteArray(m1, 0, 0)
        gdal.GetDriverByName('GTiff').CreateCopy(dst_filename, tmp_ds, 0)

        sum_test = np.sum(m1)

        src_ds = None
        tmp_ds = None

        log.info(' -- Land/Sea mask created : '+dst_filename)

        if (sum_test == 0 ) :
            dst_filename = ''

        return dst_filename



def trigger_productSubview(product):

   global PROCESSING_STATUS
   PROCESSING_STATUS='PASSED'
   infra=main_infra.mainInfra()
   #infra.checkDirectoryPresence()
   mtl = metadata_extraction.LandsatMTL(product)
   if mtl.mtl_file_name == '' :
      print ' -- Missing MTL File'
      return

   if mtl.missing_image_in_list == 'Missing_image' :
      print ' -- Missing Image files' 
      return 
 

   mtl.set_test_site_information(infra.configuration_site_description_file) 
   if str(len(mtl.test_site)) == '0' :
      print ' -- No Test site Found' 
      return 

   print " -- site "+mtl.test_site[0]   

   mtl.display_mtl_info()
  

   infra.makeProductSubview(mtl)
   return True



if __name__ == '__main__':


    if len(sys.argv) == 2 :
        product = sys.argv[1]
        log.info(" Processing of : "+product)
        mtl = metadata_extraction.LandsatMTL(product)
        dst_filename = os.path.join(product,'land_sea_mask.tif')
        if (mtl.bqa) :
            get_qa_land_sea_mask(mtl, dst_filename)
        RES = trigger_productSubview(product)
        if (RES) :
            log.info(" Cron Data Import is successfull ")
        else     :
            log.warn(" Cron Data Import is in failure  ")
        print " "


    else :
        infra=main_infra.mainInfra()
        infra.checkDirectoryPresence()

        product_list=glob.glob(os.path.join(infra.input_data_location,'uncompressed','L*'))
        if len(product_list) > 0 :
            for product in product_list:
#Apply pre processing with Land Sea Mask extract
               log.info(" Processing of : "+product)
               mtl = metadata_extraction.LandsatMTL(product)
               dst_filename = os.path.join(product,'land_sea_mask.tif')
               if (mtl.bqa) :
                    get_qa_land_sea_mask(mtl, dst_filename)
#Si resussite de Trigger Product Subview
               if trigger_productSubview(product):

                   done_repo = os.path.join(infra.input_data_location,
                                      'uncompressed','done')
                   out = os.path.join(done_repo,os.path.basename(product))
                   print os.path.exists(out) 
#Remove product in out in case of existing product
                   if (os.path.exists(out)):
                       log.warn(' -- Products already in <done> '+out)

                       cmd=' '.join(['rm -rf ',out])
                       os.system(cmd)
                       log.warn(' --- Remove past product in done : ')
                       log.warn(' --- '+os.path.basename(product)+' ')
                       log.warn(' --- '+done_repo)

	           log.info(' -- Move product to <done> \n')
                   cmd=' '.join(['mv ',product,done_repo])
                   os.system(cmd)
               else :
                  log.err(' -- Anomaly in the input product  \n')
                  log.err(' -- Product not processed with productSubview  \n')

        else :
            log.err(' -- End: No Product Found  \n')

