# -*- coding: utf-8 -*-
# test routine
import os,sys, io
import imp
import glob
import metadata_extraction
import main_infra
import log


def display_list(interest,status):

   path_to_product=os.path.join(infra.processing_location,interest,status,'*')
   product_list=glob.glob(path_to_product)

   log.infog(' -- Interest / status '+interest+' / '+status+' :')

   if len(product_list) > 0 :
      log.info(' --- Number of processed products : '+str(len(product_list)))      
      for rec in product_list :
         log.info(rec)
   else :
      log.info(' --- No product ')
   print ' '

if __name__ == '__main__':
    infra=main_infra.mainInfra()
    infra.checkDirectoryPresence()
    interest='interbandRegistration'
    display_list(interest,'input')	
    display_list(interest,'done')
    interest='directLocation'
    display_list(interest,'input')	
    display_list(interest,'done')
    


