import util
import re
import os


def configDict(config_file):
    """
    read in a configuration file and populate a dict structure of pin groups, pins, and ports
    :param config_file:
    :return: config_dict
    """
    pin_expr = "\((?P<pin>[\w\+]+)\)"
    chan_expr = "(?P<chan>\w+|\([\,\d]+\))"
    id_expr = "\"?(?P<id>\w+)?\"?"
    operation_mode_expr = "(?P<op_mode>DFP[NS])"
    searchStr = "^\s*{op_mode}\s+{chan}\s*,\s*{id}\s*,\s*{pin}".format(
            op_mode=operation_mode_expr, chan=chan_expr, id=id_expr, pin=pin_expr
    )
    f = util.FileUtils(config_file, True)

    # read in config file.  populate dict structure of pin groups, pins, and ports
    g = util.m_re(f.contents)
    g.grep("^DFP[NS]\s+(?:\w+|\([\,\d]+\)),\s*\"?\w*\"?,\([\w\+]+\)")
    pin_list_dict = [
        re.search(searchStr, a_row)
        for a_row in g.lines
    ]
    pin_list = []
    pin_map_dict = {}
    for i,m in enumerate(pin_list_dict):
        try:
            a_dict = m.groupdict()
            map_keys = list(set(a_dict.iterkeys()) - {"pin"})
            if a_dict["op_mode"] == "DFPN":
                pin_list.append(a_dict["pin"])
            pin_map_dict[a_dict["pin"]] = dict([(k, a_dict[k]) for k in map_keys])
        except AttributeError, e:
            print "Uh Oh, Error in building pin_list_dict, bailing out....\n{0}".format(e)
            raise

    g.clear_cache()
    g.grep("^DFGP")
    chk_list = [re.search("DFGP\s+\w+,\((?P<pins>[\w\,\+]+)\),\((?P<pin_group>\w+)\)", a_row) for a_row in g.lines]
    pin_group_dict = {}
    for m in chk_list:
        if m:
            pin_group, pins = m.groupdict()["pin_group"], m.groupdict()["pins"].split(",")
            if not pin_group_dict.has_key(pin_group):
                pin_group_dict[pin_group] = []
            pin_group_dict[pin_group] = list(set(pin_group_dict[pin_group] + pins))

    g.clear_cache()
    g.grep("^DFPT")
    chk_list = [re.search("DFPT\s+\((?P<pins>[\w\,]+)\),\((?P<port>\w+)\)", a_row) for a_row in g.lines]
    port_dict = {}
    for m in chk_list:
        if m:
            port, pins = m.groupdict()["port"], m.groupdict()["pins"].split(",")
            if not port_dict.has_key(port):
                port_dict[port] = []
            port_dict[port] += pins
    return pin_list, pin_map_dict, pin_group_dict, port_dict


def expandToPins(a_list, full_pin_list, pin_group_dict):
    """
    pass in a list of pins and/or pingroups mixed together, and expand the pingroups to pins
    :param a_list:
    :param full_pin_list
    :param pin_group_dict
    :return: pin_list
    """
    pin_groups_only = list(set(a_list) - set(full_pin_list))
    pin_list = list(set(a_list) - set(pin_groups_only)) if len(pin_groups_only) > 0 else a_list
    for pin_group in pin_groups_only:
        pin_list += pin_group_dict[pin_group]
    return list(set(pin_list))  # filter out any duplicates


def parsePinsField(a_string, full_pin_list, pin_group_dict):
    pin_list = expandToPins(re.sub("[\-\(\)]", "", a_string).split(), full_pin_list, pin_group_dict)
    # do we have any pins we're subtracting, i.e. -( aPin bPin....)
    if util.in_string(a_string, "-\("):
        p_string = re.sub("[\w\s]+-\(\s+", "", a_string)
        remove_pins = expandToPins(re.sub("\s+\)","", p_string.strip()).split(), full_pin_list, pin_group_dict)
        pin_list = list(set(pin_list) - set(remove_pins))
    return pin_list


