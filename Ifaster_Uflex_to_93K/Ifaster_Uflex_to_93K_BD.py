import re
import pandas as pd
from JonathanPyLib_V07 import Search_files, CreateLoopOutputFolder, find_specified_element_iloc_in_dataframe, ReadWriteFiles
from datetime import datetime
import time
import Ifaster_Uflex_to_93K_HD
from Ifaster_Uflex_to_93K_HD import Period, drive_PI, strobe_PO, SymbolDic, CategoryRowIndex, df_UFx_AC_spec


currentDateAndTime = datetime.now()
now = currentDateAndTime.strftime("%Y%m%d_%H%M%S")

Input_path = './Uflex_input'
Output_path = './93K_output'

phs_pattern = r"_UFx_ts_phs_[A-Z]_BD.txt"
phs_obj = re.compile(phs_pattern)



print("="*30+__file__+" Start "+"="*30)
start = time.time()


# df_UFx_AC_spec = pd.read_excel(Input_path+'/ifaster_UFx_AC_spec.xlsx')
# df_UFx_AC_spec = pd.read_excel(Input_path+'/output.xlsx')
# print(df_UFx_AC_spec)


path,files=Search_files(Input_path, '.txt')
CreateLoopOutputFolder(Input_path, Output_path)
BodyRWFile=ReadWriteFiles()

