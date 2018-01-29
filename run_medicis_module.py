# -*- coding: utf-8 -*-
# Source Generated with Decompyle++
# File: run_medicis_module.pyc (Python 2.7)

import os
import sys
from xml.dom import minidom
from osgeo import gdal
from osgeo import osr
import glob
from gdalconst import *
import numpy as np
import metadata_extraction
import time #sleep function
from global_variables import *

import log
import image_processing as im_p #Internal Class 


# Manage interface of Medicis / Matlab
# 2017 10 02 - Function "Create Quick look" removed to be part of image_processing module
class correl_image:
    def __init__(self,grille):
        self.grille = grille
        self.dx = ''
        self.dy = ''
        self.dc = ''
        self.mask = ''
        self.radial_error = ''
        self.radial_error_rescaled = '' 
        self.dc_mask_rescaled = ''

        self.grille_valid = False
        self.dx_valid = False
        self.dy_valid = False
        self.dc_valid = False
        self.mask_valid = False
        self.geocoded_valid = False
        self.radial_error_valid = False

#Regarde si les element existent et si images geocode existent.
        if os.path.exists(grille):
            self.grille_valid = True
        else:
        #No grid but existing processing images
            dx_name = glob.glob(
                          os.path.join(os.path.dirname(grille),'*_dx-displacement.TIF'))
            if  (len(dx_name) > 0):
               self.dx = dx_name[0]
               self.dx_valid = True

            dy_name = glob.glob(
                          os.path.join(os.path.dirname(grille),'*_dy-displacement.TIF'))
            if  (len(dy_name) > 0):
               self.dy = dy_name[0]
               self.dy_valid = True

            dc_name = glob.glob(
                          os.path.join(os.path.dirname(grille),'*_dc-confidence.TIF'))
            if  (len(dc_name) > 0):
               self.dc = dc_name[0]
               self.dc_valid = True

            mask_name = glob.glob(
                          os.path.join(os.path.dirname(grille),'*_mask.TIF'))
            if  (len(mask_name) > 0):
               self.mask = mask_name[0]
               self.mask_valid = True

    def set_output_name(self,workimage,DIROUT):
        print ' '
        print 'Geocoded Medicis Results '
        print self.grille
        print ' '
        fileId = os.path.basename(workimage).replace('.TIF', '')
        self.mask = DIROUT + '/' + fileId + '_mask.TIF'
        self.dx = DIROUT + '/' + fileId + '_dx-displacement.TIF'
        self.dy = DIROUT + '/' + fileId + '_dy-displacement.TIF'
        self.dc = DIROUT + '/' + fileId + '_dc-confidence.TIF'


    def compute_radial_error(self,productWorkingDirectory) :
        print ' '
        log.info('Compute Radial Error')
        print self.grille
        print ' '
        dx = self.dx
	dy = self.dy
        list_image = [dx,dy]
         
        dst_file_name = os.path.join(productWorkingDirectory,'radial_error.tif',)
        im_st = im_p.image(list_image)
        if (im_st.computeRadialError(dst_file_name)):
            self.radial_error = dst_file_name
            self.radial_error_valid = True
        im_st = None

        return dst_file_name

    def get_statistics(self,productWorkingDirectory,im,confidence_threshold) :

#Filter DX , DY with IM (radial error)

        print ' '
        log.infog(' -- Get statistics ')

        dc = self.dc
        dx = self.dx
	dy = self.dy
	log.info(' -- Create binary mask')
        log.info(' -- Threshold confidence Image @ value > '+str(confidence_threshold))
        list_image = []
        list_image.append(dc)
        im_st = im_p.image(list_image)

        im_st.histerysisThreshold(confidence_threshold,productWorkingDirectory)
        dc = im_st.masked_image
        dc_mask = im_st.mask_image #BINARY MASK
        im_st = None


	im_st = im_p.image([dc,dc_mask]) 
        n_value = 3.5          		     #SIGMA VALUE
        threshold = confidence_threshold     #CONFIDENCE VALUE - 
        log.info(' -- Set null value on DC for Im value >  '+str(n_value)+ 'sigma')

