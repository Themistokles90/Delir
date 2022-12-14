import math
from tempfile import TemporaryFile

import numpy as np
import pandas as pd
import xlrd
import xlwt
import sys
#import xlsxwriter
from scipy.stats import normaltest
from scipy.stats import shapiro


#  comment in: numpy-array of data (ekznr, time, value) out: numpy-array of arrays (ekznr, value) data format:
#  erstes element: [0: ekznr, 1: setpoint], folgende elemente: [0: artflow, 1: offset, 2: druck1, 3: druck2,
#  4: PH_ART, 5: PCO2_ART, 6: PO2_ART, 7: PATARTDRUCK 8: TEMP_1, 9:TEMP_2]
def group_by_id(np_data_in, np_setpoint_in):
    temp_id = np_data_in[0, 0]
    temp_head = []
    temp_data = []
    temp_combined = []
    temp_setpoint = get_setpoint(temp_id, np_setpoint_in)
    data_out_arr = []
    idx = 1

    # append the id and setpoint for the first group
    temp_head.append([temp_id, temp_setpoint])
    # temp_head.append([temp_setpoint, 0])

    # go through the data array and append all matching values
    for x in np_data_in:

        # append values for the matching id
        if temp_id == x[0]:
            temp_data.append(
                [x[3], get_offset(temp_setpoint, x[3]), x[6], x[7], x[23], x[24], x[25], x[42], x[11], x[12]])

            # if last element is reached add the data to temp_combined because the else block won't trigger
            if idx == len(np_data_in):
                # temp_data = np.trim_zeros(temp_data, 'fb')
                # temp_data = add_offset(temp_setpoint, temp_data)
                for y in temp_head:
                    temp_combined.append(y)
                for y in temp_data:
                    temp_combined.append(y)

                data_out_arr.append(temp_combined)




        # build the combined element
        else:
            # temp_data = np.trim_zeros(temp_data, 'fb')
            # temp_data = add_offset(temp_setpoint, temp_data)
            for y in temp_head:
                temp_combined.append(y)
            for y in temp_data:
                temp_combined.append(y)

            data_out_arr.append(temp_combined)

            # clear temporary arrays
            temp_head = []
            temp_data = []
            temp_combined = []

            # update temp_id and temp_head
            temp_id = x[0]
            temp_setpoint = get_setpoint(temp_id, np_setpoint_in)
            temp_head.append([temp_id, get_setpoint(temp_id, np_setpoint_in)])
            # temp_head.append([get_setpoint(temp_id, np_setpoint_in), 0])

            temp_data.append(
                [x[3], get_offset(temp_setpoint, x[3]), x[6], x[7], x[23], x[24], x[25], x[42], x[11], x[12]])

        idx = idx + 1

    return (data_out_arr)
    # data_out_arr = crop_not_running(data_out_arr)
    # print_data(data_out_arr)