for file in files:
    if phs_obj.findall(file):
        # print(phs_obj.findall(file))
        ll=phs_obj.findall(file)[0][-8]
        phase_alphat = str(ll)
        
        BodyRWFile.ReadFileLines(path[0]+'/'+file)
        ifaster_tsphs_content2 = []
        for line in BodyRWFile.ReadContent:
            ifaster_tsphs_content2.append(line.strip().split('\t'))


        df_ts = pd.DataFrame(ifaster_tsphs_content2)
        TimeSetDic=find_specified_element_iloc_in_dataframe(df_ts, ['Time Set', 'All_Pins','ALLPINS', 'Name'], False)
        
        for i in range(TimeSetDic['Time Set'][0]):
            df_ts=df_ts.drop(i, axis='rows')
        # print(TimeSetDic['ALLPINS'])
        df_ts=df_ts.drop(TimeSetDic['ALLPINS'][0], axis='rows')
        # print(df_ts)
        
        for a in df_ts.index:
            if str(df_ts.loc[a, TimeSetDic['Name'][1]]) == 'None':
                df_ts=df_ts.drop(a, axis='rows')
        # print(df_ts)

        TimeSetDataDic=find_specified_element_iloc_in_dataframe(df_ts, ['Data', 'Return', 'Open'], False)
        
        df_ts_data_unique=df_ts.iloc[TimeSetDataDic['Data'][0]+1:, TimeSetDataDic['Data'][1]].unique()
        df_ts_return_unique=df_ts.iloc[TimeSetDataDic['Return'][0]+1:, TimeSetDataDic['Return'][1]].unique()
        df_ts_open_unique=df_ts.iloc[TimeSetDataDic['Open'][0]+1:, TimeSetDataDic['Open'][1]].unique()
        # print(len(df_ts_unique))
        
        
        datalist = [str(line).strip('=_') for line in df_ts_data_unique if str(line).find('=_')!=-1]
        returnlist = [str(line).strip('=_') for line in df_ts_return_unique if str(line).find('=_')!=-1]
        openlist = [str(line).strip('=_') for line in df_ts_open_unique if str(line).find('=_')!=-1]
        
        totallist = datalist+returnlist+openlist
        # print(totallist,len(totallist))

        if [x for x in totallist if x=='drive_PI']:
            totallist.remove('drive_PI')
        if [x for x in totallist if x=='strobe_PO']:
            totallist.remove('strobe_PO')
        if [x for x in totallist if x=='']:
            totallist.remove('')


        ifaster_93K_timingset_BD = '\nEQNSET 30'+str(ord(phase_alphat)-64)+' \"ATPG_Phase_'+phase_alphat+'\"\n\nSPECS\n\n'+\
                        Period+'{:>49}'.format('[ns]')+'\n'+drive_PI+'{:>47}'.format('[ns]')+'\n'+strobe_PO+'{:>46}'.format('[ns]')+'\n'*3

        for k in totallist:
            ifaster_93K_timingset_BD = ifaster_93K_timingset_BD+'{:<51}'.format(k)+'[ns]\n'
            
        ifaster_93K_timingset_BD+='\n\nEQUATIONS\n\nTIMINGSET 1 \"Phase_'+phase_alphat+'_Set\"\nperiod = Period\n'
        ifaster_93K_timingset_BD += '\nPINS ALLPINS\n' +'{:>23}'.format('d1 = '+drive_PI)+'\n'+'{:>24}'.format('r1 = '+strobe_PO)+'\n'*2
        
        TimeSetAfterDropDic=find_specified_element_iloc_in_dataframe(df_ts, ['Time Set', 'Name'], False)
        
        
        for l in range(TimeSetAfterDropDic['Time Set'][0]+1, df_ts.shape[0]):
            if not df_ts.iloc[l, TimeSetDataDic['Return'][1]]:
                ifaster_93K_timingset_BD+='PINS '+str(df_ts.iloc[l,TimeSetAfterDropDic['Name'][1]])+'\n' +\
                    '{:>14}'.format('d1 = ')+str(df_ts.iloc[l,TimeSetDataDic['Data'][1]]).strip('=_')+'\n'+'{:>14}'.format('r1 = ')+str(df_ts.iloc[l,TimeSetDataDic['Open'][1]]).strip('=_')+'\n'*2
            else:
                ifaster_93K_timingset_BD+='PINS '+str(df_ts.iloc[l,TimeSetAfterDropDic['Name'][1]])+'\n' +\
                    '{:>14}'.format('d1 = ')+str(df_ts.iloc[l,TimeSetDataDic['Data'][1]]).strip('=_')+'\n'+'{:>14}'.format('d2 = ')+str(df_ts.iloc[l,TimeSetDataDic['Return'][1]]).strip('=_')+'\n'*2
                                    
                                    
        ifaster_93K_timingset_BD+='\n\nEQNSET 30'+str(ord(phase_alphat)-64)+' \"ATPG_Phase_'+phase_alphat+'\"\n\nWAVETBL \"ATPG_Phase_'+phase_alphat+'_type\"\n\nCHECK all\n'
                                    

        # print(ifaster_93K_timingset_BD)


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

        all_cat_typ_val = []
        all_cat_min_val = []
        all_cat_max_val = []
        index_list = []
        
        aa = [line for line in df_UFx_AC_spec.iloc[:,SymbolDic['Symbol'][1]]]
        ff = []
        for i in (range(df_UFx_AC_spec.shape[0])):
            if([x for x in totallist if x == df_UFx_AC_spec.iloc[i,SymbolDic['Symbol'][1]]]):
                ff.append(i)
        
        for i in range(len(ff)):
            for j in range(df_UFx_AC_spec.shape[1]):
                if spec_cat.findall(str(df_UFx_AC_spec.iloc[CategoryRowIndex,j])):
                    if(df_UFx_AC_spec.iloc[i,j]):
                        all_cat_typ_val.append(j)
                        all_cat_min_val.append(j+1)
                        all_cat_max_val.append(j+2)
                    
            index_list.append(ff[i])
        
        # print(len(all_cat_typ_val))
        # print(len(all_cat_period))
        
        for k in range(len(all_cat_period)):
            Frequency =  str(round(1/float(all_cat_period_val[k])/10e5))
            Cat_info += '\nSPECSET '+Frequency+' \"ATPG_Phase_'+phase_alphat+'_'+\
                        str('{:1.2f}'.format(float(all_cat_period_val[k])*10e8)).replace('.00', '')+'ns'+all_cat_period[k][-4:-1]+'\"\n\n'+\
                        '# SPECNAME'+' '*35+'*ACTUAL*   *MINIMUM*  *MAXIMUM*  UNITS COMMENT\n'+\
                        '{:<45}'.format(str(Period))+'{:<5}'.format(str('{:1.2f}'.format(float(all_cat_period_val[k])*10e8)))+'{:>33}'.format('[ns]')+'\n'+\
                        '{:<45}'.format(str(drive_PI))+'{:<5}'.format(str('{:1.2f}'.format(float(all_cat_drPI_val[k])*10e8)))+'{:>33}'.format('[ns]')+'\n'+\
                        '{:<45}'.format(str(strobe_PO))+'{:<5}'.format(str('{:1.2f}'.format(float(all_cat_drPO_val[k])*10e8)))+'{:>33}'.format('[ns]')+'\n'*2
            for m in range(len(index_list)):
                Typ_value = float(df_UFx_AC_spec.iloc[index_list[m],all_cat_typ_val[k]])*10e8
                Min_value = float(df_UFx_AC_spec.iloc[index_list[m],all_cat_min_val[k]])*10e8
                Max_value = float(df_UFx_AC_spec.iloc[index_list[m],all_cat_max_val[k]])*10e8

                Cat_info +=\
                '{:<45}'.format(str(df_UFx_AC_spec.iloc[index_list[m],SymbolDic['Symbol'][1]])) + '{:<11}'.format(str('{:1.2f}'.format(Typ_value)).replace('nan', '0.0')) +\
                '{:<11}'.format(str('{:1.2f}'.format(Min_value)).replace('nan', '')) +\
                '{:<12}'.format(str('{:1.2f}'.format(Max_value)).replace('nan', '')) +'{:>4}'.format('[ns]')+'\n'*2
            
            

        # print(Cat_info)

        ifaster_93K_timingset_BD += Cat_info
        file93Kphs='/ifaster_93K_timingset_phase_'+phase_alphat+'_BD'
        BodyRWFile.WriteFile(Output_path+file93Kphs, ifaster_93K_timingset_BD)
        print(file+'-->'+file93Kphs)
        


end = time.time()
print("execuation time: %f s" % (end-start))
print("="*30+__file__+" Complete "+"="*30+"\n")
