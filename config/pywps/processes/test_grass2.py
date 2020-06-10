
__author__ = 'Susanna Grasso'

from pywps import Process, LiteralInput, LiteralOutput, Format
import os, sys
import subprocess

## To import GISBASE from pywps.cfg
from configparser import ConfigParser
config = ConfigParser()
proc_dir = os.path.dirname(os.path.abspath(__file__))
#For accessing the file in the parent folder of the current folder
file= os.path.join(proc_dir, '/etc/pywps.cfg')
config.read(file)

class Test_Grass2(Process):

    def __init__(self):
        outputs = [LiteralOutput('text_output', 'Output text', data_type='string')]
        super(Test_Grass2, self).__init__(
            self._handler,
            identifier='test_grass2',
            version='0.1',
            title='GRASS g.gisenv -n',
            abstract='Il processo apre la location di GRASS esistente "EPSG32632/PROVA" e tramite la funzione "g.gisenv -n" restituisce il gis environment. NB. GISDATABASE, location e mapset vengono specificati nello script mentre la posizione del GISBASE viene importata dal file pywps.cfg',
            outputs=outputs,
            store_supported=True,
            status_supported=True,
        )

    def _handler(self, request, response):
        import logging
        LOGGER = logging.getLogger(__name__)
        print ('------------------ Start Test_Grass2 -------------------')
        LOGGER.info("prova test logger")


        import grass.script as grass
        import grass.script.setup as gsetup
        print("grass.script importato!")

	## Launch session
        
        GISBASE=config.get("grass", "gisbase")
        GISDBASE=config.get("grass", "gisdbase")
        location="EPSG32632"
        mapset="PROVA"
        gsetup.init(GISBASE,GISDBASE, location, mapset)

        res=grass.parse_command('g.gisenv', flags='n')
        response.outputs['text_output'].data = res
        return response