#@Coordinates where IM values > 3.5 sigma, DC == 0 
        if (im_st.sigma_threshold(im,n_value,confidence_threshold)) :
            print 'Update of DC Image :'+im_st.masked_image
            print 'Update of DC Mask  :'+im_st.mask_image

        im_masked =  im_st.masked_image     

#UPDATE DC / DC MASK WITH 3 SIGMA THRESHOLD ON DX , DY
	dc_filename = im_masked
	dc_ds = gdal.OpenShared(dc_filename)
        dc_array = dc_ds.GetRasterBand(1).ReadAsArray()            

	#dc_mask_ds = gdal.OpenShared(dc_mask_filename)
        #dc_mask_array = dc_mask_ds.GetRasterBand(1).ReadAsArray().astype(np.bool)            

#Load Input Dataset - Image  (DX ou DY)
        imx = dx
	im_ds = gdal.OpenShared(imx)
        im_array_x = im_ds.GetRasterBand(1).ReadAsArray()

        imy = dy
	im_ds2 = gdal.OpenShared(imy)
        im_array_y = im_ds2.GetRasterBand(1).ReadAsArray()

#SELECT PIXELS WHERE CONFIDENCE > Threshold
#Statistiscs - keep only values of IM where DC above threshold
        vx = im_array_x[dc_array >= confidence_threshold]
        vy = im_array_y[dc_array >= confidence_threshold]
        log.info ('                       DX / DY Native statistics : ' )

        if (np.size(vx)) > 0 :
          print('%%%%%                  min    max    median    mean    std ' )
	  mi = np.min(vx)
	  mx = np.max(vx)
	  md = np.median(vx)
	  moy = np.mean(vx)
	  std = np.std(vx)
	  print ('%%%%%  DX (line)  :       '+str(mi)+'    '+str(mx)+'    '+str(md)+'   '+str(moy)+' '+str(std)+'\n')
	  mi = np.min(vy)
	  mx = np.max(vy)
	  md = np.median(vy)
	  moy = np.mean(vy)
	  std = np.std(vy)
	  print ('%%%%%  DY (pixel) :       '+str(mi)+'    '+str(mx)+'    '+str(md)+'   '+str(moy)+' '+str(std)+'\n')

	  SUCCESS = True
	else :
	  log.warn ('No data in DC above confidence threshold ' )

	  SUCCESS = False
	




    
    def geocoded(self,workimage,refimageName,DIROUT) :
        if  not self.grille_valid :
            log.warn('Missing Grille.hdf file')
            if  self.dc_valid :
                 self.geocoded_valid = True
        else :
            self.set_output_name(workimage,DIROUT)
            log.infog('--- Geocoded Medicis Results --- ')
            src_filename = self.grille
            dst_ds0_filename = self.mask
            dst_ds1_filename = self.dx
            dst_ds2_filename = self.dy
            dst_ds3_filename = self.dc

 	    src_ds = gdal.Open(str(src_filename))
	    src_sds_name = src_ds.GetSubDatasets()
	    mask_data = gdal.Open(src_sds_name[0][0], gdal.GA_Update)
	    dx_displacement_data = gdal.Open(src_sds_name[1][0], gdal.GA_Update)
	    dy_displacement_data = gdal.Open(src_sds_name[2][0], gdal.GA_Update)
	    dc_confidence_data = gdal.Open(src_sds_name[3][0], gdal.GA_Update)

	    format = 'GTiff'
	    driver = gdal.GetDriverByName(format)
	    src_ds_prj = gdal.Open(workimage)
	    projection = src_ds_prj.GetProjection()
	    geotransform = src_ds_prj.GetGeoTransform()
	    log.info(' ')
	    log.info('Origin             = ('+str(geotransform[0])+' , '+str(geotransform[3])+')')
	    log.info('Input Pixel Size   = ('+str(geotransform[1])+' , '+str(geotransform[5])+')')
	    pixelXSize_Geo = geotransform[1]
	    pixelYSize_Geo = geotransform[5]
	    geotransformOut = geotransform
	    scX = int(np.true_divide(src_ds_prj.RasterXSize, mask_data.RasterXSize) + 0.5)
	    scY = int(np.true_divide(src_ds_prj.RasterYSize, mask_data.RasterYSize) + 0.5)
	    l = list(geotransformOut)
	    l[1] = pixelXSize_Geo * scX
	    l[5] = pixelYSize_Geo * scY
	    geotransformOut = tuple(l)
	    #print ' ==> ' + str(scX) + '  ' + str(scY)
	    log.info('Output Pixel Size  = ('+str(geotransformOut[1])+' , '+str(geotransformOut[5])+')\n')
	    #print ' '
	    mask_data.SetProjection(projection)
	    dx_displacement_data.SetProjection(projection)
	    dy_displacement_data.SetProjection(projection)
	    dc_confidence_data.SetProjection(projection)
	    mask_data.SetGeoTransform(geotransformOut)
	    dx_displacement_data.SetGeoTransform(geotransformOut)
	    dy_displacement_data.SetGeoTransform(geotransformOut)
	    dc_confidence_data.SetGeoTransform(geotransformOut)
	    dst_ds0 = driver.CreateCopy(dst_ds0_filename, mask_data, 0)
	    dst_ds1 = driver.CreateCopy(dst_ds1_filename, dx_displacement_data, 0)
	    dst_ds2 = driver.CreateCopy(dst_ds2_filename, dy_displacement_data, 0)
	    dst_ds3 = driver.CreateCopy(dst_ds3_filename, dc_confidence_data, 0)
	    log.info( ' ')
	    log.info('Creation de Mask data       :' + dst_ds0_filename)
	    log.info('Creation de DX Displacement :' + dst_ds1_filename)
	    log.info('Creation de DY Displacement :' + dst_ds2_filename)
	    log.info('Creation de DC Confidence   :' + dst_ds3_filename + '\n')
	    mask_data = None
	    dx_displacement = None
	    dy_displacement = None
	    dc_confidence = None
	    dst_ds0 = None
	    dst_ds1 = None
	    dst_ds2 = None
	    dst_ds3 = None
	    src_ds = None
	    workimageName = workimage
	    gdal_edit = os.path.join('/home/saunier/swig/python/scripts/', 'gdal_edit.py')
	    param = [
	    'python2.7',
	    gdal_edit,
	    '-mo META-TAG_IMAGEDESCRIPTION="Correlation Validity Flag, Ref/work Images:',
	    str(refimageName),
	    '/',
	    str(workimageName),
	    '"',
	    dst_ds0_filename]
	    cmd = ' '.join(param)
	    os.system(cmd)

	    param = [
	    'python2.7',
	    gdal_edit,
	    '-mo META-TAG_IMAGEDESCRIPTION="Correlation Line Displacements, Ref/work Images:',
	    str(refimageName),
	    '/',
	    str(workimageName),
	    '"',
	    dst_ds1_filename]
  	    cmd = ' '.join(param)
	    os.system(cmd)

	    param = [
	    'python2.7',
	    gdal_edit,
	    '-mo META-TAG_IMAGEDESCRIPTION="Correlation Pixel Displacements, Ref/work Images:',
	    str(refimageName),
	    '/',
	    str(workimageName),
	    '"',
	    dst_ds2_filename]
	    cmd = ' '.join(param)
	    os.system(cmd)

     	    param = [
	    'python2.7',
	    gdal_edit,
	    '-mo META-TAG_IMAGEDESCRIPTION="Correlation Confidence Matrix, Ref/work Images:',
	    str(refimageName),
	    '/',
	    str(workimageName),
	    '"',
	    dst_ds3_filename]
	    cmd = ' '.join(param)
	    os.system(cmd)

            self.dx_valid = True
            self.dy_valid = True
            self.dc_valid = True
            self.mask_valid = True
            self.geocoded_valid = True


