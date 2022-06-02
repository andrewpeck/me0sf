import csv
from os import path
from subfunc import *
from printly_dat import printly_dat
from ast import literal_eval


def run_pat_mux_analysis(patlist, MAX_SPAN=37):
    titles_iddiscrepancies = [
        "Testcase #",
        "Strip",
        "Parsed Data",
        "Pat_unit_mux ID",
        "Emulator ID",
    ]
    titles_cntdiscrepancies = [
        "Testcase #",
        "Strip",
        "Parsed Data",
        "Pat_unit_mux CNT",
        "Pat_unit_mux ID",
        "Emulator CNT",
        "Emulator ID",
    ]

    proceed = input("Would you like to analyze both the ID and CNT discrepancies? Y/N ")
    if proceed == "Y" or proceed == "y":
        # parse data for ID discrepancies
        with open("discrepancies_id.csv", "r") as csv_file:
            csv_reader = csv.reader(csv_file)
            next(csv_reader)
            testcase_nums = []
            next(csv_reader)
            for lines in csv_reader:
                testcase_nums.append(int(lines[0]))
            max_testcase_num = max(testcase_nums)
            csv_file.close()
        num_testcases = int(
            input(
                "How many ID testcases would you like to analyze? Choose up to %d. "
                % max_testcase_num
            )
        )
        with open("discrepancies_id.csv", "r") as csv_file1:
            csv_reader = csv.reader(csv_file1)
            next(csv_reader)
            with open("id_discrep_parsed.csv", "w") as csv_file2:
                csv_writer = csv.writer(csv_file2)
                csv_writer.writerow(titles_iddiscrepancies)
                for line in csv_reader:
                    if int(line[0]) <= int(num_testcases):
                        csv_writer.writerow(line)
                csv_file2.close()
            csv_file1.close()
        # parse data for CNT discrepancies
        with open("discrepancies_cnt.csv", "r") as csv_file:
            csv_reader = csv.reader(csv_file)
            testcase_nums = []
            next(csv_reader)
            for lines in csv_reader:
                testcase_nums.append(int(lines[0]))
            max_testcase_num = max(testcase_nums)
            csv_file.close()
        num_testcases = int(
            input(
                "How many CNT testcases would you like to analyze? Choose up to %d. "
                % int(max_testcase_num)
            )
        )
        with open("discrepancies_cnt.csv", "r") as csv_file1:
            csv_reader = csv.reader(csv_file1)
            next(csv_reader)
            with open("cnt_discrep_parsed.csv", "w") as csv_file2:
                csv_writer = csv.writer(csv_file2)
                csv_writer.writerow(titles_cntdiscrepancies)
                for line in csv_reader:
                    if int(line[0]) <= int(num_testcases):
                        csv_writer.writerow(line)
                csv_file2.close()
            csv_file1.close()
        # create visual for ID discrepancies between emulator and hardware design
        print("Emulator and Hardware Design Discrepancies in ID Ordered Below...")
        with open("id_discrep_parsed.csv", "r") as csv_file:
            csv_reader = csv.reader(csv_file)
            next(csv_reader)
            for line in csv_reader:
                print("\n")
                print("Testcase #%d" % int(line[0]))
                print("Strip %d" % int(line[1]))
                printly_dat(data=literal_eval(line[2]))
                print("\n")
                print("Pat_unit_mux assignment: ")
                print("Pat ID: %d" % int(line[3]))
                pattern_t = get_mypattern(pat_id=int(line[3]), patlist=patlist)
                mask_t = get_ly_mask(ly_pat=pattern_t)
                printly_dat(
                    data=literal_eval(line[2]), mask=mask_t, MAX_SPAN=MAX_SPAN
                )  # FIGURE OUT WHY THIS IS A PROBLEM
                print("\n\n")
                print("Emulator Assignment: ")
                print("Pat ID: %d" % int(line[4]))
                pattern_b = get_mypattern(pat_id=int(line[4]), patlist=patlist)
                mask_b = get_ly_mask(ly_pat=pattern_b, MAX_SPAN=MAX_SPAN)
                printly_dat(data=literal_eval(line[2]), mask=mask_b, MAX_SPAN=MAX_SPAN)
            csv_file.close()
        print("\n\n")
        # create visual for CNT discrepancies between emulator and hardware design
        print("Emulator and Hardware Design Discrepancies in CNT Ordered Below...")
        with open("cnt_discrep_parsed.csv", "r") as csv_file:
            csv_reader = csv.reader(csv_file)
            next(csv_reader)
            for line in csv_reader:
                print("\n")
                print("Testcase #%d" % int(line[0]))
                print("Strip %d" % int(line[1]))
                printly_dat(data=literal_eval(line[2]))
                print("\n")
                print("Pat_unit_mux assignment: ")
                print("Pat ID: %d" % int(line[4]))
                print("Layer Count: %d" % int(line[3]))
                pattern_t = get_mypattern(pat_id=int(line[4]), patlist=patlist)
                mask_t = get_ly_mask(ly_pat=pattern_t)
                printly_dat(data=literal_eval(line[2]), mask=mask_t, MAX_SPAN=MAX_SPAN)
                print("\n\n")
                print("Emulator Assignment: ")
                print("Pat ID: %d" % int(line[6]))
                print("Layer Count: %d" % int(line[5]))
                pattern_b = get_mypattern(pat_id=int(line[6]), patlist=patlist)
                mask_b = get_ly_mask(ly_pat=pattern_b, MAX_SPAN=MAX_SPAN)
                printly_dat(data=literal_eval(line[2]), mask=mask_b, MAX_SPAN=MAX_SPAN)
            csv_file.close()
    else:
        proceed = input("Would you like to analyze some of the ID discrepancies? Y/N ")
        if proceed == "Y" or proceed == "y":
            with open("discrepancies_id.csv", "r") as csv_file:
                csv_reader = csv.reader(csv_file)
                testcase_nums = []
                next(csv_reader)
                for lines in csv_reader:
                    testcase_nums.append(int(lines[0]))
                max_testcase_num = max(testcase_nums)
                csv_file.close()
            num_testcases = int(
                input(
                    "How many ID testcases would you like to analyze? Choose up to %d. "
                    % max_testcase_num
                )
            )
            # parse data for ID discrepancies
            with open("discrepancies_id.csv", "r") as csv_file1:
                csv_reader = csv.reader(csv_file1)
                next(csv_reader)
                with open("id_discrep_parsed.csv", "w") as csv_file2:
                    csv_writer = csv.writer(csv_file2)
                    csv_writer.writerow(
                        ["Testcase #", "Parsed Data", "Pat_unit_mux ID", "Emulator ID"]
                    )
                    for line in csv_reader:
                        if int(line[0]) <= int(num_testcases):
                            csv_writer.writerow(line)
                    csv_file2.close()
                csv_file1.close()
            # create visual for ID discrepancies between emulator and hardware design
            print("Emulator and Hardware Design Discrepancies in ID Ordered Below...")
            with open("id_discrep_parsed.csv", "r") as csv_file:
                csv_reader = csv.reader(csv_file)
                next(csv_reader)
                for line in csv_reader:
                    print("\n")
                    print("Testcase #%d" % int(line[0]))
                    print("Strip %d" % int(line[1]))
                    printly_dat(data=literal_eval(line[2]))
                    print("\n")
                    print("Pat_unit_mux assignment: ")
                    print("Pat ID: %d" % int(line[3]))
                    pattern_t = get_mypattern(pat_id=int(line[3]), patlist=patlist)
                    mask_t = get_ly_mask(ly_pat=pattern_t)
                    printly_dat(
                        data=literal_eval(line[2]), mask=mask_t, MAX_SPAN=MAX_SPAN
                    )  # FIGURE OUT WHY THIS IS A PROBLEM
                    print("\n\n")
                    print("Emulator Assignment: ")
                    print("Pat ID: %d" % line[4])
                    pattern_b = get_mypattern(pat_id=int(line[4]), patlist=patlist)
                    mask_b = get_ly_mask(ly_pat=pattern_b, MAX_SPAN=MAX_SPAN)
                    printly_dat(
                        data=literal_eval(line[2]), mask=mask_b, MAX_SPAN=MAX_SPAN
                    )
                csv_file.close()
        else:
            proceed = input(
                "Would you like to analyze some of the CNT discrepancies? Y/N "
            )
            if proceed == "N" or proceed == "n":
                print("Goodbye. ")
            else:
                with open("discrepancies_cnt.csv", "r") as csv_file:
                    csv_reader = csv.reader(csv_file)
                    testcase_nums = []
                    next(csv_reader)
                    for lines in csv_reader:
                        testcase_nums.append(int(lines[0]))
                    max_testcase_num = max(testcase_nums)
                    csv_file.close()
                num_testcases = int(
                    input(
                        "How many CNT testcases would you like to analyze? Choose up to %d. "
                        % max_testcase_num
                    )
                )
                # parse data for CNT discrepancies
                with open("discrepancies_cnt.csv", "r") as csv_file1:
                    csv_reader = csv.reader(csv_file1)
                    next(csv_reader)
                    with open("cnt_discrep_parsed.csv", "w") as csv_file2:
                        csv_writer = csv.writer(csv_file2)
                        csv_writer.writerow(
                            [
                                "Testcase #",
                                "Parsed Data",
                                "Pat_unit_mux CNT",
                                "Pat_unit_mux ID",
                                "Emulator CNT",
                                "Emulator ID",
                            ]
                        )
                        for line in csv_reader:
                            if int(line[0]) <= int(num_testcases):
                                csv_writer.writerow(line)
                        csv_file2.close()
                    csv_file1.close()
                # create visual for CNT discrepancies between emulator and hardware design
                print(
                    "Emulator and Hardware Design Discrepancies in CNT Ordered Below..."
                )
                with open("cnt_discrep_parsed.csv", "r") as csv_file:
                    csv_reader = csv.reader(csv_file)
                    next(csv_reader)
                    for line in csv_reader:
                        print("\n")
                        print("Testcase #%d" % int(line[0]))
                        print("Strip %d" % int(line[1]))
                        printly_dat(data=literal_eval(line[2]))
                        print("\n")
                        print("Pat_unit_mux assignment: ")
                        print("Pat ID: %d" % int(line[4]))
                        print("Layer Count: %d" % int(line[3]))
                        pattern_t = get_mypattern(pat_id=int(line[4]), patlist=patlist)
                        mask_t = get_ly_mask(ly_pat=pattern_t)
                        printly_dat(
                            data=literal_eval(line[2]), mask=mask_t, MAX_SPAN=MAX_SPAN
                        )
                        print("\n\n")
                        print("Emulator Assignment: ")
                        print("Pat ID: %d" % int(line[6]))
                        print("Layer Count: %d" % int(line[5]))
                        pattern_b = get_mypattern(pat_id=int(line[6]), patlist=patlist)
                        mask_b = get_ly_mask(ly_pat=pattern_b, MAX_SPAN=MAX_SPAN)
                        printly_dat(
                            data=literal_eval(line[2]), mask=mask_b, MAX_SPAN=MAX_SPAN
                        )
                    csv_file.close()


run_pat_mux_analysis(patlist)
