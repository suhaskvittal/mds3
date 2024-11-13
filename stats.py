import os
import sys
import pandas as pd
import re
import itertools
import numpy as np
import argparse
from scipy.stats.mstats import gmean

def parse_sim(file_path, avg = False):
    data = {
        "File": get_workload_from_path(file_path),
        "TYPE": "memsim"
    }

    with open(file_path, 'r') as file:
        content = file.read()

        pattern = r"DRAM_RFM\s*:\s*(\d+)"
        match = re.search(pattern, content)
        if match:
            data["NUM_RFM"] = float(match.group(1))
    return data


suites = {
    'gap6': ['cc', 'pr', 'tc', 'bfs', 'bc', 'sssp'],
    'stream4': ['add', 'triad', 'copy', 'scale'],
    'spec2k17': ['blender_17', 'bwaves_17', 'cactuBSSN_17', 'cam4_17', 'deepsjeng_17', 'fotonik3d_17', 'gcc_17', 'imagick_17', 'lbm_17', 'leela_17', 'mcf_17', 'nab_17', 'namd_17', 'omnetpp_17', 'parest_17', 'perlbench_17', 'povray_17', 'roms_17', 'wrf_17', 'x264_17', 'xalancbmk_17', 'xz_17']
}

def get_workload_from_path(file_path):
    all_workloads = list(itertools.chain.from_iterable(suites.values()))
    for workload in all_workloads:
        if workload + "." in file_path:
            vals = file_path.split(workload)
            typ = vals[0].split('/')[-1][:-1]
            name = workload
            return typ, name
    
    return None, None

def group_by_suite(df):
    # add a suite coulmn to the dataframe
    # and sort by file and suite
    df['SUITE'] = df['FILE'].apply(lambda x: next((k for k, v in suites.items() if x in v), None))
    df = df.sort_values(by=['SUITE', 'FILE'])
    # make suite the first column
    
    return df

def parse_dramsim3(file_path, avg = False):
    # print("Parsing", file_path)
    typ, name =  get_workload_from_path(file_path)
    if not typ:
        return None
    # print("Typ:", typ, "Name:", name)
    data = {
        "FILE": name,
        "TYPE": typ
    }

    with open(file_path, 'r') as file:
        content = file.read()
        refab_match = re.findall(r"num_refab_cmds\s+=\s+(\d+)", content)
        avg_refab = np.mean([int(r) for r in refab_match])

        acts_match = re.findall(r"num_act_cmds\s+=\s+(\d+)", content)
        acts_per_ref = np.mean([(int(a)/(32*int(r))) for a, r in zip(acts_match, refab_match)])
        if acts_match and refab_match:
            data["ACTS_PER_REF"] = round(acts_per_ref, 3)

        alerts_match = re.findall(r"num_alerts\s+=\s+(\d+)", content)
        alerts_per_ref = np.mean([int(a)/int(r) for a, r in zip(alerts_match, refab_match)])
        if alerts_match:
            data["ALERTS_PER_REF"] = round(alerts_per_ref, 3)

        rfms_match = re.findall(r"num_rfmab_cmds\s+=\s+(\d+)", content)
        if rfms_match:
           data["NUM_RFM"] = sum([int(m) for m in rfms_match])
        

        # // 0, 1, 2, 4, 8, 16, 32, 64, 128, 256, 512, 1024, >= 1024
        # uint32_t get_geostat_bin(uint16_t val)
        # {
        #     if (val == 0) return 0;
        #     if (val == 1) return 1;
        #     if (val <= 2) return 2;
        #     if (val <= 4) return 3;
        #     if (val <= 8) return 4;
        #     if (val <= 16) return 5;
        #     if (val <= 32) return 6;
        #     if (val <= 64) return 7;
        #     if (val <= 128) return 8;
        #     if (val <= 256) return 9;
        #     if (val <= 512) return 10;
        #     if (val <= 1024) return 11;
        #     return 12;
        # }

        prac_per_tREFI = re.findall(r"prac_per_tREFI\.(\d+)\s*=\s*(\d+)", content)
        if prac_per_tREFI:
            act4_plus = 0
            act32_plus = 0
            act64_plus = 0
            act128_plus = 0

            for m in prac_per_tREFI:
                bin_ = int(m[0])
                if bin_ > 2:
                    act4_plus += int(m[1])
                if bin_ > 6:
                    act32_plus += int(m[1])
                if bin_ > 7:
                    act64_plus += int(m[1])
                if bin_ > 8:
                    act128_plus += int(m[1])

            data["ACT4_PLUS"] = round((act4_plus * 8192)/(avg_refab * 64), 2)
            data["ACT32_PLUS"] = round((act32_plus * 8192)/(avg_refab * 64), 2)
            data["ACT64_PLUS"] = round((act64_plus * 8192)/(avg_refab * 64), 2)
            data["ACT128_PLUS"] = round((act128_plus * 8192)/(avg_refab * 64), 2)

        match = re.findall(r"average_read_latency\s*=\s*(\d+\.?\d*)", content)
        if match:
            data["AVG_READ_LATENCY"] = sum([float(m) for m in match])/len(match)

        matches = re.findall(r"CORE_\d+_IPC\s*:\s*(\d+\.?\d*)", content)
        if matches:
            data["AVG_IPC"] = sum([float(m) for m in matches])/len(matches)

        matches = re.findall(r"CORE_\d+_MPKI\s*:\s*(\d+\.?\d*)", content)
        if matches:
            avg_mpki = sum([float(m) for m in matches])/len(matches)
            data["AVG_MPKI"] = avg_mpki

        match = re.search(r"AVG_CORE_CYCLES\s*:\s*(\d+)", content)
        if match:
            avg_core_cycles = float(match.group(1))


        matches = re.findall(r"CORE_\d+_INST\s*:\s*(\d+)", content)
        if matches:
            inst = sum([float(m) for m in matches])
            data["APKI"] = (sum([int(x) for x in acts_match]) * 1000)/inst
    return data