def parseMFH(mfh_file, reg_exp="", ref_keys=None):
    """
    ref_keys
    :param mfh_file: is the file reference all the external files used to create the object in questions, such as levels
    :param reg_exp:  is a search string regular expression with two keys: ref_type and ref_name
    :param ref_keys: are the reference types for the files referenced int the mfh file, i.e, EQNSET
    :return: ref_dict
    """
    if ref_keys is None:
        ref_keys = []
    base_path = os.path.dirname(mfh_file)
    f = util.FileUtils(mfh_file, True)
    ref_dict = {}
    chk_list = util.keep_in_list(f.contents, reg_exp)
    for a_line in chk_list:
        m = re.search(reg_exp, a_line)
        if m:
            m_dict = m.groupdict()
            if len(m_dict)>0:
                ref_type, ref_name = m_dict["ref_type"], m_dict["ref_name"]
                if not ref_dict.has_key(ref_type):
                    ref_dict[ref_type] = {}
                ref_dict[ref_type][ref_name] = os.path.join(
                        base_path,
                        re.sub("\s*#.*$", "", a_line.split(":")[-1]).strip()
                )
    return ref_dict


def getSpecHeaderSpan(hdr_line):
    """
    get the spans for specname, actual, min, max, and units from a SPECSET line
    :param hdr_line:
    :return: a list of slices for each section of the hdr line, slice(0,17) for spec name
    """
    chk_list = util.my_split(hdr_line, "\s[\*U]")
    i_list = [len(a_split)+2 for a_split in chk_list[:-1]]  # 2 is the length of the search pattern
    span_indices = [0]
    running_sum = 0
    for a_num in i_list:
        running_sum += a_num
        span_indices.append(running_sum-1)
    return [slice(a,b) for a,b in zip(span_indices, span_indices[1:]+[-1])]


def _getLevelEqnSet(lvl_dict, contents, eq_start, eq_stop, specs_level_dict, full_pin_list, pin_group_dict):
    """
    process Levels EqnSet object
    :param lvl_dict: ref_dict["EQNSET"][eqnset_num]
    :param contents:
    :param eq_start:
    :param eq_stop:
    :param specs_level_dict:
    :return:
    """
    eq_contents = contents[eq_start:eq_stop]
    eq_g = util.m_re(eq_contents)
    eq_g.grep(specs_level_dict["subSections"])
    eq_indices = [int(float(a_num)-1) for a_num in eq_g.coordinates]+[len(eq_contents)]
    lvl_dict["sub_sections"] += list(set([a_row.split()[0] for a_row in eq_g.m_groups]))
    dps_i = 0
    for sub_section, sub_section_start, sub_section_stop in zip(eq_g.m_groups, eq_indices[:-1], eq_indices[1:]):
        if re.search("\\b(SPECS|EQUATIONS)\\b", sub_section):
            sub_section_type = sub_section
        else:
            sub_section_type = sub_section.strip().split()[0]
        sub_section_contents = eq_contents[sub_section_start+1:sub_section_stop]
        if not lvl_dict.has_key(sub_section_type):
            lvl_dict[sub_section_type] = {}
        if re.search("SPECS", sub_section_type):
            lvl_dict[sub_section_type] = dict([
                specs_level_dict[sub_section](a_row) for a_row in sub_section_contents
            ])
        elif re.search("EQUATIONS", sub_section_type):
            chk_list = [specs_level_dict[sub_section](a_row) for a_row in sub_section_contents]
            for field,value in chk_list:
                lvl_dict[sub_section_type][field] = "".join(value.split()) #strip out any whitespace
        elif re.search("DPSPINS", sub_section_type):
            lvl_dict[sub_section_type][dps_i] = {}
            a_string = " ".join(eq_contents[sub_section_start].split()[1:])
            pin_list = a_string.split()  # parsePinsField(a_string, full_pin_list, pin_group_dict)
            p_dict = dict([specs_level_dict["DPSPINS"](a_row) for a_row in sub_section_contents])
            lvl_dict[sub_section_type][dps_i]["pin_list"] = pin_list
            lvl_dict[sub_section_type][dps_i]["fields_dict"] = p_dict
            dps_i += 1
        elif re.search("LEVELSET", sub_section_type):
            m = re.search("^\s*LEVELSET\s+(?P<num>\d+)\s*\"?(?P<name>[\w\s\-]+)?\"?", sub_section)
            m_dict = m.groupdict()
            lvl_num, lvl_name = int(m_dict["num"]), m_dict["name"]
            lvl_dict[sub_section_type][lvl_num] = {"name": lvl_name}
            lvl_g = util.m_re(sub_section_contents)
            lvl_g.grep(specs_level_dict[sub_section_type])
            i_list = [int(float(a_num)-1) for a_num in lvl_g.coordinates] + [len(sub_section_contents)]
            for i,l_grp,l_start,l_stop in zip(
                    xrange(len(lvl_g.m_groups)), lvl_g.m_groups, i_list[:-1], i_list[1:]
            ):
                l_pin_list = expandToPins(re.sub("-\(|\)", "", l_grp).split()[1:], full_pin_list, pin_group_dict)
                p_dict = dict([
                    specs_level_dict["EQUATIONS"](a_row) for a_row in sub_section_contents[l_start+1:l_stop]
                ])
                lvl_dict[sub_section_type][lvl_num][i] = {}
                lvl_dict[sub_section_type][lvl_num][i]["pin_list"] = l_pin_list
                lvl_dict[sub_section_type][lvl_num][i]["fields_dict"] = p_dict
    pass


