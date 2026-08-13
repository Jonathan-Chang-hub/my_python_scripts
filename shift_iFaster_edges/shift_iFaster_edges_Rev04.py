import numpy as np
import io
import sys
from openpyxl import Workbook
import pandas as pd
from JonathanPyLib_V11 import *

'''
Rev = 04
'''

InputFolder = './input'
OutputFolder = './output'

if not os.path.exists(OutputFolder):
    os.makedirs(OutputFolder)


def shift_iFaster_edges_93K():
    
    CreateLoopOutputFolder(InputFolder, OutputFolder)

    paths, files=Search_files(InputFolder, '')
    MinValueExcel = ''
    OriginPath = ''

    SPECNAME_PATTERN = re.compile(r'# SPECNAME\s+\*ACTUAL\*\s+\*MINIMUM\*\s+\*MAXIMUM\*\s+UNITS COMMENT')
    
    for path, file in zip(paths, files):
        
        if(OriginPath!=path):
            MinValueExcel=create_excel('MinValue', 'MinVal', str(path).replace(f'{InputFolder}', f'{OutputFolder}'))
            OriginPath = path
        
        file_name = path+'/'+file
        RW_iFaster_file =ReadWriteFiles()
        RW_iFaster_file.ReadFileLines(file_name)
        dicMin = {}
        longestParamName = 0
        EnableParameters=False
        for line in RW_iFaster_file.ReadContent:   
            global SpecSetNum
            # print(line)
            if (re.search(r'^\s*SPECSET\s+(\d+)', line)):
                SpecSetData = re.search(r'^\s*SPECSET\s+(?P<SpecSetNum>\d+)\s*\"*(?P<SpecSetName>[\w \.]*)\"*', line)
                SpecSetNum  = SpecSetData.group('SpecSetNum')
                SpecSetName = SpecSetData.group('SpecSetName') if SpecSetData.group('SpecSetName') else ''
                #d print('found SPECSET', SpecSetNum, SpecSetName)
                EnableParameters = True
                dicMin[SpecSetName] = 0
                
            elif (EnableParameters and re.search(r'^\s*(?P<ParameterName>\w+)\s+', line)):
                param_name = re.search(r'^\s*(?P<ParameterName>\w+)\s+', line).group('ParameterName')
                longestParamName = max(longestParamName, len(param_name))
                ParamData = re.search(r'^\s*(?P<SPECNAME>\w+)\s+(?P<ACTUAL>[-\d\.]+)\s+(?P<MINIMUM>[-\d\.]*)\s*(?P<MAXIMUM>[-\d\.]*)\s*\[(?P<UNITS>\w*)\]', line)
                if ParamData.group('ACTUAL'): 
                    MinValue = ParamData.group('ACTUAL')
                    # print(MinValue)
                    if(dicMin[SpecSetName]>float(MinValue)):
                        dicMin[SpecSetName]=float(MinValue)
        
        SummaryWb = openpyxl.load_workbook(MinValueExcel)
        ws = SummaryWb['MinVal']
        print('\n'+path+'\\'+file)
        for key, value in dicMin.items():  
            print("{:<30}".format(key), 'Min:'+str(value))
            ws.append([key, value])
        SummaryWb.save(MinValueExcel)
       
        EnableParameters=False
        for i, line in enumerate(RW_iFaster_file.ReadContent):
            
            if (re.search(r'^\s*SPECSET\s+(\d+)', line)):
                SpecSetData = re.search(r'^\s*SPECSET\s+(?P<SpecSetNum>\d+)\s*\"*(?P<SpecSetName>[\w \.]*)\"*', line)
                SpecSetNum  = SpecSetData.group('SpecSetNum')
                SpecSetName = SpecSetData.group('SpecSetName') if SpecSetData.group('SpecSetName') else ''
                EnableParameters = True

            elif (re.search(SPECNAME_PATTERN, line)):
                splitContent = re.split(r'(?<!#) ', RW_iFaster_file.ReadContent[i])
                splitContent = [x for x in splitContent if x != '']
                RW_iFaster_file.ReadContent[i] = (
                                        f'{splitContent[0]:<{longestParamName+1}}'
                                        f'{splitContent[1]:<11}'
                                        f'{splitContent[2]:<11}'
                                        f'{splitContent[3]:<11}'
                                        f'{splitContent[4]:<6}'
                                        f'{splitContent[5]}'
                                    ).strip(' ')
            
            elif (EnableParameters and re.search(r'^\s*(?P<ParameterName>\w+)\s+', line) and dicMin[SpecSetName]<=0):
                if (re.match(r'Period', line)):
                    splitContent = RW_iFaster_file.ReadContent[i].split(' ')
                    splitContent = [x for x in splitContent if x != '']
                    RW_iFaster_file.ReadContent[i] = (
                                            f'{splitContent[0]:<{longestParamName+1}}'
                                            f'{splitContent[1]:<33}'
                                            f'{splitContent[2]:<11}'
                                        ).strip(' ')
                else:
                    ParamData = re.search(r'^\s*(?P<SPECNAME>\w+)\s+(?P<ACTUAL>[-\d\.]+)\s+(?P<MINIMUM>[-\d\.]*)\s*(?P<MAXIMUM>[-\d\.]*)\s*\[(?P<UNITS>\w*)\]', line)
                    
                    OriginTypValue      = float(ParamData.group('ACTUAL').strip())
                    OriginMinValue      = float(ParamData.group('MINIMUM').strip()) if ParamData.group('MINIMUM') else ''
                    OriginMaxValue      = float(ParamData.group('MAXIMUM').strip()) if ParamData.group('MAXIMUM') else ''

                    ShiftTypValue = OriginTypValue - dicMin[SpecSetName]
                    # ShiftMinValue = OriginMinValue - dicMin[SpecSetName] if ParamData.group('MINIMUM') else ''
                    # ShiftMaxValue = OriginMaxValue - dicMin[SpecSetName] if ParamData.group('MAXIMUM') else ''
                    
                    # print("{:.2f}".format(ShiftTypValue), "{:.2f}".format(ShiftMinValue) if ParamData.group('MINIMUM') else '', \
                    #       "{:.2f}".format(ShiftMaxValue) if ParamData.group('MAXIMUM') else '')
                    
                    splitContent = RW_iFaster_file.ReadContent[i].split(' ')
                    splitContent = [x for x in splitContent if x != '']
                    # print(len(splitContent), line)
                    
                    splitContent[1] = splitContent[1].replace(splitContent[1], str("{:.2f}".format(ShiftTypValue)))
                    
                    if len(splitContent) >= 5: # there are min & max values defined
                        splitContent[2] = splitContent[2].replace(splitContent[2], str("{:.2f}".format(ShiftTypValue)))
                        splitContent[3] = splitContent[3].replace(splitContent[3], str("{:.2f}".format(ShiftTypValue)))
                    
                    if len(splitContent) == 6:
                        SpecName, Actual, Minimum, Maximum, Units, Comment = splitContent
                    elif len(splitContent) == 5:
                        SpecName, Actual, Minimum, Maximum, Units = splitContent
                        Comment = ''
                    elif len(splitContent) == 4:
                        SpecName, Actual, Units, Comment = splitContent
                        Minimum = Maximum = ''
                    elif len(splitContent) == 3:
                        SpecName, Actual, Units = splitContent
                        Minimum = Maximum = ''
                        Comment = ''
                    else:
                        raise ValueError(
                            f'Unexpected number of columns ({len(splitContent)}): '
                            f'{RW_iFaster_file.ReadContent[i]}'
                        )

                    RW_iFaster_file.ReadContent[i] = (
                        f'{SpecName:<{longestParamName+1}}'
                        f'{Actual:<11}'
                        f'{Minimum:<11}'
                        f'{Maximum:<11}'
                        f'{Units:<6}'
                        f'{Comment}'
                    ).strip(' ')

        RW_iFaster_file.WriteFileLines(str(path).replace(f'{InputFolder}', f'{OutputFolder}')+'/'+file+'_shift', RW_iFaster_file.ReadContent)


