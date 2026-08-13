########################################################################
# Scan Maestro - Scan pin identifier from flat pattern
#
# Revision History
# 	- 1.0 Covers 4 projects scan templates (moka, 7981, 7922, 7925)
#	- 1.1 Incorporate call to Bill's FlatToCompressedScan tool
#   - 1.2 Deal with subset pins
#
########################################################################

import os
import subprocess


def read_file_vertically(file_path):
    vectors = []
    pin_list = []
    with open(file_path, 'r') as file:
        lines = file.readlines()
        PinList_PG_flag = False
        SubsetPins_PG_flag = False
        for line in lines:
            if line.startswith('PinList'):
                line_mod = line.replace(' ','').replace('PinList=\"','').replace('\";\n','')
                pin_list_split = line_mod.split('+')

                if len(pin_list_split) == 1:
                    PinList_PG_flag = True

                max_div = int(max(len(pin) for pin in pin_list_split) / 8)
                for idx, pin in enumerate(pin_list_split, start=1):
                    separator = ((max_div - int(len(pin) / 8)) + 1)*'\t'
                    pin_list.append(f"{idx}\t{pin}{separator}")

            if line.startswith('SubsetPins'):
                line_mod = line.replace(' ','').replace('SubsetPins SubsetPinsRef = \"','').replace('\";\n','')
                pin_list_split = line_mod.split('+')
                
                if len(pin_list_split) == 1:
                    SubsetPins_PG_flag = True
                    
                max_div = int(max(len(pin) for pin in pin_list_split) / 8)
                for idx, pin in enumerate(pin_list_split, start=1):
                    separator = ((max_div - int(len(pin) / 8)) + 1)*'\t'
                    pin_list.append(f"{idx}\t{pin}{separator}")
                
            if PinList_PG_flag and SubsetPins_PG_flag:
                return 'using_pin_group', 0, 0
            
            if line.startswith('*'):
                vectors.append(line)

    max_vector = len(vectors)
    max_length = max(len(vector) for vector in vectors)

    columns = [[] for _ in range(max_length)]
    for i in range(max_length):
        for vector in vectors:
            if i < len(vector):
                columns[i].append(vector[i])

    return pin_list, columns, max_vector


def recode_columns(columns, vectors):
    recoded_columns = []
    
    #for idx, column in enumerate(columns,start=1): #for debug
    for column in columns:
        unique_values = []
        zeros = column.count('0')
        ones = column.count('1')
        dont_cares = column.count('X')
        transition = 0
        previous_value = None

        for value in column:
            if value == '0' or value == '1':
                if value != previous_value:
                    transition += 1
                    previous_value = value
            if value not in unique_values:
                unique_values.append(value)
     
        if '0' in unique_values and '1' in unique_values:
            ones_percentage = ones / vectors
            transition_percentage = transition / vectors
            dont_cares_percentage = dont_cares / vectors

            if dont_cares_percentage > 0.9:
                unique_values.append('more_dont_cares')

            elif zeros > ones: 
                unique_values.append('more_zeros')
                if ones_percentage < 0.005:                                       #filter for rst 0
                    unique_values.append('probably_rst_0')

            elif ones > zeros: 
                unique_values.append('more_ones')

                if transition_percentage > 0.01 and ones_percentage > 0.952:      #filter for enable 1
                    unique_values.append('probably_enable_1')
                elif ones_percentage > 0.895 and ones_percentage < 0.95:          #filter for clock
                    unique_values.append('probably_clk')
                elif ones_percentage > 0.95 and ones_percentage < 0.98 and transition_percentage > 0.005:    #filter for scan_in
                    unique_values.append('probably_scan_in')
                elif ones_percentage > 0.98:                                      #filter for rst 1
                    unique_values.append('probably_rst_1')
                elif transition_percentage > 0.015 and ones_percentage > 0.88:    #filter for clock
                    unique_values.append('probably_clk')
                elif transition_percentage > 0.085:                               #filter for scan_in
                    unique_values.append('probably_scan_in')
                elif transition_percentage > 0.05:                                #filter for clock
                    unique_values.append('probably_clk')
                elif transition_percentage > 0.02 and ones_percentage > 0.85:     #filter for scan_in
                    unique_values.append('probably_scan_in')
                elif transition_percentage > 0.01 and ones_percentage > 0.80:     #filter for enable 1
                    unique_values.append('probably_enable_1')
                elif transition_percentage < 0.002:                               #filter for rst 1
                    unique_values.append('probably_rst_1')
                elif ones_percentage > 0.80:                                      #filter for clock
                    unique_values.append('probably_clk')
                elif transition_percentage > 0.01 or ones_percentage > 0.50:      #filter for scan_in
                    unique_values.append('probably_scan_in')               
            
        recoded_columns.append(unique_values)

    return recoded_columns


