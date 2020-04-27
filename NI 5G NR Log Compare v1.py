#!/usr/bin/python
# -----------------------------------------------------------------------------------
# NI 5G NR Log Compare.py
# This script reads, parses and compares 5G NR gNB and UE log files slot by slot.
#
# (C) 2020 Jun Chen, Santa Clara, USA
# Released under GNU Public License (GPL)
# Email: jun.chen@ni.com
# Version: 1.0
#  -----------------------------------------------------------------------------------
""" this script is tested using Python 3.7.4"""
import time
import datetime
import sys
import os
import os.path
from os import path

# Global Flags
flag_debug_mode=False   # Debug mode?
# Search and match the 1st HARQ id between gNB and UE after RACH success
flag_harq_id_align_on_1st_pdcch=False
# Print all searched PDCCH items from UE log file?
flag_print_ue_searched_pdcch_list=False
# Print all searched PDCCH items from gNB log file?
flag_print_gnb_searched_pdcch_list=False

# if ue_pdcch_dci11_num_max is zero, the program scans all PDCCH DCI 1_1 messsags in the log file
ue_pdcch_dci11_num_max=200 # maximum number of PDCCH DCI1_1 messages to read and parse

# drawbar length
drawbar_len=40

def drawProgressBar(percent, barLen = 20, status="Processing"):
    """ draw a progress bar on the screen with percentage and bar length"""
    sys.stdout.write("\r")
    progress = ""
    for i in range(barLen):
        if i < int(barLen * percent):
            progress += "="
        else:
            progress += " "
    if percent >=1.0:
        status="     Done!"
    sys.stdout.write("[ %s %s] %.2f%%" % (progress, status, percent * 100))
    sys.stdout.flush()

def countLines (fileName):
    """ Count the number of lines in a text file"""
    #start_time = datetime.datetime.now()
    #print ("Reading number of lines from a txt file: " + fileName + "......\n")
    num_lines = open(fileName).read().count('\n')
    #stop_time =  datetime.datetime.now()
    #delta_time=stop_time - start_time
    #elapsed_time_ms = int(delta_time.total_seconds() * 1000) # milliseconds
    #print ("Number of lines: " + str(num_lines) + " \n" )
    #print ("Elapsed time: " + str(elapsed_time_ms) + " ms\n")
    return num_lines