# TODO: crop list elements of flow-lists: only use data where machine is already running.
#  in case of ARTFLOW: values have to be above 1L for at least 4 minutes (from both list-ends)
#  to count the machine as "running"
#  MIT HANNES BESPRECHEN WIE MAN DAS VIABLE WINDOW DEFEINIEREN SOLL. 1L regel geht nicht wegen teils
#  hohen fluessen am anfang
#  schauen ob die ergebnisse so passen
def crop_not_running(in_data):
    temp_head = []
    temp_cropped = []
    temp_cropped_combined = []
    out_data = []
    temp_flowcounter = 0
    temp_is_running = False
    temp_start = 0
    temp_end = 0
    viable_window = 40
    splits = 12  # amount of needed values above x in a row
    needed_value = 1  # amount of needed value to count as "running"

    # traverse the data list of lists
    for x in in_data:
        temp_head = x[0]
        temp_cropped = x
        del temp_cropped[0]
        temp_start = 0
        temp_end = 0

        # traverse the list elements (= data set of one EKZNR) to find the startelement when machine can be considered "running"
        y = 1
        while y in range(1, len(x) - 12):

            if not temp_is_running:
                # check if 5 consecutive elements are in window
                z = y
                while z in range(y, y + 12) and not temp_is_running:
                    # for z in range(y, y+12):
                    # print(x[z][1])
                    if -viable_window <= x[z][1] <= viable_window:
                        temp_flowcounter = temp_flowcounter + 1
                        # print(temp_flowcounter)
                    else:
                        temp_flowcounter = 0
                        # print(temp_flowcounter)
                    if temp_flowcounter == 12:
                        # print(temp_flowcounter)
                        temp_start = y
                        print(str(temp_head[0]) + ": FLOW IST 4 MIN IM FENSTER ab " + str(y))
                        temp_flowcounter = 0
                        temp_is_running = True

                    z = z + 1

                temp_flowcounter = 0
            y = y + 1
            if y == len(x) - 12 and not temp_is_running:
                print(str(temp_head[0]) + ": kein valider Flow gefunden")

        temp_is_running = False

        # traverse the list in reversed order to find the last element where the machine is running
        y = len(x) - 1
        while y in range(12, len(x)):

            if not temp_is_running:

                # check if 5 consecutive elements are in window
                z = y

                while z in range(y - 11, y + 1) and not temp_is_running:

                    if -viable_window <= x[z][1] <= viable_window:
                        temp_flowcounter = temp_flowcounter + 1

                    else:
                        temp_flowcounter = 0

                    if temp_flowcounter == 12:
                        temp_end = y
                        print(str(temp_head[0]) + ": reverse FLOW IST 4 MIN IM FENSTER ab " + str(y))
                        temp_flowcounter = 0
                        temp_is_running = True

                    z = z - 1

                temp_flowcounter = 0
            y = y - 1
            if y == 12 and not temp_is_running:
                print(str(temp_head[0]) + ": reverse kein valider Flow gefunden")

        temp_is_running = False

        del temp_cropped[temp_end:len(temp_cropped)]
        del temp_cropped[0:temp_start]

        temp_cropped_combined.append(temp_head)
        temp_cropped_combined.append(temp_cropped)
        out_data.append(temp_cropped_combined)
        temp_head = []
        temp_cropped = []
        temp_cropped_combined = []

    return out_data


# alternative method that crops the data to running only entries.
# uses the fact that PH_ART, PCO2_ART and PO2_ART only have values when the hlm is running properly
# cave: start and end needs to be "trimmed" a bit to not mess up the dips later
# in: data list with head element (ekznr, setpoint) and data (flow, offset)
# out: cropped data list with head and data
def crop_not_running_alt(in_data):
    out_data = []
    print()
    print("Cropping data:")

    for operation_data in in_data:
        operation_head = operation_data.pop(0)
        operation_cropped = []
        is_running = False
        is_running_reverse = False
        temp_start = len(operation_data)
        temp_end = 0
        idx = 0
        cut_window = 0  # cut window: how much should be cut from start and end ofthe datachain?
        if len(operation_data) > 9:
            while idx < len(operation_data):
                if not math.isnan(operation_data[idx][6]) and not is_running and operation_data[idx][0] >= 1:
                    temp_start = idx + cut_window
                    is_running = True
                idx = idx + 1
            idx = len(operation_data) - 1
            while idx >= 0 and not is_running_reverse:
                if not math.isnan(operation_data[idx][6]) and not is_running_reverse and operation_data[idx][0] >= 1:
                    temp_end = idx - cut_window
                    is_running_reverse = True
                idx = idx - 1
            if is_running and is_running_reverse:
                print(str(operation_head[0]) + ": start: " + str(temp_start))
                print(str(operation_head[0]) + ": end: " + str(temp_end))

            else:
                print(str(operation_head[0]) + ": no valid start")
                print(str(operation_head[0]) + ": no valid end")

        else:
            print(str(operation_head[0]) + ": no valid start (empty)")
            print(str(operation_head[0]) + ": no valid end (empty)")

        del operation_data[temp_end:len(operation_data)]
        del operation_data[0:temp_start]

        operation_cropped.append(operation_head)
        operation_cropped.append(operation_data)
        out_data.append(operation_cropped)

    return out_data


