import re
import pandas as pd
from JonathanPyLib_V07 import Search_files, CreateLoopOutputFolder, find_specified_element_iloc_in_dataframe, ReadWriteFiles
from datetime import datetime
import time


currentDateAndTime = datetime.now()
now = currentDateAndTime.strftime("%Y%m%d_%H%M%S")

Input_path = './Uflex_input'
Output_path = './93K_output'

re_pingrp_pattern = r"_UFx_pin_grp_\w+.txt"
regex_pingrp = re.compile(re_pingrp_pattern)



print("="*30+__file__+" Start "+"="*30)
start = time.time()

PinGrpFileRW = ReadWriteFiles()

path,files=Search_files(Input_path, '.txt')
CreateLoopOutputFolder(Input_path, Output_path)

for file in files:
    if regex_pingrp.findall(file):
        PinGrpFileRW.ReadFileLines(path[0]+'/'+file)
        
        ifaster_pingrp_content2 = []
        for line in PinGrpFileRW.ReadContent:
            ifaster_pingrp_content2.append(line.strip().split('\t'))

        df_IfasterPinGrp = pd.DataFrame(ifaster_pingrp_content2)
        ElementIdxDic=find_specified_element_iloc_in_dataframe(df_IfasterPinGrp, ['Group Name', 'Pin Name'], False)
        
        for i,j in enumerate(range(len(df_IfasterPinGrp.columns))):
            GroupName=df_IfasterPinGrp.iloc[ElementIdxDic['Group Name'][0]+1:, ElementIdxDic['Group Name'][1]].unique()
        
        dic_grp_pin_name = {}
        ouput93Kpingrp=''
        for item in GroupName:
            dic_grp_pin_name_list = []
            for i,j in enumerate(range(df_IfasterPinGrp.shape[0])):
                if(item==df_IfasterPinGrp.iloc[i, ElementIdxDic['Group Name'][1]]):
                    dic_grp_pin_name_list.append(df_IfasterPinGrp.iloc[i, ElementIdxDic['Pin Name'][1]])
            dic_grp_pin_name[item]=dic_grp_pin_name_list
            if(item[1]=='I'):
                ouput93Kpingrp += 'DFGP I,('+str(dic_grp_pin_name[item]).strip('[').strip(']').replace('\'', '').replace(' ', '')+'),('+item+')\n'
            else:
                ouput93Kpingrp += 'DFGP O,('+str(dic_grp_pin_name[item]).strip('[').strip(']').replace('\'', '').replace(' ', '')+'),('+item+')\n'
        file93Kpingrp=str(file).replace('_UFx_', '_93K_')
        PinGrpFileRW.WriteFile(Output_path+'/'+file93Kpingrp.strip('.txt'), ouput93Kpingrp)
        print(file+'-->'+file93Kpingrp)
            


end = time.time()
print("execuation time: %f s" % (end-start))
print("="*30+__file__+" Complete "+"="*30+"\n")