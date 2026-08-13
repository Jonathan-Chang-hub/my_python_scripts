import re
# import numpy as np
import os
# import io
# import sys
from datetime import datetime
import time
from JonathanPyLib import Search_files, ReadFileLines, WriteFileLines


currentDateAndTime = datetime.now()
now = currentDateAndTime.strftime("%Y%m%d_%H%M%S")
inputfolder = "./input"
outputfolder = "./output"




print(" ============================ Start =============================")
start = time.time()

set_num0=int(input("Enter 0 group number:"))
set_num1=int(input("Enter 1 group number:"))

path, file=Search_files(inputfolder, '.uno')
# print(path)
# print(file)

file_index = 0
for file_index in range(len(file)):
    
    ContentATPG_UNO=ReadFileLines(path[file_index]+'/'+file[file_index], 'utf-8')

    index_title = 0
    for line in ContentATPG_UNO:
        if (line[0] != '*'):
            if re.match(r'\bPinList\b\s+=\s+"\s*.*;', line) :
                ContentATPG_UNO[index_title] = ContentATPG_UNO[index_title].replace('= \"', '= \"Null_Pin+')
                # print(ContentATPG_UNO[index_title])
            elif re.match(r'\bPinUsage\b\s+"\s*.*;', line):
                ContentATPG_UNO[index_title] = ContentATPG_UNO[index_title].replace('PinUsage \"', 'PinUsage \"Null_Pin+')
        else:
            break
        index_title = index_title+1

    # print(index_title)


    set_num = set_num1 + set_num0
    UNO_Set = int((len(ContentATPG_UNO)-index_title)/set_num)
    UNO_residue = (len(ContentATPG_UNO)-index_title)%set_num

    print("\nPattern UNO File:"+file[file_index])
    print("Total File line number:"+str(len(ContentATPG_UNO)))
    print("Total vector line number:"+str(len(ContentATPG_UNO)-index_title))
    print("0 Group number:"+str(set_num0))
    print("1 Group number:"+str(set_num1))
    print("0 & 1 Combined-Group number:"+str(set_num0+set_num1))
    print("Vector line number/Combined-Group number --> quotient:"+str(UNO_Set)+", Residue:" + str(UNO_residue))

    for i in range(UNO_Set):
        for j in range(set_num):
            if(ContentATPG_UNO[index_title+i*set_num+j][0]=="*"):
                if(j<set_num0):
                    ContentATPG_UNO[index_title+i*set_num+j] = "*0"+ContentATPG_UNO[index_title+i*set_num+j].strip("*")
                else:
                    ContentATPG_UNO[index_title+i*set_num+j] = "*1"+ContentATPG_UNO[index_title+i*set_num+j].strip("*")
    # print(i)
    
    for j in range(UNO_residue):
        if(ContentATPG_UNO[index_title+UNO_Set*set_num+j][0]=="*"):
            ContentATPG_UNO[index_title+UNO_Set*set_num+j] = "*0"+ContentATPG_UNO[index_title+UNO_Set*set_num+j].strip("*")

    if not os.path.exists(outputfolder):
        os.mkdir(outputfolder)
    
    WriteFileLines(outputfolder+'/'+file[file_index], 'utf-8', ContentATPG_UNO)


print(str(len(file))+" Pattern UNO files are modified")
end = time.time()
print("execuation time: %f s" % (end-start))
print(" ============================ Complete ===========================")


