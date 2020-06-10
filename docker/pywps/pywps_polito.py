#!/usr/bin/env python3

"""
This is example WSGI application of PyWPS copied from https://github.com/geopython/pywps-flask/blob/master/wsgi/pywps.wsgi
Copyright (c) 2016 - PyWPS PSC
"""

__author__ = "Susanna Grasso"

from pywps.app.Service import Service

# processes need to be installed in PYTHON_PATH
from processes.sleep import Sleep
from processes.ultimate_question import UltimateQuestion
from processes.centroids import Centroids
from processes.sayhello import SayHello
from processes.feature_count import FeatureCount
from processes.buffer import Buffer
from processes.area import Area


processes = [
    FeatureCount(),
    SayHello(),
    Centroids(),
    UltimateQuestion(),
    Sleep(),
    Buffer(),
    Area()
]

application = Service(processes, ['pywps_demo.cfg'])