def process_flow(in_ekz_data, window):
    head = in_ekz_data[0]
    ekz = head[0]
    setpoint = head[1]
    data = in_ekz_data[1]

    flow_min_abs = 0
    flow_max_abs = 0
    flow_min_rel = 0
    flow_max_rel = 0
    flow_min_windowed = 0
    flow_max_windowed = 0
    flow_window = window  # number of connected rows, 1 row equals 20 sec
    flow_mean = 0
    flow_median = 0
    flow_mean_offset = 0
    flow_median_offset = 0
    flow_total_neg_30_plus = 0
    flow_total_neg_10_to_30 = 0
    flow_total_within_10 = 0
    flow_total_pos_10_to_30 = 0
    flow_total_pos_30_plus = 0
    flow_cont_neg_30_plus = 0
    flow_cont_neg_10_to_30 = 0
    flow_cont_within_10 = 0
    flow_cont_pos_10_to_30 = 0
    flow_cont_pos_30_plus = 0

    # check_if_normal
    print()
    print("check_if_normal:")
    normal_counter = 0
    if len(data) >= 8:
        normal_counter = check_if_normal(in_ekz_data, 0, 'ARTFLOW1')
        if normal_counter == 0:
            print("Result: Data does not seem to be normal.")
        if normal_counter == 1:
            print("Result: Data might be Gaussian-like, further investigation needed")
        if normal_counter == 2:
            print("Result: Data seems to be normal")
    else:
        print("No Result; Dataset too small")

    # flow_min_abs, flow_min_rel, flow_max_abs, flow_max_rel:
    print()
    print("___________________________________________________________")
    print("Processing EKZ: " + str(ekz))
    print()
    if len(data) > 0:
        flow_min_abs = data[0][0]
        flow_max_abs = data[0][0]
    for row in data:
        print(row)
        if row[0] < flow_min_abs:
            flow_min_abs = row[0]
            flow_min_rel = row[1]
        if row[0] > flow_max_abs:
            flow_max_abs = row[0]
            flow_max_rel = row[1]
    print()
    print("flow_min_abs, flow_min_rel, flow_max_abs, flow_max_rel:")
    print("flow_min_abs: " + str(flow_min_abs))
    print("flow_min_rel: " + str(flow_min_rel))
    print("flow_max_abs: " + str(flow_max_abs))
    print("flow_max_rel: " + str(flow_max_rel))

    # flow_min_windowed, flow_max_windowed:
    print()
    print("flow_min_windowed, flow_max_windowed:")
    idx = 0
    temp_flow = 0
    while idx <= len(data) - flow_window:
        for window_idx in range(idx, idx + flow_window):
            temp_flow = temp_flow + data[window_idx][0]
        if idx == 0:
            flow_min_windowed = temp_flow / flow_window
            flow_max_windowed = temp_flow / flow_window
        if temp_flow / flow_window < flow_min_windowed:
            flow_min_windowed = temp_flow / flow_window
        if temp_flow / flow_window > flow_max_windowed:
            flow_max_windowed = temp_flow / flow_window
        temp_flow = 0
        idx = idx + 1
    print("flow_min_windowed: " + str(flow_min_windowed))
    print("flow_max_windowed: " + str(flow_max_windowed))

    # flow_total_neg_30_plus, flow_total_neg_10_to_30, flow_total_within_10, flow_total_pos_10_to_30, flow_total_pos_30_plus:
    print()
    print(
        "flow_total_neg_30_plus, flow_total_neg_10_to_30, flow_total_within_10, flow_total_pos_10_to_30, flow_total_pos_30_plus:")
    for row in data:
        if row[1] < -30:
            flow_total_neg_30_plus = flow_total_neg_30_plus + 20
        if -30 <= row[1] < -10:
            flow_total_neg_10_to_30 = flow_total_neg_10_to_30 + 20
        if -10 <= row[1] <= 10:
            flow_total_within_10 = flow_total_within_10 + 20
        if 10 < row[1] <= 30:
            flow_total_pos_10_to_30 = flow_total_pos_10_to_30 + 20
        if 30 < row[1]:
            flow_total_pos_30_plus = flow_total_pos_30_plus + 20
    print("flow_total_neg_30_plus: " + str(flow_total_neg_30_plus))
    print("flow_total_neg_10_to_30: " + str(flow_total_neg_10_to_30))
    print("flow_total_within_10: " + str(flow_total_within_10))
    print("flow_total_pos_10_to_30: " + str(flow_total_pos_10_to_30))
    print("flow_total_pos_30_plus: " + str(flow_total_pos_30_plus))

    # flow_cont_neg_30_plus, flow_cont_neg_10_to_30, flow_cont_within_10, flow_cont_pos_10_to_30, flow_cont_pos_30_plus:
    print()
    print(
        "flow_cont_neg_30_plus, flow_cont_neg_10_to_30, flow_cont_within_10, flow_cont_pos_10_to_30, flow_cont_pos_30_plus:")
    cathegory = 0
    temp_cont_neg_30_plus = 0
    temp_cont_neg_10_to_30 = 0
    temp_cont_within_10 = 0
    temp_cont_pos_10_to_30 = 0
    temp_cont_pos_30_plus = 0
    for row in data:

        if row[1] < -30 and cathegory == 1:
            temp_cont_neg_30_plus = temp_cont_neg_30_plus + 20
        if -30 <= row[1] < -10 and cathegory == 2:
            temp_cont_neg_10_to_30 = temp_cont_neg_10_to_30 + 20
        if -10 <= row[1] <= 10 and cathegory == 3:
            temp_cont_within_10 = temp_cont_within_10 + 20
        if 10 < row[1] <= 30 and cathegory == 4:
            temp_cont_pos_10_to_30 = temp_cont_pos_10_to_30 + 20
        if 30 < row[1] and cathegory == 5:
            temp_cont_pos_30_plus = temp_cont_pos_30_plus + 20

        if row[1] < -30 and cathegory != 1:
            temp_cont_neg_30_plus = 20
            cathegory = 1
        if -30 <= row[1] < -10 and cathegory != 2:
            temp_cont_neg_10_to_30 = 20
            cathegory = 2
        if -10 <= row[1] <= 10 and cathegory != 3:
            temp_cont_within_10 = 20
            cathegory = 3
        if 10 < row[1] <= 30 and cathegory != 4:
            temp_cont_pos_10_to_30 = 20
            cathegory = 4
        if 30 < row[1] and cathegory != 5:
            temp_cont_pos_30_plus = 20
            cathegory = 5

        if temp_cont_neg_30_plus > flow_cont_neg_30_plus:
            flow_cont_neg_30_plus = temp_cont_neg_30_plus
        if temp_cont_neg_10_to_30 > flow_cont_neg_10_to_30:
            flow_cont_neg_10_to_30 = temp_cont_neg_10_to_30
        if temp_cont_within_10 > flow_cont_within_10:
            flow_cont_within_10 = temp_cont_within_10
        if temp_cont_pos_10_to_30 > flow_cont_pos_10_to_30:
            flow_cont_pos_10_to_30 = temp_cont_pos_10_to_30
        if temp_cont_pos_30_plus > flow_cont_pos_30_plus:
            flow_cont_pos_30_plus = temp_cont_pos_30_plus

    print("flow_cont_neg_30_plus: " + str(flow_cont_neg_30_plus))
    print("flow_cont_neg_10_to_30: " + str(flow_cont_neg_10_to_30))
    print("flow_cont_within_10: " + str(flow_cont_within_10))
    print("flow_cont_pos_10_to_30: " + str(flow_cont_pos_10_to_30))
    print("flow_cont_pos_30_plus: " + str(flow_cont_pos_30_plus))

    # flow_mean, flow_median
    if len(data) != 0:
        temp_flow_only = []
        temp_offset_only = []
        for row in data:
            temp_flow_only.append(row[0])
            temp_offset_only.append(row[1])
        flow_mean = np.mean(temp_flow_only)
        flow_median = np.median(temp_flow_only)
        flow_mean_offset = np.mean(temp_offset_only)
        flow_median_offset = np.median(temp_offset_only)

    print()
    print("flow_mean, flow_median, flow_mean_offset, flow_median_offset:")
    print("flow_mean: " + str(flow_mean))
    print("flow_median: " + str(flow_median))
    print("flow_mean_offset: " + str(flow_mean_offset))
    print("flow_median_offset: " + str(flow_median_offset))

    # create exportable list filled with processed data:
    export_list = [["EKZ", head[0]],
                   ["Sollfluss", head[1]],
                   ["normal check", normal_counter],
                   ["min_abs", flow_min_abs],
                   ["min_rel", flow_min_rel],
                   ["max_abs", flow_max_abs],
                   ["max_rel", flow_max_rel],
                   ["min_windowed " + str(flow_window * 20) + " Sec", flow_min_windowed],
                   ["max_windowed " + str(flow_window * 20) + " Sec", flow_max_windowed],
                   ["mean_abs", flow_mean],
                   ["mean_rel", flow_mean_offset],
                   ["median_abs", flow_median],
                   ["median_rel", flow_median_offset],
                   ["<= -30% Sec total", flow_total_neg_30_plus],
                   ["]-30% - -10%] Sec total", flow_total_neg_10_to_30],
                   ["-10% - 10% Sec total", flow_total_within_10],
                   ["10% - 30% Sec total", flow_total_pos_10_to_30],
                   [">=30% ueber Soll ges.", flow_total_pos_30_plus],
                   ["Sek >=30% unter Soll cont.", flow_cont_neg_30_plus],
                   ["Sek 10%-30% unter Soll cont.", flow_cont_neg_10_to_30],
                   ["Sek 10% um Soll cont.", flow_cont_within_10],
                   ["Sek 10%-30% ueber Soll cont.", flow_cont_pos_10_to_30],
                   ["Sek >=30% ueber Soll cont.", flow_cont_pos_30_plus]]

    return export_list


