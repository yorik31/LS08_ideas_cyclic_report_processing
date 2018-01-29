#!/usr/bin/python
# -*- coding: utf-8 -*-
import os
import sys
from xml.dom import minidom
from os import listdir
import numpy as np
import glob
import imp
import shutil #CP / MV directory
import time
import re
from global_variables import *
import log
import http_side


metadata_extraction = imp.load_source('metadata_extraction',os.path.join(PY_CLASS,'metadata_extraction.py'))

#c:/DEV/PERFORMANCE_EVALUATION_shell/productImport/xq/

def create_ql(image_data_list,outputdir):



        log.info( '- Generate qL of ')
        if not image_data_list:
                print '--! Empty directory'
                return

        image_rad=os.path.basename(image_data_list[0]).split('_')[0]
        output_file_list = []

        for file_name in image_data_list:
                image_data=file_name
                stret = os.path.join(outputdir,'stret.tif')
                cmd=' '.join(['gdal_contrast_stretch -ndv 0 -outndv 0 -linear-stretch 125 100 ',image_data,stret])
                os.system(cmd)

                image_data_rs = os.path.join(outputdir,os.path.basename(file_name))
                cmd=' '.join(['gdalwarp  -srcnodata 0  -r average -of GTiff -tr 300 300 -ot Byte ',
                               stret,image_data_rs])
                os.system(cmd)

                cmd=' '.join(['rm -f',stret])
                os.system(cmd)
                output_file_list.append(image_data_rs)



        image_string = ' '
        for file_name in output_file_list :
           image_string =  ' '.join([image_string,file_name])

        log.info( '-- Build VRT file '+'\n')
        vrt_filename=os.path.join(outputdir,''.join([image_rad,'_ql.vrt'])  )
        cmd=' '.join(['gdalbuildvrt -separate',vrt_filename,image_string])
        os.system(cmd)

        log.info( '-- Build JPG file '+'\n')
        ext='.jpg'
        #Convertion of vrt to png
        qlfile_name=os.path.join(outputdir,''.join([image_rad,'_ql_bd234',ext]))
        cmd=' '.join(['gdal_translate -of jpeg',vrt_filename,qlfile_name,'-b 3 -b 2 -b 1 -a_nodata 0'])
        os.system(cmd)

        log.info( '-- Clean BackLog '+'\n')
        cmd=' '.join(['rm -f' , image_string])
        os.system(cmd)

        cmd=' '.join(['rm -f' , vrt_filename])
        os.system(cmd)


def extract_metadata(product,http_outputdir):

	#<Input> : Product - directory of the product

	#Produit Inconnu recherche les infos sur le wflow.
	#ppScript=os.environ['HOME']
	rootDir=str(os.getcwd())
	print " "
	print  os.path.join(rootDir,'wflow.xml')
	print " "
	queryPath='/'.join([os.environ['ppScript'],'productImport','xq'])
	print " In processing : "+product
	print " "
	print " - Recherche du WorkFlow"
	print " "
	xql_file_name=os.path.join(queryPath,'selectQuerynameForAccess.xql')
	cmd=' '.join(['sh queryLight.sh -f',xql_file_name,
			'-variable file', product,'>',os.path.join(rootDir,'wflow.xml')])
	os.system(cmd)
	
	
	#execute de
	xml_file=os.path.join(rootDir,'wflow.xml')
	xmldoc = minidom.parse(xml_file)
	queryName=xmldoc.getElementsByTagName('browseQueryName')[0].firstChild.data
	addhocScript=xmldoc.getElementsByTagName('addhocScript')[0].firstChild.data
	log.info( '-Execute queryName'+'\n')	
	
	xql_file_name='/'.join([queryPath,queryName])
	product_name=os.path.basename(product)
	out_file=os.path.join(rootDir,'md.xml')
	cmd=' '.join(['sh queryLight.sh -f',xql_file_name,
			'-variable file', product,'>',out_file])
	print cmd
	os.system(cmd)
	print "-- End of query Light"
	print " "
	print "-- Move md File"
	
	input_file=out_file	
	product_name=product_name.replace('.TIFF','')
	out_file='/'.join([product,'m_metadata.xml'])
	print "-- Destination File : "+out_file
	cmd=' '.join(['cp',input_file,out_file])
	os.system(cmd)

	cmd=' '.join(['cp',out_file,http_outputdir])
	os.system(cmd)


        log.info( '-- Clean BackLog '+'\n')
        outfile=os.path.join(rootDir,'md.xml')
	cmd=' '.join(['rm -f',outfile])
	os.system(cmd)
        outfile=os.path.join(rootDir,'wflow.xml')
	cmd=' '.join(['rm -f',outfile])
	os.system(cmd)
        
        log.info( '- End of processing '+'\n')
	

	#c:/DATA/Lybia_4/MSS_L1T_ESA/LS05_RFUI_MSS_GEO_1P_19870204T081532_19870204T081601_015580_0181_0040_8CC4/LS05_RFUI_MSS_GEO_1P_19870204T081532_19870204T081601_015580_0181_0040_8CC4.TIFF
	

def main(argv):

#
	
	product=argv
        http = http_side.performance_report(product)
        http_outputdir=http.md_location

        log.info( '-- Extract XML Metadata '+'\n')
        extract_metadata(product,http_outputdir)

        listql=[]
        listql.append(glob.glob(os.path.join(product,'*B2.TIF'))[0]) # QL Generation
        listql.append(glob.glob(os.path.join(product,'*B3.TIF'))[0]) # QL Generation
        listql.append(glob.glob(os.path.join(product,'*B4.TIF'))[0]) # QL Generation

           
        outputdir=http.ql_location
        log.info( '-- Create QUICK LOOK FOR THE Full Image '+'\n')

        create_ql(listql,outputdir)




if __name__ == '__main__':
	if len(sys.argv) > 1:
		main(sys.argv[1])
	else:
		print "Un Seul parametre attendu"
		print "Parametre d entree: Chemin vers repertoire du produit"
		print "le contener des produits ESA se termine par .TIFF "
			