def parse_directory(directory_path, avg):
    all_data = []

    for entry in os.listdir(directory_path):
        entry_path = os.path.join(directory_path, entry)

        if os.path.isdir(entry_path):
            all_data.extend(parse_directory(entry_path, avg))
        elif "sim_" in entry_path:
            file_data = parse_sim(entry_path, avg = avg)
            if file_data:
                all_data.append(file_data)
        else:
            file_data = parse_dramsim3(entry_path, avg = avg)
            if file_data:
                all_data.append(file_data)
    return all_data



def pivot(df, column):
    print("Coulmns:", df.columns)
    pivot_table = df.pivot_table(index='FILE', columns='TYPE', values=column)

    # Reset index to flatten the DataFrame
    pivot_table = pivot_table.reset_index()

    return pivot_table

def add_best(df):
    # add best IPC column, max of all the columns except file
    columns = df.columns
    columns = columns.drop(['FILE'])

    df['best'] = df[columns].max(axis=1)
    return df

def rfm_slowdown(df):
    df['slowdown.rfm16'] = (100 * (df['rfm16'] - df['baseline'])) / df['rfm16']
    df['slowdown.rfm32'] = (100 * (df['rfm32'] - df['baseline'])) / df['rfm32']

    return df

def add_slowdown(df, baseline):
    # compare evey column excpet file to best and update the value of each column
    columns = df.columns
    columns = columns.drop(['FILE', baseline])

    for c in columns:
        df[c] = round(df[c] / df[baseline], 4)

    df[baseline] = round(df[baseline] / df[baseline], 4)

    return df

def compare_prac(df):
    # compare all the prac coulmns with their non-prac counterparts
    # col, colprac

    non_prac_cols = []

    for c in df.columns:
        if c.endswith("prac"):
            non_prac_col = c[:-4]
            print("Comparing", non_prac_col, c)
            df[c] = round(df[c] / df[non_prac_col], 4)
            non_prac_cols += [non_prac_col]
            df[non_prac_col] = round(df[non_prac_col] / df[non_prac_col], 4)
    
    # drop the non-prac columns
    df = df.drop(columns=non_prac_cols)

    return df


def add_mean(df, dropna=False):
    mean_row = {"FILE": "MEAN"}

    for c in df.columns:
        if c not in ['FILE']:
            mean_row[c] = round(df[c].dropna().mean(), 3)

    # Convert the geomean_row to a DataFrame and concatenate
    mean_df = pd.DataFrame([mean_row], columns=df.columns)
    df = pd.concat([df, mean_df], ignore_index=True)

    return df

def add_geomean(df, dropna=False):
    geomean_row = {"FILE": "GEOMEAN"}

    for c in df.columns:
        if c not in ['FILE']:
            geomean_row[c] = gmean(df[c].dropna())

    # Convert the geomean_row to a DataFrame and concatenate
    geomean_df = pd.DataFrame([geomean_row], columns=df.columns)
    df = pd.concat([df, geomean_df], ignore_index=True)

    return df

def main(args):
    data = []
    for directory in args.directory_path:
        if not os.path.isdir(directory):
            print("Invalid directory path")
        data += parse_directory(directory, False)
    
    
    df = pd.DataFrame(data)


    if args.type:
        df = df[df['TYPE'] == args.type]
    else:
        df = pivot(df, args.pivot)

    if args.ignorecols:
        df = df.drop(columns=args.ignorecols)
    
    if args.cols:
        # add FILE column to the list of columns
        args.cols = ['FILE'] + args.cols
        df = df[args.cols]

    if args.dropna:
        df = df.dropna()

    if not args.noslowdown and args.baseline == "best":
        df = add_best(df)
    
    if args.mean:
        df = add_mean(df)
    elif args.gmean:
        df = add_geomean(df)

    if not args.noslowdown:
        df = add_slowdown(df, args.baseline)
    elif args.prac:
        df = compare_prac(df)

    df = group_by_suite(df)

    print(df.to_string())
    print(df.to_csv(index=False))

       
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Parse stats files')
    # multiple directories can be passed
    parser.add_argument('directory_path', type=str, nargs='+', help='Path to the directory containing stats files')
    parser.add_argument('-pivot', type=str, default="AVG_IPC", help='Column to pivot on')
    parser.add_argument('-mean', action='store_true', help='Add mean row')
    parser.add_argument('-gmean', action='store_true', help='Add geomean row')
    parser.add_argument('-dropna', action='store_true', help='Drop rows with Nan')
    parser.add_argument('-ignorecols', nargs='+', help='Columns to ignore')
    parser.add_argument('-cols', nargs='+', help='Columns to Select')
    parser.add_argument('-noslowdown', action='store_true', help='Do not calculate slowdown')
    parser.add_argument('-prac', action='store_true', help='Compare prac columns')
    parser.add_argument('-baseline', type=str, default='best', help='Baseline column for slowdown')
    parser.add_argument('-type', type=str, help='Type of workload to select')
    args = parser.parse_args()
    main(args)

