#!/usr/bin/env python3

__author__ = 'Susanna Grasso'

from pywps import Process, LiteralInput, ComplexInput, ComplexOutput, Format
import sys,os,re,math
import numpy as np
from types import *
import shutil
import logging
LOGGER = logging.getLogger('PYWPS')

## To import GISBASE and GISDBASE from pywps.cfg
from configparser import ConfigParser
config = ConfigParser()
proc_dir = os.path.dirname(os.path.abspath(__file__))
#For accessing the file in the parent folder of the current folder
file= os.path.join(proc_dir, '/etc/pywps.cfg')
config.read(file)

class Renerfor_delimitazione(Process):
    """Main process class"""
    def __init__(self):
        """Process initialization"""
        ### PROCESS INPUT/OUTPUT
        ## Input
        inputs = [
            LiteralInput('nome_bacino', 'Nome del bacino',
                         data_type='string',
                         abstract="Inserire il nome che si vuole dare al bacino",
                         min_occurs=1),

            LiteralInput('InputX', 'Coordinata X (32632) della sezione di chiusura',
                         data_type='float',
                         abstract="Coordinata X (nel sistema di riferimento WGS-84-UTM32N) della sezione di chiusura del bacino",
                         min_occurs=1,
                         max_occurs=1),

            LiteralInput('InputY', 'Coordinata Y (32632) della sezione di chiusura',
                         data_type='float',
                         abstract="Coordinata Y (nel sistema di riferimento WGS-84-UTM32N) della sezione di chiusura del bacino",
                         min_occurs=1,
                         max_occurs=1),
        ]
        ## Outputs
        outputs = [
            ComplexOutput('shapefilebacino', 'Bacino delimitato in formato GML',
                          abstract="Vettoriale del bacino delimitato in formato GML",
                          supported_formats=[Format('application/gml+xml')]
                          )
        ]

        ## init process
        super(Renerfor_delimitazione, self).__init__(
            self._handler,
            identifier = "renerfor_delimitazione",
            title="Renerfor delimitazione",
            abstract="RENERFOR - Procedura di delimitazione di bacino",
            version = "0.1",
            inputs=inputs,
            outputs=outputs,
            store_supported = "true",
            status_supported = "true",
        )


    def _handler(self, request, response):

        nome_bacino = request.inputs['nome_bacino'][0].data
        coordX = float(request.inputs['InputX'][0].data)
        coordY = float(request.inputs['InputY'][0].data)

        #Set variabili per richiamare grass script
        GISBASE = config.get('grass', 'gisbase')
        os.environ['GRASS_SKIP_MAPSET_OWNER_CHECK'] = '1' ## aggiunto dopo
        import grass.script as grass
        import grass.script.setup as gsetup

        print("---- Start renerfor_delimitazione process ---- ")

        #Set up location and mapset (eventualmente da cambiare) per richiamare questo mapset grass da python
        GISDBASE=config.get("grass", "gisdbase")
        location="EPSG32632"
        mapset="PROVA"
        gsetup.init(GISBASE,GISDBASE, location, mapset)

        gisenv=grass.parse_command('g.gisenv', flags='n')
        print("Test gisenv: %s" % gisenv)

        list=grass.parse_command('g.list', type="rast")
        print("g.list rast: %s " %list)

        # pulizia preventiva
        LOGGER.info(" ---- Pulizia mapset ---- ")
        grass.run_command('g.remove', flags='f', type='raster', name='MASK')
        grass.run_command('g.remove', flags='f', type='raster', name='BACINO')
        grass.run_command('g.remove', flags='f', type='vector', name='BACINOvect')

        # import raster map_drain
        import subprocess
        p1=grass.start_command('g.region', raster='piemonte_drain_r100@PROVA', stderr=subprocess.PIPE)
        stdoutdata, stderrdata = p1.communicate()
        print("Error occured: %s" % stderrdata)

        #grass.run_command('g.region', raster='piemonte_drain_r100@PERMANENT', quiet=True)

        #estrazione bacino
        p2=grass.start_command('r.water.outlet', input='piemonte_drain_r100@PROVA', output='BACINO', coordinates='%f,%f' %(coordX,coordY), overwrite=True, stderr=subprocess.PIPE)
        stdoutdata, stderrdata = p2.communicate()
        print("Error occured: %s" % stderrdata)

        p3= grass.start_command('r.to.vect', input='BACINO', output='BACINOvect', type="area", stderr=subprocess.PIPE)
        stdoutdata, stderrdata = p3.communicate()
        print("Error occured: %s" % stderrdata)

        # OUTPUT SHAPE FILE
        #tmpFolderPath=os.getcwd()
        #uid=str(self.pywps.UUID)

        outpath=config.get("server", "outputpath")
        outfile=os.path.join(outpath,nome_bacino+".gml")
        if os.path.isfile(outfile):
            os.remove(outfile)
        res=grass.start_command('v.out.ogr', flags='c', input='BACINOvect', type="area", output=outfile, format="GML", stderr=subprocess.PIPE)
        stdoutdata, stderrdata = res.communicate()
        print("Error occured: %s" % stderrdata) 

        #NEW - creo anche l'output in formato geojson
        outfile2=os.path.join(outpath,nome_bacino+".geojson")
        if os.path.isfile(outfile2):
            os.remove(outfile2)
        grass.start_command('v.out.ogr', flags='c', input='BACINOvect', type="area", output=outfile2, format="GeoJSON", stderr=subprocess.PIPE)

        #res=grass.run_command('v.out.ogr', 'c', input='BACINOvect', type='area', dsn='%s' %("shapefilebacino-"+str(uuid)+".shp"), format='ESRI_Shapefile')

        # pulizia
        LOGGER.info(" ---- Pulizia mapset ---- ")
        grass.run_command('g.remove', flags='f', type='raster', name='MASK')
        grass.run_command('g.remove', flags='f', type='raster', name='BACINO')
        grass.run_command('g.remove', flags='f', type='vector', name='BACINOvect')


        #outfile2=os.getcwd()+"/shapefilebacino-"+str(uuid)+".gml"

        response.outputs['shapefilebacino'].file = outfile
        return