def _getLevelSpsSet(lvl_dict, contents, eq_start, eq_stop, specs_level_dict):
    spec_hdr_keys = ["specname", "actual", "minimum", "maximum", "units"]
    eq_contents = contents[eq_start:eq_stop]
    eq_g = util.m_re(eq_contents)
    eq_g.grep(specs_level_dict["subSections"])
    eq_indices = [int(float(a_num)-1) for a_num in eq_g.coordinates]+[len(eq_contents)]
    lvl_dict["sub_sections"] = list(set([a_row.split()[0] for a_row in eq_g.m_groups]))
    for sub_section, sub_section_start, sub_section_stop in zip(eq_g.m_groups, eq_indices[:-1], eq_indices[1:]):
        sub_section_type = sub_section.strip().split()[0]
        sub_section_contents = eq_contents[sub_section_start+1:sub_section_stop]
        if not lvl_dict.has_key(sub_section_type):
            lvl_dict[sub_section_type] = {}
        if re.search("SPECSET", sub_section_type):
            m = re.search("^\s*SPECSET\s+(?P<num>\d+)\s*\"?(?P<name>[\w\s\-]+)?\"?", sub_section)
            m_dict = m.groupdict()
            spec_num, spec_name = int(m_dict["num"]), m_dict["name"]
            lvl_dict[sub_section_type][spec_num] = {"specset_name": spec_name, "SPECS":{}}
            hdr_i = util.find_index(sub_section_contents, "# SPECNAME\s+\*+ACTUAL")
            hdr_slices = getSpecHeaderSpan(sub_section_contents[hdr_i])
            spec_lines = util.remove_from_list(
                [re.sub("\s*#\s*.*$", "", a_row) for a_row in sub_section_contents],
                "^\s*$"
            )
            for a_line in spec_lines:
                units = re.findall(r"\[.*?\]",a_line)[0].strip('[] ')
                a_line = a_line[:a_line.find('[')]
                parts = a_line.split()
                name = parts[0]
                actual = parts[1]
                if len(parts)>2:
                    minVal = parts[2]
                else:
                    minVal = ''
                    maxVal = ''
                if len(parts)>3:
                    maxVal = parts[3]
                else:
                    maxVal = ''
                #a_dict = dict([
                #    (a_key, re.sub("[\[\]]", "", a_line[a_slice]).strip())
                #    for a_key,a_slice in zip(spec_hdr_keys,hdr_slices)
                #])
                #key_list = list(set(a_dict.iterkeys()) - {"specname"})
                lvl_dict[sub_section_type][spec_num]["SPECS"][name] =\
                    {'actual': actual, 'minimum':minVal, 'maximum': maxVal, 'UNUTS': units}
                #   dict([
                #        (a_key, a_dict[a_key]) for a_key in key_list
                #])
    pass


