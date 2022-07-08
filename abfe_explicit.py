from __future__ import division

from datetime import datetime
import sys
import time
import random

from openmm.app import *
from openmm import *
from openmm.unit import *

from openmm_async_re import openmm_job_AmberABFE

if __name__ == '__main__':

    # Parse arguments:
    usage = "%prog <ConfigFile>"

    if len(sys.argv) != 2:
        print("Please specify ONE input file")
        sys.exit(1)

    commandFile = sys.argv[1]

    print("")
    print("=======================================")
    print("AToM ABFE Asynchronous Replica Exchange")
    print("=======================================")
    print("")
    print("Started at: " + str(time.asctime()))
    print("Input file:", commandFile)
    print("")
    sys.stdout.flush()

    rx = openmm_job_AmberABFE(commandFile, options=None)

    rx.setupJob()

    rx.scheduleJobs()
