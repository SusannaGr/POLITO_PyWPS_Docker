# -*- coding: utf-8 -*- 
#!/usr/bin/python
##########################################################
#
# PROCEDURA:    Procedura WPS (Renerfor_CDP_Report_browser)
# LINGUA :      Italiana
#
# SCOPO:        Restituisce i descrittori di bacino, gli L-momenti regionali e la curva di Durata delle Portate naturalizzata 
#               stimati secondo il modello regionale RENERFOR per la stima delle curve di durata delle portate.  

#-------------Mappe/dati di base utilizzati -------------
# DEM input: piemonte_dem_r100
# MAPPA: piemonte_MAP_r250
# MAPPA IDFa: piemonte_IDFa_r250
# piemonte_fourierB1_r50
# piemonte_pioggemensili_cv_
# italy_CLC2000_r100

# Da inserire da parte dell'utente:
# VETTORE di delimitazione del bacino (per Es. ChisoneProva)

#-------------Output-------------
# Stringa dei descrittori, degli L-momenti regionali e parametri della distribuzione del bacino calcolati (in base allo shapefile inserito)
# Grafico CDP
############################################################

from pywps.Process import WPSProcess
from types import *

import sys,os,re,math
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from math import gamma,log,sqrt

#Importa lo script python
import funzioni_BurrXII_browser as fun

# Setup environment: necessary to import grass.script
GISBASE = "/usr/local/grass-6.4.3/"
sys.path.append(GISBASE + "etc/python/")
os.environ['GISBASE'] = GISBASE
GISDBASE=os.environ['GISDBASE'] = "/data/grass/gisdbase_grass6"
os.environ['GISRC'] ="/home/idrologi/.grassrc6"
os.environ['PATH'] = os.environ['PATH'] + ':' + GISBASE + "scripts/"
os.environ['PATH'] = os.environ['PATH'] + ':' + GISBASE + "bin/"
os.environ['PYTHONPATH']= GISBASE + "etc/python/grass/script/"
os.environ['LD_LIBRARY_PATH'] = GISBASE + "lib/"

import grass.script as grass
#import grass.script.setup as gsetup

#location="WGS84-UTM32N_32632"
#mapset="proveGTPro"

#gsetup.init(GISBASE,GISDBASE, location, mapset)

