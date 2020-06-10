#!/usr/bin/env python3

"""
WSGI application of PyWPS for POLITO Renerfor Project
"""

__author__ = "Susanna Grasso"

from pywps.app.Service import Service

# processes need to be installed in PYTHON_PATH
from processes.sayhello import SayHello
#from processes.area import Area
from processes.test_grass2 import Test_Grass2
from processes.renerfor_delimitazione import Renerfor_delimitazione
from processes.renerfor_descrittori_test import Renerfor_descrittori

processes = [
    SayHello(),
    Test_Grass2(),
    Renerfor_delimitazione(),
    Renerfor_descrittori(),
]

application = Service(processes)
