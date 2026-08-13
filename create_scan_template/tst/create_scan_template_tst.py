import re
import time
from JonathanPyLib_V14 import *
from TST_class import *
import csv


CSV_WRITE_VEC_NUM = 10000

def create_scan_template_tst(tst_pattern_file:str):
    file = tst_pattern_file.split('/')[-1]
    path = tst_pattern_file.replace(f"{file}", '')
    
    print(">>> " + file)
    tst_pattern: TstPattern = TstPattern(tst_pattern_file)

    tst_pattern.get_assign_pads()
    print("assign pads number:", len(tst_pattern.tst_assign_pads))

    output_path = str(path).replace(f"{INPUT_FOLDER}", f"{OUTPUT_FOLDER}") + '/'
    output_file = str(file).replace('.tst', '').replace('.gz', '') + '.csv'
    aiias_csv = output_path + output_file
    
    scan_in = ['0', '1', 'X']
    scan_out1 = ['H', 'L', 'X']
    scan_out2 = ['H', 'L']
    scan_in.sort()
    scan_out1.sort()
    scan_out2.sort()
    
    df = tst_pattern.create_pad_alias_dataframe()
    print("pattern depth:", tst_pattern.tst_depth)        

    type_dic = {}
    if re.search(r"_SSN", str(file), re.IGNORECASE):
        for pad in df.columns:
            unique_col_list = list(df[pad].unique())
            unique_col_list.sort()
            if unique_col_list == ['X']:
                type_dic[pad] = [pad, '', '', '']
            elif unique_col_list == scan_in or unique_col_list == ['1'] or unique_col_list == ['1', 'X'] or \
                unique_col_list == ['0'] or unique_col_list == ['0', 'X'] or unique_col_list == ['0', '1']:
                type_dic[pad] = [pad, 'SCAN_IN', '0,1,X', '']
            elif unique_col_list == scan_out1 or unique_col_list == scan_out2 or unique_col_list == ['H'] or unique_col_list == ['L']\
                or unique_col_list == ['H', 'X'] or unique_col_list == ['L', 'X']:
                type_dic[pad] = [pad, 'SCAN_OUT', '', '']
            
            output_file = str(file).replace('.tst', '').replace('.gz', '') + '_unique.csv'
            with open(output_path + output_file, 'a', newline='', encoding='utf-8') as fu:
                uu = pad + ','
                for item in unique_col_list:
                    uu = str(uu) + item + ','
                fu.write(uu+'\n')
            fu.close()
    else:
        for pad in df.columns:
            unique_col_list = list(df[pad].unique())
            unique_col_list.sort()
            if unique_col_list == ['X']:
                type_dic[pad] = [pad, '', '', '']
            elif unique_col_list == scan_in:
                count0 = (df[pad] == '0').sum()
                count1 = (df[pad] == '1').sum()
                type_dic[pad] = [pad, 'SCAN_IN', '0,1,X', str(count0) + ' ' + str(count1)]
            elif unique_col_list == scan_out1 or unique_col_list == scan_out2 or unique_col_list == ['H'] or unique_col_list == ['L']\
                or unique_col_list == ['H', 'X'] or unique_col_list == ['L', 'X']:
                type_dic[pad] = [pad, 'SCAN_OUT', '', '']
            elif unique_col_list == ['1'] or unique_col_list == ['1', 'X']:
                type_dic[pad] = [pad, 'RST', '1', '']
            elif unique_col_list == ['0'] or unique_col_list == ['0', 'X']:
                type_dic[pad] = [pad, 'RST', '0', '']
            elif unique_col_list == ['0', '1']:
                count0 = (df[pad] == '0').sum()
                count1 = (df[pad] == '1').sum()
                if count0 > count1:
                    type_dic[pad] = [pad, 'SCAN_IN', '0,1', str(count0) + ' ' + str(count1)]
                    # if count0/count1 > 10:
                    #     type_dic[pad] = [pad, 'ENABLE', '0', str(count0) + ' ' + str(count1)]
                elif count1 > count0:
                    type_dic[pad] = [pad, 'CLK', '1', '']
            output_file = str(file).replace('.tst', '').replace('.gz', '') + '_unique.csv'
            with open(output_path + output_file, 'a', newline='', encoding='utf-8') as fu:
                uu = pad + ','
                for item in unique_col_list:
                    uu = str(uu) + item + ','
                fu.write(uu+'\n')
        fu.close()
    
    output_file = str(file).replace('.tst', '').replace('.gz', '') + '_template.txt'
    write_type_to_csv = ['']
    write_logic_to_csv = ['']
    write_01counts_to_csv = ['']
    with open(output_path + output_file, 'w', encoding='utf-8') as fo:
        for pad in type_dic:
            type = ""
            for indx, item in enumerate(type_dic[pad]):
                type += str(item) + '\t'
                if indx == 1:
                    write_type_to_csv.append(item)
                if indx == 2:
                    write_logic_to_csv.append(item)
                if indx == 3:
                    write_01counts_to_csv.append(item)
            fo.write(type + '\n')
    fo.close()
    
    with open(aiias_csv, mode='w', newline='', encoding='utf-8') as fc:
        writer = csv.writer(fc)
        writer.writerow(write_type_to_csv)
        writer.writerow(write_logic_to_csv)
        writer.writerow(write_01counts_to_csv)
    
    # default start index if no H/L found
    csv_write_start = 1
    H_detected = False
    for vec, val in tst_pattern.alias.items():
        s = str(val)
        if 'H' in s:
            csv_write_start = vec - 1
            H_detected = True
            break
        if 'L' in s and not H_detected:
            csv_write_start = vec - 1
            break
        
    df.iloc[csv_write_start:csv_write_start + CSV_WRITE_VEC_NUM].to_csv(aiias_csv, index=True, mode = 'a', encoding='utf-8')


def main():
    print('='*50 + " Process Start " + '='*50)
    start = time.time()
    #--------------------------------------------------------------------------------------------------------------------------------------------#
    
    CreateLoopOutputFolder(INPUT_FOLDER, OUTPUT_FOLDER)
    
    # create_scan_template_tst('./PAT/ATPG/OCC/PAA/ATPG_OCC_PAA_comp_setup_SSN_DVFS_0P80V_200M_20250813_v0.tst.gz')
    
    paths, files = Search_files(INPUT_FOLDER, ['.tst', '.gz'])
    for path, file in zip(paths, files):
        create_scan_template_tst(path + '/' + file)
    
    
    #--------------------------------------------------------------------------------------------------------------------------------------------#
    end = time.time()
    result=(divmod(end-start, 60))
    
    print(f"execuation time: {result[0]:.0f} m {result[1]:.2f} s")
    print('='*50 + " Process Completed " + '='*50)

if __name__ == '__main__':
    main()