def getLevels(levels_file, spec_levels_groups, full_pin_list, pin_group_dict):
    """
    Parse out levels objects, split into EQN and SPS sections for a dictionary
    :param levels_file:
    :param spec_levels_groups:
    :return: big levels dict, containing all info pertaining to equation sets, level sets, pins, etc....
    """
    f = util.FileUtils(levels_file, True)
    g = util.m_re(f.contents)
    g.grep(spec_levels_groups["topLevel"])
    # with levels, the eqnset is broken down into two sets: Equation(EQN) and Spec(SPS)
    start_pts,stop_pts = util.find_blocks(
            g.m_groups, spec_levels_groups["startClause"], spec_levels_groups["stopClause"]
    )
    ref_dict = {"EQN":{}, "SPS":{}}
    for start, stop in zip(start_pts, stop_pts):
        contents = g.allLines[int(float(g.coordinates[start])-1): int(float(g.coordinates[stop])-1)]
        if util.in_string(g.lines[start], "EQN"):
            level_key = "EQN"
        else:
            level_key = "SPS"
        level_dict = spec_levels_groups[level_key]
        b = util.m_re(contents)
        for remove_expr in level_dict["remove"]:
            b.sub(remove_expr,"")
        contents = util.remove_from_list(contents, "^\s*$")
        b = util.m_re(contents)
        b.grep(level_dict["topLevel"])
        i_list = [int(float(a_num)-1) for a_num in b.coordinates]
        if len(i_list)>1:
            eqn_set_indices = [(a,b) for a,b in zip(i_list,i_list[1:]+[len(contents)])]
        else:
            eqn_set_indices = [(i_list[0], len(contents))]
        for (eq_start,eq_stop) in eqn_set_indices:
            eq_m = re.search("^\s*EQNSET\s+(?P<eq_num>\d+)\s*\"?(?P<eq_name>[\w\s\-\.]+)?\"?", contents[eq_start])
            eq_num, eq_name = -99, ""
            try:
                eq_dict = eq_m.groupdict()
                eq_num, eq_name = int(eq_dict["eq_num"]), eq_dict["eq_name"]
            except KeyError, e:
                if eq_num == -99:
                    print "Uh Oh, we should always have an EQNSET number\n{0}".format(e)
                    print "\n{0}".format(contents[eq_start])
                    raise
                else:
                    pass # may not always have an equation set name
            ref_dict[level_key][eq_num] = {"eq_name": eq_name, "sub_sections":[]}
            if level_key == "EQN":
                _getLevelEqnSet(
                    ref_dict[level_key][eq_num], contents, eq_start, eq_stop,
                    level_dict, full_pin_list, pin_group_dict
                )
            elif level_key == "SPS":
                _getLevelSpsSet(ref_dict[level_key][eq_num], contents, eq_start, eq_stop, level_dict)
    return ref_dict