def comparePrintUeGnBLogResults(msg_count, ue_field_name_pat_arr, gn_field_name_pat_arr,  ue_field_var, gn_field_var,
                                flag_connected_state_found, flag_1st_pdcch_harq_after_rach_matched, flag_print_pdcch_list):
    """ Compare log results between UE and gNB log data """
    status="N/A"
    flag_print_all_mismatched_fields=False

    if flag_connected_state_found :
        status="RACH Success"
    else:
        status="RACH Failed"
    if flag_connected_state_found and flag_1st_pdcch_harq_after_rach_matched:
        status = status + " + " + "1st HARQ id is matched after RACH success"


    # Compute # of mismatched fields between UE and gNB log data
    num_field_gn=len(gn_field_name_pat_arr)
    num_field_ue=len(ue_field_name_pat_arr)
    mismatched_field_arr=[]
    mismatched_list=[];
    mismatched_list_2d=[[0]*msg_count for i in range(num_field_gn)]

    if (msg_count<1):
        for i in range(num_field_gn):
            mismatched_field_arr.append("N/A")
    else:
        mismatched_field_arr = [0 for i in range(num_field_gn)]
        for idx in range(msg_count):
            val_ue=ue_field_var[num_field_ue*idx: num_field_ue*(idx+1)]
            # Combine DCI bits[0] and DCI bits[1]
            tmp="%s%s" % (str(val_ue[-2]), str(val_ue[-1]))
            val_ue=val_ue[0:-2]
            #print(val_ue)
            val_ue.append(tmp)
            #print(val_ue)
            # Change PRB end to PRB length
            val_ue[6]=val_ue[6]-val_ue[5]+1
            # gNB field values
            val_gn = gn_field_var[num_field_gn * idx: num_field_gn * (idx + 1)]
            #print(gn_field_var)

            flag_mismatch=False
            for idx2 in range (num_field_gn):
                v_ue=val_ue[idx2]
                v_gn=val_gn[idx2]
                if idx2==num_field_gn -1:
                   digits=len( gn_field_var[-1])
                   v_ue=v_ue[0:digits]
                   #print(v_ue)
                   #print(v_gn)
                if v_ue != v_gn:
                        mismatched_field_arr[idx2]+=1
                        flag_mismatch=True
                        mismatched_list_2d[idx2][idx]=1
                else:
                        mismatched_list_2d[idx2][idx] = 0
            if flag_mismatch:
                mismatched_list.append(idx)

     # Print

    print("\n---------------------------------------------------------------------------")

    print("Summary of UE and gNB log data parsing and comparison")
    print("UE Status: %s \n" %status)
    field_name_list = ue_field_name_pat_arr[0:-2]
    print("%20s %20s" %("Item", "Mismatched Count"))
    field_name_list.append("DCI bits")
    for i in range (len(field_name_list)):
        if (msg_count < 1):
            print("%20s %20s" % (field_name_list[i], mismatched_field_arr[i]))
        else:
           print("%20s %20d" %(field_name_list[i], mismatched_field_arr[i]))

    print("---------------------------------------------------------------------------")


    # Print mismatched items in each category (field name)
    for idx in range (num_field_gn-1, -1, -1):
        if mismatched_field_arr[idx] ==0:
            continue
        # Print mismatched field values
        print("\nList of mismatched %s field between gNB and UE log messages: " % gn_field_name_pat_arr[idx])
        print("    UE  : %s" % ue_field_name_pat_arr)
        print("    gNB : %s" % gn_field_name_pat_arr)
        count=0
        for idx2 in range (msg_count):
             if  mismatched_list_2d [idx][idx2] > 0:
                # UE field values
                val_ue = ue_field_var[num_field_ue * idx2: num_field_ue * (idx2 + 1)]
                print("%3d.UE  : %s" % (count + 1, val_ue))

                # gNB field values
                val_gn = gn_field_var[num_field_gn * idx2: num_field_gn * (idx2 + 1)]
                print("    gNB : %s" % (val_gn))
                count +=1


    # Print a list of all mistached items
    idx=0;
    if flag_print_all_mismatched_fields and len(mismatched_list)>0:
        # Print mismatched field values
        print("\nList of mismatched fields between gNB and UE log messages: ")
        print("    UE  : %s" %ue_field_name_pat_arr)
        print("    gNB : %s" %gn_field_name_pat_arr)
        for mismatched_idx in mismatched_list:
            # UE field values

            val_ue = ue_field_var[num_field_ue * mismatched_idx: num_field_ue * (mismatched_idx + 1)]
            print("%3d.UE  : %s" %(idx+1, val_ue))

            # gNB field values
            val_gn = gn_field_var[num_field_gn * mismatched_idx: num_field_gn * (mismatched_idx + 1)]
            print("    gNB : %s" % (val_gn))

    if flag_print_pdcch_list and msg_count>0:
        # Print field values of searched PDCCH messages in gNB log file
        print("\nList of searched PDCCH messages with fields between gNB and UE log messages: ")
        print("    UE  : %s" %ue_field_name_pat_arr)
        print("    gNB : %s" %gn_field_name_pat_arr)
        for idx in range(msg_count):
            # UE field values

            val_ue = ue_field_var[num_field_ue * idx: num_field_ue * (idx + 1)]
            print("%3d.UE  : %s" %(idx+1, val_ue))

            # gNB field values
            val_gn = gn_field_var[num_field_gn * idx: num_field_gn * (idx + 1)]
            print("    gNB : %s" % (val_gn))
            #idx +=1