def process_data(in_ekz_data, window, id_parameter, list_groups):
    # if id_parameter == 0:
    #    return process_flow(in_ekz_data, window)
    # if id_parameter == 1:
    #    return

    # list_groups: [from, to] [from, to] ,....
    head = in_ekz_data[0]
    ekz = in_ekz_data[0][0]
    setpoint = in_ekz_data[0][1]
    data = in_ekz_data[1]
    pointer = id_parameter  # 0-9
    # id info: erstes element: [0: ekznr, 1: setpoint], folgende elemente: [0: artflow, 1: offset, 2: druck1,
    # 3: druck2, 4: PH_ART, 5: PCO2_ART, 6: PO2_ART, 7: PATARTDRUCK 8: TEMP_1, 9:TEMP_2]
    name_parameter = get_parameter_name(id_parameter)
    nan_marker = 0
    min_abs = 0
    max_abs = 0
    window = window
    min_windowed = 0
    max_windowed = 0
    mean = 0
    median = 0
    list_data = []
    list_export = []

    print()
    print("___________________________________________________________")
    print("Processing " + name_parameter + " for EKZ: " + str(ekz))

    # list_export[0] = [get_parameter_name(id_parameter)]
    # adding the EKZ to list_export
    list_export.append(["EKZ", head[0]])

    # extracting data:
    for element in data:
        # print(element)
        list_data.append(element[pointer])
    # print_data(list_data)

    # check_for_NAN:
    for element in list_data:
        if math.isnan(element):
            nan_marker += 1
    list_data = [element for element in list_data if not math.isnan(element)]
    list_export.append(["NaN_marker", nan_marker])

    # check_if_normal
    print()
    print(name_parameter + ": check_if_normal:")
    temperature_normal_counter = 0
    if len(data) >= 8:
        temperature_normal_counter = check_if_normal(in_ekz_data, pointer, name_parameter)
        if temperature_normal_counter == 0:
            print(name_parameter + ": Result: Data does not seem to be normal.")
        if temperature_normal_counter == 1:
            print(name_parameter + ": Result: Data might be Gaussian-like, further investigation needed")
        if temperature_normal_counter == 2:
            print(name_parameter + ": Result: Data seems to be normal")
    else:
        print(name_parameter + ": No Result; Dataset too small")
    list_export.append(["normal check", temperature_normal_counter])

    if id_parameter == 0:
        list_export.append(["target value", setpoint])

    # Min, Max
    if len(list_data) > 0:
        min_abs = list_data[0]
        max_abs = list_data[0]

    for element in list_data:
        # print(row)
        if element < min_abs:
            min_abs = element
        if element > max_abs:
            max_abs = element
    print()
    print(name_parameter + ": min_abs, max_abs:")
    print(name_parameter + ": min_abs: " + str(min_abs))
    print(name_parameter + ": max_abs: " + str(max_abs))
    # add min_abs and max_abs to list_export:
    list_export.append(["min_abs", min_abs])
    list_export.append(["max_abs", max_abs])

    # windowed min, max
    print()
    print(name_parameter + ": min_windowed, max_windowed:")
    idx = 0
    temp_ph_art = 0
    while idx <= len(list_data) - window:
        for window_idx in range(idx, idx + window):
            temp_ph_art = temp_ph_art + list_data[window_idx]
        if idx == 0:
            min_windowed = temp_ph_art / window
            max_windowed = temp_ph_art / window
        if temp_ph_art / window < min_windowed:
            min_windowed = temp_ph_art / window
        if temp_ph_art / window > max_windowed:
            max_windowed = temp_ph_art / window
        temp_ph_art = 0
        idx = idx + 1
    print(name_parameter + ": min_windowed: " + str(min_windowed))
    print(name_parameter + ": max_windowed: " + str(max_windowed))
    # add min_windowed and max_windowed to list_export:
    list_export.append(["min_windowed " + str(window * 20) + " Sec", min_windowed])
    list_export.append(["max_windowed " + str(window * 20) + " Sec", max_windowed])

    # Mean , Median
    if len(list_data) != 0:
        mean = np.mean(list_data)
        median = np.median(list_data)
    print()
    print(name_parameter + ": mean, median:")
    print(name_parameter + ": mean: " + str(mean))
    print(name_parameter + ": median: " + str(median))
    # add mean and median to list_export:
    list_export.append(["mean", mean])
    list_export.append(["median", median])

    # processing the groups:
    print()
    print(name_parameter + ": total and cont sek groups:")

    # preparing the list.groups for temp values
    for group in list_groups:
        group.append(0)  # group[2] : total sek
        group.append(0)  # group[3] : temp cont sek
        group.append(0)  # group[4] : cont sek
        # print(group)

    pointer_group = -1
    for element in list_data:
        for id_group, group in enumerate(list_groups):
            # print(list_groups)
            if group[0] <= element < group[1]:
                group[2] += 20
                if pointer_group != id_group:
                    group[3] = 20
                    pointer_group = id_group
                else:
                    group[3] += 20
                if group[3] > group[4]:
                    group[4] = group[3]

    for group in list_groups:
        print(
                name_parameter + ": group " + str(group[0]) + " (incl) - " + str(group[1]) + " (excl) total: " + str(
            group[2]))
        print(name_parameter + ": group " + str(group[0]) + " (incl) - " + str(group[1]) + " (excl) cont: " + str(
            group[4]))
        list_export.append([str(group[0]) + " incl to " + str(group[1]) + " excl total", group[2]])
        list_export.append([str(group[0]) + " incl to " + str(group[1]) + " excl cont", group[4]])

    print(list_export)

    return list_export