def executeMedicis(image1, image2, grille, paramMedicis):

    print '--- Dense Matching with Medicis'
    print '---  image 1 : ' + image1
    print '---  image 2 : ' + image2
    print '---  grille : ' + grille
    print '---  paramMedicis : ' + paramMedicis
    grille_image = grille
    grille_log = grille.replace('.hdf','_log.txt')
    cmd = ' '.join(['PRO_Medicis -imaref_in ',image1,
                   ' -formref_in TIFF -imasec_in ',image2,
                   ' -formsec_in TIFF -gri_out ', grille_image,
                    '-fconfi_in ', paramMedicis ,' -flog_out ',
                     grille_log ])
    os.system(cmd)
    print cmd





########								########
#									       #	
# geocodedMedicsResults : OLD BECAUSE INCLUDED IN THE CLASS "CORREL_IMAGE"     #
#									       #
########								       #	

def geocodedMedicsResults(grille, workimage, refimageName, DIROUT):
    cor = correl_image(grille)

    if  not cor.grille_valid :
        print 'Missing Grille.hdf file'
        if not cor.dc_valid :
            return False
        else :
            print 'Consider existing dx,dy,dc'

    else :

        print ' '
        print 'Geocoded Medicis Results '
        print grille
        print ' '
        src_filename = grille + '.hdf'
        fileId = os.path.basename(workimage).replace('.TIF', '')
        dst_ds0_filename = DIROUT + '/' + fileId + '_mask.TIF'
        dst_ds1_filename = DIROUT + '/' + fileId + '_dx-displacement.TIF'
        dst_ds2_filename = DIROUT + '/' + fileId + '_dy-displacement.TIF'
        dst_ds3_filename = DIROUT + '/' + fileId + '_dc-confidence.TIF'

        if not cor.mask_valid :

	    src_ds = gdal.Open(str(src_filename))
	    src_sds_name = src_ds.GetSubDatasets()
	    mask_data = gdal.Open(src_sds_name[0][0], gdal.GA_Update)
	    dx_displacement_data = gdal.Open(src_sds_name[1][0], gdal.GA_Update)
	    dy_displacement_data = gdal.Open(src_sds_name[2][0], gdal.GA_Update)
	    dc_confidence_data = gdal.Open(src_sds_name[3][0], gdal.GA_Update)

	    format = 'GTiff'
	    driver = gdal.GetDriverByName(format)
	    src_ds_prj = gdal.Open(workimage)
	    projection = src_ds_prj.GetProjection()
	    geotransform = src_ds_prj.GetGeoTransform()
	    print ' '
	    print 'Origin = (', geotransform[0], ',', geotransform[3], ')'
	    print ' '
	    print 'Input Pixel Size = (', geotransform[1], ',', geotransform[5], ')'
	    pixelXSize_Geo = geotransform[1]
	    pixelYSize_Geo = geotransform[5]
	    geotransformOut = geotransform
	    scX = int(np.true_divide(src_ds_prj.RasterXSize, mask_data.RasterXSize) + 0.5)
	    scY = int(np.true_divide(src_ds_prj.RasterYSize, mask_data.RasterYSize) + 0.5)
	    l = list(geotransformOut)
	    l[1] = pixelXSize_Geo * scX
	    l[5] = pixelYSize_Geo * scY
	    geotransformOut = tuple(l)
	    print ' ==> ' + str(scX) + '  ' + str(scY)
	    print ' '
	    print 'Output Pixel Size = (', geotransformOut[1], ',', geotransformOut[5], ')'
	    print ' '
	    mask_data.SetProjection(projection)
	    dx_displacement_data.SetProjection(projection)
	    dy_displacement_data.SetProjection(projection)
	    dc_confidence_data.SetProjection(projection)
	    mask_data.SetGeoTransform(geotransformOut)
	    dx_displacement_data.SetGeoTransform(geotransformOut)
	    dy_displacement_data.SetGeoTransform(geotransformOut)
	    dc_confidence_data.SetGeoTransform(geotransformOut)
	    dst_ds0 = driver.CreateCopy(dst_ds0_filename, mask_data, 0)
	    dst_ds1 = driver.CreateCopy(dst_ds1_filename, dx_displacement_data, 0)
	    dst_ds2 = driver.CreateCopy(dst_ds2_filename, dy_displacement_data, 0)
	    dst_ds3 = driver.CreateCopy(dst_ds3_filename, dc_confidence_data, 0)
	    print ' '
	    print 'Creation de Mask data       :' + dst_ds0_filename
	    print 'Creation de DX Displacement :' + dst_ds1_filename
	    print 'Creation de DY Displacement :' + dst_ds2_filename
	    print 'Creation de DC Confidence   :' + dst_ds3_filename
	    print ' '
	    mask_data = None
	    dx_displacement = None
	    dy_displacement = None
	    dc_confidence = None
	    dst_ds0 = None
	    dst_ds1 = None
	    dst_ds2 = None
	    dst_ds3 = None
	    src_ds = None
	    workimageName = workimage
	    gdal_edit = os.path.join('/home/saunier/swig/python/scripts/', 'gdal_edit.py')
	    param = [
	    'python2.7',
	    gdal_edit,
	    '-mo META-TAG_IMAGEDESCRIPTION="Correlation Validity Flag, Ref/work Images:',
	    str(refimageName),
	    '/',
	    str(workimageName),
	    '"',
	    dst_ds0_filename]
	    cmd = ' '.join(param)
	    os.system(cmd)

	    param = [
	    'python2.7',
	    gdal_edit,
	    '-mo META-TAG_IMAGEDESCRIPTION="Correlation Line Displacements, Ref/work Images:',
	    str(refimageName),
	    '/',
	    str(workimageName),
	    '"',
	    dst_ds1_filename]
  	    cmd = ' '.join(param)
	    os.system(cmd)

	    param = [
	    'python2.7',
	    gdal_edit,
	    '-mo META-TAG_IMAGEDESCRIPTION="Correlation Pixel Displacements, Ref/work Images:',
	    str(refimageName),
	    '/',
	    str(workimageName),
	    '"',
	    dst_ds2_filename]
	    cmd = ' '.join(param)
	    os.system(cmd)

     	    param = [
	    'python2.7',
	    gdal_edit,
	    '-mo META-TAG_IMAGEDESCRIPTION="Correlation Confidence Matrix, Ref/work Images:',
	    str(refimageName),
	    '/',
	    str(workimageName),
	    '"',
	    dst_ds3_filename]
	    cmd = ' '.join(param)
	    os.system(cmd)
    
    return True