def readParseUeLogData(f_ue_log, ue_field_name_pat_arr, ue_log_conn_pattern, ue_log_sync_pattern, ue_log_dcitype_pattern,
                        ue_log_chtype_pattern, ue_pdcch_dci11_num_max, flag_debug_mode, flag_print_pdcch_list):
    ue_field_var=[]
    flag_connected_state_found = False


    # Search Connected string
    # # e.g. 2020-03-10 23:29:00.247479 [PHY ] [INFO] SYSTEM:  {system state: Connected, sync valid: TRUE}
    #ue_log_conn_pattern="Connected"
    #ue_log_sync_pattern="sync valid: TRUE"
    #ue_log_dcitype_pattern="DCIType: 1_1"
    #ue_log_chtype_pattern="PDCCH"

    print ("Reading lines and searching Connected status from NR UE log file...")
    print ("UE log file name: %s" % (file_name_ue_log))
    print ("Number of lines: " + str(num_lines_ue_log))

    if num_lines_ue_log < 1:
        print ("ERROR: empty NR UE log file ! \n")
        #sys.exit(-1)  # Exit main program
        return [ue_field_var, flag_connected_state_found]

    progressbar_step_lines=50;
    line_idx=0;  # zero-based line index for reading a file

    conn_state_line_idx=0
    pdcch_dci11_count=0
    # A space of searched PDCCH slots with DCI 1_1
    #lines_to_read = [conn_state_line_idx, num_lines_ue_log]
    pdcch_dci11_list = []  # a list of searched PDCCH messages
    for line in f_ue_log.readlines():
        if (line_idx % progressbar_step_lines==0):
            progressbar_label="Line "+str(line_idx)
            drawProgressBar( line_idx/num_lines_ue_log, drawbar_len, progressbar_label)
        if not flag_connected_state_found and line.find(ue_log_conn_pattern) > 0 and line.find(ue_log_sync_pattern) >0:
            print ("\n"+line)
            print ("Connected and SYNC states were found at Line %d !" % (line_idx+1))
            flag_connected_state_found=True
            conn_state_line_idx=line_idx
            print("\nSearching PDCCH messages with DCI 1_1 format...")
        if flag_connected_state_found:
            # Search PDCCH DCI 1_1
            # Example:
            # 2020-03-10 23:29:19.938827 [PHY ] [INFO] PDCCH:  {SFN: 465, SlotNo: 11, DCIType: 1_1, DCI Length: 50,
            # CC: 0, NLayers: 4, MCS: 31, PdschStartSymbol: 1, PdschLenSymbol: 13, PRB start: 0, PRB end: 272,
            # NoREs: 39312, TBsize: 868584, RV: 0, HARQProcNo: 12, NDIToggled: 0, RNTI type: 0,
            # DciBits[0]: 0xFFFFE1F1, DciBits[1]: 0x88140000, DciBits[2]: 0x00000000}
            if line.find(ue_log_chtype_pattern) >0 and line.find(ue_log_dcitype_pattern) >0:
                pdcch_dci11_list.append(line)
                pdcch_dci11_count+=1
        line_idx +=1  # increase line index
        if  ue_pdcch_dci11_num_max>0 and pdcch_dci11_count>=ue_pdcch_dci11_num_max:
            print ("\nStop searching PDCCH DCI 1_1 messages as the maximum number of %d messages are acquired !" % (ue_pdcch_dci11_num_max))
            break;

    drawProgressBar( 1.0, drawbar_len)

    # print PDCCH DCI 1_1 information
    print("\nNumber of PDCCH DCI 1_1 messages: %d" % (pdcch_dci11_count))
    if pdcch_dci11_count > 1:
       print("The first PDCCH DCI 1_1 message: ")
       print(pdcch_dci11_list[0])
       print("The last PDCCH DCI 1_1 message: ")
       print(pdcch_dci11_list[-1])
    else:
        print ("ERROR: PDCCH DCI 1_1 messages were NOT found in the UE log file ! \n")
        #sys.exit(-1)  # Exit main program

    if not flag_connected_state_found:
        print ("ERROR: Connected and SYNC states were NOT found in the UE log file ! \n")
        #sys.exit(-1)  # Exit main program

    if not flag_connected_state_found or pdcch_dci11_count <1:
        return [ue_field_var, flag_connected_state_found]  # Error, exit function !

    ue_field_len= len(ue_field_name_pat_arr)
    ue_dci_digi_len = 8

    print("\nParsing fields and extracting field values from PDCCH DCI 1_1 messages (NR UE log data)...")
    for line in pdcch_dci11_list:
        if flag_debug_mode:
            print(line)
        for i, search_str in enumerate(ue_field_name_pat_arr):
            pos1 = line.find(search_str)
            substr = line[pos1 + len(search_str) + 1:]
            if search_str.find("DciBits") >= 0:
                pos2 = substr.find("0x")
                substr2 = substr[pos2 + 2:pos2 + 10]
                substr2 = substr2.strip()
                if flag_debug_mode:
                    print("%s=%s" % (search_str, substr2.upper()))
                ue_field_var.append(substr2.upper())

            else:
                pos2 = substr.find(",")
                substr2 = substr[0:pos2]
                val = int(substr2.strip())
                if flag_debug_mode:
                   print("%s=%d" % (search_str, val))
                ue_field_var.append(val)
    if flag_debug_mode:
       print('List of ue_field_var is %s' % str(ue_field_var))

    if len(ue_field_var)> 0:
       print("List of extracted field values from the first PDCCH DCI 1_1 message: ")
       print(ue_field_var[0:ue_field_len ])
    if len(ue_field_var)> 1:
       print("List of extracted field values from the last PDCCH DCI 1_1 message: ")
       print(ue_field_var[-ue_field_len:-1])

    print("Number of parsed PDCCH DCI 1_1 messages:     %d" % (len(ue_field_var)/ue_field_len))

    if flag_debug_mode and flag_print_pdcch_list and len(ue_field_var)>0:
        # Print field values of searched PDCCH messages in UE log file
        print("\nList of searched PDCCH messages with fields from UE log file: ")
        print("    UE  : %s" %ue_field_name_pat_arr)
        for idx in range(len(ue_field_var)):
            # UE field values
            val_ue = ue_field_var[ue_field_len * idx: ue_field_len * (idx + 1)]
            print("%3d.UE  : %s" %(idx+1, val_ue))

    return [ue_field_var, flag_connected_state_found]

