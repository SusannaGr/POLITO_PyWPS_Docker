from pywps import Process, LiteralInput, ComplexInput, ComplexOutput, FORMATS, Format
from pywps.inout.outputs import MetaLink, MetaLink4, MetaFile
from pywps.inout.literaltypes import AllowedValue
from pywps.app.Common import Metadata

import sys,os,re,math
import subprocess
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from math import gamma,log,sqrt

#Importa lo script python
from . import funzioni_BurrXII_browser as fun

## To import GISBASE and GISDBASE from pywps.cfg
from configparser import ConfigParser
config = ConfigParser()
proc_dir = os.path.dirname(os.path.abspath(__file__))
#For accessing the file in the parent folder of the current folder
file= os.path.join(proc_dir, '/etc/pywps.cfg')
config.read(file)

import logging
LOGGER = logging.getLogger("PYWPS")

class Renerfor_descrittori(Process):
    def __init__(self):
        inputs = [
		    LiteralInput('namebacino', 'Nome del bacino',
                         data_type='string',
                         abstract="Inserire il nome del bacino",
                         min_occurs=1),
            ComplexInput('vectorbacino', 'Vettoriale del bacino',
                          abstract="Vettoriale del bacino delimitato in formato GML-XML",
                          supported_formats=[Format('application/gml+xml'),Format('application/vnd.geo+json')]
                          )
        ]
        outputs = [
            ComplexOutput('output', 'METALINK v3 output',
                          abstract='Testing metalink v3 output',
                          as_reference=False,
                          supported_formats=[FORMATS.METALINK]),
            ComplexOutput('output_meta4', 'METALINK v4 output',
                          abstract='Testing metalink v4 output',
                          as_reference=False,
                          supported_formats=[FORMATS.META4])
        ]

        super(Renerfor_descrittori, self).__init__(
            self._handler,
            identifier='renerfor_descrittori_test',
            title='renerfor_descrittori_test',
            abstract='Inserimento di uno shapefile in formato GML e ritorno di un link per visualizzazione di un pdf scelto come esempio',
            version='0.1',
            inputs=inputs,
            outputs=outputs,
            store_supported=True,
            status_supported=True
        )

    def _handler(self, request, response):
        response.update_status('PyWPS Process started.', 0)
        LOGGER.info("starting ...")
        max_outputs = 1

        # Variabili in input
        vectorbacino=request.inputs['vectorbacino'][0].file
        nomebacino=request.inputs['namebacino'][0].data

        # Variabili per output
        workdir=self.workdir
        file_path = config.get('server', 'outputpath')
        file_url = config.get('server', 'outputurl')

        nome_report_PDF="Report_CDP_"+str(self.uuid)+".pdf"
        nome_grafico="CDP_"+str(self.uuid)+".png"

        file_report_PDF= os.path.join(file_path, nome_report_PDF)
        url_report_PDF = os.path.join(file_url, nome_report_PDF)
        file_grafico=os.path.join(file_path, nome_grafico)
        url_grafico = os.path.join(file_url, nome_grafico)

        #Definizione ambiente di GRASS
        import grass.script as grass
        import grass.script.setup as gsetup

        GISBASE=config.get('grass', 'gisbase')
        GISDBASE=config.get("grass", "gisdbase")
        location="EPSG32632"
        mapset="PROVA"
        gsetup.init(GISBASE,GISDBASE, location, mapset)

        gisenv=grass.parse_command('g.gisenv', flags='n')
        print("Test gisenv: %s" % gisenv)

        list=grass.parse_command('g.list', type="rast")
        print("g.list rast: %s " %list)
      
        ######### ESTRAZIONE DESCRITTORI DEL BACINO DA GRASS #########
        print('######### ESTRAZIONE DESCRITTORI DEL BACINO DA GRASS #########')
        #caricamento vettoriale in GRASS
        res=grass.start_command('v.in.ogr', input=vectorbacino, output='basin', overwrite = True, min_area='0',stderr=subprocess.PIPE)
        stdoutdata, stderrdata = res.communicate()
        print("Error occured: %s" % stderrdata)

        # Configurazione della regione di GRASS
        grass.run_command('g.region', vector='basin')

        #trasforma il vettore del bacino in un raster
        grass.run_command('v.to.rast', input='basin', output='BASIN', use='cat', type='area', overwrite = True)

        #quota media e area ('piemonte_dem_r100')
        stats_dem = grass.parse_command('r.univar', flags='eg', map='piemonte_dem_r100@PROVA', zones='BASIN')
        quota_media=float(stats_dem['mean'])
        quota_max=float(stats_dem['max'])
        area_km=float(stats_dem['n']) * 0.01
        ipso75=float(stats_dem['first_quartile'])
        print(quota_media, quota_max, area_km, ipso75)

        #media afflusso annuo ('piemonte_MAP_r250')
        #grass.run_command('g.region', vect='basin', res='250')
        stats_MAP = grass.parse_command('r.univar', flags='g', map='piemonte_MAP_r250@PROVA', zones='BASIN')
        MAP_media = float(stats_MAP['mean'])
        MAP_std = float(stats_MAP['stddev'])

        #media e STD coefficiente pluviale orario CPP ('piemonte_IDFa_r250')
        #grass.run_command('g.region', vect='basin', res='250')
        stats_IDFa = grass.parse_command('r.univar', flags='g', map='piemonte_IDFa_r250@PROVA', zones='BASIN')
        IDFa_media = float(stats_IDFa['mean'])
        IDFa_std = float(stats_IDFa['stddev'])
    
        #media coefficiente regime pluviometrico B1 ('piemonte_fourierB1_r50')
        #grass.run_command('g.region', vect='basin', res='50')
        stats_fourierB1 = grass.parse_command('r.univar', flags='g', map='piemonte_fourierB1_r50@PROVA', zones='BASIN')
        fourierB1_media = float(stats_fourierB1['mean'])
    
        #media coefficiente variazione regime pluviometrico ('piemonte_rp_cv_r50')
        #grass.run_command('g.region', vect='basin', res='50')
        stats_rpcv = grass.parse_command('r.univar', flags='g', map='piemonte_pioggemensili_cv_r50@PROVA',zones='BASIN')
        rpcv_media = float(stats_rpcv['mean'])
    
        #percentuale classi CORINE riclassifcato
        cells_CLC = grass.read_command('r.stats', flags='1n', input='italy_CLC2000_r100@PROVA')
        all_cells_CLC = cells_CLC.count('1') + cells_CLC.count('2') + cells_CLC.count('3') + cells_CLC.count('4') + cells_CLC.count('5')
        clc2_percentuale = float(cells_CLC.count('2')) / float(all_cells_CLC) * 100
        clc3_percentuale = float(cells_CLC.count('3')) / float(all_cells_CLC) * 100
    
        # pulizia del workspace di GRASS
        grass.run_command('g.remove', flags='f', type='raster', name='MASK')
        grass.run_command('g.remove', flags='f', type='raster', name='BASIN')
        grass.run_command('g.remove', flags='f', type='vector', name='basin')

        testo =""
        testo1 = "I descrittori del bacino '%s' sono: \n" %(nomebacino)
        testo1 += "Area (km2): "+ str(round(area_km,3)) + "\n"+ "quota_media (m slm):  "+ str(round(quota_media,3)) + "\n" + "quota_massima (m slm):  " + str(round(quota_max,3)) + "\n" + "curva_ipso_75percento (m slm):  " + str(round(ipso75,3)) + "\n" + "MAP (mm):  " + str(round(MAP_media,3)) + "\n" + "IDFa (mm):  " + str(round(IDFa_media,3)) + "\n" + "IDFa_std (mm/h):  " + str(round(IDFa_std,3)) + "\n" + "fourier_B1:  " + str(round(fourierB1_media,3)) + "\n" +"CV rp:  " + str(round(rpcv_media,3)) + "\n" + "clc2_perc:  " + str(round(clc2_percentuale,3)) + "\n" + "clc3_perc:  " + str(round(clc3_percentuale,3))+"\n"
        
        print(testo1)
        ########## STIMA L-MOMENTI REGIONALI E PARAMETRI DISTRIBUZIONE ##########
        ## Calcolo portata L-momenti regionali
        c_int=IDFa_media/MAP_media
        Y=-7.3605*10**2+1.2527*MAP_media+3.2569*10**(-1)*quota_media+5.2674*fourierB1_media-6.7185*clc2_percentuale
        LCV=-2.896*10**(-1)-2.688*10**(-3)*clc3_percentuale+9.643*10**(-5)*ipso75+1.688*10**(-4)*MAP_media+2.941*10*c_int
        LCA=4.755*quota_max**(-0.2702)*IDFa_std**0.06869*rpcv_media**0.2106
        L1=Y*area_km/31536.0

        testo2 = "\n Gli L-momenti della CDP stimati, per l' area di studio sulla base delle caratteristiche geomorfologice del bacino, secondo la procedura regionale Renerfor sono: \n"
        testo2 += "L1:" + str(round(L1,3)) + "\n" + "LCV: "+str(round(LCV,3))+ "\n"+"LCA:" + str(round(LCA,3))+"\n \n"

        print(testo2)   
        ## Calcolo dei parametri della distribuzione funzioni riscritte a partire dal pacchetto per R Hydroapps(Ganora) per RENERFOR
        d=np.array(range(1,366))
        p=1-d/366.0
        LCAinf=fun.tau3BurrXII_WeibullBound(LCV)
        LCAsup=fun.tau3BurrXII_ParetoBound(LCV)
        risultati=fun.parBurrXIIapprox(L1, LCV, LCA)
        #risultati=('BurrXII','a: 8.5; b: 1; c: 2.8', p)
        distribuzione=risultati[0]
        parametri=risultati[1]
        x=risultati[2]
         
        testo3 ="Gli L-momenti L-CV e L-CA della Curva di Durata delle Portate (CDP), stimati a partire dai descrittori di bacino, ricadono, come riportato nella seguente figura, nel dominio di esistenza della distribuzione: "+ str(distribuzione)+".\n"
        testo3 += "I parametri stimati della distribuzione indicata hanno valore: \n"+ str(parametri)+". \n \n"
        testo4 =" La Curva di durata delle portate in regime naturale (non influenzata da derivazioni), ottenuta dal modello regionale Renerfor, viene riportata nel presente Report."
         
        #Creazione grafico CDP 
        fun.grafico_FDC_semplice_browser(x,file_grafico)
        #fun.figura_FDC_due_assi(x) #prova
        ##########################################################################################
        ##########################################################################################
        # OUTPUT
        testo=testo1+testo2+testo3+testo4
        
        #Creazione Report PDF
        with PdfPages(file_report_PDF) as pdf:
            #plt.rc('text', usetex=False)
            figura_testo=plt.figure(figsize=(8,6))
            # Pagina 1: Risultati testuali
            plt.text(-0.12, 1.01,testo, ha='left',va='top', wrap=True,fontsize=10)
            plt.ylim(0, 1)
            plt.xlim(0, 1)
            plt.setp(plt.gca(), frame_on=False, xticks=(), yticks=())
            pdf.savefig(figura_testo)
            plt.close()
            # Pagina 2: Dominio di Burr
            figura_dominio=fun.figura_dominio_burr(LCV,LCA)
            pdf.savefig(figura_dominio)
            plt.close()
            # Pagina 2: Curva di Durata
            figura_FDC=fun.figura_FDC_due_assi(x)
            pdf.savefig(figura_FDC)
            plt.close()

        #output = "Puoi visualizzare e scaricare il grafico della curva di durata delle portate all'url: \n %s" %('http://130.192.28.30/wpsoutputs/'+str(nome_grafico))
        #output += "\n"+"Puoi visualizzare e scaricare il Report PDF all'url: \n %s" %(url_report_PDF))
	

        # generate MetaLink v3 output
        ml3 = MetaLink('Report PDF', 'MetaLink', workdir=self.workdir)
        mf = MetaFile('REPORT_PDF.pdf', 'Report PDF CDP', fmt=FORMATS.TEXT)
        mf.url=url_report_PDF
        ml3.append(mf)
        response.outputs['output'].data = ml3.xml

        # ... OR generate MetaLink v4 output (recommended)
        ml4 = MetaLink4('Report PDF', 'MetaLink4', workdir=self.workdir)
        mf = MetaFile('REPORT_PDF.pdf', 'Report PDF CDP', fmt=FORMATS.TEXT)
        mf.file=file_report_PDF
        ml4.append(mf)
        response.outputs['output_meta4'].data = ml4.xml

        response.update_status('PyWPS Process completed.', 100)
        return response
