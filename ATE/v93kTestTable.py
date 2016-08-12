"""
set of utility classes and functions relevant to parsing and manipulating v93k limits tables objects
"""
__author__ = "jacob keezel"
__email__ = "jacob@anoralabs.com"
__version__ = "2.0"
__since__ = "13/04/2016" # date of origin, rev 1.0
__date__ = "10/08/2016"  # date of most recent rev

import util
import re

class limitsTable(object):
    """
    build limits table dictionary keyed of Suite Name and pin name, use testtable limits object for reference
        :param csv_file:
    """
    def __init__(self, csv_file):
        self.header, self.start_test_table_fields, self.end_test_table_fields, self.tm_list = [], [], [], []
        self.parse_table(csv_file)

    def parse_table(self, csv_file):
        """
        make test limits dict, based on TestSuite:{
                                            <TestName>: {<Pin>:{Units:<string>, TestNumber:<int>,
                                                        <TestMode>:{Lsl:<value>, Usl:<value>}...}}...}

        :param csv_file:
        :return:
        """
        f = util.FileUtils(csv_file, True)
        index1 = util.find_index(f.contents, "^\s*\"?Suite name")
        index2 = util.find_index(f.contents, "^\s*\"?Test mode")
        test_table_fields = re.sub("\"", "", f.contents[index1]).strip().split(",")
        test_modes = re.sub("\"", "", f.contents[index2]).strip().split(",")
        self.header = [",".join(test_table_fields), ",".join(test_modes)]
        i = util.find_index(test_table_fields, "^Lsl$")
        j = util.find_index(test_table_fields, "^Bin_s_num")
        self.start_test_table_fields = test_table_fields[:i]
        self.end_test_table_fields = test_table_fields[j:]
        self.tm_list = [test_modes[x] for x in xrange(i, j, 2)]
        test_table_keys = test_table_fields[:i] + self.tm_list + test_table_fields[j:]
        tt_keys = list(set(test_table_keys) - set(self.tm_list + ["Suite name", "Pins", "Test name"]))
        test_mode_indices_dict = dict([(test_modes[x], {"Lsl": x, "Usl": x+1}) for x in xrange(i, j, 2)])
        test_fields_indices_dict = dict([(a_field, x) for (x, a_field) in enumerate(test_table_fields[:i])] +
                                        [(a_field, x) for (x, a_field) in enumerate(test_table_fields[j:], j)])
        self.test_limits_dict = {}
        f_contents = [
            re.sub("\"","", a_row.strip())
            for a_row in f.contents[2:] if util.in_string(a_row.replace('"',''), "^\w+,")
            ]
        for a_row in f_contents:
            a_list = a_row.split(",")
            suite_name = a_list[test_fields_indices_dict["Suite name"]]
            test_name = a_list[test_fields_indices_dict["Test name"]]
            pin_name = a_list[test_fields_indices_dict["Pins"]]
            if suite_name not in self.test_limits_dict:
                self.test_limits_dict[suite_name] = {}
            if test_name not in self.test_limits_dict[suite_name]:
                self.test_limits_dict[suite_name][test_name] = {}
            if pin_name not in self.test_limits_dict[suite_name][test_name]:
                self.test_limits_dict[suite_name][test_name][pin_name] = {}
            t_dict = self.test_limits_dict[suite_name][test_name][pin_name]
            for test_mode in self.tm_list:
                usl, lsl = int(test_mode_indices_dict[test_mode]["Usl"]), int(test_mode_indices_dict[test_mode]["Lsl"])
                if test_mode not in t_dict:
                    t_dict[test_mode] = {}
                t_dict[test_mode]["Lsl"] = a_list[lsl]
                t_dict[test_mode]["Usl"] = a_list[usl]
            for a_key in tt_keys:
                t_dict[a_key] = a_list[test_fields_indices_dict[a_key]]

    def get_limit(self, test_suite_name, test_instance, test_pin, test_mode, test_limits_dict=None):
        """
        Use self.test_number_lookup_table to get test_suite_name, test_instance, etc. from test_number
        test number is the key to reference the tsname which is the main key for v93k_test_limits_dict
        upper and lower limits are Lsl and Usl, which are accessed from the test category key name, i.e.
        "F22".  Use PinName to get to the test mode, limits and units, i.e.
        test_limits_dict[test_suite_name][test_instance][test_pin][test_mode].
        :param test_suite_name:
        :param test_instance:
        :param test_pin:
        :param test_mode:
        :param test_limits_dict:
        :return: upper_limit, lower_limit, unit
        """
        if not test_limits_dict:
            test_limits_dict = self.test_limits_dict
        a_dict = test_limits_dict[test_suite_name][test_instance][test_pin]
        return a_dict[test_mode]["Usl"], a_dict[test_mode]["Lsl"], a_dict["Units"]

    def create_limits_file(self, file_name, header=None, test_limits_dict=None, test_suite_list=None):
        """
        generate a limits file from the self.test_limits_dict object, using the instance objects:
            header, start_test_table_fields, end_test_table_fields, and tm_list
        write limits specified from the test_suite_list, if None, then write all the test_suite
        records from the test_limits_dict object
        :param file_name:
        :param test_suite_list:
        :return:
        """
        if not test_limits_dict:
            test_limits_dict = self.test_limits_dict
        if not header:
            header = self.header
        create_limits_table(file_name, header, self.end_test_table_fields, test_limits_dict, test_suite_list)

    def create_limit(self, test_suite_name, test_instance, test_pins, test_modes, test_numbers, usl_list, lsl_list, test_limits_dict=None):
        """
        create a limit from test_modes, usl_list, lsl_list, test_pins, and test_numbers
        :param test_suite_name:
        :param test_instance:
        :param test_pins:
        :param test_modes:
        :param test_numbers:
        :param usl_list:
        :param lsl_list:
        :param test_limits_dict:
        :return:
        """
        if not test_limits_dict:
            test_limits_dict = self.test_limits_dict
        if not isinstance(test_modes, list):
            test_modes = [test_modes]
        if not isinstance(test_pins, list):
            test_pins = [test_pins]
        if not isinstance(test_numbers, list):
            test_numbers = [test_numbers]
        if not isinstance(usl_list, list):
            usl_list = [usl_list]
        if not isinstance(lsl_list, list):
            lsl_list = [lsl_list]
        pass


