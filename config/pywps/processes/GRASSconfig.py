import os,sys
from configparser import ConfigParser
config = ConfigParser()
file='/etc/pywps.cfg'
config.read(file)

def fun_config():
    GISBASE=config.get("grass", "gisbase")
    #GISBASE="gisbase=/usr/lib/grass78"
    GRASS_PATH=[os.path.join(GISBASE, "bin"),os.path.join(GISBASE, "scripts")]
    GRASS_LD_LIBRARY_PATH=os.path.join(GISBASE, "lib")
    GRASS_PYTHONPATH=[os.path.join(GISBASE, "etc/python"), os.path.join(GISBASE, "etc/python/grass/script/")]

    os.environ['PATH']+= os.pathsep + os.pathsep.join(GRASS_PATH)
    os.environ['LD_LIBRARY_PATH']= os.pathsep + os.pathsep.join(GRASS_LD_LIBRARY_PATH)
    os.environ['PYTHONPATH']=os.pathsep + os.pathsep.join(GRASS_PYTHONPATH)
    os.environ['GRASS_SKIP_MAPSET_OWNER_CHECK'] = '1'

    sys.path.append(GRASS_PYTHONPATH[0])
    sys.path.append(GRASS_PYTHONPATH[1])
    print (GISBASE)