def cropData_accordingSHP(pixel_resolution,input_file,output_file,shp_layer):

  
    shape_file=shp_layer
    cmd=' '.join(['gdalwarp -q -cutline', shape_file,
                  '-crop_to_cutline -t_srs EPSG:32630 -tap',
                  '-tr' ,str(pixel_resolution),str(pixel_resolution),'-r average -overwrite',
                  '-of GTiff',input_file,output_file])
    os.system(cmd)
    print "save in : "+output_file


def maskMedicisResults(DIROUT,workimage,shapefile):    
#To remove noise due to image margin

    shp_layer=shapefile

    fileId = os.path.basename(workimage).replace('.TIF', '')
    dst_ds0_filename = DIROUT + '/' + fileId + '_mask.TIF'
    dst_ds1_filename = DIROUT + '/' + fileId + '_dx-displacement.TIF'
    dst_ds2_filename = DIROUT + '/' + fileId + '_dy-displacement.TIF'
    dst_ds3_filename = DIROUT + '/' + fileId + '_dc-confidence.TIF'

    #Process mask    
    out_f=dst_ds0_filename
    tmp_image=DIROUT + '/tmpImage.tif'
    cmd=' '.join(['mv',out_f,tmp_image])
    os.system(cmd)
    
    pixel_resolution=30
    input_file=tmp_image
    output_file=out_f
    cropData_accordingSHP(pixel_resolution,input_file,output_file,shp_layer)

    #Process dx
    out_f=dst_ds1_filename
    tmp_image=DIROUT + '/tmpImage.tif'
    cmd=' '.join(['mv',out_f,tmp_image])
    os.system(cmd)
    
    pixel_resolution=30
    input_file=tmp_image
    output_file=out_f
    cropData_accordingSHP(pixel_resolution,input_file,output_file,shp_layer)

    #Process dy    
    out_f=dst_ds2_filename
    tmp_image=DIROUT + '/tmpImage.tif'
    cmd=' '.join(['mv',out_f,tmp_image])
    os.system(cmd)
    
    pixel_resolution=30
    input_file=tmp_image
    output_file=out_f
    cropData_accordingSHP(pixel_resolution,input_file,output_file,shp_layer)
    
    #Process dc
    out_f=dst_ds3_filename
    tmp_image=DIROUT + '/tmpImage.tif'
    cmd=' '.join(['mv',out_f,tmp_image])
    os.system(cmd)
    
    pixel_resolution=30
    input_file=tmp_image
    output_file=out_f
    cropData_accordingSHP(pixel_resolution,input_file,output_file,shp_layer)
    


