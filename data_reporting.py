import os.path as osp
import sys
import time

import daetools.pyDAE as dae
from daetools.pyDAE.data_reporters import daeMatlabMATFileDataReporter
import scipy.io as sio


class MyMATDataReporter(daeMatlabMATFileDataReporter):
    """
    See Source code for pyDataReporting.daeMatlabMATFileDataReporter
    """
    def WriteDataToFile(self):
        mdict = {}
        for var in self.Process.Variables:
            # Remove the model name part of the output key for
            # brevity.
            dkeybase = var.Name[var.Name.index(".")+1:]
            # Remove dots from variable keys. This enables the mat
            # file to be read by, e.g., MATLAB.
            dkeybase = dkeybase.replace(".", "_")
            mdict[dkeybase] = var.Values
            mdict[dkeybase + '_times'] = var.TimeValues
        sio.savemat(self.ConnectionString,
                    mdict, appendmat=False, format='5',
                    long_field_names=False, do_compression=False,
                    oned_as='row')


def setupDataReporters(simulation, outdir):
    """
    Create daeDelegateDataReporter and add data reporters:
     - daeMatlabMATFileDataReporter
    """
    datareporter = dae.daeDelegateDataReporter()
    simulation.dr = MyMATDataReporter()
    datareporter.AddDataReporter(simulation.dr)
    # Connect data reporters
    simName = simulation.m.Name + time.strftime(" [%d.%m.%Y %H:%M:%S]",
                                                time.localtime())
    matDataName = "output_data.mat"
    matfilename = osp.join(outdir, matDataName)
    if not simulation.dr.Connect(matfilename, simName):
        sys.exit()
    # a hack to make compatible with pre/post r526 daetools
    try:
        simulation.dr.ConnectionString = simulation.dr.ConnectString
    except AttributeError:
        pass
    return datareporter