def check_if_normal(ekz_data_in, dimension, name_parameter):
    normal_counter = 0
    idx = 0
    data_to_check = []
    while idx in range(0, len(ekz_data_in[1])):
        data_to_check.append(ekz_data_in[1][idx][dimension])
        idx += 1

    # Shapiro-Wilk Test:
    stat, p = shapiro(data_to_check)
    print(name_parameter + ': Shapiro test: Statistics=%.3f, p=%.3f' % (stat, p))
    alpha = 0.05
    if p > alpha:
        print(name_parameter + ': Shapiro test: Sample looks Gaussien (fail to reject H0')
        normal_counter += 1
    else:
        print(name_parameter + ': Shapiro test: Sample does not look Gaussien (reject H0)')

    # D'Agostino's K^2 Test
    stat, p = normaltest(data_to_check)
    print(name_parameter + ': Agostino test: Statistics=%.3f, p=%.3f' % (stat, p))
    # interpret
    alpha = 0.05
    if p > alpha:
        print(name_parameter + ': Agostino test: Sample looks Gaussian (fail to reject H0)')
        normal_counter += 1
    else:
        print(name_parameter + ': Agostino test: Sample does not look Gaussian (reject H0)')

    # Anderson-Darling Test
    # result = anderson(data_to_check)
    # print('Statistic: %.3f' % result.statistic)
    # p = 0
    # for i in range(len(result.critical_values)):
    #    sl, cv = result.significance_level[i], result.critical_values[i]
    #    if result.statistic < result.critical_values[i]:
    #        print('%.3f: %.3f, data looks normal (fail to reject H0)' % (sl, cv))
    #    else:
    #        print('%.3f: %.3f, data does not look normal (reject H0)' % (sl, cv))

    return normal_counter