def addDigitalElevationImage(inputImage, productWorkingDirectory, demReference):
    print ' '
    print '--Look for SRTM Tile'
    ppScript = os.environ['ppScript']
    denseMatchingDir = ppScript + '/geometricProcessing/denseMatching'
    src_ds = gdal.Open(inputImage)
    prj = src_ds.GetProjection()
    geotransform = src_ds.GetGeoTransform()
    fileId = os.path.basename(inputImage).replace('.TIF', '')
    dst_filename = productWorkingDirectory + '/' + fileId + '_dem_merge.TIF'
    pyScript = denseMatchingDir + '/getSRTM3.py'
    param = [
        'python2.7 ',
        pyScript,
        inputImage,
        demReference,
        dst_filename,
        prj,
        str(list(geotransform)[1])]
    cmd = ' '.join(param)
    os.system(cmd)
    src_ds = None


def processStandardMedicisOutput(pixelSpacing, medicisDirectory,
				resultDirectory, matlabProcessingDir,
				activityLabel):

    # processStandardMedicisOutput : Lite Version with fake variables
    # Ce repertoire <rootdir> est indique dans le path de matlab
    rootdir='/home/saunier/Documents/MATLAB'

    print '-- Create Matlab File For correlation annalysis --'
    print '-- Script temporaire MATLAB stocker dans' + medicisDirectory
    print '-- No metada File is considered --'
    mfile = os.path.join(rootdir, 'main.m')
    print ' '
    ch = ['Save matlab main file :']

    print ''.join(ch)
    print mfile
    print ' '
    f = open(mfile, 'w+')

    activity = 'geometrie'

    task = 'directLocation'
    pixelSize = pixelSpacing

    importOption = 'yes'

    rad=os.path.basename(medicisDirectory)
    filename = rad+'_monoTemp.mat'

    observationDate = '2015-11-11'
    site='La Crau'

    #targetPath = os.path.join(resultDirectory, activity, task, filename)
    targetPath = os.path.join(resultDirectory,filename)

    param = ['pointMatDestination=',"'",targetPath,"';",'\n']
    f.write(''.join(param))
    param = ["addpath('",matlabProcessingDir,"');",'\n']
    f.write(''.join(param))
    print 'Generate Main'
    param = ['LOC.productPath=',"'",medicisDirectory,"';",'\n']
    f.write(''.join(param))
    param = ['LOC.sceneId=',"'",sceneId,"';",'\n']
    f.write(''.join(param))
    param = ['LOC.pixelSize=' + str(pixelSize) + ';','\n']
    f.write(''.join(param))
    param = ['importOption=',"'",importOption,"';",'\n']
    f.write(''.join(param))
    param = ['a=importMedicisRepo(LOC.productPath,LOC.sceneId,LOC.pixelSize,importOption);','\n']
    f.write(''.join(param))

    param = ['LOC.sw=',"'",'TBD',"';",'\n']
    f.write(''.join(param))


    param = ['LOC.dispar=a;','\n']
    f.write(''.join(param))
    param = ['LOC.obsDate=',"'",observationDate,"';",'\n']
    f.write(''.join(param))
    param = ['LOC.doy=',"'",'111',"';",'\n']
    f.write(''.join(param))

    param = ['LOC.site=',"'",site,"';",'\n']
    f.write(''.join(param))
    

    param = ['activityLabel=',"'",activityLabel,"';",'\n']
    f.write(''.join(param))
    


    result = os.path.exists(targetPath)
    
    param = [
        'save(pointMatDestination,',
        "'a');\n"]
    f.write(''.join(param))
    f.write('clear;\n')
    f.write('exit')
    print '--Execute Matlab'
    
    cmd = 'matlab -nosplash -r main &'
    os.system(cmd)
    #time.sleep(10)

    print " "
    print "save mat file in :"    
    print targetPath
    print " "



     
