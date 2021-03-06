import ConfigParser
from time import strftime
import os
import re

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
import numpy
import time
import ast

import ycsb_parser

data_base_path = os.path.abspath('../../data/latency')

output_dir_name = time.strftime('%m-%d-%H%M')
output_dir_path = '%s/processed/%s' % (data_base_path, output_dir_name)
try:
    os.mkdir(output_dir_path)
except:
    pass

raw_data_root = '%s/raw' % data_base_path

profile_dicts = {}
prob_rows_dict = {'bw': [], 'gcloud': []}
for profile_name in ['bw', 'gcloud']:
    for job_id in os.listdir('%s/%s' % (raw_data_root, profile_name)):
        job_path = '%s/%s/%s' % (raw_data_root, profile_name, job_id)
        if not os.path.isdir(job_path):
            continue
        for experiment_id in os.listdir(job_path):
            if re.search('[0-9][0-9]\-[0-9][0-9]\-[0-9][0-9][0-9][0-9]$', experiment_id) is not None:
                cur_dir_path = '%s/%s' % (job_path, experiment_id)

                print 'CDF', profile_name, job_id, experiment_id

                meta = ConfigParser.SafeConfigParser()
                meta.read('%s/meta.ini' % cur_dir_path)
                config_dict = meta._sections['config']
                config_dict['result_dir_name'] = job_id

                output_fs = filter(lambda x: x.find('execution-output-') != -1 and x.find('stderr') == -1, os.listdir(cur_dir_path))
                aggregate_dicts = {'read': None, 'update': None}
                for fname in output_fs:
                    f = open('%s/%s' % (cur_dir_path, fname))
                    f_buf = f.read()
                    for rw in ['read', 'update']:
                        bucket_dict = ycsb_parser.parse_latency_bucket(f_buf, rw)
                        if aggregate_dicts[rw] is None:
                            aggregate_dicts[rw] = bucket_dict
                        else:
                            for key, value in bucket_dict.iteritems():
                                if key in aggregate_dicts[rw]:
                                    aggregate_dicts[rw][key] += value
                                else:
                                    aggregate_dicts[rw][key] = value

                if profile_name not in profile_dicts:
                    profile_dicts[profile_name] = aggregate_dicts
                else:
                    for rw in aggregate_dicts.keys():
                        for key, value in aggregate_dicts[rw].iteritems():
                            if key in profile_dicts[profile_name][rw]:
                                profile_dicts[profile_name][rw][key] += value
                            else:
                                profile_dicts[profile_name][rw][key] = value

                # PBS Probability
                if meta.has_option('result', 'pbs_probabilities'):
                    pbs_probs = ast.literal_eval(meta.get('result', 'pbs_probabilities'))
                    for t, prob in enumerate(pbs_probs):
                        prob_rows_dict[profile_name].append({'time': t, 'probability': prob})


for profile_name in profile_dicts.keys():
    aggregate_dicts = profile_dicts[profile_name]
    for rw in aggregate_dicts.keys():
        aggregate_dict = aggregate_dicts[rw]
        total_num_operations = reduce(lambda x, y: x + y, aggregate_dict.values())
        for key in aggregate_dict.keys():
            aggregate_dict[key] = float(aggregate_dict[key]) / total_num_operations
        rows = []
        for i, key in enumerate(sorted(aggregate_dict.keys())):
            if i == 0:
                rows.append({'0latency': key + 1, '1cumulative': aggregate_dict[key]})
            else:
                cum = rows[i - 1]['1cumulative'] + aggregate_dict[key]
                rows.append({'0latency': key + 1, '1cumulative': cum})
        df = pd.DataFrame(rows)
        df.to_csv('%s/cumulative-%s-%s.csv' % (output_dir_path, rw, profile_name), header=False, index=False)


for rw in ['read', 'update']:
    paths = filter(lambda x: re.search('.*cumulative\-%s\-.*\.csv' % rw, x) is not None,
                   ['%s/%s' % (output_dir_path, x) for x in os.listdir(output_dir_path)])
    print paths
    bw_path = filter(lambda x: x.split('/')[-1].find('bw') != -1, paths)[0]
    gcloud_path = filter(lambda x: x.split('/')[-1].find('gcloud') != -1, paths)[0]

    output_path = '%s/%s-cdf.png' % (output_dir_path, rw)

    os.system('./plot-latency-cdf.sh --rw=%s --output_path=%s --bw=%s --gcloud=%s' %
              (rw, output_path, bw_path, gcloud_path))

    print('./plot-latency-cdf.sh --rw=%s --output_path=%s --bw=%s --gcloud=%s' %
          (rw, output_path, bw_path, gcloud_path))


# for profile_name in profile_dicts.keys():
#     df = pd.DataFrame(prob_rows_dict[profile_name])
#     grouped = df.groupby('time')
#     df = grouped.mean()
#     csv_file_path = '%s/%s-consistency-probability.csv' % (output_dir_path, profile_name)
#     df.to_csv(csv_file_path)
#
# output_path = '%s/consistency-probability.png' % output_dir_path
# os.system('./plot-consistency-probability.sh --output_path=%s --bw=%s --gcloud=%s' %
#               (output_path, '%s/bw-consistency-probability.csv' % output_dir_path,
#                '%s/gcloud-consistency-probability.csv' % output_dir_path))