def _getTimingEqnSet(t_dict, contents, eq_start, eq_stop, specs_timing_dict, full_pin_list, pin_group_dict):
    """
    process Timing EqnSet object
    :param t_dict:
    :param contents:
    :param eq_start:
    :param eq_stop:
    :param specs_timing_dict:
    :param full_pin_list:
    :param pin_group_dict:
    :return:
    """
    eq_contents = contents[eq_start:eq_stop]
    eq_g = util.m_re(eq_contents)
    eq_g.grep(specs_timing_dict["subSections"])
    eq_indices = [int(float(a_num)-1) for a_num in eq_g.coordinates]+[len(eq_contents)]
    t_dict["sub_sections"] += list(set([a_row.split()[0] for a_row in eq_g.m_groups]))
    for sub_section, sub_section_start, sub_section_stop in zip(eq_g.m_groups, eq_indices[:-1], eq_indices[1:]):
        if re.search("\\b(SPECS|EQUATIONS)\\b", sub_section):
            sub_section_type = sub_section
        else:
            sub_section_type = sub_section.strip().split()[0]
        sub_section_contents = eq_contents[sub_section_start+1:sub_section_stop]
        if not t_dict.has_key(sub_section_type):
            t_dict[sub_section_type] = {}
        if re.search("SPECS", sub_section_type):
            t_dict[sub_section_type] = dict([
                specs_timing_dict[sub_section_type](a_row) for a_row in sub_section_contents
            ])
        elif re.search("EQUATIONS", sub_section_type):
            chk_list = [specs_timing_dict[sub_section](a_row) for a_row in sub_section_contents]
            for field,value in chk_list:
                t_dict[sub_section_type][field] = "".join(value.split()) #strip out any whitespace
        elif re.search("DEFINES", sub_section_type):
            t_dict[sub_section_type] = specs_timing_dict[sub_section_type](sub_section)
        elif re.search("TIMINGSET", sub_section_type):
            m = re.search("^\s*TIMINGSET\s+(?P<num>\d+)\s*\"?(?P<name>[\w\s\-]+)?\"?", sub_section)
            m_dict = m.groupdict()
            t_num, t_name = int(m_dict["num"]), m_dict["name"]
            t_dict[sub_section_type][t_num] = {"name": t_name}
            t_g = util.m_re(sub_section_contents)
            t_g.grep(specs_timing_dict[sub_section_type])
            i_list = [int(float(a_num)-1) for a_num in t_g.coordinates] + [len(sub_section_contents)]
            for i,t_grp,t_start,t_stop in zip(
                    xrange(len(t_g.m_groups)), t_g.m_groups, i_list[:-1], i_list[1:]
            ):
                if re.search("^\s*period", t_grp):
                    t_dict[sub_section_type][t_num]["period"] = "".join(t_grp.split("=")[-1].strip().split())
                else:
                    t_pin_list = expandToPins(re.sub("-\(|\)", "", t_grp).split()[1:], full_pin_list, pin_group_dict)
                    p_dict = dict([
                        specs_timing_dict["EQUATIONS"](a_row) for a_row in sub_section_contents[t_start+1:t_stop]
                    ])
                    t_dict[sub_section_type][t_num][i] = {}
                    t_dict[sub_section_type][t_num][i]["pin_list"] = t_pin_list
                    t_dict[sub_section_type][t_num][i]["fields_dict"] = p_dict
        pass