def searchExtractUeGnbLogFields (pdcch_line_arr, ue_field_var,pdcch_dci11_count,ue_field_len,
                                 gn_field_name_pat_arr, sfn_curr, slot_idx_curr, harq_id_curr, flag_harq_id_check,
                                 log_dict_sfn_slot_occur):
    gn_field_var=[]
    flag_matched_pdcch_frame=False
    gn_log_dcibits_pat = "DCI bits"  # DCI bits pattern

    matched_sfn_slot_count=0  # start from zero!
    sfn_slot_occur=1
    for ue_pdcch_idx in range (pdcch_dci11_count):
        sfn = ue_field_var[ue_pdcch_idx * ue_field_len]
        slot_idx = ue_field_var[ue_pdcch_idx * ue_field_len + 1]
        if (sfn_curr==sfn) and (slot_idx_curr==slot_idx):
            matched_sfn_slot_count +=1
            if matched_sfn_slot_count==1:
               [log_dict_sfn_slot_occur, sfn_slot_occur] = updateSfnSlotOccurence(log_dict_sfn_slot_occur, sfn_curr,
                                                                               slot_idx_curr)

            if sfn_slot_occur==matched_sfn_slot_count:
                if flag_harq_id_check:
                    harq_id = ue_field_var[ue_pdcch_idx * ue_field_len + 7]
                    if harq_id_curr==harq_id:
                        flag_matched_pdcch_frame=True
                    else:
                        flag_matched_pdcch_frame=False
                else:
                    flag_matched_pdcch_frame=True
            else:
                 flag_matched_pdcch_frame=False
            if flag_matched_pdcch_frame:
               break

    ue_pdcch_matched_idx=ue_pdcch_idx

    if not flag_matched_pdcch_frame:
        return [flag_matched_pdcch_frame, gn_field_var, ue_pdcch_matched_idx, log_dict_sfn_slot_occur]

    # print (gn_pdcch_list_tmp)
    for i, search_str in enumerate(gn_field_name_pat_arr):
        for x in pdcch_line_arr:
            if x.find(search_str) >= 0:
                substr1 = x[x.rfind(":") + 1:]
                if search_str == gn_log_dcibits_pat:  # DCI bits field
                    substr2 = substr1.strip()
                    # if flag_debug_mode:
                    #  print("%s, string=%s" % (search_str, substr2))
                    gn_field_var.append(substr2.upper())
                    break

                else:  # other fields
                    val = int(substr1.strip())
                    # if flag_debug_mode:
                    #   print("%s, val=%d" % (search_str, val))
                    gn_field_var.append(val)
                    break

    sfn_gn = ue_field_var[ue_pdcch_idx * ue_field_len]
    slot_idx_gn = ue_field_var[ue_pdcch_idx * ue_field_len + 1]

    if (sfn!=sfn_gn or slot_idx_gn !=slot_idx):
        print ("\mERROR: Parsed SFN and Slot values are not equal to current SFN and Slot: sfn=%d, sfn_gn=%d, slot_idx=%d, slot_idx_gn=%d !" %(sfn, sfn_curr, slot_idx, slot_idx_curr))

    if flag_debug_mode:
        print('\nList of PDCCH fields is %s' % str(gn_field_var))

    return [flag_matched_pdcch_frame, gn_field_var, ue_pdcch_matched_idx, log_dict_sfn_slot_occur]

def computeSfnSlotOccurence(ue_field_var,pdcch_dci11_count,ue_field_len):
    ue_log_sfn_slot_occur={}
    for ue_pdcch_idx in range (pdcch_dci11_count):
        sfn = ue_field_var[ue_pdcch_idx * ue_field_len]
        slot_idx = ue_field_var[ue_pdcch_idx * ue_field_len + 1]
        name="SFN="+str(sfn)+","+"Slot="+str(slot_idx)
        if name in ue_log_sfn_slot_occur:
            ue_log_sfn_slot_occur[name] +=1
        else:
            ue_log_sfn_slot_occur.update({name: 1})
    return ue_log_sfn_slot_occur


def updateSfnSlotOccurence(log_dict_sfn_slot_occur, sfn,slot_idx):
    name="SFN="+str(sfn)+","+"Slot="+str(slot_idx)
    if name in log_dict_sfn_slot_occur:
        log_dict_sfn_slot_occur[name] +=1
    else:
        log_dict_sfn_slot_occur.update({name: 1})
    sfn_slot_occur=log_dict_sfn_slot_occur[name]
    return [log_dict_sfn_slot_occur, sfn_slot_occur]