# in: setpoint and value
# out: offset in percent
def get_offset(in_setpoint, in_value):
    print(in_value)
    print(in_setpoint)

    if in_value == in_setpoint:
        return 0
    try:
        return ((in_value - in_setpoint) / in_setpoint) * 100
    except ZeroDivisionError:
        return 100


# in: EKZNr as id, setpoint array
# out: Setpoint for this EKZNr
# if no setpoint found, return 0
def get_setpoint(ekznr, np_setpoint_in):
    setpoint_temp = 0
    for x in np_setpoint_in:
        if ekznr == x[0]:
            setpoint_temp = x[1]
    if setpoint_temp == 0:
        print("NO SETPOINT")
    return setpoint_temp


# in: filename
# return: numpy array
def load_xlsx(filename):
    #df_data = pd.read_excel(filename, sheet_name=None)

    df_data = pd.read_excel(filename, engine='openpyxl')

    #try:

    #except:
    #    print("Error, : " + str(sys.exc_info()[0]) + " occurred, check placement and name of files")

    np_data = df_data.to_numpy()
    return np_data

def load_xls(filename):
    #try:
    df_data = pd.read_excel(filename)

    #except:
     #   print("Error, : " + str(sys.exc_info()[0]) + " occurred, check placement and name of files")



    np_data = df_data.to_numpy()
    return np_data