def _getTimingSpsSet(t_dict, eq_contents, specs_timing_dict, spec_list):
    # spec_hdr_keys = ["specname", "actual", "minimum", "maximum", "units"]
    spec_hdr_keys = ["specname", "actual", "units"]
    eq_g = util.m_re(eq_contents)
    eq_g.grep("[{}]")  #pull out {} blocks, such as SYNC { ..... }
    if eq_g.pattern_count >= 2:
        start_pts,stop_pts = util.find_blocks(eq_g.m_groups, "{", "}")
        i_list = [
            (int(float(eq_g.coordinates[s_a])-2), int(float(eq_g.coordinates[s_b])))
            for s_a,s_b in zip(start_pts, stop_pts)
            ]
        del_indices=[]
        for (x,y) in i_list:
            del_indices += range(x,y)
        eq_contents = [
            eq_contents[i] for i in list(sorted(set(xrange(len(eq_contents))) - set(del_indices)))
            ]
        eq_g = util.m_re(eq_contents)
    else:
        eq_g.clear_cache()
    eq_g.grep(specs_timing_dict["subSections"]) # get all eqnset references with SPECIFICATION block
    t_dict["sub_sections"] = [a_row.split()[0].strip() for a_row in eq_g.m_groups]
    if not util.in_list(t_dict["sub_sections"], "SPECNAME"):
        t_dict["sub_sections"].append("SPECNAME, missing actual # SPECNAME comment")
        eq_g.m_groups.append("# SPECNAME")
        eq_g.coordinates.append("-1.1")
    for a_grp,i in zip(eq_g.m_groups, [int(float(a_num)-1) for a_num in eq_g.coordinates]):
        if not util.in_string(a_grp, "SPECNAME"):
            sub_section_type = a_grp.split()[0].strip()
        else:
            sub_section_type = "SPECS"
        if sub_section_type == "WAVETBL":
            t_dict[sub_section_type] = re.sub("\"", "", a_grp.partition(" ")[-1]).strip()
        elif sub_section_type == "PORT":
            t_dict[sub_section_type] = re.sub("^\s*PORT\s+", "", a_grp).split()
        elif sub_section_type == "SPECS":
            t_dict[sub_section_type] = {}
            # hdr_i = util.find_index(eq_contents, "# SPECNAME\s+\*+ACTUAL")
            # hdr_slices = getSpecHeaderSpan(eq_contents[hdr_i])
            # spec_lines = util.remove_from_list(
            #     [re.sub("\s*#\s*.*$", "", a_row) for a_row in eq_contents[hdr_i+1:]],
            #     "^\s*$"
            # )
            spec_lines = util.keep_in_list(eq_contents, "^\s*(?:{0})\s+".format("|".join(spec_list)))
            for a_line in spec_lines:
                # a_dict = dict([
                #     (a_key, re.sub("[\[\]]", "", a_line[a_slice]).strip())
                #     for a_key,a_slice in zip(spec_hdr_keys,hdr_slices)
                # ])
                spec_name, _dummy, a_string = re.sub("\t","    ",a_line.strip()).partition(" ")
                actual_value,_dummy, a_string = a_string.strip().partition(" ")
                units = None
                u_m = re.search("\[\s*(?P<units>\w+)?\s*\]",a_string)
                if u_m:
                    units = u_m.groupdict()["units"]
                a_dict = {
                    "specname": spec_name,
                    "actual": actual_value,
                    "units": units if not units is None else ""
                }
                key_list = list(set(a_dict.iterkeys()) - {"specname"})
                t_dict[sub_section_type][a_dict["specname"]] = dict([(a_key, a_dict[a_key]) for a_key in key_list])
    pass


def _getTimingGlobalSpecVars(t_dict, eq_contents):
    """
    determine if we have any global variables in a timing SPECIFICATION object
    """
    spec_hdr_keys = ["specname", "actual", "minimum", "maximum", "units"]
    eq_g = util.m_re(eq_contents)
    eq_g.grep("[{}]")  #pull out {} blocks, such as SYNC { ..... }
    if eq_g.pattern_count >= 2:
        start_pts,stop_pts = util.find_blocks(eq_g.m_groups, "{", "}")
        i_list = [
            (int(float(eq_g.coordinates[s_a])-2), int(float(eq_g.coordinates[s_b])))
            for s_a,s_b in zip(start_pts, stop_pts)
            ]
        del_indices=[]
        for (x,y) in i_list:
            del_indices += range(x,y)
        eq_contents = [
            eq_contents[i] for i in list(set(xrange(len(eq_contents))) - set(del_indices))
            ]
        eq_g = util.m_re(eq_contents)
    else:
        eq_g.clear_cache()
    hdr_i = util.find_index(eq_contents, "# SPECNAME\s+\*+ACTUAL")
    if hdr_i > -1:
        hdr_slices = getSpecHeaderSpan(eq_contents[hdr_i])
        spec_lines = util.remove_from_list(
            [re.sub("\s*#\s*.*$", "", a_row) for a_row in eq_contents[hdr_i+1:]],
            "^\s*$"
        )
        for a_line in spec_lines:
            a_dict = dict([
                (a_key, re.sub("[\[\]]", "", a_line[a_slice]).strip())
                for a_key,a_slice in zip(spec_hdr_keys,hdr_slices)
            ])
            key_list = list(set(a_dict.iterkeys()) - {"specname"})
            t_dict[a_dict["specname"]] = dict([(a_key, a_dict[a_key]) for a_key in key_list])
    pass


