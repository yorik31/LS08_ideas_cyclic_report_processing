# -*- coding: utf-8 -*-
import os,sys
import numpy as np

class correl_report:

    def __init__(self,file_name):
         self.file_name = file_name
         self.exist = False
         self.scene_id = ''
         self.roi = ''
         self.ref_band = ''
         self.work_band = ''
         self.confidence = ''
         self.totalPixels = ''
         self.bkgPixels = ''
         self.confidentPixels = ''
         self.percentage_confident_pixel = ''
         self. mean_x = ''
         self.mean_y = ''
         self.std_x = ''
         self.std_y = ''
         self.rms_x = ''
         self.rms_y = ''
         self.rms = ''

    def parse_file(self):
         result_file = str(self.file_name)
         if (len(result_file)>2) :
            if (os.path.exists(self.file_name[0])):
               f = open(self.file_name[0],'r')
               read_data = f.readlines()
               f.close()
               self.exist = True
               ch = (read_data[0]).split(' ')
               self.filename = ch[0]
               seq = ch[0].split('_')
               self.ref_band = np.int(seq[4].replace('REF',''))
               self.work_band = seq[6].replace('WORK','')
               self.scene_id  = seq[0]
               self.roi  = seq[2]
               self.confidence_value = ch[1]
               self.totalPixels = np.float(ch[2])
               self.bkgPixels = np.float(ch[3])
               self.confidentPixels = np.float(ch[4])
               self.percentage_confident_pixel = np.divide(self.confidentPixels,self.totalPixels)*100
               self.mean_x = ch[6]
               self.mean_y = ch[7]
               self.std_x = ch[8]
               self.std_y = ch[9]
               self.rms_x = ch[10]
               self.rms_y = ch[11]
               self.rms = ch[12].replace(',','')

    def export_record(self) :
            ch_out = ' '.join([self.scene_id,self.roi,str(self.ref_band),self.work_band,
                           str(self.confidence_value),
                           str(self.totalPixels),str(self.confidentPixels),
                           str(self.bkgPixels),
                           str(self.percentage_confident_pixel),
                           self.mean_x,self.mean_y,self.std_x,self.std_y,
                           self.rms_x,self.rms_y,self.rms])       
            return ch_out


    def get_header(self) :
            ch_out = ' '.join(['Scene_id','roi_name','reference_band','work_band',
                           'confidence_value','totalPixels','confidentPixels',
                           'bkgPixels','percentage_confident_pixel','mean_x',
                           'mean_y','std_x','std_y',
                           'rms_x','rms_y','rms'])       
            return ch_out
            

       
