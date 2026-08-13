import re
import pandas as pd
from JonathanPyLib_V07 import Search_files, CreateLoopOutputFolder, txt_to_excel, ReadWriteFiles
from datetime import datetime
import time
# from tkinter import filedialog
import sys
import IfasterPingrp_Uflex_to_93K


currentDateAndTime = datetime.now()
now = currentDateAndTime.strftime("%Y%m%d_%H%M%S")

Input_path = './Uflex_input'
Output_path = './93K_output'

phs_pattern = r"_UFx_ts_phs_[A-Z]_HD.txt"
phs_obj = re.compile(phs_pattern)

ACspec_pattern = r"_UFx_AC_spec.txt"
ACspec_obj = re.compile(ACspec_pattern)

print("="*30+__file__+" Start "+"="*30)
start = time.time()


path,files=Search_files(Input_path, '.txt')
CreateLoopOutputFolder(Input_path, Output_path)
for file in files:
    if ACspec_obj.findall(file):
        txt_to_excel(path[0]+'/'+file, path[0]+'/'+file)
        break
        # print(path[0]+'/'+file)
    else:
        continue

# print("Please Select the ifaster UFx AC spec txt file for transfering to excel")
# IfasterUFxACSpecFile=filedialog.askopenfilename(title='Select the ifaster UFx AC spec txt file', filetypes=[('TXT', '.*txt')], initialdir='.')


IfasterUFxACSpecFile=(str(path[0]+'/'+file)).replace('.txt', '.xlsx')
df_UFx_AC_spec = pd.read_excel(IfasterUFxACSpecFile)
# print(df_UFx_AC_spec)

SymbolDic = {}
cat_patn1 = r"Cat_ATPG_\w+_\w+"
spec_cat1 = re.compile(cat_patn1)

for i in range(df_UFx_AC_spec.shape[0]):
    for j in range(df_UFx_AC_spec.shape[1]):
        if [x for x in ['Symbol','Period', 'drive_PI', 'strobe_PO'] if df_UFx_AC_spec.iloc[i,j]==x]:
            # print(f"\"{df_UFx_AC_spec.iloc[i,j]}\""+' '+f"{i,j}")
            SymbolDic[df_UFx_AC_spec.iloc[i,j]] = [i,j]
        elif spec_cat1.match(str(df_UFx_AC_spec.iloc[i,j])):
            CategoryRowIndex = i



Period = df_UFx_AC_spec.iloc[SymbolDic['Period'][0], SymbolDic['Period'][1]]
drive_PI = df_UFx_AC_spec.iloc[SymbolDic['drive_PI'][0], SymbolDic['drive_PI'][1]]
strobe_PO = df_UFx_AC_spec.iloc[SymbolDic['strobe_PO'][0], SymbolDic['strobe_PO'][1]]




HeaderRWFile=ReadWriteFiles()

for file in files:
    if phs_obj.findall(file):
        # print(phs_obj.findall(file))
        ll=phs_obj.findall(file)[0][-8]
        phase_alphat = str(ll)
        
        
        ifaster_93K_timingset_HD = '\nEQNSET 10'+str(ord(phase_alphat)-64)+' \"ATPG_Phase_'+phase_alphat+'\"\n\nSPECS\n\n'+\
                        Period+'{:>49}'.format('[ns]')+'\n'+drive_PI+'{:>47}'.format('[ns]')+'\n'+strobe_PO+'{:>46}'.format('[ns]')+'\n'*4+\
                        'EQUATIONS\n\nTIMINGSET 1 \"Phase_'+phase_alphat+'_Set\"\nperiod = Period\n'
        
        ifaster_93K_timingset_HD = ifaster_93K_timingset_HD +'\nPINS ALLPINS\n' +'{:>23}'.format('d1 = '+drive_PI)+'\n'+'{:>24}'.format('r1 = '+strobe_PO)+'\n'*5+\
                                    'EQNSET 10'+str(ord(phase_alphat)-64)+' \"ATPG_Phase_'+phase_alphat+'\"\n\nWAVETBL \"ATPG_Phase_'+phase_alphat+'_type\"\n\nCHECK all\n\n'
                                    
        # print(ifaster_93K_timingset_HD)
        
        
        cat_patn = r"Cat_ATPG_"+rf'{phase_alphat}'+r"_[\dp]+ns_\w{2}_"
        spec_cat = re.compile(cat_patn)
        
        all_cat_period = []
        all_cat_period_val = []
        all_cat_drPI_val = []
        all_cat_drPO_val = []
        Cat_info = ''

        for i,j in enumerate(range(len(df_UFx_AC_spec.columns))):
            if spec_cat.findall(str(df_UFx_AC_spec.iloc[CategoryRowIndex,j])):
                cat_period=spec_cat.findall(str(df_UFx_AC_spec.iloc[CategoryRowIndex,j]))
                all_cat_period.append(cat_period[0])
                all_cat_period_val.append(df_UFx_AC_spec.iloc[SymbolDic['Period'][0],j])
                all_cat_drPI_val.append(df_UFx_AC_spec.iloc[SymbolDic['drive_PI'][0],j])
                all_cat_drPO_val.append(df_UFx_AC_spec.iloc[SymbolDic['strobe_PO'][0],j])

        for k in range(len(all_cat_period)):
            Frequency =  str(round(1/float(all_cat_period_val[k])/10e5))
            Cat_info += 'SPECSET '+Frequency+' \"ATPG_Phase_'+phase_alphat+'_'+str('{:1.2f}'.format(float(all_cat_period_val[k])*10e8)).replace('.00', '')+'ns'+all_cat_period[k][-4:-1]+'\"\n\n'+\
                        '# SPECNAME                     *ACTUAL*   *MINIMUM*  *MAXIMUM*  UNITS COMMENT\n'+\
                        '{:<31}'.format(str(Period))+'{:<6}'.format(str('{:1.2f}'.format(float(all_cat_period_val[k])*10e8)))+'{:>32}'.format('[ns]')+'\n'+\
                        '{:<31}'.format(str(drive_PI))+'{:<6}'.format(str('{:1.2f}'.format(float(all_cat_drPI_val[k])*10e8)))+'{:>32}'.format('[ns]')+'\n'+\
                        '{:<31}'.format(str(strobe_PO))+'{:<6}'.format(str('{:1.2f}'.format(float(all_cat_drPO_val[k])*10e8)))+'{:>32}'.format('[ns]')+'\n'*4



        # print(Cat_info)

        ifaster_93K_timingset_HD += Cat_info
        file93Kphs='/ifaster_93K_timingset_phase_'+phase_alphat+'_HD'
        # WriteFile(Output_path+file93Kphs, 'utf-8', ifaster_93K_timingset_HD)
        HeaderRWFile.WriteFile(Output_path+file93Kphs, ifaster_93K_timingset_HD)
        print(file+'-->'+file93Kphs)
        

end = time.time()
print("execuation time: %f s" % (end-start))
print("="*30+__file__+" Complete "+"="*30+"\n")