from __future__ import division
import sys,os,re,math
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from math import gamma,log,sqrt

import pywps.configuration as config
file_path = config.get_config_value('server', 'outputpath')

#####################################################################################
######    CALCOLO DEI PARAMETRI DELLA DISTRIBUZIONE A PARTIRE DAGLI L-MOMENTI  ######
######                                 E                                       ######
######                      CREAZIONE CURVA DI DURATA                          ######
#####################################################################################

# Calcolo dei parametri della distribuzione a partire dagli L-momenti utilizzando la funzione di approssimazione 'parBurrXII.approx <- function(L1, tau, tau3)' proposta dal pacchetto Hydroapps(Ganora) per R sviluppato all'interno del progetto RENERFOR
# "Parameters k and c are appoximated accordi to Ganora & Laio (2014). These equations are valid only for pairs of tau-tau3 in the k<=0 domain"
# " Lmoments (i.e. L1=mean, tau=L-CV=L2/L1, tau3=L-skewness=L-CA=L3/L2) as a function of the distribution parameters "


############################### DEFINIZIONE FUNZIONI ################################
# Case k->-inf (Pareto distribution), upper bound of the domain of non-positive k (tau3 as a function of tau) 
def tau3BurrXII_WeibullBound(tau):
    tau3=((1/tau)*(-2+2*(3**(np.log(1-tau)/np.log(2)))+3*tau))
    return tau3

# Case k->0 (Weibull distribution), lower bound of the domain of non-positive k: tau3 (alias LCA) as a function of tau (alias LCV)
def tau3BurrXII_ParetoBound(tau):
    tau3=((1+3*tau)/(3+tau))
    return tau3

########################### FUNZIONI CREAZIONI GRAFICI #############################
def grafico_FDC_semplice_browser(x,file_grafico):
    d=np.array(range(1,366))
    plt.plot(d,x)
    plt.legend(loc="upper left")
    plt.title('Curva delle Portate regionale \n') # oppure 'CDP stimata per il bacino non strumentato'
    plt.xlabel('giorni')
    #plt.xlim(0,365)
    plt.ylabel('Portata [m3/s]') 
    plt.grid()
    plt.savefig(file_grafico)
    
# Per crezione grafico CDP annua + complesso: con doppio asse giorni e frequenza di non superamento
# Calcolo funzione di non superamento
def day_not_exceedance(f):
    day=(f/100)*366
    return day

def figura_FDC_due_assi(x):
    d=np.array(range(1,366))
    fig=plt.figure()
    fig.suptitle('Curva delle Portate regionale \n') # oppure 'CDP stimata per il bacino non strumentato'
    ax1 = fig.add_subplot(111)
    #ax1.set_title("Title for first plot") #### crea il titolo solo per il subplot ma da errori
    ax1.plot(d, x, color="b") # regular plot (red)
    ax1.set_xlabel('giorni')
    #ax1.set_xlim(0, 366) ############### NEL CASO IN CUI VOLESSI CHE L'ASSE X PARTISSE DA ZERO
    ax1.set_ylabel('Portata [m3/s]') # or 'Average daily flow rate Q [m3/ s]'
    ax2 = ax1.twiny() # ax1 and ax2 share y-axis
    fig.subplots_adjust(bottom=0.2)
    percent=[0,10,20,30,40,50,60,70,80,90,100]
    newlabel=['0%','10%','20%','30%','40%','50%','60%','70%','80%','90%','100%'] # labels of the xticklabels: the position in the new x-axis (percentage of exceedance)
    newpos=[day_not_exceedance(f) for f in percent] #position of the xticklabels in the old x-axis (days - axes)
    ax2.set_xticks(newpos)
    ax2.set_xticklabels(newlabel)
    ax2.xaxis.set_ticks_position('bottom') # set the position of the second x-axis to bottom
    ax2.xaxis.set_label_position('bottom') # set the position of the second x-axis to bottom
    ax2.spines['bottom'].set_position(('outward', 36))
    ax2.set_xlabel('Percentuale di non superamento')
    ax2.set_xlim(ax1.get_xlim())
    #fig.show()
    # Save the figure
    plt.savefig(os.path.join(file_path,'CDP_doppio_asse.png'), bbox_inches='tight', pad_inches=0.02, dpi=150)
    plt.show()
    return fig

