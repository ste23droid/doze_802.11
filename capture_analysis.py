import os
import pyshark
import numpy as np
import matplotlib.pyplot as plt

def add_bar_label(rects, ax):

    for rect in rects:
        height = rect.get_height()
        ax.text(rect.get_x() + rect.get_width()/2., height,
                "{0:.2f}".format(height),
                ha='center', va='bottom')

def build_power_ratios_graph(scenario_name, bit_0_ratios, bit_1_ratios):
    n_groups = 5
    fig, ax = plt.subplots()
    index = np.arange(n_groups)
    bar_width = 0.35
    opacity = 0.4
    rects_bit0 = ax.bar(index, bit_0_ratios, bar_width,
                    alpha=opacity, color='b',
                    label='PWR MGT Bit 0: Radio ON')

    rects_bit1 = ax.bar(index + bar_width, bit_1_ratios, bar_width,
                    alpha=opacity, color='r',
                    label='PWR MGT Bit 1: Radio SLEEP')

    ax.set_xlabel('Durations')
    ax.set_ylabel('Power Ratios')
    ax.set_yticks(np.arange(0, 1.1, 0.1))
    ax.set_title(scenario_name)
    ax.set_xticks(index + bar_width / 2)
    ax.set_xticklabels(('10 min', '30 min', '1 h', '2 h', '3 h'))
    ax.legend()
    add_bar_label(rects_bit0, ax)
    add_bar_label(rects_bit1, ax)
    fig.tight_layout()
    plt.show()

def build_avg_packets_graph(scenario_name, inputs):
    n_groups = 5
    fig, ax = plt.subplots()
    index = np.arange(n_groups)
    bar_width = 0.35
    opacity = 0.4

    rects_avg_packets = ax.bar(index, inputs, bar_width,
                        alpha=opacity, color='g')

    ax.set_xlabel('Durations')
    ax.set_ylabel('Average number of packets')
    ax.set_title(scenario_name)
    ax.set_xticks(index)
    ax.set_xticklabels(('10 min', '30 min', '1 h', '2 h', '3 h'))
    add_bar_label(rects_avg_packets, ax)
    fig.tight_layout()
    plt.show()

# compute results for each scenario (e.g Android 6 2.4 GHz)
def compute_results(base_directory, scenario_name):

    print("\n############################ SCENARIO " + scenario_name + " ##################################")

    # cumulative results needed to build the graphs for this scenario
    pwr_mgt_bit_1_results = []
    pwr_mgt_bit_0_results = []
    avg_num_packets_results = []

    # base directory + nested folders containing captures for 10 minutes, 30 minutes, 1 hour and so on...
    sub_directories = [x[0] for x in os.walk(base_directory)]

    # consider only nested subdirectories and put them in alphabetical order.
    # these are the folders: 10 min, 30 min, 1h, 2h, 3h
    nested_sub_directories = sorted(sub_directories[1:])

    # consider each duration's folder for this scenario
    for folder in nested_sub_directories:
        tot_pwr_bit_1 = 0
        tot_pwr_bit_0 = 0

        current_folder = os.fsdecode(folder)
        # list of capture files in this folder
        capture_files = []

        # get all capture files inside the duration folder
        for file in os.listdir(current_folder):
            filename = os.fsdecode(file)
            # all our captures are in .pcapng or .pcap format
            if filename.endswith(".pcapng") or filename.endswith(".pcap"):
                complete_file_name = os.path.join(current_folder, filename)
                capture_files.append(complete_file_name)

        nl = '\n'
        print("------------------------------------------------------------------------------------")
        print(f"Capture files in folder:\n{nl.join(capture_files)}")
        print("Please wait...\n")

        # iterate on all capture files inside the current folder
        for capture_file in capture_files:
            capture_pwr_bit_1 = 0
            capture_pwr_bit_0 = 0

            capture = pyshark.FileCapture(capture_file)
            # iterate on all packets in the capture
            for pkt in capture:

                try:
                    # consider only valid packets sent by the Nexus 5
                    if pkt['wlan'].get_field('sa') == 'PUT_HERE_YOUR_DEVICE_MAC_ADDRESS':

                            # get wlan.fc.pwrmgt field inside the packet
                            pwr_mgt_bit = pkt['wlan'].get_field('fc_pwrmgt')
                            if pwr_mgt_bit == '1':
                                capture_pwr_bit_1 += 1
                                tot_pwr_bit_1 += 1
                            elif pwr_mgt_bit == '0':
                                capture_pwr_bit_0 += 1
                                tot_pwr_bit_0 += 1
                except:
                     # packet corrupted, we don't consider it
                    continue

            # results of the capture
            print("Capture " + capture_file)
            print(f"PWR MGT BIT = 1: {capture_pwr_bit_1}")
            print(f"PWR MGT BIT = 0: {capture_pwr_bit_0}")
            print("Please wait...\n")

        tot_packets = tot_pwr_bit_1 + tot_pwr_bit_0
        # sanity check
        if tot_packets != 0:
            ratio_pwr_bit_1 = float("{0:.2f}".format(tot_pwr_bit_1 / tot_packets))
            ratio_pwr_bit_0 = float("{0:.2f}".format(1 - ratio_pwr_bit_1))
            avg_num_packets = float("{0:.2f}".format(tot_packets/len(capture_files)))

            print("DURATION RESULTS")
            print(f"AVG PWR MGT BIT = 1: {ratio_pwr_bit_1}")
            print(f"AVG PWR MGT BIT = 0: {ratio_pwr_bit_0}")
            print(f"AVG NUMBER OF PACKETS: {avg_num_packets}\n")

            # add results for this duration folder (e.g 10 minutes) to the overall scenario results
            pwr_mgt_bit_0_results.append(ratio_pwr_bit_0)
            pwr_mgt_bit_1_results.append(ratio_pwr_bit_1)
            avg_num_packets_results.append(avg_num_packets)

    # build power ratio plot for the scenario
    build_power_ratios_graph(scenario_name, pwr_mgt_bit_0_results, pwr_mgt_bit_1_results)

    # build average number of packets for the scenario
    build_avg_packets_graph(scenario_name, avg_num_packets_results)

# compute results for all the scenarios we need
def main():
    compute_results("./captures/00_Android_6/2.4_GHz", "Android 6 (Doze) - 2.4 GHz")
    compute_results("./captures/01_Android_4/2.4_GHz", "Android 4 (No Doze) - 2.4 GHz")
    compute_results("./captures/00_Android_6/5_GHz", "Android 6 (Doze) - 5 GHz")
    compute_results("./captures/01_Android_4/5_GHz", "Android 4 (No Doze) - 5 GHz")

if __name__ == '__main__':
    main()