def updateMultitemporalMatFile(metadata, medicisDirectory,
			      resultDirectory, matlabProcessingDir,
			      activityLabel, pixelSpacing, rootdir):


    # Result Directory est un maintenant le nom du fichier matlab
    #
    print '-- Update Multi Temporal Matlab File '
    print '-- Script temporaire MATLAB stocker dans :' + rootdir
    mfile = os.path.join(rootdir, 'main.m')
    f = open(mfile, 'w+')
    targetPath=resultDirectory 
    param = ['pointMatDestination=',"'",targetPath,"';",'\n']
    f.write(''.join(param))
    param = ["addpath('", matlabProcessingDir,"');",'\n']
    f.write(''.join(param))
    
    mtl=metadata
    if (isinstance(mtl,metadata_extraction.LandsatMTL)) :
         print '--- mtl object'
         productPath=medicisDirectory
         sceneId=mtl.landsat_scene_id
         site=mtl.test_site
         sw=mtl.processing_sw
         swNumber=''
         obsDate=mtl.observation_date
         doy=mtl.doy
    else:
          print '-- mtl file'
          xmldoc = minidom.parse(metadataFile)
          productPath = xmldoc.getElementsByTagName('productLocationOnDisk')[0].firstChild.data
          sceneId = xmldoc.getElementsByTagName('fileName')[0].firstChild.data
          if len(xmldoc.getElementsByTagName('siteName')) > 0:
            site = xmldoc.getElementsByTagName('siteName')[0].firstChild.data
          else:
            site = 'unknown'

          sw = xmldoc.getElementsByTagName('sw')[0]
          swNumber = sw.getElementsByTagName('number')[0].firstChild.data
          obsDate = xmldoc.getElementsByTagName('obsDate')[0].firstChild.data
          doy = xmldoc.getElementsByTagName('doy')[0].firstChild.data

    pixelSize = pixelSpacing
    importOption = 'yes'

    param = [
        "activityLabel='",
        activityLabel,
        "';",
        '\n']
    f.write(''.join(param))
    print 'Generate Main'
    param = [
        'LOC.productPath=',
        "'",
        medicisDirectory,
        "';",
        '\n']
    f.write(''.join(param))
    param = [
        'LOC.sceneId=',
        "'",
        sceneId,
        "';",
        '\n']
    f.write(''.join(param))
    param = [
        'LOC.site=',
        "'",
        site,
        "';",
        '\n']
    f.write(''.join(param))
    param = [
        'LOC.sw=',
        "'",
        swNumber,
        "';",
        '\n']
    f.write(''.join(param))
    param = [
        'LOC.obsDate=',
        "'",
        obsDate,
        "';",
        '\n']
    f.write(''.join(param))
    param = [
        'LOC.doy=' + str(doy),
        ';\n']
    f.write(''.join(param))
    param = [
        'LOC.pixelSize=' + str(pixelSize) + ';',
        '\n']
    f.write(''.join(param))
    param = [
        'importOption=',
        "'",
        importOption,
        "';",
        '\n']
    f.write(''.join(param))
    param = [
        'a=importMedicisRepo(LOC.productPath,LOC.sceneId,LOC.pixelSize,importOption);',
        '\n']
    f.write(''.join(param))
    param = [
        'LOC.dispar=a;',
        '\n']
    f.write(''.join(param))
