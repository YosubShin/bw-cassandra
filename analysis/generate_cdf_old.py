import ConfigParser
from time import strftime
import os
import re

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
import numpy

from repo.analysis import ycsb_parser


data_base_path = '../data'

def plot_throughput_vs_latency():
    # profile_names = ['emulab-ramdisk', 'emulab', 'emulab-network', 'bw', 'bw-network']
    profile_names = ['bw', 'emulab-ramdisk']

    rows = []

    for profile_name in profile_names:
        data_root = '%s/raw/%s' % (data_base_path, profile_name)
        print profile_name
        for dir_name in os.listdir(data_root):
            if re.search('[0-9][0-9]\-[0-9][0-9]\-[0-9][0-9][0-9][0-9]$', dir_name) is not None:
                cur_dir_path = '%s/%s' % (data_root, dir_name)

                result = None
                print dir_name
                for fname in os.listdir(cur_dir_path):
                    if fname.find('output-') != -1:
                        f = open('%s/%s' % (cur_dir_path, fname))
                        try:
                            cur_result = ycsb_parser.parse_execution_output(f.read())
                        except Exception, e:
                            print str(e)
                            continue
                        if result is None:
                            result = cur_result
                        else:
                            print fname
                            new_result = dict()
                            new_result['update_num_operations'] = result['update_num_operations'] + cur_result['update_num_operations']
                            new_result['read_num_operations'] = result['read_num_operations'] + cur_result['read_num_operations']
                            new_result['overall_num_operations'] = result['overall_num_operations'] + cur_result['overall_num_operations']

                            new_result['update_average_latency'] = result['update_average_latency'] * result['update_num_operations'] / new_result['update_num_operations'] \
                                                                   + cur_result['update_average_latency'] * cur_result['update_num_operations'] / new_result['update_num_operations']
                            new_result['read_average_latency'] = result['update_average_latency'] * result['update_num_operations'] / new_result['update_num_operations'] \
                                                                   + cur_result['update_average_latency'] * cur_result['update_num_operations'] / new_result['update_num_operations']

                            new_result['overall_throughput'] = result['overall_throughput'] + cur_result['overall_throughput']
                            result = new_result

                meta = ConfigParser.SafeConfigParser()
                meta.read('%s/meta.ini' % cur_dir_path)
                config_dict = meta._sections['config']
                config_dict['result_dir_name'] = dir_name
                result.update(config_dict)

                rows.append(result)

    df = pd.DataFrame(rows)

    df_1node = df[df['num_cassandra_nodes'] == '1']

    output_dir_name = strftime('%m-%d-%H%M')
    os.mkdir('%s/processed/%s' % (data_base_path, output_dir_name))
    df.to_csv('%s/processed/%s/data.csv' % (data_base_path, output_dir_name))

    # # Plot Emulab vs. Blue Waters on ram disk
    # plt.figure()
    # ax = df_1node[df_1node['profile'] == 'emulab-ramdisk'].plot(label='emulab-ramdisk', kind='scatter', x='overall_throughput', y='read_average_latency', color='DarkBlue')
    # df_1node[df_1node['profile'] == 'bw'].plot(label='bw-ramdisk', kind='scatter', x='overall_throughput', y='read_average_latency', ax=ax, color='DarkGreen')
    # plt.savefig('%s/processed/%s/bw-emulab-latency-throughput.png' % (data_base_path, output_dir_name))
    #
    # # Plot BW-ramdisk vs. BW-network
    # plt.figure()
    # ax = df_1node[df_1node['profile'] == 'bw-network'].plot(label='bw-network', kind='scatter', x='overall_throughput', y='read_average_latency', color='DarkBlue')
    # df_1node[df_1node['profile'] == 'bw'].plot(label='bw-ramdisk', kind='scatter', x='overall_throughput', y='read_average_latency', ax=ax, color='DarkGreen')
    # plt.savefig('%s/processed/%s/bw-latency-throughput.png' % (data_base_path, output_dir_name))
    #
    # # Plot Emulab-ramdisk vs. Emulab-localdisk vs. Emulab-network
    # plt.figure()
    # ax = df_1node[df_1node['profile'] == 'emulab'].plot(label='emulab-localdisk', kind='scatter', x='overall_throughput', y='read_average_latency', color='DarkBlue')
    # df_1node[df_1node['profile'] == 'emulab-ramdisk'].plot(label='emulab-ramdisk', kind='scatter', x='overall_throughput', y='read_average_latency', ax=ax, color='DarkGreen')
    # df_1node[df_1node['profile'] == 'emulab-network'].plot(label='emulab-network', kind='scatter', x='overall_throughput', y='read_average_latency', ax=ax, color='Red')
    # plt.savefig('%s/processed/%s/emulab-latency-throughput.png' % (data_base_path, output_dir_name))

    # # # Plot BW-ramdisk 1 node vs. 2 node vs. 3 nodes
    # plt.figure()
    # colors = [None, 'red', 'black', 'yellow', 'green', 'blue', 'violet', 'pink', 'LightBlue']
    # ax = df[df['profile'] == 'bw'][df['num_cassandra_nodes'] == '1'].plot(label='1 node', kind='scatter', x='overall_throughput', y='read_average_latency', color=colors[1])
    # for i in range(2, 6):
    #     df[df['profile'] == 'bw'][df['num_cassandra_nodes'] == ('%d' % i)].plot(label=('%d nodes' % i), kind='scatter', x='overall_throughput', y='read_average_latency', ax=ax, color=colors[i])
    # ax.legend(loc='best')
    # plt.savefig('%s/processed/%s/bw-num-nodes-latency-throughput.png' % (data_base_path, output_dir_name))
    #
    # # Plot Emulab-ramdisk 1 node vs. 2 node
    # plt.figure()
    # ax = df[df['profile'] == 'emulab-ramdisk'][df['num_cassandra_nodes'] == '1'][df['num_hosts'] == '20'].plot(label='1 node', kind='scatter', x='overall_throughput', y='read_average_latency', color=colors[1])
    # for i in range(2, 8):
    #     df[df['profile'] == 'emulab-ramdisk'][df['num_cassandra_nodes'] == ('%d' % i)].plot(label=('%d nodes' % i), kind='scatter', x='overall_throughput', y='read_average_latency', ax=ax, color=colors[i])
    # # df[df['profile'] == 'emulab-ramdisk'][df['num_cassandra_nodes'] == '2'][df['num_hosts'] == '20'].plot(label='2 nodes', kind='scatter', x='overall_throughput', y='read_average_latency', ax=ax, color='DarkGreen')
    # # df[df['profile'] == 'emulab-ramdisk'][df['num_cassandra_nodes'] == '3'][df['num_hosts'] == '20'].plot(label='3 nodes', kind='scatter', x='overall_throughput', y='read_average_latency', ax=ax, color='Red')
    # # df[df['profile'] == 'emulab-ramdisk'][df['num_cassandra_nodes'] == '4'][df['num_hosts'] == '20'].plot(label='4 nodes', kind='scatter', x='overall_throughput', y='read_average_latency', ax=ax, color='Yellow')
    # ax.legend(loc='best')
    # plt.savefig('%s/processed/%s/emulab-num-nodes-latency-throughput.png' % (data_base_path, output_dir_name))

    colors = matplotlib.cm.rainbow(numpy.linspace(0, 1, 8))
    # ['.', ',', 'o', 'v', '^', '<', '>', '1', '2', '3', '4', 's', 'p', '*', 'h', 'H', '+', 'x', 'D', 'd', '|', '_']
    markers = ['o', '^', 's', 'p', '*', 'h', '+', 'x', 'D', '|', '_']

    plt.figure()
    for i in range(0, 1):
        cur_df = df[df['profile'] == 'bw'][df['num_cassandra_nodes'] == '%d' % (i + 1)]
        plt.scatter(x=cur_df['overall_throughput'], y=cur_df['read_average_latency'], c=colors[i], marker=markers[i],
                    label='%d nodes' % (i + 1))
    plt.legend(loc='best')
    plt.savefig('%s/processed/%s/bw-num-nodes-latency-throughput.png' % (data_base_path, output_dir_name))


    plt.figure()
    for i in range(0, 3):
        cur_df = df[df['profile'] == 'emulab-ramdisk'][df['num_cassandra_nodes'] == '%d' % (i + 1)]
        plt.scatter(x=cur_df['overall_throughput'], y=cur_df['read_average_latency'], c=colors[i], marker=markers[i],
                    label='%d nodes' % (i + 1))
    plt.legend(loc='best')
    plt.savefig('%s/processed/%s/emulab-num-nodes-latency-throughput.png' % (data_base_path, output_dir_name))

    # ax = df[df['profile'] == 'emulab-ramdisk'][df['num_cassandra_nodes'] == '1'][df['num_hosts'] == '20'].plot(label='1 node', kind='scatter', x='overall_throughput', y='read_average_latency', color='DarkBlue')

def main():
    plot_throughput_vs_latency()

if __name__ == "__main__":
    main()
