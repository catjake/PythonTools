"""
set of utility functions pertenant to operations for parsing and manipulating datalog type
data structures
"""
__author__ = "jacob keezel"
__email__ = "jacob@anoralabs.com"
__version__ = "2.0"
__since__ = "10/06/2016" # date of origin, rev 1.0
__date__ = "10/08/2016"  # date of most recent rev

import util
import re


def generateCsvLog(l_dict, fields_list, format_string):
    """

    :param r_dict: {"tnum": <string>, "site": <string>, "low": <string>....}
    :return: format_string.format(**kwargs)
    """
    a_dict = dict([(a_key, l_dict[a_key]) for a_key in fields_list])
    return format_string.format(**a_dict)

def findDuplicates(test_number_list):
    """
    pass in a test number list, determine if any are duplicates
    :param test_number_list:
    :return: dictionary keyed by test_number: <num of instances (duplicates)>
    """
    s_list = sorted(test_number_list)
    a_dict = {}
    for i, j in zip(s_list[1:], s_list[:-1]):
        if (i - j) == 0:
            if i in a_dict:
                a_dict[i] += 1
            else:
                a_dict[i] = 1
    return a_dict


def addDuplicate(tn):
    m = re.search("_DUPE\d+", tn)
    if m:
        base_name = tn.rpartition("_")[0]
        dupe_name = tn.rpartition("_")[-1]
        rev_num = "{0:03d}".format(int(dupe_name.replace("DUPE",""))+1)
    else:
        rev_num, base_name = "{0:03d}".format(1), tn
    return "{0}_DUPE{1}".format(base_name, rev_num)


def compareValues(val1, val2):
    str1 = "N/A" if val1 == None or val1 == "" else val1
    str2 = "N/A" if val2 == None or val2 == "" else val2
    num1 = 0 if not (re.search("^(?:\*\*\*|n\.a\.|N/A)$", str1) == None) else float(str1)
    num2 = 0 if not (re.search("^(?:\*\*\*|n\.a\.|N/A)$", str2) == None) else float(str2)
    mod_ratio = 0.0
    if abs(num1) > abs(num2):
        mod_ratio = num1/(num2 if num2 != 0.0 else 1) % 10
    else:
        mod_ratio = num2/(num1 if num1 != 0.0 else 1) % 10

    return (num1 - num2), mod_ratio


def valuesMatch(val1, val2, threshold=0.001):
    delta = compareValues(val1, val2)
    if delta < threshold:
        return True
    else:
        return False


def parse_unit(unit):
    if len(unit) == 0:
        return "", ""
    if re.search("^(?:m|M|n|p|k|K|g|G)", unit) and len(unit)>1:
        return unit[0], unit[1:]
    else:
        return "", unit


class createCsvLog(object):
    fields_dict = {
        "parametric": "tnum site tname tpin unit low result high".split(),
        "format_parametric": "{tnum},{site},{tname},{tpin},{unit},{low},{result},{high}",
        "functional": "tnum site pname result".split(),
        "format_functional": "{tnum},{site},{pname},,,,{result},"
    }

    def __init__(self, test_records_dict):
        self.test_records_dict = test_records_dict
        self.test_name_list = test_records_dict.keys()
        self.test_lookup_dict = {}
        self.generateTestLookUpTable(self.test_records_dict, self.test_lookup_dict)
        self.csv_log = self.generateTestRecords(self.test_records_dict, self.test_name_list)

    def generateTestRecords(self, test_records_dict, test_name_list):
        chk_list = [",".join(self.fields_dict["parametric"])] # uniform header, more fields in parametric
        for tn in test_name_list:
            for test_number in test_records_dict[tn]["testnumbers"]:
                r_dict = test_records_dict[tn][test_number]
                test_type, l_dict = r_dict["type"], r_dict["log"]
                chk_list.append(
                    generateCsvLog(
                        l_dict,
                        self.fields_dict[test_type],
                        self.fields_dict["format_{0}".format(test_type)]
                    )
                )
        return chk_list

    def generateTestLookUpTable(self, test_records_dict, test_lookup_dict):
        for tn in test_records_dict.iterkeys():
            for test_number in test_records_dict[tn]["testnumbers"]:
                test_lookup_dict[test_number] = tn


