import re
import time
import openpyxl
from openpyxl.styles import Font
import pandas as pd
from JonathanPyLib_V14 import *
import csv

Ver = '26.07.09'

INPUT_FOLDER = './input/'
OUTPUT_FOLDER = './output/'
SPACE_NUMBER:int = 4

class TimingSet():
    def __init__(self, timing:str, format:str, drive:str, _return:str):
        self.timing = timing
        self.format = format
        self.drive = drive
        self._return = _return

class PadsWithTiming():
    def __init__(self, pads:list, timing:str, direction:str):
        self.pads = pads
        self.timing = timing
        self.direction = direction
        
class Timing():
    def __init__(self, ts:str, cycle:int):
        self.ts = ts
        self.cycle = cycle
        self.TimingSet = []
        
        
class TstPattern():
    
    def __init__(self, tstfile):
        self.tstfile = tstfile
        self.tst_name = str(tstfile.split('/')[-1])
        self.tst_RW = ReadWriteFiles()
        self.tst_RW_multiline = ReadWriteFiles()
        self.extention = os.path.splitext(str(tstfile.split('/')[-1]))[1]
        self.timing_set = []
        self.pads_with_timing = []
        self.timing = []
        
        
        if self.extention == '.gz':
            self.tst_RW.read_gz_lines(self.tstfile, 'rt')       # read tst.gz or .tst file content
            self.tst_RW_multiline.read_gz(self.tstfile, 'rt')
        elif self.extention == '.tst':
            self.tst_RW.read_file_lines(self.tstfile)
            self.tst_RW_multiline.read_file(self.tstfile)
        
        self.tst_content = self.tst_RW.read_content
        
        self.tst_assign_pads = []                           # ASSIGN pads in tst
        self.assign_pads_number = 0                         # ASSIGN pads number in tst
        self.enable_ts = []
        self.all_ts = []
        self.alias = {}                                     # self.alias['/* 1 */'] = ['X', 'X', '0', 'H', ...]
        self.tst_dataframe = pd.DataFrame()                 # row: vector number of tst, column: ASSIGN pads
        self.tst_depth = 0
        
        
    def get_assign_pads(self):
        assign_pad_string = FindReMultiline(r"ASSIGN (.+?);$", self.tst_RW_multiline.read_content)
        pads=str(assign_pad_string[0]).replace(' ', '').replace('\n', '')
        self.tst_assign_pads = pads.split(',')
        self.assign_pads_number = len(self.tst_assign_pads)
        
        return self.tst_assign_pads
        

    def get_enable_ts(self):
        self.enable_ts = FindReMultiline(r"ENABLE\s+(.+?);$", self.tst_RW_multiline.read_content)
        self.enable_ts = unique_list(self.enable_ts)
        
        return self.enable_ts
    
    
    def get_all_ts(self):
        self.all_ts = FindReMultiline(r"TIMING\s+(.+?) ;$", self.tst_RW_multiline.read_content)
        self.all_ts = unique_list(self.all_ts)
        
        return self.all_ts
        
        
    def extract_alias(self):
        cycle=0
        for line in self.tst_content:
            if(re.match(r"\w+;\s\/\*\s\d+\s\*\/", line)):
                separate_aliases = list(line.split(';')[0])
                vec_in_tst = line.split(';')[1]
                matched_vector_num = re.search(r"\/\* (?P<vec_num>\d+) \*\/", vec_in_tst)
                vec_key = matched_vector_num.group('vec_num')
                
                self.alias[int(vec_key)] = separate_aliases
                cycle = int(vec_key)
                
                # if(cycle==10000):
                #     break
        self.tst_depth = cycle
        
        return self.alias
        
    
    def create_pad_alias_dataframe(self):
        self.extract_alias()
        data = pd.DataFrame()
        for pad_index in range(0, len(self.tst_assign_pads)):
            col_list_alias = []
            for vector in self.alias:
                col_list_alias.append(self.alias[vector][pad_index])
            Ser = pd.Series(col_list_alias, index = range(1, len(self.alias)+1))    #Ser1 = pd.Series(range(0,7), index = range(100, 107))
            data_each = pd.DataFrame({ f'{self.tst_assign_pads[pad_index]}' : Ser }) 
            data = pd.concat([data, data_each], axis=1)
            
            process_percent = pad_index/(len(self.tst_assign_pads)-1)
            show_progress_percent("Building \""+ self.tst_name + "\" content dataframe -> ", process_percent)
        self.tst_dataframe = data
        print()
        
        return self.tst_dataframe
    
    def extract_input_timing(self):
        input_reg = re.compile(r"INPUT\(([\d,]+)\)\s+(.+?);", re.MULTILINE | re.DOTALL)
        bidirect_reg = re.compile(r"BIDIRECT\(([\d,]+)\)\s+(.+?);", re.MULTILINE | re.DOTALL)
        output_reg = re.compile(r"OUTPUT\(([\d,]+)\)\s+(.+?);", re.MULTILINE | re.DOTALL)

        input_timing = input_reg.findall(self.tst_RW_multiline.read_content)
        # print("Input Timing: ", input_timing[0][1] if len(input_timing) > 0 else "None")
        
        if len(input_timing) > 0:
            for timing in input_timing:
                pads = timing[1].replace('\n', '').replace(' ', '').replace('\t', '').split(',')
                self.pads_with_timing.append(PadsWithTiming(pads, timing[0], 'INPUT'))
        
        bidirect_timing = bidirect_reg.findall(self.tst_RW_multiline.read_content)
        if len(bidirect_timing) > 0:
            for timing in bidirect_timing:
                pads = timing[1].replace('\n', '').replace(' ', '').replace('\t', '').split(',')
                self.pads_with_timing.append(PadsWithTiming(pads, timing[0], 'BIDIRECT'))
        
        output_timing = output_reg.findall(self.tst_RW_multiline.read_content)
        if len(output_timing) > 0:
            for timing in output_timing:
                pads = timing[1].replace('\n', '').replace(' ', '').replace('\t', '').split(',')
                self.pads_with_timing.append(PadsWithTiming(pads, timing[0], 'OUTPUT'))
        
        print("Pads with Timing:")
        for p in self.pads_with_timing:
            print(f"  {p.direction}: timing={p.timing}, pads={', '.join(p.pads)}")

        return input_timing, bidirect_timing, output_timing