class m_limitsTable(object):
    """
    really a wrapper for the limitsTable class to handle multiple instances of limits tables
    objects
    """
    def __init__(self, file_list):
        self.test_limits_dict = {}
        self.test_number_lookup_table = {}
        self.parse_file_list(file_list, self.test_limits_dict, self.test_number_lookup_table)

    def parse_file_list(self, file_list, test_limits_dict, test_number_lookup_table):
        for a_file in file_list:
            lt = limitsTable(a_file)
            for tsname,a_dict in lt.test_limits_dict.iteritems():
                if not tsname in test_limits_dict:
                    test_limits_dict[tsname] = {}
                for tname, t_dict in a_dict.iteritems():
                    test_limits_dict[tsname][tname] = t_dict
                    for tpin, r_dict in t_dict.iteritems():
                        tnum, tinstance = int(r_dict["Test number"]), r_dict["used Instance Name"]
                        test_number_lookup_table[tnum] = {
                            "tsname": tsname,
                            "tinstance": tinstance,
                            "tname": tname,
                            "tpin": tpin
                        }


def create_limits_table(file_name, header=None, end_test_table_fields=None, test_limits_dict=None, test_suite_list=None):
    """
    create limits table object
    :param file_name:
    :param header:
    :param end_test_table_fields:
    :param test_limits_dict:
    :param test_suite_list:
    :return:
    """
    chk_list = [] + header
    if not test_suite_list:
        test_suite_list = test_limits_dict.keys()
    for test_suite in test_suite_list:
        a_dict = self.test_limits_dict[test_suite]
        for test_name, r_dict in a_dict.iteritems():
            for test_pin, t_dict in r_dict.iteritems():
                a_string = "{0},{1},{2},".format(test_suite, test_name, test_pin)
                a_string += "{0},{1},{2},".format(t_dict["Units"], t_dict["Lsl_typ"], t_dict["Usl_typ"])
                for test_mode in self.tm_list:
                    a_string += "{0},{1},".format()
                a_string += ",".join([t_dict[a_key] for a_key in self.end_test_table_fields])
                chk_list.append(a_string)
    f = util.FileUtils(file_name)
    f.write_to_file(chk_list)


def get_missing_test_numbers(a_dict, logged_test_numbers):
    """
    generated a list of test numbers not present in logged_test_numbers, meaning they exist
    in the limits table, but are likely not being tested in the test flow
    :param a_dict: test_limits_dict[tsname]
    :param logged_test_numbers:
    :return: missing test numbers list
    """
    tnum_list = []
    for tname, t_dict in a_dict.iteritems():
        for tpin, r_dict in t_dict.iteritems():
            tnum_list.append(int(r_dict["Test number"]))
    missing = list(set(tnum_list) - set(logged_test_numbers))
    return missing, tnum_list
