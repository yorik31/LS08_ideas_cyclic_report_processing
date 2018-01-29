# -*- coding: utf-8 -*-
import os,sys
import imp
import glob
import imp
import metadata_extraction
import main_infra
import log

if __name__ == '__main__':
    infra=main_infra.mainInfra()
    infra.checkDirectoryPresence()