def load_csv(filename):
    #try:
    df_data = pd.read_csv(filename)

    #except:
        #print("Error, : " + str(sys.exc_info()[0]) + " occurred, check placement and name of files")



    np_data = df_data.to_numpy()
    return np_data



def print_data(in_data):
    print()
    print("Dataprint:")
    for x in in_data:
        print(x)


def save_file(export_list, year):
    print()
    print("writing to file: export_data.xlsx")
    book = xlwt.Workbook(encoding="utf-8")

    for parameter in export_list:
        print(parameter[0])
        sheet = book.add_sheet(parameter[0][0])
        print(parameter)
        for column, title in enumerate(parameter[1][0]):
            sheet.write(0, column, title[0])
        for row, ekz_data in enumerate(parameter[1]):
            for column, data in enumerate(ekz_data):
                # print(data)
                sheet.write(row + 1, column, data[1])

    name = "Resources/"+str(year) +"/"+str(year)+"_export_data.xlsx"
    book.save(name)
    book.save(TemporaryFile())


def get_parameter_name(id_parameter):
    # id info: erstes element: [0: ekznr, 1: setpoint], folgende elemente: [0: artflow, 1: offset, 2: druck1, 3: druck2, 4: PH_ART, 5: PCO2_ART, 6: PO2_ART, 7: PATARTDRUCK 8: TEMP_1, 9:TEMP_2]
    return {
        0: "ARTFLOW",
        1: "OFFSET",
        2: "DRUCK1",
        3: "DRUCK2",
        4: "PH_ART",
        5: "PCO2_ART",
        6: "PO2_ART",
        7: "PATARTDRUCK",
        8: "TEMP_1",
        9: "TEMP_2"
    }.get(id_parameter)


def get_groups(id_parameter):
    # [0: artflow, 1: offset, 2: druck1, 3: druck2, 4: PH_ART, 5: PCO2_ART, 6: PO2_ART, 7: PATARTDRUCK 8: TEMP_1,
    # 9:TEMP_2]
    return {
        0: [[-float('inf'), 1.5], [1.5, 3], [3, 4.5], [4.5, 6], [6, float('inf')]],
        1: [[-float('inf'), -50], [-50, -30], [-30, -10], [-10, 10], [10, 30], [30, float('inf')]],
        2: [[-float('inf'), 120], [120, 160], [160, 200], [200, 240], [240, 280], [280, float('inf')]],
        3: [[-float('inf'), 120], [120, 160], [160, 200], [200, 240], [240, 280], [280, float('inf')]],
        4: [[-float('inf'), 6.8], [6.8, 7], [7, 7.2], [7.2, 7.4], [7.4, 7.6], [7.6, float('inf')]],
        5: [[-float('inf'), 20], [20, 30], [30, 40], [40, 50], [50, 60], [60, float('inf')]],
        6: [[-float('inf'), 70], [70, 110], [110, 140], [140, 190], [190, 240], [240, float('inf')]],
        7: [[-float('inf'), 40], [40, 60], [60, 80], [80, 100], [100, float('inf')]],
        8: [[-float('inf'), 31], [31, 33], [33, 35], [35, 37], [37, 39], [39, float('inf')]],
        9: [[-float('inf'), 31], [31, 33], [33, 35], [35, 37], [37, 39], [39, float('inf')]],
    }.get(id_parameter)


