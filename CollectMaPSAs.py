import argparse
import sys, os
import csv
import numpy as np
import pandas as pd
import pickle
from datetime import datetime

from derivative import *
import MakeModulePlots

import warnings
warnings.filterwarnings("ignore")

def get_recent(cmd):

    files = os.popen(cmd).read().split()

    if len(files) < 1:
        print("Error: no files specified")
        return "0"

    # to be added: if a file contains "skipped test" then remove it from the list

    elif len(files) == 1:
        return files[0]

    else:
        maxnbr = 0
        maxidx = -1

        for j, f in enumerate(files):
            numbers_from_string = int(''.join(list(filter(str.isdigit, f))))
            if numbers_from_string > maxnbr:
                maxnbr = numbers_from_string
                maxidx = j
        return files[maxidx]

class MPA:
    """MPA class"""
    def __init__(self, mapsa_name, chip_number, scurves):
        self.mapsa_name = mapsa_name
        self.index = chip_number
        self.directory = '../Results_MPATesting/' + mapsa_name + '/'

        cmd = 'ls '+ self.directory +'log*_'+ str(self.index) +'_*.log'
        self.log_file = get_recent(cmd)

        self.fill_pixels()
        self.add_derivative()

        if scurves:
            print("Saving s-curves")
            self.set_Scurves()
        else:
            self.set_currents()
#            self.set_memerrs()
#            self.set_regerrs()

    def set_currents(self):

        if len(self.log_file) <= 1:
            self.I_ana = -1
            self.I_dig = -1
            self.I_pad = -1
            self.I_tot = -1
            return

        # I_ana
        cmd = "grep P_ana " + self.log_file
        x = os.popen(cmd).read()
        x = x.replace('I= ', 'CUT')
        x = x.replace(' mA', 'CUT')
        y = x.split('CUT')
        self.I_ana = float(y[1])

        # I_dig
        cmd = "grep P_dig " + self.log_file
        x = os.popen(cmd).read()
        x = x.replace('I= ', 'CUT')
        x = x.replace(' mA', 'CUT')
        y = x.split('CUT')
        self.I_dig = float(y[1])

        # I_pad
        cmd = "grep P_pad " + self.log_file
        x = os.popen(cmd).read()
        x = x.replace('I= ', 'CUT')
        x = x.replace(' mA', 'CUT')
        y = x.split('CUT')
        self.I_pad = float(y[1])

        # I_tot
        cmd = "grep Total: " + self.log_file
        x = os.popen(cmd).read()
        x = x.replace('I= ', 'CUT')
        x = x.replace(' mA', 'CUT')
        y = x.split('CUT')
        self.I_tot = float(y[1])

        return

    def set_regerrs(self):

        if len(self.log_file) <= 1:
            self.regerr_peri = -2
            self.regerr_row = -2
            self.regerr_pixel = -2
            return

        # Peri errors
        cmd = "grep 'Total MPA errors:' " + self.log_file
#        if self.mapsa_name == "QP_no27p1" and self.index == 13:
#            cmd = "grep 'Total MPA errors:' /uscms/home/jennetd/nobackup/mapsa-round2/Results_MPATesting/QP_no27p1/log_mpa_test_QP_no27p1_Chip13_2021_03_22_14_12_54.log"

        x = os.popen(cmd).read()
        y = x.split()[-1]
        self.regerr_peri = float(y)

        # Row errors              
        cmd = "grep 'Total row errors:' " + self.log_file
#        if self.mapsa_name == "QP_no27p1" and self.index == 13:
#            cmd = "grep 'Total row errors:' /uscms/home/jennetd/nobackup/mapsa-round2/Results_MPATesting/QP_no27p1/log_mpa_test_QP_no27p1_Chip13_2021_03_22_14_12_54.log"

        x = os.popen(cmd).read()
        y = x.split()[-1]
        self.regerr_row = float(y)

        # Pixel errors              
        cmd = "grep 'Total pixel errors:' " + self.log_file
