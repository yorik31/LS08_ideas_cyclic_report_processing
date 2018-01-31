#!/usr/bin/python

import os, sys
import numpy as np
from osgeo import gdal
from gdalconst import *
from osgeo.gdalnumeric import *
from osgeo.gdalconst import *
import numpy as np
import re as r
import glob
#define with raster Image and mtl file if available


class Statistics:

    def __init__(self, image_path,roi_id):
        #print 'image_statics_class'
        self.image_name = image_path
        self.image_radical = os.path.basename(self.image_name).split('.')[0]

        reg = 'B\d{1,2}'
        p = r.compile(reg)
        u = p.search(image_path)
        band_id = (u.group(0).replace('B',''))
        self.image_id = self.image_radical
        self.channel_number = band_id
        self.roi_id = str(roi_id)
        self.stats = StatisticsValues()

    def get_statistics(self):
        mean_value = 0
        src_ds = load_ds(self.image_name)
        ma2=processing(src_ds) #effectue seuillage et test
        self.stats.update(ma2)
        input_ch=' '.join([self.image_id,self.channel_number,self.roi_id])
        ch=self.stats.display(input_ch)
        return ch

class StatisticsValues:

    def __init__(self):
       # print 'statics_values_class'
        self.len = -1
        self.min = -1
        self.max = -1
        self.sum = -1
        self.mean = -1
        self.std = -1

    def update(self, oned_array):
        #print 'statics_values_update'
        self.len = (len(oned_array))
        self.min = (oned_array.min())
        self.max = (oned_array.max())
        self.sum = (oned_array.sum())
        self.mean = (oned_array.mean())
        self.std =  (oned_array.std())

    def display(self, label):

        seq = []
        seq.append(label.split(' ')[0])
        seq.append(label.split(' ')[1])
        seq.append(label.split(' ')[2])
        seq.append(self.len)
        seq.append(self.min)
        seq.append(self.max)
        seq.append(self.sum)
        seq.append(self.mean)
        seq.append(self.std)
        ch = ' '.join([str(label), str(self.len), str(self.min),
                                   str(self.max), str(self.sum),
                                   str(self.mean), str(self.std)])
        #print ch
        return seq


def load_ds(ds_name):

    file=ds_name
    src_ds=gdal.Open(file,GA_ReadOnly)
    if src_ds is None:
            print "Unable to Open "+file
            #sys.exit(1)
   # print "[ RASTER BAND COUNT ]: ", src_ds.RasterCount
    return src_ds



def processing(input_ds):

     #Test plusieurs methodes pour calcule les moyennes , std ... en enlevant les pixel a zero

     #Renvoie ma2, un 1D array contenant les valeurs sans les 0
     src_ds = input_ds
     cols = src_ds.RasterXSize
     rows = src_ds.RasterYSize
     xcount = cols
     ycount = rows
     data = src_ds.GetRasterBand(1).ReadAsArray().astype(np.float32)
     #Image d origine
     data1 = data.ravel() #linearise les valeurs pour obtenir le nombre d elements
     #displayStatistics(data,'test 1 : ')
     #displayStatistics(data1,'origine : ')

     #Image avec un seuil applique

     #1
     ma = np.where(data > 0) #selection des valeurs non nul
     #2
     ma2 = np.extract(data > 0,data) #selection des valeurs de data qui satisfont la condition >0

     #displayStatistics(data[ma],'test 2 : ')
     #displayStatistics(ma2,'test 3 : ')
     src_ds.FlushCache()
     data = None
     #ma = None

     return ma2

def displayStatistics(array,label):

    ch = ' '.join([str(label) , str(len(array)), str(array.min()), str(array.max()), str(array.sum()),
                    str(array.mean()), str(array.std())
                    ])
    print ch