def main():
    print('='*50 + " Processing Start " + '='*50)
    start = time.time()
    
    CreateLoopOutputFolder(INPUT_FOLDER, OUTPUT_FOLDER)
    paths, files = Search_files(INPUT_FOLDER, ['.gz', '.tst'])
    
    global file_index
    file_index = 0
    # for path, file in zip(paths, files):
    #     print(">>> " + file)
    #     TstPattern(path + '/' + file)
    
    minority = TstPattern('./input/ATPG_STUCK_PA_comp_chain_noram_saf_no_setup_1_20230602_v0.tst')
    print(minority.get_assign_pads())
    alias_dic = minority.extract_alias()
    # input_timing, bidirect_timing, output_timing = minority.extract_input_timing()
    # print(input_timing)
    # print(bidirect_timing)
    # print(output_timing)

    with open('people_pandas.csv', mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow([''])
        writer.writerow([''])

    df = minority.create_pad_alias_dataframe()
    print(df)
    print(minority.tst_depth)
    
    df.to_csv('people_pandas.csv', index=False, mode = 'a', encoding='utf-8')
    
    end = time.time()
    result=(divmod(end-start, 60))
    
    print(f"execuation time: {result[0]} m " + '{:.2f}'.format(result[1]) + "s")
    print('='*50 + " Processing Completed " + '='*50)

if __name__ == '__main__':
    main()