def write_file(file_path, columns, pins):
    scan_type_record = []

    scan_type_mapping = {
        '0': f"RST\t0",
        '1': f"RST\t1",
        '1 0 more_zeros probably_rst_0': f"RST\t0",
        '1 0 more_ones probably_rst_1': f"RST\t1",
        '0 1 more_ones probably_rst_1': f"RST\t1",
        '0 1 more_ones probably_clk': f"CLK\t1",
        '1 0 more_ones probably_clk': f"CLK\t1",
        'X 1 0 more_ones probably_clk': f"CLK\t1",
        'X 0 1 more_ones probably_clk': f"CLK\t1",
        '1 0 more_ones probably_scan_in': f"SCAN_IN\t0,1",
        '0 1 more_ones probably_scan_in': f"SCAN_IN\t0,1",
        'X 1 0 more_ones probably_scan_in': f"SCAN_IN\t0,1",
        'X 0 1 more_ones probably_scan_in': f"SCAN_IN\t0,1",
        '0 1 more_ones probably_enable_1': f"ENABLE\t1",
        '0 1 more_zeros probably_enable_0': f"ENABLE\t0",
        '1 0 more_zeros': f"ENABLE\t0",        
        '0 1 more_ones': f"ENABLE\t1",
        '0 1 more_zeros': f"SCAN_IN\t0,1",
        'X 0 1 more_zeros': f"SCAN_IN\t0,1",
        'X 1 0 more_zeros': f"SCAN_IN\t0,1",
        'X 1 0 more_ones': f"SCAN_IN\t0,1",        
        'X H L': f"SCAN_OUT",
        'X L H': f"SCAN_OUT",
        'X L': f"SCAN_OUT",
        'X': '',
        'X 1': '',
        'X 0': '',
        'X 1 0 more_dont_cares': '',
        'X 0 1 more_dont_cares': '',
        '1 0 more_ones': f"CLK\t1"
    }

    with open(file_path, 'w') as file:
        for row in columns:
            line = ' '.join(str(value) for value in row)
            #print(f"{line}") #for debug
            line = scan_type_mapping.get(line, 'skip')

            if line != 'skip':
                scan_type_record.append(line)
                
        for idx, record in enumerate(scan_type_record):
            file.write(f"{pins[idx]}{record}\n")


def process_uno(current_dir, file_name):
    input_file = os.path.join(current_dir, file_name)
    recoded_pins, columns, max_vector = read_file_vertically(input_file)

    if 'using_pin_group' in recoded_pins:
        print(f"Using Pingroup name! Change it to Pin names in {file_name} and re-run script.")
        return

    recoded_columns = recode_columns(columns, max_vector)

    output_file = input_file.replace('.uno', '_scan_template.txt')
    write_file(output_file, recoded_columns, recoded_pins)

    template = file_name.replace('.uno', '_scan_template.txt')
    print("Scan template completed and written to", template)

    # Run FlatToCompressedScan_R2 tool    
    from sys import platform
    if platform == "linux" or platform == "linux2": 
        cmd = f"./FlatToCompressedScan_R2.0_L210609 -log -C mdtk -ST {template} ./{file_name}"
        subprocess.run(cmd, shell=True, check=True)

    return output_file


def run_checker(file_to_check_path):
    file_checker_path = file_to_check_path.replace('_scan_template.txt', '_scan_template_checker.txt')

    with open(file_to_check_path, 'r') as file_to_check, open(file_checker_path, 'r') as file_checker:
        for line_to_check, line_checker in zip(file_to_check, file_checker):
            if line_to_check != line_checker:
                print("\tFirst Mismatched!")
                print("\tCaptured: ",line_to_check.replace('\n',''))
                print("\t Checker: ",line_checker.replace('\n',''))
                return False

        # Check if one file has more lines than the other
        if len(file_to_check.readlines()) != len(file_checker.readlines()):
            return False

    return True


def main():
    current_dir = os.getcwd()
    current_dir = "./input/uno"

    uno_files = [f for f in os.listdir(current_dir) if os.path.isfile(os.path.join(current_dir, f)) and f.endswith('.uno')]

    if uno_files:
        print("Uno(s) found, creating scan template...")
        for file_name in uno_files:            
            process_uno(current_dir, file_name)
        print("Done! Completed scan template creation and flat to compressed scan pattern conversion(for linux only).")
    else:
        print("No Uno found, running scan template checker...")
        current_dir = os.path.join(current_dir, 'checker')

        if os.path.exists(current_dir):
            unos_to_check = [f for f in os.listdir(current_dir) if os.path.isfile(os.path.join(current_dir, f)) and f.endswith('.uno')]

            for uno_to_check in unos_to_check:
                template_to_check = process_uno(current_dir, uno_to_check)
                template_to_check = os.path.join(current_dir, template_to_check)
                uno_to_check = uno_to_check.replace('.uno', '_scan_template.txt')

                if run_checker(template_to_check):
                    print("\tPASSED checker! Done checking",uno_to_check)  
                else: 
                    print("\tFAILED checker! Done checking",uno_to_check)
                    
                os.remove(os.path.join(current_dir,uno_to_check))

        else:
            print("No checker files, exiting script...")


if __name__ == '__main__':
    main()
    