def getTiming(timing_file, spec_timing_groups, full_pin_list, pin_group_dict, ref_eqn_dict):
    """
    ref_eqn_dict is a running copy of the ref_dict["EQN"] dictionary, and is treated as "read-only",
    with the sole purpose as a reference for the SPEC parameters that get determined in the 
    ref_dict["SPS"] dictionary.
    """
    ref_dict = {"EQN":{}, "SPS":{}, "WVT":{}}
    f = util.FileUtils(timing_file, True)
    g = util.m_re(f.contents)
    g.grep(spec_timing_groups["topLevel"])
    # with timing, the eqnset is broken down into two sets: Equation(EQN) and Spec(SPS)
    start_pts,stop_pts = util.find_blocks(
            g.m_groups, spec_timing_groups["startClause"], spec_timing_groups["stopClause"]
    )
    for start, stop in zip(start_pts, stop_pts):
        contents = g.allLines[int(float(g.coordinates[start])-1): int(float(g.coordinates[stop])-1)]
        if util.in_string(g.lines[start], "EQN"):
            timing_key = "EQN"
        elif util.in_string(g.lines[start], "WVT"):
            timing_key = "WVT"
            break
        else:
            timing_key = "SPS"
            b = util.m_re(contents)
            b.grep(spec_timing_groups["SPS"]["SPECIFICATION"])
            specName = re.sub("^\s*SPECIFICATION\s+\"|\"", "", b.m_groups[0]).strip()
            ref_dict["SPS"] = {specName:{"GLOBALS":{}}}
        timing_dict = spec_timing_groups[timing_key]
        b = util.m_re(contents)
        for remove_expr in timing_dict["remove"]:
            b.sub(remove_expr,"")
        contents = util.remove_from_list(contents, "^\s*$")
        b = util.m_re(contents)
        b.grep(timing_dict["topLevel"])
        i_list = [int(float(a_num)-1) for a_num in b.coordinates]
        if len(i_list)>1:
            eqn_set_indices = [(a,b) for a,b in zip(i_list,i_list[1:]+[len(contents)])]
        else:
            eqn_set_indices = [(i_list[0], len(contents))]
        if timing_key == "SPS": # let's check for globals
            _getTimingGlobalSpecVars(ref_dict[timing_key][specName]["GLOBALS"], contents[util.find_index(contents,"{")+1:i_list[0]])

        for (eq_start,eq_stop) in eqn_set_indices:
            eq_m = re.search("^\s*EQNSET\s+(?P<eq_num>\d+)\s*\"?(?P<eq_name>[\w\s\-\.]+)?\"?", contents[eq_start])
            eq_num, eq_name = -99, ""
            try:
                eq_dict = eq_m.groupdict()
                eq_num, eq_name = int(eq_dict["eq_num"]), eq_dict["eq_name"]
            except KeyError, e:
                if eq_num == -99:
                    print "Uh Oh, we should always have an EQNSET number\n{0}".format(e)
                    print "\n{0}".format(contents[eq_start])
                    raise
                else:
                    pass # may not always have an equation set name
            if timing_key == "EQN":
                ref_dict[timing_key][eq_num] = {"eq_name": eq_name, "sub_sections":[]}
                _getTimingEqnSet(
                        ref_dict[timing_key][eq_num], contents, eq_start, eq_stop,
                        timing_dict, full_pin_list, pin_group_dict
                )
            elif timing_key == "SPS":
                ref_dict[timing_key][specName][eq_num] = {"name":eq_name}
                _getTimingSpsSet(ref_dict[timing_key][specName][eq_num], contents[eq_start:eq_stop], timing_dict, ref_eqn_dict[eq_num]["SPECS"].keys())
    return ref_dict

def sortByInt(wList):
    m_list = [re.search("^[A-Za-z_]+(?P<id>\d+)\w*$", aWft) for aWft in wList]
    a_dict = dict([(int(m.groupdict()["id"]), aWft) for m,aWft in zip(m_list,wList)])
    sortedList = [a_dict[id] for id in sorted(a_dict.iterkeys())]
    return sortedList