#        if self.mapsa_name == "QP_no27p1" and self.index == 13:
#            cmd = "grep 'Total pixel errors:' /uscms/home/jennetd/nobackup/mapsa-round2/Results_MPATesting/QP_no27p1/log_mpa_test_QP_no27p1_Chip13_2021_03_22_14_12_54.log"

        x = os.popen(cmd).read()
        y = x.split()[-1]
        self.regerr_pixel = float(y)

        return

    def set_memerrs(self):

        df = pd.DataFrame(index=['1.0V','1.2V'],columns=['error','stuck','I2C','missing'])

        cmd = 'ls '+ self.directory + 'mpa_test_*_'+ str(self.index) + '_*_Mem105_Summary.csv' 
        csvfilename = get_recent(cmd)
        if csvfilename != "0":
            with open(csvfilename, 'r') as f:
                reader = csv.reader(f, delimiter=' ')
                for row in reader:
                    if row[0] == '':
                        continue
                    df['error']['1.0V'] = float(row[0])
                    df['stuck']['1.0V'] = float(row[0])
                    df['I2C']['1.0V'] = float(row[0])
                    df['missing']['1.0V'] = float(row[0])

        cmd = 'ls '+ self.directory + 'mpa_test_*_'+ str(self.index) + '_*_Mem125_Summary.csv'
        csvfilename = get_recent(cmd)
        if csvfilename != "0":
            with open(csvfilename, 'r') as f:
                reader = csv.reader(f, delimiter=' ')
                for row in reader:
                    if row[0] == '':
                        continue
                    df['error']['1.2V'] = float(row[0])
                    df['stuck']['1.2V'] = float(row[0])
                    df['I2C']['1.2V'] = float(row[0])
                    df['missing']['1.2V'] = float(row[0])

        df = df.fillna(value=-2)

        self.memerrs = df
        return

    def fill_pixels(self):

        cmd = 'ls '+ self.directory + 'mpa_test_*_'+ str(self.index) + '_*_pixelalive.csv'
        self.pixels = pd.read_csv(get_recent(cmd),index_col=0,header=0)
        self.pixels.columns = ['pa']

        cmd = 'ls '+ self.directory + 'mpa_test_*_'+str(self.index) + '_*_PostTrim_CAL_CAL_RMS.csv'
        tmp = pd.read_csv(get_recent(cmd),names=['index','value'],header=0)
        self.pixels['CAL_RMS'] = tmp['value']
        self.pixels['CAL_RMS'][abs(self.pixels['CAL_RMS']-2.0)<0.000001] = -1
        self.pixels['CAL_RMS'][self.pixels['pa']<100] = np.nan

        cmd = 'ls '+ self.directory + 'mpa_test_*_'+str(self.index) + '_*_PostTrim_CAL_CAL_Mean.csv'
        tmp = pd.read_csv(get_recent(cmd),names=['index','value'],header=0)
        self.pixels['CAL_Mean'] = tmp['value']
        self.pixels['CAL_Mean'][self.pixels['CAL_RMS']<0] = np.nan
        self.pixels['CAL_Mean'][self.pixels['pa']<100] = np.nan

        cmd = 'ls '+ self.directory + 'mpa_test_*_'+str(self.index) + '_*_PostTrim_THR_THR_RMS.csv'
        tmp = pd.read_csv(get_recent(cmd),names=['index','value'],header=0)
        self.pixels['THR_RMS'] = tmp['value']
        self.pixels['THR_RMS'][abs(self.pixels['THR_RMS']-2.0)<0.000001] = -1
        self.pixels['THR_RMS'][self.pixels['pa']<100] = np.nan

        cmd = 'ls '+ self.directory + 'mpa_test_*_'+str(self.index) + '_*_PostTrim_THR_THR_Mean.csv'
        tmp = pd.read_csv(get_recent(cmd),names=['index','value'],header=0)
        self.pixels['THR_Mean'] = tmp['value']
        self.pixels['THR_Mean'][self.pixels['THR_RMS']<0] = np.nan
        self.pixels['THR_Mean'][self.pixels['pa']<100] = np.nan

        cmd = 'ls '+ self.directory + 'mpa_test_*_'+str(self.index) + '_*_PreTrim_CAL_CAL_RMS.csv'
        tmp = pd.read_csv(get_recent(cmd),names=['index','value'],header=0)
        self.pixels['CAL_RMS_pretrim'] = tmp['value']
        self.pixels['CAL_RMS_pretrim'][abs(self.pixels['CAL_RMS_pretrim']-2.0)<0.00001] = -1
        self.pixels['CAL_RMS_pretrim'][self.pixels['pa']<100] = np.nan

        cmd = 'ls '+ self.directory + 'mpa_test_*_'+str(self.index) + '_*_PreTrim_CAL_CAL_Mean.csv'
        tmp = pd.read_csv(get_recent(cmd),names=['index','value'],header=0)
        self.pixels['CAL_Mean_pretrim'] = tmp['value']
        self.pixels['CAL_Mean_pretrim'][self.pixels['CAL_RMS_pretrim']<0] = np.nan
        self.pixels['CAL_Mean_pretrim'][self.pixels['pa']<100] = np.nan

        cmd = 'ls '+ self.directory + 'mpa_test_*_'+str(self.index) + '_*_PreTrim_THR_THR_RMS.csv'
        tmp = pd.read_csv(get_recent(cmd),names=['index','value'],header=0)
        self.pixels['THR_RMS_pretrim'] = tmp['value']
        self.pixels['THR_RMS_pretrim'][abs(self.pixels['THR_RMS_pretrim']-2.0)<0.000001] = -1
        self.pixels['THR_RMS_pretrim'][self.pixels['pa']<100] = np.nan

        cmd = 'ls '+ self.directory + 'mpa_test_*_'+str(self.index) + '_*_PreTrim_THR_THR_Mean.csv'
        tmp = pd.read_csv(get_recent(cmd),names=['index','value'],header=0)
        self.pixels['THR_Mean_pretrim'] = tmp['value']
        self.pixels['THR_Mean_pretrim'][self.pixels['THR_RMS_pretrim']<0] = np.nan
        self.pixels['THR_Mean_pretrim'][self.pixels['pa']<100] = np.nan

        cmd = 'ls '+ self.directory + 'mpa_test_*_'+str(self.index) + '_*_BumpBonding_Noise_BadBump.csv'
        tmp = pd.read_csv(get_recent(cmd),names=['index','value'],header=0)
        self.pixels['Bump_RMS'] = tmp['value']
        self.pixels['Bump_RMS'][abs(self.pixels['Bump_RMS']-2.0)<0.000001] = -1
        self.pixels['Bump_RMS'][self.pixels['pa']<100] = np.nan

        cmd = 'ls '+ self.directory + 'mpa_test_*_'+str(self.index) + '_*_mask_test.csv'
        tmp = pd.read_csv(get_recent(cmd),names=['index','value'],header=0)
        self.pixels['mask'] = tmp['value']
