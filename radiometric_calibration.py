#!/usr/bin/python
# -*- coding: utf-8 -*-
import os
from os import *
import glob
from xml.dom import minidom
import numpy as np
from osgeo import gdal, ogr
from osgeo.gdalnumeric import *
from osgeo.gdalconst import *


class radiometric_calibration:

    def __init__(self,product_path,mtl):
        self.product = mtl
        print " -- Radiometric Calibration, Product : "+product_path
        if len(self.product.radiance_image_list) == 0:
            print "%%%%% Warning, no Identified Radiance file, as results of processing"
        test_file = [os.path.exists(str(f)) for f in self.product.radiance_image_list]
        #Et si test_file est vide on ne doit pas continuer
        #Confition sur self.product.radiance_image_list

        if  test_file[1] is False :
            self.convert_to_radiance()

        test_file = [os.path.exists(str(f)) for f in self.product.rhotoa_image_list]
        if test_file[1] is False:
            self.convert_to_reflectance()

        #clean B6 band transformation
        #Note : Ne supporte le nouveau format landsat
        list = glob.glob(os.path.join(product_path,'L*_R[A,H][D,O]_B6.TIF'))
        [os.system(' '.join(['rm -f', f])) for f in list]

        mtl.update_image_file_list()


    def convert_to_radiance(self):
        print " -- Convert to Radiance -- "
        input_image_list = self.product.dn_image_list
        output_image_list = self.product.radiance_image_list
        gain_list=self.product.rescaling_gain
        offset_list=self.product.rescaling_offset
        for index,image_in in enumerate(input_image_list):

                band_index=int((os.path.basename(image_in).split('B')[1]).split('.')[0])
                print "band index :"+str(band_index)
                image_out= output_image_list[index]
                gain = gain_list[band_index-1]
                offset = offset_list[band_index-1]
                #print image_in
                #print image_out+' '+str(gain)+' '+str(offset)

                #ouvir image to Array
                input_ds=gdal.Open(image_in)
                if input_ds is None:
                    print 'No file'
                
                data_in = input_ds.GetRasterBand(1).ReadAsArray()
                #.astype(np.byte)
                mask = np.where((data_in > 0),1,0)
                
                radiance_data=np.multiply(data_in,gain)+np.multiply(mask,offset)

                #Write the out file
                driver = gdal.GetDriverByName('GTiff')
                dst_name=image_out
                cols=input_ds.RasterXSize
                rows=input_ds.RasterYSize
                dst_ds=driver.Create(image_out,cols,rows,1,gdal.GDT_Float32)

                #CopyDasetInfo(src_ds,dst_ds)
                dst_ds.SetProjection(input_ds.GetProjection())
                dst_ds.SetGeoTransform(input_ds.GetGeoTransform())
                dst_ds.GetRasterBand(1).WriteArray(radiance_data,0,0) 
                dst_ds.GetRasterBand(1).SetNoDataValue(0.0)

                dst_ds.FlushCache()
                dst_ds=None
                input_ds=None
                image_in=None
                mask=None
                radiance_data=None
                data_in=None
  
    def convert_to_reflectance(self):
        input_image_list = self.product.radiance_image_list
        output_image_list = self.product.rhotoa_image_list
        coefficient_list=self.product.radiance_to_reflectance_coefficient

        for index,image_in in enumerate(input_image_list):
                band_index=int((os.path.basename(image_in).split('B')[1]).split('.')[0])
                image_out = output_image_list[index]
                gain = coefficient_list[band_index - 1]
                #print '-- Image input : '+image_in
                #print '-- Image output / Gain : '+image_out+' '+str(gain)
                #ouvir image to Array
                input_ds=gdal.Open(image_in)
                if input_ds is None:
                    print ' - No file'
                    print ' - '
                    print '- Please, before to Relectance, Applied to Radiance Transformation' 
                    print '---> Command : r.toRadiance()' 
                    print ' '
                    print ' '
                    return
    
                data_in = input_ds.GetRasterBand(1).ReadAsArray()
                #.astype(np.byte)
                mask = np.where((data_in > 0),1,0)
                reflectance_data=np.multiply(data_in,gain)
                
                #Write the out file
                driver = gdal.GetDriverByName('GTiff')
                dst_name=image_out
                cols=input_ds.RasterXSize
                rows=input_ds.RasterYSize
                dst_ds=driver.Create(image_out,cols,rows,1,gdal.GDT_Float32)

                #CopyDasetInfo(src_ds,dst_ds)
                dst_ds.SetProjection(input_ds.GetProjection())
                dst_ds.SetGeoTransform(input_ds.GetGeoTransform())
                dst_ds.GetRasterBand(1).WriteArray(reflectance_data,0,0) 
                dst_ds.GetRasterBand(1).SetNoDataValue(0.0)

                dst_ds.FlushCache()
                dst_ds=None
                input_ds=None
                image_in=None
                mask=None
                radiance_data=None
                data_in=None

