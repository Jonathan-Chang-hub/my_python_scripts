from openpyxl.styles import Font
from JonathanPyLib_V14 import *
import csv
import time


class UnoPattern():
    
    def __init__(self, unofile):
        self.unofile = unofile
        self.uno_name = str(unofile.split('/')[-1])
        self.uno_RW = ReadWriteFiles()
        self.uno_RW_multiline = ReadWriteFiles()
        self.extention = os.path.splitext(str(unofile.split('/')[-1]))[1]
        
        self.uno_RW.read_file_lines(self.unofile)
        self.uno_RW_multiline.read_file(self.unofile)
        
        self.uno_content_lines = self.uno_RW.read_content
        
        self.PinList_pins = []                          
        self.PinList_number = 0                         
        self.SubsetPins_pins = []                           
        self.SubsetPins_number = 0                        
        self.waveform_ref = []
        self.alias = {}                                     # self.alias['1'] = ['X', 'X', '0', 'H', ...]
        self.uno_dataframe = pd.DataFrame()                 # row: vector number of tst, column: ASSIGN pads
        self.uno_depth = 0
        
        
    def get_pin_list_pins(self):
        pad_string = FindReMultiline(r"PinList = ([\w\+\"]+?);$", self.uno_RW_multiline.read_content)
        pads=str(pad_string[0]).replace('\"', '').strip()
        self.PinList_pins = pads.split('+')
        self.PinList_number = len(self.PinList_pins)
        
        return self.PinList_pins
    
    
    def get_subset_pin_list_pins(self):
        pad_string = FindReMultiline(r"SubsetPins SubsetPinsRef = \"([\w\+]+?)\";$", self.uno_RW_multiline.read_content)
        if pad_string == []:
            self.SubsetPins_pins = []
            return pad_string
        pads=str(pad_string[0]).replace(' ', '').replace('\n', '')
        self.SubsetPins_pins = pads.split('+')
        self.SubsetPins_number = len(self.SubsetPins_pins)
        
        return self.SubsetPins_pins
        

    def get_waveform_ref(self):
        self.waveform_ref = FindReMultiline(r"Default WaveformTable\s+(\w+?);$", self.uno_RW_multiline.read_content)
        self.waveform_ref = unique_list(self.waveform_ref)
        
        return self.waveform_ref
        
        
    def extract_alias(self):
        matched_alias = FindReMultiline(r"\*([01HLPX]+?)\*[ \w+]*;\s\"(\d+?)\"$", self.uno_RW_multiline.read_content)  # *10XX1XXX0X10X01000* SubsetPinsRef; "1"
        for index, tuple in enumerate(matched_alias):
            self.alias[int(tuple[1])] = tuple[0]
            show_progress_percent("extract uno alias vector-> ", index/len(matched_alias))
        print()
        self.uno_depth = len(matched_alias)
        return self.alias
        
    
    def create_pad_alias_dataframe(self):
        self.extract_alias()
        
        if(self.SubsetPins_number > 0):
            used_pin_number = self.SubsetPins_number
            used_pin_list = self.SubsetPins_pins
        else:
            used_pin_number = self.PinList_number
            used_pin_list = self.PinList_pins
        data = pd.DataFrame()
        for pad_index in range(0, used_pin_number):
            col_list_alias = []
            for vector in self.alias:
                col_list_alias.append(self.alias[vector][pad_index])
                
            Ser = pd.Series(col_list_alias, index = range(1, len(self.alias)+1))    #Ser1 = pd.Series(range(0,7), index = range(100, 107))
            data_each = pd.DataFrame({ f'{used_pin_list[pad_index]}' : Ser }) 
            data = pd.concat([data, data_each], axis=1)
            
            show_progress_percent("Building \""+ self.uno_name + "\" content dataframe -> ", pad_index/(used_pin_number-1))
        self.uno_dataframe = data
        print()
        
        return self.uno_dataframe