#        self.pixels['mask'][self.pixels['pa']<100] = np.nan

#        cmd = 'ls '+ self.directory + 'mpa_test_*_'+str(self.index) + '_*_Trim_trimbits.csv'
#        tmp = pd.read_csv(get_recent(cmd),names=['index','value'],header=0)
#        self.pixels['trimbits'] = tmp['value']

        return

    def add_derivative(self):
        
        cmd = 'ls '+ self.directory + 'mpa_test_*_'+str(self.index) +'_*_PostTrim_CAL_CAL.csv'
        CALS = pd.read_csv(get_recent(cmd),index_col=0,header=0)
        cmd = 'ls '+ self.directory + 'mpa_test_*_'+str(self.index) +'_*_PostTrim_THR_THR.csv'
        THRS = pd.read_csv(get_recent(cmd),index_col=0,header=0)

        cmd = 'ls '+ self.directory + 'mpa_test_*_'+str(self.index) +'_*_PreTrim_CAL_CAL.csv'
        CALS_pretrim = pd.read_csv(get_recent(cmd),index_col=0,header=0)
        cmd = 'ls '+ self.directory + 'mpa_test_*_'+str(self.index) +'_*_PreTrim_THR_THR.csv'
        THRS_pretrim = pd.read_csv(get_recent(cmd),index_col=0,header=0)

        cmd = 'ls '+ self.directory + 'mpa_test_*_'+str(self.index) +'_*_BumpBonding_SCurve_BadBump.csv'
        BumpS = pd.read_csv(get_recent(cmd),index_col=0,header=0)

        t1 = datetime.now()
        mean, sigma = derivative_THR(THRS_pretrim)
        self.pixels['THR_Mean_pretrim_DER'] = mean
        self.pixels['THR_RMS_pretrim_DER'] = sigma
#        print('THR_pretrim',(datetime.now()-t1).total_seconds())

        t1 = datetime.now()
        mean, sigma = derivative_THR(THRS)
        self.pixels['THR_Mean_DER'] = mean
        self.pixels['THR_RMS_DER'] = sigma
#        print('THR_posttrim',(datetime.now()-t1).total_seconds())

        t1 = datetime.now()
        mean, sigma = derivative_CAL(CALS_pretrim)
        self.pixels['CAL_Mean_pretrim_DER'] = mean
        self.pixels['CAL_RMS_pretrim_DER'] = sigma
#        print('CAL_pretrim',(datetime.now()-t1).total_seconds())

        t1 = datetime.now()
        mean, sigma = derivative_CAL(CALS)
        self.pixels['CAL_Mean_DER'] = mean
        self.pixels['CAL_RMS_DER'] = sigma