#Text File for statistics
    param = [
        'txt_file = [LOC.productPath filesep \'stat.txt\']',
        ';\n']
    f.write(''.join(param))
#Open the Text File to store statistics - set Varialbes fid
    param = [
        'fid = fopen(txt_file,\'w\')',
        ';\n']
    f.write(''.join(param))
#Set Variables  - index
    param = [
        'index=1',
        ';\n']
    f.write(''.join(param))
#Applied methods
    param = [
        'a.getSummary(fid,index)',
        ';\n']
    f.write(''.join(param))

#Figure 1 => CE
    param = [
        ' figure(1);saveas(gcf,[LOC.productPath filesep \'CE.png\'])',
        ';\n']
    f.write(''.join(param))
#Figure 2 => Historgram
    param = [
        ' figure(2);saveas(gcf,[LOC.productPath filesep \'XYhistogram.png\'])',
        ';\n']
    f.write(''.join(param))
#Figure 3 => Repartition Function
    param = [
        ' figure(3);saveas(gcf,[LOC.productPath filesep \'Distribution.png\'])',
        ';\n']
    f.write(''.join(param))
    param = ['close all ;','\n']
    f.write(''.join(param))


    print('----')    
    print(targetPath)

    result = os.path.exists(targetPath)

    print (result)
    print('----')    

    if result:
        print ('Add record')
        param = [
            'disp(',
            "'-- Addrecord to current object ');",
            '\n']
        f.write(''.join(param))
        param = [
            'disp(',
            "'-- Load Destination file ');",
            '\n']
        f.write(''.join(param))

        f.write('load(pointMatDestination);\n')
        f.write('multiTemp=multiTemp.addRecord(LOC.sceneId,LOC.obsDate(1:4),LOC.doy,LOC.sw,LOC.dispar,LOC.site);\n')
    else:
        print ('Create Multi Temp object')

        param = [
            'disp(',
            "'-- Create Multi Temporal Object ');",
            '\n']
        f.write(''.join(param))  
        f.write('multiTemp=multiTempGeoAnalysis(LOC.sceneId,LOC.obsDate(1:4),LOC.doy,LOC.sw,LOC.dispar,activityLabel,LOC.site);\n')

    param = [
        'disp(',
         "'-- Save into MAT FILE ');",
         '\n']
    f.write(''.join(param))  

    param = [
        'save(pointMatDestination,',
        "'multiTemp');\n"]
    f.write(''.join(param))
    f.write('clear;\n')

    param = [
        'disp(',
         "'-- EXIT NOW ');",
         '\n']
    f.write(''.join(param))  

    f.write('exit')
    print '--Execute Matlab'
    cmd = 'matlab -nosplash -r main &'
    os.system(cmd)

    return targetPath

if __name__ == '__main__':
    executeMedicis(argv)