class shift_iFaster_edges_UFx():
    
    def __init__(self, AC_spec_file:str):
        self.AcSpecDataStruct=makeNestedStruct(3, list)
        self.AcSpecMinValStruct=makeNestedStruct(1, float)
        self.AC_specRW = ReadWriteFiles()
        self.AC_specRW.ReadFileLines(AC_spec_file)
        self.SymbolDetectFlag=False
        self.StructCreateFlag=False
        self.categorys = []
        self.iFasterParameters = []
        self.ParamName = ''
        
        OutputExcelFolder = ''
        AC_spec_file_list = AC_spec_file.split('/')
        self.MinValueExcelName = AC_spec_file_list[-1].rsplit('.', 1)[0]
        for i in range(len(AC_spec_file_list)-1):
            OutputExcelFolder += AC_spec_file_list[i]+'/'
        self.MinValueExcel=create_excel(self.MinValueExcelName+'_MinVal', self.MinValueExcelName, OutputExcelFolder.replace(f'{InputFolder}', f'{OutputFolder}'))

        print(AC_spec_file)
        self.get_MinNegativeVal()
        self.shift_NegativeVal(AC_spec_file)
    
    def detect_keyWord(self, items:list, keyword:str):
        if([x for x in items if keyword in items]):
            return True
    
    def get_MinNegativeVal(self):
        for line in self.AC_specRW.ReadContent:
            LineElements = line.strip('\n').split('\t')
            LineElements.pop()
            
            if(self.detect_keyWord(LineElements, 'Selector')):
                for LineElement in LineElements:
                    if(re.match(r'Cat_', LineElement, re.IGNORECASE)):
                        self.AcSpecDataStruct[LineElement]
                        self.categorys.append(LineElement)
            
            if(self.detect_keyWord(LineElements, 'Symbol')):
                self.SymbolDetectFlag = True
                continue
            
            if(self.detect_keyWord(LineElements, 'Period')):
                continue
            
            if(self.SymbolDetectFlag):
                if(LineElements[0]==''):
                    LineElements.pop(0)
                ParamName = LineElements[0]
                self.iFasterParameters.append(ParamName)
                
                ValList=LineElements
                del ValList[0 : ValList.index('Sel0')+2]
                i=0
                for category in self.categorys:
                    self.AcSpecDataStruct[category][ParamName]['Typ']=ValList[3*i]
                    self.AcSpecDataStruct[category][ParamName]['Min']=ValList[3*i+1]
                    self.AcSpecDataStruct[category][ParamName]['Max']=ValList[3*i+2]
                    i+=1
                # break
        
        SummaryWb = openpyxl.load_workbook(self.MinValueExcel)
        ws = SummaryWb[self.MinValueExcelName]
        ws.append(['Category', 'Parameter','Min Negative Value'])
        print("{:<31}".format("category"), "{:<45}".format("parammeter"), "{:^5}".format("symbol"), "{:>10}".format("val"))
        for category in self.AcSpecDataStruct:
            MinVal = 0.0
            for parammeter in self.iFasterParameters:
                if (parammeter != 'Period'):
                    for symbol in ['Typ', 'Min', 'Max']:
                        strval = self.AcSpecDataStruct[category][parammeter][symbol]
                        if(strval != ''):
                            val=float(strval)
                            if(isinstance(val, float)):
                                if(val<MinVal and val<0):
                                    MinVal = val
                                    self.AcSpecMinValStruct[category] = MinVal
                                    ws.append([category, parammeter, MinVal])
                                    print("{:<31}".format(category), "{:<45}".format(parammeter), "{:^5}".format(symbol), "{:>10}".format(val))
        self.SymbolDetectFlag=False

        SummaryWb.save(self.MinValueExcel)

            
    def shift_NegativeVal(self, AC_spec_file:str):
        
        for j in range(len(self.AC_specRW.ReadContent)):
            line = self.AC_specRW.ReadContent[j]
            LineElements = line.split('\t')
            
            if(self.detect_keyWord(LineElements, 'Symbol')):
                self.SymbolDetectFlag = True
                continue
            
            if(self.detect_keyWord(LineElements, 'Period')):
                continue
            
            if(self.SymbolDetectFlag):
                Selindex=LineElements.index('Sel0')
                k = Selindex+2
                for category in self.AcSpecDataStruct:
                    if(self.AcSpecMinValStruct[category] and self.AcSpecMinValStruct[category]<0):
                        if(LineElements[k] != ''):
                            val=float(LineElements[k])
                            val += abs(self.AcSpecMinValStruct[category])
                            LineElements[k] = val
                        if(LineElements[k+1] != ''):
                            val=float(LineElements[k+1])
                            val += abs(self.AcSpecMinValStruct[category])
                            LineElements[k+1] = val
                        if(LineElements[k+2] != ''):
                            val=float(LineElements[k+2])
                            val += abs(self.AcSpecMinValStruct[category])
                            LineElements[k+2] = val
                        # print(category, abs(self.AcSpecMinValStruct[category]), k)
                    k+=3
                ShiftReadContent = ''
                for k in range(len(LineElements)):
                    if(k<len(LineElements)-1):
                        ShiftReadContent += str(LineElements[k])+'	'
                    elif(k==len(LineElements)-1):
                        ShiftReadContent += str(LineElements[k])
                        
                self.AC_specRW.ReadContent[j] = ShiftReadContent
                
        self.AC_specRW.WriteFileLines(AC_spec_file.replace(f"{InputFolder}", f"{OutputFolder}").replace('.txt', '_shift.txt'), self.AC_specRW.ReadContent)

    
if __name__=='__main__':
    
    def main():
        print("choose your iFaster format!")
        print("1:93K    2:UFx    (type 1 or 2)")
        iFasterFormat=input()
        
        if(iFasterFormat == '1'):
            shift_iFaster_edges_93K()
        elif(iFasterFormat == '2'):
            paths, files = Search_files(InputFolder, '')
            CreateLoopOutputFolder(InputFolder, OutputFolder)
            for path, file in zip(paths, files):
                if(re.match(r'ifaster_UFx_AC', file, re.IGNORECASE)):
                    shift_iFaster_edges_UFx(path+'/'+file)
                    print('*'*20+' \"' + file + '\" shifted '+'*'*20 + '\n')
        else:
            print("unkown, please type 1 or 2")
            main()
    main()
    