#        print('CAL_posttrim',(datetime.now()-t1).total_seconds())

        t1 = datetime.now()
        mean, sigma = derivative_CAL(BumpS)
        self.pixels['Bump_Mean_DER'] = mean
        self.pixels['Bump_RMS_DER'] = sigma
#        print('Bump',(datetime.now()-t1).total_seconds())

        return

    # S curves
    def set_Scurves(self):

        cmd = 'ls '+ self.directory + 'mpa_test_*_'+str(self.index) +'_*_PostTrim_CAL_CAL.csv'
        self.CALS = pd.read_csv(get_recent(cmd),index_col=0,header=0)
        cmd = 'ls '+ self.directory + 'mpa_test_*_'+str(self.index) +'_*_PostTrim_THR_THR.csv'
        self.THRS = pd.read_csv(get_recent(cmd),index_col=0,header=0)

        cmd = 'ls '+ self.directory + 'mpa_test_*_'+str(self.index) +'_*_PreTrim_CAL_CAL.csv'
        self.CALS_pretrim = pd.read_csv(get_recent(cmd),index_col=0,header=0)
        cmd = 'ls '+ self.directory + 'mpa_test_*_'+str(self.index) +'_*_PreTrim_THR_THR.csv'
        self.THRS_pretrim = pd.read_csv(get_recent(cmd),index_col=0,header=0)

        cmd = 'ls '+ self.directory + 'mpa_test_*_'+str(self.index) +'_*_BumpBonding_SCurve_BadBump.csv'
        self.BumpS = pd.read_csv(get_recent(cmd),index_col=0,header=0)
        
        return

class MaPSA:
    """MaPSA class"""
    def __init__(self, name, label, scurves=False):

        # Set some properties
        self.name = name
        self.label = label
        self.directory = '../Results_MPATesting/' + self.name + '/'
        self.mpa_chips = []
        self.set_IV()

        # Add MPAs
        for i in range(1,17):
            chip = MPA(self.name,i,scurves)
            self.add_mpa(chip)
        
        # Pickle it
        print("Pickling MaPSA " + self.name)
        mapsafile = open('pickles/'+self.label+'.pkl', 'wb')
        pickle.dump(self, mapsafile, protocol=-1)
        mapsafile.close()

        MakeModulePlots.PlotAllPlotsModulesAutomated(self.name,mapsaname=self.label,show_plot=False,save_plot=True)
        
    def add_mpa(self, mpa):
        if(len(self.mpa_chips) >= 16):
            print("Error: MaPSA already has 16 associated MPAs")
            return

        self.mpa_chips += [mpa]
        print("Constructed " + self.name + " Chip " + str(len(self.mpa_chips)))

        return

    def set_IV(self):
        csvfilename = self.directory+'IVScan_'+self.name+'.csv'
        Vpoints = []
        Ipoints = []
        with open(csvfilename, 'r') as f:
            reader = csv.reader(f, delimiter=',')
            for row in reader:

                if row[0] == '':
                    continue

                if(float(row[-1]) !=0 ):
                    Vpoints += [float(row[len(row)-2])]
                    Ipoints += [float(row[-1])]
                else:
                    Vpoints += [float(row[len(row)-4])]
                    Ipoints += [float(row[len(row)-3])]
                    
        df = pd.DataFrame()
        df["V"] = Vpoints
        df["I"] = Ipoints
        self.IV = df

        return 

def main():

    parser = argparse.ArgumentParser(description='MaPSA summary plots')
    parser.add_argument('-n','--name',nargs='+',help='name of output directory')
    parser.add_argument('-f','--files',nargs='+',help='list of text files containing names of MaPSAs to process')
    args = parser.parse_args()

    mapsa_names = []
    mapsa_labels = []
    mapsas = []
    
    for f1 in args.files:
        print('Reading MaPSA names from ' + f1)
        with open(f1) as f:
            reader = csv.reader(f,delimiter=' ')
            mapsa_info = [row for row in reader]
            mapsa_names = [row[0] for row in mapsa_info]
            mapsa_labels = [row[1] for row in mapsa_info]
    print(mapsa_labels)

    scurves = True

    for i in range(len(mapsa_names)):

        # Read MaPSA object from file, if available
        fname = 'pickles/'+mapsa_labels[i]+'.pkl'
        if os.path.isfile(fname):
            print("Loading MaPSA " + mapsa_labels[i])
            mapsa = pickle.load(open(fname,'rb'))
        else: # Create it
            mapsa = MaPSA(mapsa_names[i],mapsa_labels[i],scurves)

        mapsas += [mapsa]

    name = args.name[0]

if __name__ == "__main__":
    main()