def readParseGnbLogData(f_gn_log, gn_msg3_search_pat, gn_field_name_pat_arr, ue_field_var, pdcch_dci11_count,
                        ue_field_len, flag_harq_id_align_on_1st_pdcch, flag_debug_mode):
    # Define search patterns for gNB log fields
    # Some fields in each DL slot configuration of 5G NR gNB log
    # nRBStart: 32
    # nRBSize: 241
    # nHARQID: 2
    # nStartSymbolIndex: 1
    # nNrOfSymbols: 13
    # DCI bits                 :9fffe150483400
    # Define search patters for gNB log fields
    #gn_field_name_pat_arr = ["nSFN", "nSlot", 'nMCS[0]', "nRBStart", "nRBSize",  "nStartSymbolIndex", "nNrOfSymbols", "nHARQID",
    #                         "DCI bits"];
    gn_field_name_pat_arr_len = len(gn_field_name_pat_arr)
    # gn_pdcch_dci11_dft follows elements defined in gn_field_name_pat_arr
    # gn_pdcch_dci11_dft = [0, 0, 0, 0, 0, 0, 0, "FFFFFFFFFFFFFFFF"]

    gn_field_var = []  # a list of searched gNB PDCCH messages
    ue_field_match_var = []
    flag_1st_pdcch_harq_after_rach_matched=False
    # PDCCH search flags
    flag_msg3_found=False
    flag_pdcch_sfn_found = False
    flag_pdcch_slot_found = False
    flag_pdcch_harq_found = False
    flag_pdcch_dci_found = False
    flag_pdcch_slot_end_found = False
    flag_pdcch_info_copied = False
    flag_pddch_info_clear = False

    # PDCCH search patterns
    gn_log_sfn_pat = gn_field_name_pat_arr[0];  # SFN pattern
    gn_log_slot_pat = gn_field_name_pat_arr[1];  # Slot pattern
    gn_log_dcibits_pat = "DCI bits"  # DCI bits pattern
    gn_log_ndci_pat = "nDCI"  # nDCI pattern
    gn_log_harq_pat = "nHARQID"
    gn_log_slot_end_pat = gn_field_name_pat_arr[-1];  # "nUEnPduIdx"
    gn_log_dci11_val = 1;
    progressbar_step_lines = 154
    # Line index of file readline
    line_idx = 0
    # PDCCH message index in ue_field_var array
    ue_pdcch_idx = 0
    # Initial SFN and Slot Index, HARQ Id
    #sfn = ue_field_var[ue_pdcch_idx * ue_field_len]
    #slot_idx = ue_field_var[ue_pdcch_idx * ue_field_len + 1]
    #harq_id = ue_field_var[ue_pdcch_idx * ue_field_len + 7]
    sfn_curr=0
    slot_idx_curr=0
    harq_id_curr=0

    sfn_line_start_idx = 0
    sfn_lines_len = 112
    gn_log_sfn_harqid_distance = 56
    gn_log_sfn_slot_distance=1
    gn_log_sfn_ndci_distance=3
    gn_log_sfn_dcibits_distance=97

    gn_pdcch_list_tmp = []
    gn_pdcch_field_var = []
    flag_harq_id_check=False
    gn_pdcch_count=0
    log_dict_sfn_slot_occur={}


    if flag_debug_mode:
        print("Starting to search MSG3 bytes: %s ..." % gn_msg3_search_pat)

    # NOTE: zero-based line indices!!
    for line in f_gn_log.readlines():
        if (line_idx % progressbar_step_lines==0):
            progressbar_label = "Line " + str(line_idx)
            drawProgressBar(line_idx / num_lines_gn_log, drawbar_len, progressbar_label)
        # Next line if empty string
        # if len(line) <=1:
        #    line_idx += 1  # increase line index
        #    continue
        # Found SFN

        if (not flag_msg3_found):
            if line.find(gn_msg3_search_pat) >=0:
                flag_msg3_found=True
                print("\nMSG3 pattern is found! MSG3 bytes -> %s at Line %d !"
                          % (gn_msg3_search_pat, line_idx))
        # Found SFN
        if flag_msg3_found and not flag_pdcch_sfn_found:
            if line.find(gn_log_sfn_pat) == 0:
                substr = line[line.rfind(":") + 1:]
                sfn_curr = int(substr.strip())
                flag_pdcch_sfn_found = True
                sfn_line_start_idx = line_idx
                gn_pdcch_list_tmp.append(line.strip())
                if flag_debug_mode:
                    print("\nPDCCH SFN header is found: SFN=%d, sfn_line_start_idx=%d at Line %d"
                          % (sfn_curr, sfn_line_start_idx, line_idx))
        # Found Slot
        if flag_pdcch_sfn_found and (not flag_pdcch_slot_found):
              if line.find(gn_log_slot_pat) == 0 :
                substr = line[line.rfind(":") + 1:].strip()
                slot_idx_curr = int(substr)
                flag_pdcch_slot_found = True
                gn_pdcch_list_tmp.append(line.strip())
                if flag_debug_mode:
                    print("\nPDCCH SLOT header is found: SFN=%d, Slot Index=%d at Line %d"
                          % (sfn_curr, slot_idx_curr, line_idx))
              else:
                  if (line_idx-sfn_line_start_idx) >= gn_log_sfn_slot_distance:
                      flag_pdcch_sfn_found =False
                      flag_pddch_info_clear=True
                      if flag_debug_mode:
                         print("\nPDCCH frame header-> Wrong Slot!  SFN=%d, Slot Index=%d at Line %d"
                                % (sfn_curr, slot_idx_curr, line_idx))
                         print(line)

        # Save lines after SFN and slot are matched
        if flag_pdcch_slot_found:
            gn_pdcch_list_tmp.append(line.strip())
            # Search nDCI pattern
            if not flag_pdcch_dci_found:
                if line.find(gn_log_ndci_pat) == 0: #and (line_idx-sfn_line_start_idx) < 10:
                    substr = line[line.rfind(":") + 1:].strip()
                    dci_val = int(substr)
                    # print("\nSlot=%d at Line %d " % (slot_val, line_idx))
                    if (dci_val == gn_log_dci11_val):
                        flag_pdcch_dci_found = True
                        if flag_debug_mode:
                            print("\nMatched nDCI pattern is found: %s at Line %d"
                                  % (line, line_idx))
                else:
                    if (line_idx - sfn_line_start_idx) >= gn_log_sfn_ndci_distance:
                        flag_pdcch_sfn_found = False
                        flag_pdcch_slot_found =False
                        flag_pddch_info_clear =True
                        if flag_debug_mode:
                            print("\nPDCCH frame header-> Wrong nDCI position!  SFN=%d, Slot Index=%d at Line %d"
                                  % (sfn_curr, slot_idx_curr, line_idx))
                            print(line)
           # Search slot end separator pattern
            if flag_pdcch_dci_found:
                if line.find(gn_log_slot_end_pat) >= 0:
                    flag_pdcch_slot_end_found = True
                    if flag_debug_mode:
                        print("\nMatched slot end/separator is found: %s at Line %d"
                              % (line, line_idx))
                else:
                    if (line_idx-sfn_line_start_idx) >= gn_log_sfn_dcibits_distance:
                        flag_pdcch_sfn_found = False
                        flag_pdcch_slot_found =False
                        flag_pdcch_dci_found = False
                        flag_pddch_info_clear= True
                        if flag_debug_mode:
                            print("\nPDCCH frame header-> Wrong Slot End position!  SFN=%d, Slot Index=%d at Line %d"
                                  % (sfn_curr, slot_idx_curr, line_idx))
                            print(line)

        # Go to find HARQ ID
        if flag_pdcch_dci_found:
            # Search HARQ ID
            if (not flag_pdcch_harq_found): # and flag_harq_id_align_on_1st_pdcch and gn_pdcch_count==0:
                # print(line)
                if line.find(gn_log_harq_pat) >= 0:
                    # print (line)
                    substr = line[line.rfind(":") + 1:].strip()
                    harq_id_curr = int(substr)
                    # print("\nHARQ id =%d at Line %d" % (harq_val, line_idx))
                    if (line_idx-sfn_line_start_idx) == gn_log_sfn_harqid_distance:
                        flag_pdcch_harq_found = True
                        #flag_1st_pdcch_harq_after_rach_matched=True
                        if flag_debug_mode:
                             print(
                                "\nHARQ IQ header is found! SFN=%d, Slot Index=%d, HARQ id=%d at Line %d"
                                % (sfn_curr, slot_idx_curr, harq_id_curr, line_idx))
                    else:
                        if flag_debug_mode:
                            print("\nMismatched HARQ id=%d! Clear the current search window at Line %d !" % (
                            harq_id_curr, line_idx))
                        flag_pddch_info_clear = True

        # if flag_pdcch_harq_found :
        #    print("\n")
        #    print (line)
        # Copy and parse required field values
        if flag_pdcch_slot_end_found and not flag_pddch_info_clear:
            if flag_harq_id_align_on_1st_pdcch and not flag_harq_id_check:
                flag_harq_id_check=True
            else:
                flag_harq_id_check=False
            #if flag_debug_mode:
            #print(
            #        "\nParsing and extracting field values: sfn_curr=%d, slot_idx_curr=%d, harq_id_curr=%d, flag_harq_id_check=%d"
             #       % (sfn_curr, slot_idx_curr, harq_id_curr, flag_harq_id_check))
            [flag_matched_pdcch_frame, gn_field_var_tmp, ue_pdcch_matched_idx, log_dict_sfn_slot_occur]=searchExtractUeGnbLogFields( gn_pdcch_list_tmp, ue_field_var, pdcch_dci11_count, ue_field_len,
                                        gn_field_name_pat_arr, sfn_curr, slot_idx_curr, harq_id_curr,
                                        flag_harq_id_check, log_dict_sfn_slot_occur)
            if flag_matched_pdcch_frame and len(gn_field_var_tmp)>0:
                for x in gn_field_var_tmp:
                    gn_field_var.append(x)
                ue_field_var_tmp= ue_field_var[ue_pdcch_matched_idx * ue_field_len: (ue_pdcch_matched_idx + 1) * ue_field_len]
                for x in ue_field_var_tmp:
                   ue_field_match_var.append(x)

            if flag_matched_pdcch_frame and flag_harq_id_check:
                flag_1st_pdcch_harq_after_rach_matched=True;

            gn_pdcch_count=int(len(gn_field_var)/gn_field_name_pat_arr_len)
            flag_pdcch_info_copied = True
            if flag_debug_mode:
                print('\nList of returned PDCCH fields is %s' % str(gn_field_var_tmp))

        # Reset all flags and search next PDCCH DCI 1_1 frame if
        if flag_pddch_info_clear:  # or ((not flag_pdcch_slot_end_found) and ((line_idx-sfn_line_start_idx) >= sfn_lines_len)):
            flag_pdcch_sfn_found = False
            flag_pdcch_slot_found = False
            flag_pdcch_harq_found = False
            flag_pdcch_dci_found = False
            flag_pdcch_slot_end_found = False
            flag_pdcch_info_copied = False
            flag_pddch_info_clear = False

            sfn_line_start_idx = 0
            sfn_curr = 0
            slot_idx_curr = 0
            harq_id_curr = 0
            gn_pdcch_list_tmp.clear()

        # Reset all flags and go to next PDCCH DCI 1_1 frame
        if flag_pdcch_info_copied:
            # Go to Next SFN and Slot in ue_field_var list
            ue_pdcch_idx += 1
            if  gn_pdcch_count >= pdcch_dci11_count:
                print(
                    "\nStop searching PDCCH DCI 1_1 messages in gNB log file as the number (%d) of messages is counted !"
                    % pdcch_dci11_count)
                break;
            else:
                flag_pdcch_sfn_found = False
                flag_pdcch_slot_found = False
                flag_pdcch_harq_found = False
                flag_pdcch_dci_found = False
                flag_pdcch_slot_end_found = False
                flag_pdcch_info_copied = False
                flag_pddch_info_clear = False
                sfn_line_start_idx = 0
                sfn_curr=0
                slot_idx_curr=0
                harq_id_curr=0
                gn_pdcch_list_tmp.clear()

        line_idx += 1  # increase line index

    # Stop progress bar
    drawProgressBar(1.0, drawbar_len)
    print("\nNumber of lines: %d" % line_idx)
    #gn_pdcch_count=int(len(gn_field_var)/gn_field_name_pat_arr_len )
    if flag_debug_mode:
        print("\ngn_pdcch_list_tmp: %s" % gn_pdcch_list_tmp)
        print("\nNumber of lines: %d" % line_idx)
        print('\nList of PDCCH fields is %s' % str(gn_field_var))

    if len(gn_field_var)> 0:
       print("\nList of extracted field values from the 1st PDCCH DCI 1_1 message: ")
       print(gn_field_var[0:gn_field_name_pat_arr_len])

    print("Number of parsed PDCCH DCI 1_1 messages:     %d" % gn_pdcch_count)

    return [gn_field_var, ue_field_match_var, gn_pdcch_count, flag_msg3_found,  flag_1st_pdcch_harq_after_rach_matched]