#tau=LCV
#tau3=LCA
def figura_dominio_burr(LCV,LCA):
    tau = np.linspace(0, 1)
    fig, ax = plt.subplots()
    fig.suptitle('Dominio della funzione di BurrXII') # or Extended BurrXII domain bounded by the Pareto and the Weibull distributions
    line1_pareto = ax.plot(tau, tau3BurrXII_ParetoBound(tau), label='Pareto', color="grey", linewidth=0.7) #color ='b'
    line2_weibull = ax.plot(tau, tau3BurrXII_WeibullBound(tau), label='Weibull', color="grey", linewidth=0.7) #color='r'
    ax.text(0.3, 0.7, "Pareto", ha="center", va="center") #color ='b'
    ax.text(0.7, 0.3, "Weibull", ha="center", va="center") #color='r'
    plt.xlabel('LCV (tau)')
    plt.ylabel('LCA (tau3)')
    ax.scatter(LCV,LCA, marker='x',color="grey",linewidth=0.7)
    plt.text(LCV+0.015, LCA+0.015, '('+str(LCV)+', '+str(LCA)+')', fontsize=8) #I valori di LCA e LCV calcolati per dimostrare in caso del dominio ricade
    #plt.show()
    plt.savefig(os.path.join(file_path,'dominio_Burr.png'), bbox_inches='tight', pad_inches=0.02, dpi=150)
    return fig
    
def parBurrXIIapprox(L1, LCV, LCA):
    LCAinf=tau3BurrXII_WeibullBound(LCV)
    LCAsup=tau3BurrXII_ParetoBound(LCV)
    d=np.array(range(1,366))
    p=1-d/366.0
    if LCA<LCAsup and LCA>LCAinf:
        distribuzione="BurrXII"
        tau=LCV
        tau3=LCA
        # stima di k (secondo formula approssimata)
        k =np.log(-(24-33*tau+9*tau**3-8*(1-tau)**(np.log(3)/np.log(2))*(3+tau)+sqrt((24-33*tau+9*tau**3-8*(1-tau)**(np.log(3)/np.log(2))*(3+tau))**2-24*tau*(-4*(1-tau)**(np.log(3)/np.log(2))*(3+tau)+3*(4-5*tau+tau**3))*(-1+tau*(-3+tau3)+3*tau3)))/(24*(1-tau)**(np.log(3)/np.log(2))*(3+tau)-18*(4-5*tau+tau**3)) ) / np.log(3/2) 
        # stima di c (secondo formula approssimata)
        if k < -1:
            c = -((k+(5/2)**(1+k)*k+k*tau+k*sqrt((2/5)**(-2*(1+k))+2**-k*5**(1+k)*(1-3*tau)+(1+tau)**2))/(4*tau))
        else: 
            c = -(2/3)*(5/2-(2/5)**(-1-k))*(1+k-1/tau)+2/3*(-1+(5/2)**(1+k))*(-k-np.log(2)/np.log(1-tau))
        # stima di a (funzione dei valori k e c calcolati con la formula approssimata)
        a= L1*(-k)**(1+1/c)*gamma(1-1/k)/(gamma(1+1/c)*gamma(-1/c-1/k)) 
        param=a,k,c
        parametri='a: '+str(a)+'; b: '+str(-k)+'; c: '+str(c)
        x=a*(1/k*(1-(1-p)**k))**(1/c) #funzione quantile di Burr
    elif LCA>LCAsup:
        distribuzione="Pareto"
        cp=-(LCV+1)/(2*LCV)
        ap=L1*(1+cp)/cp
        parametri='aP: '+str(ap)+'; cP: '+str(cp)
        param=ap,cp
        x=ap*(1-p)**(1/cp) #funzione quantile Pareto
    elif LCA<LCAinf:
        distribuzione="Weibull"
        cw=-np.log(2)/(np.log(1-LCV))
        aw=L1*cw/(gamma(1/cw))
        param=aw,cw
        parametri='aW: '+str(aw)+'; cW: '+str(cw)
        x=aw*(-np.log(1-p))**(1/cw) #funzione quantile Weibull
    else:
        raise Exception('Errore nel calcolo degli L-momenti')
    return distribuzione, parametri, x