# DEBUG with example data
def process_example_data():
    data_in = group_by_id(
        load_xlsx('Resources/example_full_data.xlsx'),
        load_xlsx('Resources/2014_setpoint.xlsx'))
    data_cropped = crop_not_running_alt(data_in)
    print_data(data_cropped)
    list_export_complete = []
    list_export_parameter = [[], []]
    window = 7

    for id_parameter in range(0, 9):
        list_export_parameter[0] = [get_parameter_name(id_parameter)]
        list_export_parameter[1] = []

        for ekz_data in data_cropped:
            # noinspection PyTypeChecker
            list_export_parameter[1].append(process_data(ekz_data, window, id_parameter, get_groups(id_parameter)))

        list_export_complete.append(list_export_parameter)
        list_export_parameter = [[], []]

    print_data(list_export_complete)

    save_file(list_export_complete)


def process_full_data():
    for year in range(2019, 2020):
        data_in = group_by_id(
            load_xlsx("Resources/" + str(year) + "PERFUSION.xlsx"),
            load_xlsx('Resources/targetflow.xlsx'))
        data_cropped = crop_not_running_alt(data_in)
        print_data(data_cropped)
        list_export_complete = []
        list_export_parameter = [[], []]
        window = 7

        for id_parameter in range(0, 9):
            list_export_parameter[0] = [get_parameter_name(id_parameter)]
            list_export_parameter[1] = []

            for ekz_data in data_cropped:
                # noinspection PyTypeChecker
                list_export_parameter[1].append(process_data(ekz_data, window, id_parameter, get_groups(id_parameter)))

            list_export_complete.append(list_export_parameter)
            list_export_parameter = [[], []]

        print_data(list_export_complete)

        save_file(list_export_complete, year)


def calculate_targetflow(year):
    print("reading patclin for year (" + year + ") and calculating target flow...")


def process_data_of_year(year):
    create_targetflow_from_patclin_of_year(year)
    data_in = group_by_id(
        load_xlsx("Resources/" + str(year) + "/PERFUSION.xlsx"),
        load_xls("Resources/" + str(year) + "/targetflow.xls"))
    data_cropped = crop_not_running_alt(data_in)
    print_data(data_cropped)
    list_export_complete = []
    list_export_parameter = [[], []]
    window = 7

    for id_parameter in range(0, 9):
        list_export_parameter[0] = [get_parameter_name(id_parameter)]
        list_export_parameter[1] = []

        for ekz_data in data_cropped:
            # noinspection PyTypeChecker
            list_export_parameter[1].append(process_data(ekz_data, window, id_parameter, get_groups(id_parameter)))

        list_export_complete.append(list_export_parameter)
        list_export_parameter = [[], []]

    print_data(list_export_complete)

    save_file(list_export_complete, year)

def save_targetflow(targetflow_list, year):
    print()
    print("writing to file: targetflow.xls")
    df = pd.DataFrame(targetflow_list)
    writer = pd.ExcelWriter('Resources/'+str(year)+'/targetflow.xls', engine='xlwt')
    df.to_excel(writer, sheet_name='targetflow', index = False)
    writer.save()

def create_targetflow_from_patclin_of_year(year):
    print("...reading PATCLIN.xls from " + str(year) + "...")
    patclin_in = load_xls("Resources/" + str(year) + "/PATCLIN.xls")
    print(patclin_in)
    #calculate BSA , then targetflow.
    # BSA = sqrt(WeightKG * HeightCM)/60
    # TF = BSA * 2,4
    targetflow = []
    tf_iterator = 0
    for element in patclin_in:
        #targetflow.append([element[0], calculate_targetflow(element[5], element[4])])
        targetflow.append([element[0], element[8]])
        #print targetflow[tf_iterator]
        tf_iterator = tf_iterator+1
    print(targetflow)

    save_targetflow(targetflow,year)


def calculate_targetflow(weight, height):
    return round((np.sqrt(float(weight)*float(height))/60)*2.4, 2)

def comma_to_dot (number):
    try:
        number = number.replace(',', '.')
    except:
        print
    return number


print("Make sure all needed files are named correctly (PERFUSION.xls or PATCLIN.xlsx) and located in /Resources/[year].")
year = input("Enter year to process data:")
process_data_of_year(year)
#create_targetflow_from_patclin_of_year(year)