if __name__ == "__main__":
    """ Main Function"""

    # Log File Folders and names
    #__File__= 'C:/Users/junchen/Desktop/DCI Issues'
    #this_dir = os.path.dirname(__File__)
    #file_name_ue_log= os.path.realpath( "{0}/log_4_21_2020_7_30_PM_dc3f1275/UE logs/run_2020_04_22_00_35_47/log_text_0.txt".format(this_dir))
    #file_name_gn_log = os.path.realpath("{0}/log_4_21_2020_7_30_PM_dc3f1275/gNB/gNBlogs_2020.04.22-00.37.50/gNB_log.txt".format(this_dir))

    # 5G NR UE log file name
    #file_name_ue_log = "log_text_0.txt"
    # 5G NR gNB log file name
    #file_name_gn_log = "gNB_log_small_test.txt"
    #file_name_gn_log = "gNB_log.txt"

    print ("\n---------------------------------------------------------------------------")
    print ("Checking 5G NR and gNB log log files... ")
    print ( "---------------------------------------------------------------------------\n")

    __UE_DIR__ = "C:/Users/junchen/Desktop/DCI Issues/log_3_17_2020_3_09_PM_483e6352/UE/run_2020_03_17_20_14_26"
    file_name_ue_log = __UE_DIR__ + "/" + "log_text_0.txt"
    print("UE log file name: %s" % file_name_ue_log)
    print ("UE log directory exists:" + str(path.exists(__UE_DIR__)))
    print ("UE log file exists:     " + str(path.exists(file_name_ue_log)))

    __GN_DIR__ = "C:/Users/junchen/Desktop\DCI Issues\log_3_17_2020_3_09_PM_483e6352\gNB\gNBlogs_2020.03.17-20.15.48"
    file_name_gn_log = __GN_DIR__ + "/" + "gNB_log.txt"
    print("gNB log file name: %s" % file_name_gn_log)
    print ("gNB log directory exists:" + str(path.exists(__GN_DIR__)))
    print ("gNB log file exists:     " + str(path.exists(file_name_gn_log)))

    print ("\n---------------------------------------------------------------------------")
    print ("Starting 5G NR log parsing and comparison between gNB and UE log files")
    print ( "---------------------------------------------------------------------------\n")
    start_time = datetime.datetime.now()
    print("Start time: " + start_time.strftime("%c"))
    ##################################################
    # 5G NR UE Log Message Processing
    #################################################
    print("\n---------------------------------------------------------------------------")
    print("Processing 5G NR UE log file...")
    print("---------------------------------------------------------------------------")
    num_lines_ue_log=countLines (file_name_ue_log);
    f_ue_log = open(file_name_ue_log, "r")
    print ("UE log file name: %s" % (file_name_ue_log))
    print ("Number of lines: " + str(num_lines_ue_log))

    # Define search patterns for UE log fields
    ue_field_name_pat_arr = ["SFN", "SlotNo", "MCS", "PdschStartSymbol", "PdschLenSymbol", "PRB start", "PRB end",
                             "HARQProcNo",
                             "DciBits[0]", "DciBits[1]"]
    ue_log_conn_pattern="Connected"
    ue_log_sync_pattern="sync valid: TRUE"
    ue_log_dcitype_pattern="DCIType: 1_1"
    ue_log_chtype_pattern="PDCCH"
    ue_field_len=len(ue_field_name_pat_arr)

    # Read and parse UE log messages from its log file
    [ue_field_var, flag_connected_state_found]= readParseUeLogData(f_ue_log, ue_field_name_pat_arr, ue_log_conn_pattern, ue_log_sync_pattern,
                       ue_log_dcitype_pattern, ue_log_chtype_pattern, ue_pdcch_dci11_num_max, flag_debug_mode, flag_print_ue_searched_pdcch_list);

    #print("Number of field values/elements in the list: %d" %len(ue_field_var))
    #pdcch_dci11_count = int(len(ue_field_var) / ue_field_len)
    #ue_log_sfn_slot_occur=computeSfnSlotOccurence(ue_field_var, pdcch_dci11_count, ue_field_len)
    #print("ue_log_sfn_slot_occur= %s" %ue_log_sfn_slot_occur)
    #for k, v in ue_log_sfn_slot_occur.items():
    #    if v>1:
    #       print("%s = %d" %{k, v})

    # Close file handler of 5G NR UE log
    f_ue_log.close()

    if not flag_connected_state_found or len(ue_field_var) <1:
        print ("Exiting the main function... \n")
        sys.exit(-1)  # Exit main program

    ##################################################
    # 5G NR gNB Log Message Processing
    #################################################
    print("\n---------------------------------------------------------------------------")
    print("Processing 5G NR gNB log file...")
    print("---------------------------------------------------------------------------")

    num_lines_gn_log=countLines (file_name_gn_log);  # count lines in gNB log file
    f_gn_log = open(file_name_gn_log, "r")  # open gNB log file
    print ("gNB log file name: %s" % (file_name_gn_log))
    print ("Number of lines: " + str(num_lines_gn_log))

    # Define search patters for gNB log fields
    gn_field_name_pat_arr = ["nSFN", "nSlot", 'nMCS[0]', "nStartSymbolIndex", "nNrOfSymbols", "nRBStart", "nRBSize",
                             "nHARQID", "DCI bits"];
    # Search pattern for MSG3 in the gNB log file
    # "An even simpler way you be to just search for MSG3 bytes since they are always the same in the successful RACH case:
    # “3a 21 21 3f"
    gn_msg3_search_pat="3a 21 21 3f"
    print("\nReading lines from the gNB log file and searching gNB configurations slot by slot...\n")
    # Read and Parse gNB log messages from its log file (using matched UE log fields)
    pdcch_dci11_count=int(len(ue_field_var)/ue_field_len)
    print("Number of PDCCH Messages: %d" %pdcch_dci11_count)
    [gn_field_var,ue_field_match_var, gn_pdcch_count, ret_msg3_found,  ret_1st_pdcch_harq_id_matched]=readParseGnbLogData(f_gn_log, gn_msg3_search_pat, gn_field_name_pat_arr, ue_field_var,  pdcch_dci11_count, ue_field_len,
                                                                      flag_harq_id_align_on_1st_pdcch, flag_debug_mode);


    #print (ue_field_match_var)
    #print (gn_field_var)

    if not ret_msg3_found:
        print("\nERROR: No MSG3 bytes (%s) is found in gNB log file ! " %gn_msg3_search_pat)

    if len(gn_field_var)<1:
        print("\nERROR: No PDCCH DCI 1_1 messages are found in gNB log file ! ")

    if flag_harq_id_align_on_1st_pdcch and (not ret_1st_pdcch_harq_id_matched):
        print("\nERROR: The first HARQ ID of PDCCH DCI 1_1 after RACH success from UE log is mismatched in gNB log file ! ")

    if len(gn_field_var)<1  or len (ue_field_match_var) <1:
        msg_count=0
    else:
        msg_count=gn_pdcch_count

    # Compare log data and print results
    comparePrintUeGnBLogResults(msg_count, ue_field_name_pat_arr, gn_field_name_pat_arr, ue_field_match_var, gn_field_var,
                                flag_connected_state_found,  ret_1st_pdcch_harq_id_matched, flag_print_gnb_searched_pdcch_list)

    # Close file handler of 5G NR gNB log
    f_gn_log.close()

    print("\n---------------------------------------------------------------------------")
    end_time = datetime.datetime.now()
    delta_time=end_time - start_time
    elapsed_time = int(delta_time.total_seconds()) # seconds
    print ("Elapsed time: " + str(elapsed_time) + " seconds\n")