class Process(WPSProcess):
    """Main process class"""
    def __init__(self):

        # init process
        WPSProcess.__init__(self,
            identifier = "Renerfor_CDP_Report_browser",
            title="Renerfor_CDP_Report_browser",
            version = "0.1",
            storeSupported = "true",
            statusSupported = "true",
            abstract="RENERFOR CDP Report",
            grassLocation = "WGS84-UTM32N_32632")

        # PROCESS INPUT/OUTPUT

        # Input
        self.vectorbacino=self.addComplexInput(identifier="vectorbacino",
                                                 title="Shapefile bacino",
                                                 formats=[{'mimeType':'text/xml'}])
                                
        self.namebacino = self.addLiteralInput(identifier = "namebacino",
                                           title = "Nome dell bacino",
                                           type = StringType)

        #self.GRASSregionin= self.addLiteralInput(identifier="GRASSregionin",
        #                                   title="GRASS region extent (xmin,xmax,ymin,ymax). Leave blank to use min covering extent",
        #                                   type = StringType)
        # Output

        self.urlPDF=self.addLiteralOutput(identifier="urlPDF",
                                            title="url_Report_PDF",
                                            type= StringType)

        # self.imageOut=self.addComplexOutput(identifier="CDP",
                                            # title="Curva Regionale delle Portate",
                                            # abstract="Grafico CDP Renerfor",
                                            # formats=[{"mimeType": "image/x-png"},{"mimeType":"image/png"}],
                                            # asReference=False)
        
    def execute(self):
         uuid=str(self.pywps.UUID)
         nome_report_PDF="Report_CDP_"+str(uuid)+".pdf"
         file_report_PDF="/var/www/wpsoutputs/"+str(nome_report_PDF)
         nome_grafico="CDP_"+str(uuid)+".png"
         file_grafico="/var/www/wpsoutputs/"+str(nome_grafico)
         nomebacino=str(self.namebacino.getValue())
         #Cancellazione vecchi grafici e Report
         ## if file exists, delete it ##
         if os.path.isfile(file_report_PDF):
             os.remove(file_report_PDF)
         if os.path.isfile(file_grafico):
             os.remove(file_grafico)
			 
         ################### ESTRAZIONE DESCRITTORI DEL BACINO DA GRASS #################################
         #carica shp in grass
         grass.run_command('v.in.ogr', flags='o', dsn='%s' %(self.vectorbacino.getValue()), output='basin', min_area='0')
    
         #configura regione
         grass.run_command('g.region', flags='d')
         grass.run_command('g.region', vect='basin', res='100')
    
         #trasforma in raster
         grass.run_command('v.to.rast', input='basin', output='BASIN', use='cat', type='area')
    
         #definisce l'area di interesse per le statistiche
         grass.run_command('r.mask', input='BASIN')
    
         #quota media e area ('piemonte_dem_r100')
         grass.run_command('g.region', vect='basin', res='100')
         stats_dem = grass.parse_command('r.univar', flags='eg', map='piemonte_dem_r100@DTM100_PIEMONTE')
         quota_media=float(stats_dem['mean'])
         quota_max = float(stats_dem['max'])
         area_km = float(stats_dem['n']) * 0.01
         ipso75 = float(stats_dem['first_quartile'])
    
         # curva ipsografica
         #cells_DEM = grass.read_command('r.stats', flags='1n', input=map_dem)
         #cells_DEMp = grass.parse_command('r.stats', flags='1n', input=map_dem)
    
         #media afflusso annuo ('piemonte_MAP_r250')
         grass.run_command('g.region', vect='basin', res='250')
         stats_MAP = grass.parse_command('r.univar', flags='g', map='piemonte_MAP_r250@PERMANENT')
         MAP_media = float(stats_MAP['mean'])
         MAP_std = float(stats_MAP['stddev'])
    
         #media e STD coefficiente pluviale orario CPP ('piemonte_IDFa_r250')
         grass.run_command('g.region', vect='basin', res='250')
         stats_IDFa = grass.parse_command('r.univar', flags='g', map='piemonte_IDFa_r250@PERMANENT')
         IDFa_media = float(stats_IDFa['mean'])
         IDFa_std = float(stats_IDFa['stddev'])
    
         #media coefficiente regime pluviometrico B1 ('piemonte_fourierB1_r50')
         grass.run_command('g.region', vect='basin', res='50')
         stats_fourierB1 = grass.parse_command('r.univar', flags='g', map='piemonte_fourierB1_r50@PERMANENT')
         fourierB1_media = float(stats_fourierB1['mean'])
    
         #media coefficiente variazione regime pluviometrico ('piemonte_rp_cv_r50')
         grass.run_command('g.region', vect='basin', res='50')
         stats_rpcv = grass.parse_command('r.univar', flags='g', map='piemonte_pioggemensili_cv_r50@PERMANENT')
         rpcv_media = float(stats_rpcv['mean'])
    
         #percentuale classi CORINE riclassifcato
         cells_CLC = grass.read_command('r.stats', flags='1n', input='italy_CLC2000_r100@PERMANENT')
         all_cells_CLC = cells_CLC.count('1') + cells_CLC.count('2') + cells_CLC.count('3') + cells_CLC.count('4') + cells_CLC.count('5')
         clc2_percentuale = float(cells_CLC.count('2')) / float(all_cells_CLC) * 100
         clc3_percentuale = float(cells_CLC.count('3')) / float(all_cells_CLC) * 100
    
         # pulizia del workspace di GRASS
         grass.run_command('r.mask', flags='r')
         grass.run_command('g.remove', rast='BASIN')
         grass.run_command('g.remove', vect='basin')
        
         testo =""
         testo1 = "I descrittori del bacino '%s' sono: \n" %(nomebacino)
         testo1 += "Area (km2): "+ str(round(area_km,3)) + "\n"+ "quota_media (m slm):  "+ str(round(quota_media,3)) + "\n" + "quota_massima (m slm):  " + str(round(quota_max,3)) + "\n" + "curva_ipso_75percento (m slm):  " + str(round(ipso75,3)) + "\n" + "MAP (mm):  " + str(round(MAP_media,3)) + "\n" + "IDFa (mm):  " + str(round(IDFa_media,3)) + "\n" + "IDFa_std (mm/h):  " + str(round(IDFa_std,3)) + "\n" + "fourier_B1:  " + str(round(fourierB1_media,3)) + "\n" +"CV rp:  " + str(round(rpcv_media,3)) + "\n" + "clc2_perc:  " + str(round(clc2_percentuale,3)) + "\n" + "clc3_perc:  " + str(round(clc3_percentuale,3))+"\n"
         #################### STIMA L-MOMENTI REGIONALI E PARAMETRI DISTRIBUZIONE #################################
         ## Calcolo portata L-momenti regionali
         c_int=IDFa_media/MAP_media
         Y=-7.3605*10**2+1.2527*MAP_media+3.2569*10**(-1)*quota_media+5.2674*fourierB1_media-6.7185*clc2_percentuale
         LCV=-2.896*10**(-1)-2.688*10**(-3)*clc3_percentuale+9.643*10**(-5)*ipso75+1.688*10**(-4)*MAP_media+2.941*10*c_int
         LCA=4.755*quota_max**(-0.2702)*IDFa_std**0.06869*rpcv_media**0.2106
         L1=Y*area_km/31536

         testo2 = "\n Gli L-momenti della CDP stimati, per l' area di studio sulla base delle caratteristiche geomorfologice del bacino, secondo la procedura regionale Renerfor sono: \n"
         testo2 += "L1:" + str(round(L1,3)) + "\n" + "LCV: "+str(round(LCV,3))+ "\n"+"LCA:" + str(round(LCA,3))+"\n \n"
         
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
         #output += "\n"+"Puoi visualizzare e scaricare il Report PDF all'url: \n %s" %('http://130.192.28.30/wpsoutputs/'+str(nome_report_PDF))
		 link='http://130.192.28.30/wpsoutputs/'+str(nome_report_PDF)
		 self.urlPDF.setValue(link)
         return