import logging
import re
import string
import sys
import traceback
import os
import fnmatch
import commands
import getopt
import copy
import random
import pickle
import json
import csv
import shutil
import gzip
import mmap
from time import localtime, time, mktime, struct_time
from operator import itemgetter, attrgetter
from itertools import chain, islice, tee, ifilter, ifilterfalse
from collections import namedtuple
from struct import pack, unpack
from math import sqrt

var = """util-> python module that contains the following classes and functions:
m_grep ->
    intent is to grep a regexp pattern from a text_window dump, list of strings, or single string, this class is used
    in many other classes

Strip_C_Comments ->
    To counter cases such as an object defined with comments and/or cases of redundancy and unused code, strip out all
    C like comments, C++ comments, and #if 0 blocks.  Might have to add #if False blocks to list.

CaptureBlocks ->
    Tag the start and stop of a block, such as a C function, enVision Object, vector field of a Catalyst IMAGE test
    pattern, etc.

Join_M_Lines ->
    In order to speed up analysis of multi-line statements that terminate with a character such as a semicolon
    (think tl, c, c++, etc), this class joins statements that contain multiple lines into 1.  This is especially handy
    with digital pattern files, where op-codes and labels on one line are followed by analog hdw calls, ac microcodes
    and channel data on 1 or more lines.

FileUtils(FileStats) -> FileUtils inherits FileStats, functions based on os module for miscellaneous things like
    determining and resolving  absolute path of a file, evaluating it's timestamp, boolean functions such as is_file,
    is_path_relative, and append_to_file.

find_index, sort_numbers, my_sort, sort_unique, split_list, _list_copy, _list_reduce, _dictionary_copy,
    _dictionary_reduce, PrettyPrint

handy lambda functions:
    get_cr: Used in pretty_format, check for carriage return at EOL, return the _sre.SRE_Match obj or None
    strip_tw: Used in func:pretty_format, strip trailing whitespace, append CR if found with get_cr
    do_scramble: Used in class:Scramble, for scrambling (remapping) list indices around based on map_dict
    shuffle: Used in class:DeScramble, for shuffling (remapping) list indices around based on list_seq and map_dict
    get_mmap_position: Used in class:mmap_utils, a pass through function returns current position in mmap_obj
        if pos>-1 and pos!=None.
    """

#handy lambda functions
get_cr = lambda a_str: re.search(re.compile('$\r?\n'), a_str)


strip_tw = lambda a_str: '%s%s'%(a_str.rstrip(), get_cr(a_str).group() if get_cr(a_str) else '')


do_scramble = lambda a_list, map_dict: [ a_list[map_dict[i]] for i in sorted(map_dict.iterkeys()) ]


shuffle = lambda a_list, map_dict, list_seq: [a_list[map_dict[i]] for i in xrange(len(list_seq)) ]


get_mmap_position = lambda mmap_obj, pos:pos if (pos>-1 and pos!=None) else mmap_obj.tell()


resort_list = lambda a_list, sort_by_fields=itemgetter(0), key_func=lambda x:x : \
    sorted(a_list,key=lambda x:sort_by_fields(key_func(x)))


def get_newline_offset(mmap_obj, position=None, offset=0):
    """
    Used in mmap_utils, returns newline offset in bytes, based on the position and offset parameters.
    offset defaults to 0, typically, it's -1, to determine newline offset preceding position value
    postion defaults to None, typically determining newline offset based on current position in mmap_obj,
    which is mmap_obj.tell()
    """
    current_position = get_mmap_position(mmap_obj, position)
    newline_offsets = current_position + offset
    return newline_offsets

hex2int = lambda a_hex_string: int(a_hex_string, 16)
bin2int = lambda a_binary_string: int(a_binary_string, 2)
int2hex = lambda integer_number: hex(integer_number)
int2bin = lambda integer_number: bin(integer_number)
bin2hex = lambda a_binary_string: int2hex(bin2int(a_binary_string))
hex2bin = lambda a_hex_string: int2bin(hex2int(a_hex_string))
#functions
#


def find_closest_pt(a_pt, start_pts, end_pts):
     for i, start_pt, end_pt in zip(xrange(len(start_pts)), start_pts, end_pts):
         if a_pt>=start_pt and a_pt<=end_pt: break
     return(start_pt, end_pt)


def find_closest_pt_iter(a_pt, start_pts, end_pts):
     for end_pt in end_pts:
         if end_pt>=a_pt: break
     start_pt = start_pts[0]
     num_start_pts = len(start_pts)
     i = 0
     while start_pt<=end_pt and start_pt<=a_pt and i < num_start_pts:
         i += 1
         prev_start_pt = start_pt
         start_pt = start_pts[i] if i<num_start_pts else prev_start_pt
     yield (prev_start_pt, end_pt)


def find_closest_pts(a_pts_list, start_pts, end_pts):
    start_stop_iter = find_closest_pts_iter(a_pts_list, start_pts, end_pts)
    return( list(start_stop_iter))


def find_closest_pts_iter(a_pts_list, start_pts, end_pts):
    num_start_pts, num_end_pts = len(start_pts), len(end_pts)
    for a_pt in a_pts_list:
        yield find_closest_pt_iter(a_pt, start_pts, end_pts).next()


def expand_sequence(a_list):
    """expand_sequence: pass in a list of integers, i.e. 1, 2, 3, 5, 11, 12, 13 which returns a sequence by 1's:
    1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13"""
    chk_list = [ (a1, a2) for a1, a2 in zip(a_list[:-1], a_list[1:]) if a2-a1>1 ]
    expanded_seq = []
    for a1, a2 in zip(a_list[:-1], a_list[1:]): expanded_seq += [a1, a2] if a2-a1==1 else []
    for a1, a2 in chk_list: expanded_seq += range(a1, a2+1)
    return sort_unique(expanded_seq)


def string_cast(a_list):
    """cast elements from list to string"""
    if type(a_list) != type([1, 2, 3]): return('%s'%a_list)
    else: 
        list_indices = xrange(len(a_list))
        a_iter = string_cast_iter(a_list)
        return( [ a_iter.next() for i in list_indices ])
        #return([ '%s'%a_line for a_line in a_list])


def string_cast_iter(a_list):
    if type(a_list) == type("a_string"): a_iter = iter([a_list])
    elif type(a_list) == type([0, 1, 2]): a_iter = iter(a_list)
    else: a_iter = a_list
    for a_line in a_iter: yield '%s'%a_line


def int2bin(n, count=24):
    """returns the binary of integer n, using count number of digits"""
    return "".join([str((n >> y) & 1) for y in range(count-1, -1, -1)])


def utp_average(inAry, utps):
    """utp_average(inAry, num_utps)
pass in a list of floats and the number of utps to average into 1 utp cycle."""
    effective_N = len(inAry)/utps
    utpRange, elementRange = range(utps), range(effective_N)
    outAry = inAry[:effective_N]
    for i in utpRange: outAry = [ (outAry[j]+inAry[i*effective_N+j])/2.0 for j in elementRange ]
    return(outAry)


def my_split(a_string, delim='\s*', include_empties=False):
    search_pattern = re.compile(delim)
    m = re.split(search_pattern, a_string)
    if len(m)>0:
        if not include_empties: a_list = [ a_string for a_string in m if len(a_string)>0 ]
        else: a_list = [ a_string for a_string in m ]
        return(a_list)
    else:
        return(a_string)


def old_my_split(a_string, delim='\s*', include_empties=False):
    search_pattern = re.compile(delim)
    m = re.split(search_pattern, a_string)
    if len(m)>0:
        if not include_empties: a_list = [ a_string for a_string in m if len(a_string)>0 ]
        else: a_list = [ a_string for a_string in m ]
        return(a_list)
    else:
        return(a_string)


def pretty_format(a_list, delimeter=':', joint='', do_left_just=True, do_rstrip=False):
    """pretty_format(a_list[, delimeter=':', joint='', do_left_just=True, do_rstrip=False])
delimeter: default ':', can use regex, the parameter for splitting the line in a_list
joint: default '', the parameter for joining back the reformatted line in a_list
do_left_just: default True, left justify each column, if False, then right justify
do_rstrip: default False, strip all trailing whitespace and append CR if found per line in a_list
Usage: pretty_list = pretty_format(a_list,':',':', do_rstrip=True)
pass in a list of strings with each string consisting of sub strings seperated
by a delimeter such as ':', a friendlier to the eyes list is returned, i.e.
a_list=['PinName:Direction:ChainName:ChainLength',
        'EXT_DATA0:scan_in_pin:ChainLength1:2141', 
        'EXT_ADR0:scan_out_pin:ChainLength1:2141',
        'EXT_DATA1:scan_in_pin:ChainLength2:2141',
        'EXT_ADR1:scan_out_pin:ChainLength2:2141', 
        'EXT_DATA2:scan_in_pin:ChainLength3:2141', 
        'EXT_ADR2:scan_out_pin:ChainLength3:2141', 
        'EXT_DATA3:scan_in_pin:ChainLength4:2141', 
        'EXT_ADR3:scan_out_pin:ChainLength4:2141', 
        'EXT_DATA4:scan_in_pin:ChainLength5:2141', 
        'EXT_ADR4:scan_out_pin:ChainLength5:2141', 
        'EXT_DATA5:scan_in_pin:ChainLength6:2141', 
        'EXT_ADR5:scan_out_pin:ChainLength6:2141', 
        'EXT_DATA6:scan_in_pin:ChainLength7:2141', 
        'EXT_ADR6:scan_out_pin:ChainLength7:2141', 
        'EXT_DATA7:scan_in_pin:ChainLength8:2141', 
        'EXT_ADR7:scan_out_pin:ChainLength8:2141']
would return a list:
['PinName  : Direction   : ChainName   : ChainLength', 
 'EXT_DATA0: scan_in_pin : ChainLength1: 2141       ', 
 'EXT_ADR0 : scan_out_pin: ChainLength1: 2141       ', 
 'EXT_DATA1: scan_in_pin : ChainLength2: 2141       ', 
 'EXT_ADR1 : scan_out_pin: ChainLength2: 2141       ', 
 'EXT_DATA2: scan_in_pin : ChainLength3: 2141       ', 
 'EXT_ADR2 : scan_out_pin: ChainLength3: 2141       ', 
 'EXT_DATA3: scan_in_pin : ChainLength4: 2141       ', 
 'EXT_ADR3 : scan_out_pin: ChainLength4: 2141       ', 
 'EXT_DATA4: scan_in_pin : ChainLength5: 2141       ', 
 'EXT_ADR4 : scan_out_pin: ChainLength5: 2141       ', 
 'EXT_DATA5: scan_in_pin : ChainLength6: 2141       ', 
 'EXT_ADR5 : scan_out_pin: ChainLength6: 2141       ', 
 'EXT_DATA6: scan_in_pin : ChainLength7: 2141       ', 
 'EXT_ADR6 : scan_out_pin: ChainLength7: 2141       ', 
 'EXT_DATA7: scan_in_pin : ChainLength8: 2141       ', 
 'EXT_ADR7 : scan_out_pin: ChainLength8: 2141       ']
 """
    if joint == '': joint = delimeter+' ' 
    #delimeterRange = range(len(a_list[0].split(delimeter)))
    c_list =[]
    # determine number of columns, pad the lines with fewer columns
    b_list, col_list = [ my_split(a_line, delimeter) for a_line in a_list ], [ len(my_split(a_line, delimeter)) for a_line in a_list ]
    aRange, num_cols = range(len(a_list)), max(col_list)
    cRange = range(num_cols)
    pad_size = [ 0 for i in cRange ]
    for i in aRange:
        if col_list[i] < (num_cols):
           a_list[i]+= joint*(num_cols-1-col_list[i])
           b_list[i] += [ '' for j in xrange(col_list[i], num_cols) ]
        # get max length for each column
        for j in cRange:
            if len(b_list[i][j])> pad_size[j]: pad_size[j] = len(b_list[i][j])
    for i in aRange:
        for j in cRange:
            if do_left_just: b_list[i][j] = b_list[i][j].strip().ljust(pad_size[j])
            else: b_list[i][j] = b_list[i][j].strip().rjust(pad_size[j])
        c_list.append(joint.join(b_list[i]))
    if do_rstrip: c_list = [ strip_tw(a_row) for a_row in c_list ]
    return c_list


def mk_vertical(a_list, seperator=''):
    """mk_vertical(a_list[, seperator=''])
pass in a_list of strings, seperator is optional, defaults to '', and return a
formatted list which is transposed by 90 degrees of the list passed in, hence 'vertical', for 
example, a_list = ['CLKIN27', 'CLKINEXT', 'CLKINEXTSEL', 'MULCTRL1', 'MULCTRL0', 'CLKIN25', 
    'CLKIN25SEL', 'CLKSEL', 'DDR_32', 'VCXO_CTRL', 'RESETN', 'TRSTN', 'TCK', 'RTCK', 'TDI', 
    'TMS', 'TDO', 'TEST3', 'TEST2', 'TEST1', 'TEST0', 'DCLK', 'BYTE_START', 'PACCLK', 'DERROR',
    'DATAIN7', 'DATAIN6', 'DATAIN5', 'DATAIN4', 'DATAIN3', 'DATAIN2', 'DATAIN1', 'DATAIN0', 
    'EXT_CS0', 'EXT_CS1', 'EXT_CS2', 'EXT_CS3', 'EXT_CS4', 'EXT_CS5', 'EXT_OE', 'EXT_WE0', 
    'EXT_WE1', 'EXT_WAIT', 'EXT_DATA15', 'EXT_DATA14']
passed in would return a list:
['  C                                          ',
 '  L   C               B                    EE', 
 '  K   L  V            Y                    XX', 
 ' CIMM K  C            T                   ETT', 
 'CLNUUCI  X            E  DDDDDDDDEEEEEE EEX__', 
 'LKELLLNCDOR           _PDAAAAAAAAXXXXXXEXXTDD', 
 'KIXCCK2LD_ET     TTTT SAETTTTTTTTTTTTTTXTT_AA', 
 'INTTTI5KRCSR R   EEEEDTCRAAAAAAAA______T__WTT', 
 'NESRRNSS_TESTTTTTSSSSCACRIIIIIIIICCCCCC_WWAAA', 
 '2XELL2EE3RTTCCDMDTTTTLRLONNNNNNNNSSSSSSOEEI11', 
 '7TL105LL2LNNKKISO3210KTKR76543210012345E01T54']
"""
    max_length = 0
    for item in a_list:
        if len(item) > max_length: max_length= len(item)
    rows = range(max_length)
    b_list = [item.rjust(max_length) for item in a_list]
    v_list=[]
    for x in rows:
        line = ''
        for item in b_list:
            line += item[x]+seperator
        v_list.append(line)
    return v_list


def force_column_width(a_list, num_per_row, delimeter=',', prefix=''):
    """limit the number of elements in a list to a set number per row, i.e.
    from a pinlist, just print up to 12 pins per row"""
    b_list = []
    if len(a_list)>=num_per_row:
        for i in xrange(len(a_list)/num_per_row):
            b_list.append('%s%s'%(prefix, delimeter.join(a_list[i*num_per_row:(i+1)*num_per_row])))
            if i*num_per_row<len(a_list): b_list[-1] += delimeter
    else:
        i=-1
    if (len(a_list)%num_per_row) !=0: # pick up the last row, or only one row...
        b_list.append('%s%s'%(prefix, delimeter.join(a_list[(i+1)*num_per_row:])))
    return b_list


def m_search_rcrsv(a_list, grep_regex, i=0, step=1, index_list=None, debug=False, pm_info=None):
    """find all indices in list that match search on grep_regex, not as fast as keep_in_list_coordinates,
    more of an exercise to write a recursive function.  This one is a recursive (__search_rcrsv__) within a recursive"""
    if index_list is None: index_list = [] 
    index_list.append(search_rcrsv(a_list, grep_regex, i, step, debug=debug, pm_info=pm_info))
    if index_list[-1]>-1: 
        return m_search_rcrsv(a_list, grep_regex, index_list[-1]+1, step, index_list, debug, pm_info)
    else: return index_list[:-1]


def search_rcrsv(a_list, grep_regex, i=0, step=1, debug=False, list_copy=None, pm_info=None):
    """Breaks a_list into subsections if len(a_list)>sys.getrecursionlimit()/2, otherwise, likely 
    get an internal loop error because depth level of recursion gets exceeded"""
    mk_slice = lambda block_count, block_size, list_size:slice(block_count*block_size,\
        (block_count+1)*block_size if (block_count+1)*block_size<=list_size else list_size)
    max_block_size, list_size = sys.getrecursionlimit()/2, len(a_list)
    within_slice = lambda a1, a_slice: a1>=a_slice.start and a1<=a_slice.stop
    if len(a_list)>max_block_size:
        num_blocks = int(list_size/max_block_size)
        for blkcnt, a_slice in [(blk_num, mk_slice(blk_num, max_block_size, list_size)) for blk_num in xrange(num_blocks+1)]:
            if i>a_slice.stop: continue
            i_start = i if within_slice(i, a_slice) else 0
            index = __search_rcrsv__(a_list[a_slice], grep_regex, i_start%max_block_size, step, debug)
            if isinstance(pm_info, list):
                pm_info.append('blkcnt: %d, a_slice: %s, index: %d'%(blkcnt, a_slice, index))
            if index>-1:
                index += blkcnt*max_block_size
                break
        return index
    else:
        return __search_rcrsv__(a_list, grep_regex, i, step, debug=debug)


def __search_rcrsv__(a_list, grep_regex, i=0, step=1, debug=False, list_copy=None, last_index=None):
    """recursive search, in increments of step, i.e. 1 search forward by 1, find match
    for grep_regex in a_list"""
    if debug: print 'entry, i: %d'%i
    if list_copy is None: list_copy = string_cast(a_list)
    if last_index is None: last_index = len(a_list)-1
    if not (i>-1 and i<last_index):
        if debug: print 'conditional never true in list, i: %d'%i
        return -1
    elif in_string(list_copy[i], grep_regex):
        if debug: print 'found it: %d'%i
        return i 
    else:
        if debug: print 'conditional not true, i: %d'%i
        return __search_rcrsv__(a_list, grep_regex, i+step, step, debug, list_copy, last_index)


def example_chk_recursive(i, x, J=None):
    if J == None: J = []
    J.append(i)
    if i>x:
        print 'i: %d, x: %d'%(i, x)
        example_chk_recursive(i-1, x, J)
    else:
        print 'condition met: i <= x'
    return 'local i: %d, last recursion i: %d'%(i, J[-1])


def find_index(aList, search_param):
    """usage: index = find_index(aList, search_param) 
    where: aList is a list and search_param is a string expression
           index is the first occurrence of the search_param found in the list
           starting from left to right"""
    ListCopy, SearchParam = string_cast(aList), re.compile(string_cast(search_param))
    if type(ListCopy) == type('a_string'): ListCopy = [ListCopy]
    for a_value in ListCopy:
        m = SearchParam.search(a_value)
        if m != None:
            return(ListCopy.index(a_value))
    return(-1)


def find_block(m_groups, start_clause, stop_clause, index_offset=0):
    found = False
    chk_list = [ 1 if cmp(a_cell, start_clause)==0 else -1 for a_cell in m_groups ]
    chk_sum = [chk_list[0]]
    for a_num in chk_list[1:]: chk_sum.append(a_num+chk_sum[-1])
    start_index, stop_index = find_index(chk_sum,'^1\\b'), find_index(chk_sum,'^0\\b')
    start_index = (start_index+index_offset) if start_index>-1 else -1
    stop_index = (stop_index+index_offset) if stop_index>-1 else -1
    return start_index, stop_index


def find_blocks(m_groups, start_clause, stop_clause, offset=0):
    # start_stop_iter = find_blocks_iter(m_groups, start_clause, stop_clause, offset)
    # return(list(start_stop_iter))
    start_pts, stop_pts = [], []
    [(start_pts.append(start_pt), stop_pts.append(stop_pt))for start_pt, stop_pt in find_blocks_iter(m_groups, start_clause, stop_clause, offset)]
    return (start_pts, stop_pts)


def find_blocks_iter(m_groups, start_clause, stop_clause, offset=0):
    current_offset = offset
    start, stop = -1,-1
    while current_offset < len(m_groups):
        start, stop = find_block(m_groups[current_offset:], start_clause, stop_clause, current_offset)
        if start>-1 and stop>-1: current_offset = stop+1
        else: current_offset = len(m_groups)
        yield (start, stop)


def my_reverse_in_place(inp):
    a_list = [a_member for a_member in inp]
    a_list.reverse()
    return(a_list)


def my_sort_in_place(inp, do_reverse=1):
    a_list = [a_member for a_member in inp]
    my_sort(a_list, do_reverse)
    return(a_list)


def sort_numbers(inp, direction=1):
    """usage: sort_numbers(aList[, direction]) sort list from min to max, unless direction=-1, then reversed"""
    if False:
        length = len(inp)-1
        i = 0
        j = 1
        while i < length:
            for currValue in inp[i+1:]:
                if inp[i]>currValue:
                   my_swap(inp, i, j)
                j+=1
            i=i+1
            j=i+1
        if direction == -1: inp.reverse()
    else: inp.sort(reverse=False if direction==1 else True)


def my_sort_numbers_in_place(inp, direction=1):
    # -- a_list = [a_member for a_member in inp]
    # -- sort_numbers(a_list, direction)
    return(sorted(inp, reverse=False if direction==1 else True))


def my_sort(inp, direction=1):
    """usage: my_sort(aList[, direction]) sort list from min to max, unless direction=-1"""
    length = len(inp)-1
    i = 0
    j = 1
    
    if False:
        while i < length:
            for currValue in inp[i+1:]:
                if cmp(inp[i], currValue)==1:
                   my_swap(inp, i, j)
                j+=1
                
            i=i+1
            j=i+1
    else: inp.sort()
    if direction == -1:
        inp.reverse()


def my_swap(myList, index_1, index_2):
    myList[index_2], myList[index_1] = myList[index_1], myList[index_2]


def calc_average(myList):
    totalSum=0
    count = len(myList)
    for sum in myList:
        totalSum += sum
    return ( totalSum/len(myList) )


def calc_stdev(aList):
    avgX = sum(aList)/len(aList)
    sumSq = sum( pow((x - avgX), 2) for x in aList )
    stdev = sqrt( sumSq / (len(aList) - 1) )
    return stdev

def unique_sub_list(a_list):
    return(list(iter_unique_members(a_list)))


def sort_unique(a_list):
    return(my_sort_in_place(unique_sub_list(a_list)))


def iter_sort_unique(a_iter):
    return(sorted(iter_unique_members(a_iter)))


def iter_unique_members(a_iter):
    members = []
    for a_element in a_iter:
        if not a_element in members: 
            members.append(a_element)
            yield a_element


def split_list(a_list, delimeter='\s', field=0):
    """usage: split_list(aList[, delimeter, field]) where: delimeter defaults to '\s' and field = 0"""
    out = []
    for a_value in a_list:
        out.append(a_value.split(delimeter)[field])
    return(out)


def grep_list(a_list, search_param):
    """Only grep on string types, will handle a list of multitype, but
    only operate on indices of string type"""
    out=[]
    str_type = type("a_str")
    if type(a_list) == str_type: a_list = [a_list]
    for a_value in a_list:
        if type(a_value) == str_type:
            m = re.search(search_param, a_value)
            if m != None: out.append(a_value)
    return(out)


def in_string(a_str, search_param):
    if not isinstance(a_str, str): a_str = string_cast(a_str)
    if not isinstance(search_param, str): search_param = string_cast(search_param)
    #a_iter = re.finditer(re.compile(search_param), a_str)
    #return len([m for m in a_iter if m])>0
    return True if re.search(re.compile(search_param), a_str) else False


def in_list(a_list, search_param):
    """usage: in_list(aList, regexp) "is regexp in list" is more flexible than "is obj in list\""""
    #g = m_re(a_list)
    #g.grep(search_param)
    #return(g.pattern_count>0)
    if not isinstance(search_param, str): search_param = string_cast(search_param)
    if isinstance(a_list, str): return in_string(a_list, search_param)
    else: a_iter = ( '%s'%a_line for a_line in a_list )
    return (in_iter(a_iter,'%s'%search_param).next())


def in_iter(a_iter, search_param):
    search_pattern = re.compile(search_param)
    found_pattern = False
    for a_line in a_iter:
        if search_pattern.search(a_line):
            found_pattern = True
            break
    yield found_pattern


def in_list_rcrsv(a_list, search_param, i=None, last_element=None):
    if i is None: i=0
    if last_element is None: last_element = len(a_list)-1
    m = re.search(re.compile(search_param), a_list[i])
    if not m and i<len(a_list):
        return in_list_rcrsv(a_list, search_param, i+1)
    elif m: return True
    else: return False


def _list_copy(srcList, destList, overwrite=0):
    """usage: _list_copy(srcList, destList[, overwrite] where: overwrite defaults to 0, append items from srcList to destList if not 
already in destList"""
    try:
        type(destList)
    except NameError:
        destList = []
    for item in srcList:
        if item not in destList and not overwrite: 
            destList.append(item)
        elif item in destList and overwrite:
            insert_here = destList.index(item)
            Null = destList.pop(insert_here)
            destList.insert(insert_here, item)


def _list_intersect(srcList, destList):
    """usage: _list_intersect(srcList, destList) update destList with the intersection of itself and srcList"""
    diffList = list(set(destList).difference(set(srcList)))
    _list_reduce(diffList, destList)


def _list_add(srcList, destList):
    """usage: _list_add(srcList, destList) append items from srcList that are not in destList"""
    a_dict = dict([(a, i) for i, a in enumerate(srcList)])
    i_dict = dict([(i, a) for a, i in a_dict.iteritems() ])
    a_set = set(srcList)
    for a in destList: a_set.discard(a)
    diffList = [ i_dict[a_] for a_ in sorted(a_dict[a] for a in a_set) ]
    destList += diffList


def _list_reduce(srcList, destList):
    """usage: _list_reduce(srcList, destList) Remove items (all occurences) from destList that are in srcList"""
    a_dict = dict([(a, i) for i, a in enumerate(destList)])
    i_dict = dict([(i, a) for a, i in a_dict.iteritems() ])
    a_set = set(destList).intersection(set(srcList))
    for a_ in reversed(sorted(a_dict[a] for a in a_set)): destList.pop(a_)
    #destList = [ i_dict[a_] for a_ in sorted(a_dict[a] for a in a_set) ]


def _dictionary_copy(srcDict, destDict):
    """usage: _dictionary_copy(srcDict, destDict) add dictionary key:value pairs that aren't present in destDict from srcDict"""
    for aKey in srcDict:
        try:
            destDict.update({aKey:srcDict[aKey].copy()}) # dicts, sets
        except AttributeError:
            try:
                destDict.update({aKey:srcDict[aKey][:]}) # list, tuples, strings, unicode
            except TypeError:
                destDict.update({aKey:srcDict[aKey]}) # ints


def _dictionary_reduce(srcDict, destDict):
    """usage: _dictionary_reduce(srcDict, destDict) reduce key value list from destDict that are in srcDict"""
    list_type = type([1, 2, 34])
    for aKey in srcDict:
        if destDict.has_key(aKey):
            _list_reduce(srcDict[aKey], destDict[aKey])
            if type(destDict[aKey]) == list_type and destDict[aKey] == []: 
                destDict.__delitem__(aKey)


def PrettyPrint(aList, add_cr=1):
    """usage: PrettyPrint(aList[, add_cr=1]) print out list, item by item, to stdout"""
    if type(aList) == type(''): aList = [aList]
    for line in aList:
        if add_cr: print line
        else: print line,
    pass


def list_dimensions(a_list):
    var_type, dim_list= type(a_list), []
    b_list = a_list
    if len(b_list)==0: return []
    while var_type == type([]):
        dim_list.append(len(b_list))
        b_list = b_list[0]
        var_type = type(b_list)
    return(dim_list)


def flatten_list(a_list):
    flat_list = list(chain.from_iterable(a_list)) 
    while len(list_dimensions(flat_list))>1:
        flat_list = list(chain.from_iterable(flat_list))
    return(flat_list)


def recursive_flatten(a, result=None):
    """Flattens a nested list.
        >>> flatten_list([ [1, 2, [3, 4] ], [5, 6], 7])
        [1, 2, 3, 4, 5, 6, 7] """
    if result is None: result = []
    for x in a:
        if isinstance(x, list): recursive_flatten(x, result)
        else: result.append(x)
    return(result)


def get_list_size(a_list):
    return sum( len(a_row) for a_row in a_list)


def ConvertToStrings(a_list):
    return([str(a_line) for a_line in a_list])


def pass_through(a_value, output=None, a_condition=True, print_output=True, stdout_func=None):
    """Useful debug tool for doing something in a generator of some sort, i.e.
    chk_stat = lambda i, total, p, a_file:'Elapsed Time %f: %s: %7.4f%% done...'%(p.get_overall_elapsed_time(start_time), a_file,(float(i)/total)*100)
    chk_cond = lambda a, b : a%b==0
    num_files, num_chk = len(file_listing), 20
    chk_list = util.flatten_list([a_grep.output for a_grep in iter(\
        [ util.pass_through(util.SysCommand('gzip -dc %s | grep -c Default\ Background'%a_file),\
            chk_stat(i, num_files, pm, a_file),\
            chk_cond((i if i<(num_files-1) else 0), num_chk)) 
        for i, a_file in zip(util.InfiniteCounter(start=-1), file_listing) ])])
    The instance for util.SysCommand "passes through", and output of lambda function chk_stat is printed 
    to the console"""
    if a_condition and print_output and output != None: 
        if not stdout_func: print output
        else: stdout_func(output)
    return(a_value)


class BaseTypeOperator:

    def __init__(self, key_order):
        pass

    def VarTypeAndValue(self):
        pass


def GetBaseType(a_string, key_order='Dec Hex Binary Octal Float'.split()):
    """return the type function and value of the string as a number, i.e. 
    GetBaseType('0x14') would return (<function hex>, 20), so if we did:
        f, num = GetBaseType('0x14')
        then f(num) = 20 """
    StringType, NumValue = str, str(a_string)
    base_dict = {'Binary':(bin, lambda a: int(a, 2),'(?:0b)[01]+(?i)'),'Octal':(oct, lambda a: int(a, 8),'(?:0o)?[01234567]+(?i)'), \
        'Dec':(int, lambda a: int(a, 10),'\d+'),'Hex':(hex, lambda a: int(a, 16),'(?:0x)?[a-f\d]+(?i)'), \
        'Float':(float, lambda a: float(a),'[\-\de]+[\.\de\-+]+(?i)')}
    for a_key in key_order: 
        try:
            bob, function, prefix = base_dict[a_key] #subtle, but want to break only when a valid match is found
            if None != prefix: 
                if not in_list(a_string,'\\b%s\\b'%prefix): StringType, NumValue = str, str(a_string)
                else: 
                    StringType, NumValue = bob, function(a_string)
                    break
        except ValueError:
            continue
    return (StringType, NumValue)


def SpecialJoin(a_list, joint=',', num_elements_per_line=20):
    """pass in a list, must be strings, return a list with num_elements_per_line joined for each entry 
    i.e. a_list = [ str(i) for i in xrange(200)] """
    brk_indices = [ i for i in xrange(len(a_list)) if (i % num_elements_per_line)==0 ]
    b_list = [ joint.join(a_list[brk_indices[i]:brk_indices[i+1]]) for i in xrange(len(brk_indices)-1) ] + [joint.join(a_list[brk_indices[-1]:])] 
    b_list = [ '%s%s'%(a_line, joint) for a_line in b_list[:-1] ] + [b_list[-1]]
    return(b_list)


def SplitLines(a_list, new_line_length=None, new_line_terminator=None):
    if new_line_length:
        b_list = []
        new_line_terminator = '\s' if not new_line_terminator else new_line_terminator
        for a_line in a_list:
            line_length, new_line_list = len(a_line), []
            if line_length > new_line_length:
                start, stop = 0, new_line_length
                while line_length > stop or (stop-start)==new_line_length:
                    sub_line = a_line[start:stop]
                    g = m_re(sub_line)
                    g.grep(new_line_terminator)
                    if g.pattern_count>0:
                        indices = [int(a_coord.split('.')[-1])+1 for a_coord in g.coordinates if (int(a_coord.split('.')[-1])+1)<new_line_length]
                        if len(indices)>0 and indices[-1]<(stop-start): 
                            stop, sub_line  = start+indices[-1], sub_line[:indices[-1]]
                    new_line_list+=[sub_line]
                    start = stop
                    stop = (stop + new_line_length) if (stop+new_line_length)<line_length else line_length
            else: start, stop = 0, line_length
            if len(a_line[start:stop])>0: new_line_list.append(a_line[start:stop])
            elif in_list(a_line,'^\s*$'): new_line_list.append(a_line)
            b_list += new_line_list
        return(b_list)
    else: return(a_list)


def string_replace(a_list, a_pattern, replace_with):
    g = m_re(a_list)
    g.sub(a_pattern, replace_with)
    return(g.allLines)


def shift_element(a_list, i, direction=1):
    """move element up or down in a list based on direction, which defaults to 1 for up. down would be -1"""
    new_i = i-direction
    if i == 0: 
        if direction<0: 
            a_list.insert(i-direction, a_list.pop(i))
            new_i = i-direction 
        else: 
            a_list.append(a_list.pop(i))
            new_i = len(a_list)-1
    else: 
        if i == (len(a_list)-1) and direction<0: 
            a_list.insert(0, a_list.pop(i))
            new_i = 0
        else: 
            a_list.insert(i-direction, a_list.pop(i))
            new_i = i-direction
    return(new_i)


def GetTheLocalTime():
    t = localtime()
    return( '%04d%02d%02d:%02d%02d:%02d'%(t.tm_year, t.tm_mon, t.tm_mday, t.tm_hour, t.tm_min, t.tm_sec) )


def add_cr(aList):
    if type(aList) == type('a_string'):
        if aList[-1] != '\n': aList = aList+'\n'
    else:
        aRange = range(len(aList))
        for i in aRange:
            try:
                if aList[i] == '': aList[i]='\n'
                elif aList[i][-1] != '\n': aList[i] += '\n'
            except IndexError: # might be a blank line, ''
                print 'index is: ', i
                print 'aList[i]: ', aList[i]
                raise


def add_cr_iter(a_iter):
    for a_line in a_iter:
        if len(a_line)>0:
            if a_line[-1] != '\n': yield a_line+'\n'
            else: yield a_line
        else: yield '\n'


def dict_to_list(a_dict, keys_list, column_delimeter=':'):
    """convert a dictionary set of keys to a single column delimited list.
    i.e. a_dict = {0:[1, 2, 3, 4], 1:[4, 3, 2, 1], 2:[5, 6, 7, 8]}
    dict_to_list(a_dict, keys_list, column_delimeter)
    where keys_list = [1, 2, 0] and column_delimeter=':'
    would return a_list = ['4:5:1','3:6:2','2:7:3','1:8:4']
    
    Handy for dumping a dictionary of lists into a spreadsheet"""
    a_list = [ a_cell for a_cell in string_cast(a_dict[keys_list[0]]) ]
    if len(keys_list)>0:
        for a_key in keys_list[1:]: a_list = [ '%s%s%s'%(a_cell, column_delimeter, next_cell) for a_cell, next_cell in zip(a_list, string_cast(a_dict[a_key])) ]
    return(a_list)


def sub_iterator(a_iter, a_pattern, sub_pattern):
    search_pattern = re.compile(a_pattern)
    for a_line in a_iter:
        if search_pattern.search(a_line): a_line = search_pattern.sub(sub_pattern, a_line)
        yield a_line, len(a_line)


def iscatter(a_iter, num_iterators=2):
    """Specialized tee from itertools.  Evaluate a function that returns an iterable, them make multiple 
    copies based on the num_iterators parameter, which defaults to 2
    For example:
        g = grep_iterator(a_pattern, do_match=True)
        g_coordinates_iter, g_lines_iter, g_lengths_iter = iscatter(g.grep(\
            mmap_obj.read_lines_iter(length=length, offset=offset)), num_iterators)
    """
    new_iters_list = []
    for start_index, loop_iter in zip(xrange(num_iterators), tee(chain.from_iterable(a_iter), num_iterators)):
        new_iters_list.append(islice(loop_iter, start_index, None, num_iterators))
    return new_iters_list


def count_iter(a_iter):
    i = 0
    for a_line in a_iter:
        i+=1
    yield i


def keep_in_list_coordinates(a_list, a_pattern):
    """grep -l a_pattern: return indices of matching elements in a_list as a new list """
    search_pattern = re.compile(a_pattern)
    full_line_range = xrange(len(a_list))
    new_list =list( (i for i, a_line in zip(full_line_range, a_list) if search_pattern.search(a_line)) )
    return(new_list)


def replace_in_list(a_list, a_pattern, sub_pattern):
    search_pattern = re.compile(a_pattern)
    line_range = xrange(len(a_list))
    a_iter = (search_pattern.sub(sub_pattern, a_line) for a_line in a_list )
    return([ a_iter.next() for i in line_range ])


def keep_in_list(a_list, a_pattern):
    """grep a_pattern: return matching elements in a_list as a new list """
    search_pattern = re.compile(a_pattern)
    new_list = list( (a_line for a_line in a_list if search_pattern.search(a_line)) )
    return(new_list)


def remove_from_list(a_list, a_pattern):
    """grep -v a_pattern: return non-matching elements in a_list as a new list """
    search_pattern = re.compile(a_pattern)
    new_list = list( (a_line for a_line in a_list if not search_pattern.search(a_line)) )
    return(new_list)


def CastToNumber(a_string):
    f, a_value = GetBaseType(a_string)
    return a_value


def id_generator(size=8, a_string=string.ascii_uppercase + string.digits, invalid_first_chars=''):
    scrambled_string = ''.join(random.choice(a_string) for x in xrange(size)).lower()
    if scrambled_string[0] in invalid_first_chars:
        scrambled_string = random.choice(string.ascii_lowercase)+scrambled_string[1:]
    chars_indices = list(sorted(random.sample(xrange(len(scrambled_string)), len(scrambled_string)-1)))
    return ( ''.join([a_char.upper() if i in chars_indices else a_char.lower() for i, a_char in enumerate(scrambled_string)]) )


class m_grep(object):
    """usage: 
        g = m_grep(<str|array of strings>)
        g.grep(<regexp>)
    intent is to grep a regexp pattern from a text_window dump, list of strings, or single string and
    return:
        m_groups: list of matches
        coordinates: location of each match in array/string passed in and referenced in m_groups
        lines: the whole line for each match found
        m: last list of matches found for last query
        pattern_count: number of matches for last query
    some helpful flags (do help(re) for more info)
        (?i) ignore case, i.e. 'pattern(?i)' would return Pattern, pattern, PATTERN, etc.
    Note: back-slashes need to be doubled for compiled expresion, i.e \b -> \\b """

    def __init__(self, a_list):
        self.a_list = a_list
        self.allLines = string_cast(a_list)
        if type(self.allLines) == type(""): self.allLines =[self.allLines]
        self.aRange = xrange(len(self.allLines))
        self.clear_cache()

    def grep(self, pattern):
        self.pattern_count=0
        self.coordinates=[]
        self.lines=[]
        self.search_pattern=re.compile(pattern)
        m_iter = self._process_m(self.m_findall(self.search_pattern, self.allLines))
        for m, m_groups, a_line, coordinates, pattern_count in m_iter:
            self.m = m
            self.m_groups += m_groups
            self.lines.append(a_line)
            self.coordinates += coordinates
            self.pattern_count += pattern_count

    def m_findall(self, a_pattern, a_list):
       a_iter = ((row, a_line) for row, a_line in enumerate(a_list, 1))
       for row, a_line in a_iter:
           m = a_pattern.findall(a_line)
           if len(m)>0:
               yield (row, m, a_line)

    def _process_m(self, m_iter):
        for row, m, a_line in m_iter:
            coordinates, pattern_count, found_one = [], 0, False
            m_groups=self.expand_tuple(m)
            coordinates = ['%d.%d'%(row, column) for column, start in self._get_coordinates(a_line, m_groups)]
            pattern_count = len(coordinates)
            yield (m, m_groups, a_line, coordinates, pattern_count)

    def _get_coordinates(self, a_line, m_groups, start_index=0):
        a_string, col_list = a_line, []
        for a_word in m_groups:
            a_col = a_string.find(a_word, start_index)
            start_index = a_col+len(a_word)
            yield a_col, start_index

    def old_grep(self, pattern):
        self.pattern_count=0
        self.coordinates=[]
        self.lines=[]
        self.search_pattern=re.compile(pattern)
        row=0
        for eachLine in self.allLines:
            row += 1
            self.m = re.findall(self.search_pattern, eachLine)
            if self.m != []:
                self.expand_tuple(self.m)
                self.lines.append(eachLine)
                column=0
                for m_str in self.m:
                    self.m_groups.append(m_str)
                    column = eachLine.find(self.m_groups[-1], column) 
                    if column>-1: 
                        self.coordinates.append(str(row)+"."+str(column) )
                    column += 1 
                self.pattern_count += len(self.m)

    def _experimental_expand_tuple(self, a_list):
        list_copy = []
        for i in reversed(xrange(len(a_list))): 
            list_copy += [ a_cell for a_cell in reversed(a_list.pop(i)) if a_cell != '' ]
        for a_member in reversed(list_copy): a_list.append(a_member)
        return(a_list)

    def expand_tuple(self, a_list):
        """Pass in a list which may consist of strings and/or tuples.  Expand out each tuple to list element members. """
        num_elements = len(a_list) # this is variable, depending on how many times a tuple is expanded into more list elements and/or tuples.....
        i = 0
        while i < num_elements:
            if type(a_list[i]) == type(()):
                a_tuple = a_list.pop(i)
                a_tuple_range=reversed(xrange(len(a_tuple)))
                for member in a_tuple_range:
                    if a_tuple[member] != '':
                        a_list.insert(i, a_tuple[member])
                num_elements = len(a_list)
            else: i += 1
        return(a_list)

    def clear_cache(self):
        """clear all grep results for this instance of my_grep"""
        self.m, self.coordinates, self.m_groups, self.lines, self.pattern_count=[], [], [], [], 0


class m_re(m_grep):
    """wrapper class for re, some useful functions like replacing a pattern
       with a replacement, i.e. "_C84" -> "_relay", i.e. a_string = "NSTANDBY_C91+NSTANDBY_C92+A_BYP_C4+PVDD_CAP_C26", so,
       the search_pattern=re.compile('(?P<id>\w+)C\d+') and replacement string would be '\g<id>relay', thus the
       result would be "NSTANDBY_relay+NSTANDBY_relay+A_BYP_relay+PVDD_CAP_relay"
       or change upper case to lower case
    """

    def __init__(self, a_list):
        super(m_re, self).__init__(a_list)

    def sub(self, pattern, replc):
        self.grep(pattern)
        self.search_pattern = re.compile(pattern)
        for i in self.aRange:
            self.m = self.search_pattern.sub(replc, self.allLines[i])
            if self.m != self.allLines[i]:
                self.allLines[i] = self.m
                if type(self.a_list) == type('a_string'): self.a_list = self.m
                elif type(self.a_list[i]) == type('a_string'): self.a_list[i] = self.m

    def lower(self, pattern):
        self.grep(pattern)
        self.search_pattern = re.compile(pattern)
        for i in self.aRange:
            self.m = re.findall(self.search_pattern, self.allLines[i])
            if self.m != []:
               for a_word in self.m:
                   self.allLines[i] = re.sub(a_word, a_word.lower(), self.allLines[i])
                   if type(self.a_list[i]) == type('string'): self.a_list[i] = self.allLines[i]

    def upper(self, pattern):
        self.grep(pattern)
        self.search_pattern = re.compile(pattern)
        for i in self.aRange:
            self.m = re.findall(self.search_pattern, self.allLines[i])
            if self.m != []:
                for a_word in self.m:
                   self.allLines[i] = re.sub(a_word, a_word.upper(), self.allLines[i])
                   if type(self.a_list[i]) == type('string'): self.a_list[i] = self.allLines[i]


class Strip_C_Comments:
    """Strip out:
    All C like comments, to counter cases such as an object defined within comments 
    All #if 0 blocks, to counter cases of redundancy and unused code"""

    def __init__(self, all_lines):
        self.all_lines = all_lines
        self.grep_comments = m_grep(self.all_lines)
        self.grep_comments.grep('(//|/\*|\*/)')
        self.change_list=[] #{}
        if self.grep_comments.pattern_count > 0: self.strip_comments(self.grep_comments, self.change_list, self.all_lines)
        if in_list(self.all_lines,'//'): self.all_lines = self.strip_cpp(self.all_lines)
        self.grep_if_0 = m_grep(self.all_lines)
        self.grep_if_0.grep('(#if\s*0?\s*)')
        if self.grep_if_0.pattern_count > 0: self.strip_if_0(self.grep_if_0, self.all_lines)

    def strip_comments(self, g, change_list, all_lines):
        """strip out all c-type comment blocks"""
        self.partials=[]
        self.comment_blocks = CaptureBlocks(all_lines,'/\*','\*/')
        self.block_sizes = []
        aRange = range(len(self.comment_blocks.start_pts))
        self.block_sizes = [self.comment_blocks.end_pts[i] - self.comment_blocks.start_pts[i] for i in aRange]
        aRange = range(len(self.block_sizes))
        for i in aRange:
            if self.block_sizes[i] > 1: self.change_list.append((self.comment_blocks.start_pts[i], self.comment_blocks.end_pts[i]) )
            else: # comment block is on same line, check to see if any of line is "uncommented"
                index = self.comment_blocks.start_pts[i]
                if len(all_lines[index].strip('\n')) - (all_lines[index].find('/*')+all_lines[index].find('*/') + 2) == 0: #whole line is comment
                    self.change_list.append((self.comment_blocks.start_pts[i], self.comment_blocks.end_pts[i]) )
                else: # part of line uncommented
                    aList = all_lines[index].split('/')
                    bRange = range(len(aList))
                    bRange.reverse()
                    for k in bRange:
                        m = re.search('\*.*\*', aList[k])
                        if m != None: 
                            aList.pop(k)
                        all_lines[index] = ' '.join(aList)
                    self.partials.append((index, all_lines[index], ' '.join(aList)))
        aRange = range(len(change_list))
        aRange.reverse()
        for i in aRange:
            all_lines.__delslice__(change_list[i][0], change_list[i][1])

    def strip_cpp(self, all_lines):
        """strip out c++ style comments"""
        return [ a[0] for a in sub_iterator(all_lines,'//.*','') ]

    def deprecated_strip_cpp(self, g, all_lines):
        indices = [ int(float(coordinate))-1 for coordinate in g.coordinates ]
        for index in indices:
            all_lines[index] = all_lines[index][:all_lines[index].find('//')]

    def strip_if_0(self, g, all_lines):
        """strip out #if 0 blocks"""
        self.start_pts, self.end_pts = [], []
        g.clear_cache()
        g.grep('(#if\s*0?\s*|#endif)')
        gs = m_grep(g.m_groups)
        gs.grep('\s*#if\s*(0)')
        aRange = range(gs.pattern_count)
        for i in aRange:
            self.start_pts.append( int(float(g.coordinates[int(float(gs.coordinates[i]))-1]))-1 )
        i = 0
        while i < g.pattern_count:
            if g.m_groups[i].find('#if') > -1 and g.m_groups[i].find('0') > -1: 
                closed = g.m_groups[i].count('#if')
                while closed != 0:
                    i += 1
                    closed += g.m_groups[i].count('#if') - g.m_groups[i].count('#endif')
                self.end_pts.append(int(float(g.coordinates[i])) )
            i += 1
        self.start_pts.reverse()
        self.end_pts.reverse()
        aRange = range(len(self.start_pts))
        for i in aRange:
            all_lines.__delslice__(self.start_pts[i], self.end_pts[i])


class CaptureBlocks(object):
    """usage: c = CaptureBlocks(all_lines, block_start_string, block_stop_string, start_phrase)
Use escape character \ for special characters, like *, (, and ), when doing this,
set start_phrase to appropriate value, such as ( or if blocking out preproccessor statements, like
#if 0, then 0, or in the case of a field entry, like vector (...., then set start_phrase to vector.
start_phrase should be a substring of block_start"""

    def __init__(self, all_lines, block_start='{', block_stop = '}', start_phrase=''):
        self.all_lines = all_lines
        self.start_pts, self.end_pts = [], []
        if start_phrase == '': start_phrase = block_start.replace('\\','')
        self.block_start, self.block_stop, self.start_phrase = block_start, block_stop, start_phrase
        self.g = m_grep(self.all_lines)
        if block_start == '/\*':
            self.comment_block(self.all_lines, self.block_start, self.block_stop)
        else:
            self.capture_block(self.all_lines, self.block_start, self.block_stop, start_phrase)

    def comment_block(self, all_lines, block_start='/\*', block_stop='\*/', start_phrase='/*'):
        self.g.clear_cache()
        self.start_pts, self.end_pts = [], []
        self.g.grep('('+block_start+'|//|'+block_stop+')')
        index, indices = find_index(self.g.m_groups,'//'), []
        while index > -1:
            indices.append(index)
            current_index = find_index(self.g.m_groups[index+1:],'//')
            if current_index > -1: index = current_index + index + 1
            else: index = -1
        if len(indices) > 0:
            indices.reverse()
            Null = [ (self.g.m_groups.pop(index), self.g.coordinates.pop(index)) for index in indices ]
            self.g.pattern_count -= len(indices)
        count = self.g.pattern_count 
        i=0
        while i<count-1:
            if self.g.m_groups[i] == self.g.m_groups[i+1]:
                self.g.m_groups.pop(i+1)
                self.g.coordinates.pop(i+1)
                count -= 1
            i += 1
        self.g.pattern_count = count
        i = 0
        while i < self.g.pattern_count:
            if self.g.m_groups[i].find(start_phrase) > -1: 
                closed = self.g.m_groups[i].count(start_phrase)
                self.start_pts.append(int(float(self.g.coordinates[i]))-1 )
                while closed != 0:
                    i += 1
                    try:
                        closed += self.g.m_groups[i].count(start_phrase) - self.g.m_groups[i].count(block_stop.replace('\\',''))
                    except IndexError:
                        print "g.pattern_count: ", self.g.pattern_count," i: ", i," closed: ", closed," start_phrase: ", start_phrase
                        print "last start_pt: ", self.start_pts[-2]," and stop_pt: ", self.end_pts[-1]
                        print "current start_pt: ", self.start_pts[-1]
                        if (i-1) in range(len(g.coordinates)) and (i-1) in range(len(g.m_groups)):
                            print g.coordinates[i-1],': ', g.m_groups[i-1]
                        # index -1, skips escape character, \, needed for grep function
                        closed = 0
                        i = self.g.pattern_count
                self.end_pts.append(int(float(self.g.coordinates[i])) )
            i += 1

    def specific_block(self, block_start, block_stop, start_phrase):
        self.g.clear_cache()
        self.g.grep(block_start)
        self.end_pts, self.start_pts = [], [ int(float(i))-1 for i in self.g.coordinates ]
        for start_pt in self.start_pts:
            closed, i = self.all_lines[start_pt].count(start_phrase), start_pt
            while closed != 0:
                i += 1
                try:
                    closed += self.all_lines[i].count(start_phrase) - self.all_lines[i].count(block_stop)
                except IndexError:
                    print "Exceeded last line of file"
            self.end_pts.append(i+1)

    def capture_block(self, all_lines, block_start='{', block_stop='}', start_phrase='{'):
        self.g.clear_cache()
        self.start_pts, self.end_pts = [], []
        if in_list(all_lines, block_start) and in_list(all_lines, block_stop):
            self.g.grep('(%s|%s|%s)'%(block_start, block_stop, start_phrase))
            search_start_pattern = re.compile(block_start)
            search_stop_pattern = re.compile(block_stop)
            start_stop_iter = self._process_engine(all_lines, self.g, search_start_pattern, search_stop_pattern, start_phrase)
            for start, stop in start_stop_iter:
                self.start_pts.append(start)
                self.end_pts.append(stop)
        else:
            pass

    def _process_engine(self, all_lines, g, search_start_pattern, search_stop_pattern, start_phrase):
        """yield: start_pt and end_pt, """
        i=0
        while i < self.g.pattern_count:
            start_pt, end_pt = None, None
            m = search_start_pattern.search(g.m_groups[i])
            if m != None: 
                closed = g.m_groups[i].count(m.group())
                start_pt = int(float(g.coordinates[i]))-1 
                while closed != 0:
                    i += 1  # what happens if block_start and block_stop are on the same line?
                    try:
                        m_stop = re.search(search_stop_pattern, self.g.m_groups[i])
                        #closed += self.g.m_groups[i].count(start_phrase) - self.g.m_groups[i].count(block_stop.replace('\\',''))
                        closed += g.m_groups[i].count(start_phrase)
                        if m_stop != None: closed -= g.m_groups[i].count(m_stop.group())
                    except IndexError:
                        print "g.pattern_count: ", g.pattern_count," i: ", i," closed: ", closed," start_phrase: ", start_phrase
                        print "current start_pt: ", start_pt
                        if (i-1) in range(len(g.coordinates)) and (i-1) in range(len(g.m_groups)):
                            print g.coordinates[i-1],': ', g.m_groups[i-1]
                        # index -1, skips escape character, \, needed for grep function
                        closed = 0
                        i = self.g.pattern_count
                end_pt = int(float(g.coordinates[i] if i in xrange(len(g.coordinates)) else -1)) 
                yield (start_pt, end_pt)
            i += 1

    def old_capture_block(self, all_lines, block_start='{', block_stop='}', start_phrase='{'):
        self.g.clear_cache()
        self.start_pts, self.end_pts = [], []
        self.g.grep('('+block_start+'|'+block_stop+'|'+start_phrase+')')
        search_start_pattern = re.compile(block_start)
        search_stop_pattern = re.compile(block_stop)
        i = 0
        while i < self.g.pattern_count:
            m = re.search(search_start_pattern, self.g.m_groups[i])
            if m != None: 
                closed = self.g.m_groups[i].count(m.group())
                self.start_pts.append(int(float(self.g.coordinates[i]))-1 )
                while closed != 0:
                    i += 1  # what happens if block_start and block_stop are on the same line?
                    try:
                        m_stop = re.search(search_stop_pattern, self.g.m_groups[i])
                        #closed += self.g.m_groups[i].count(start_phrase) - self.g.m_groups[i].count(block_stop.replace('\\',''))
                        closed += self.g.m_groups[i].count(start_phrase)
                        if m_stop != None: closed -= self.g.m_groups[i].count(m_stop.group())
                    except IndexError:
                        print "g.pattern_count: ", self.g.pattern_count," i: ", i," closed: ", closed," start_phrase: ", start_phrase
                        print "last start_pt: ", self.start_pts[-2]," and stop_pt: ", self.end_pts[-1]
                        print "current start_pt: ", self.start_pts[-1]
                        print self.g.coordinates[i-1],': ', self.g.m_groups[i-1]
                        raise
                        # index -1, skips escape character, \, needed for grep function
                self.end_pts.append(int(float(self.g.coordinates[i])) )
            i += 1


class Join_M_Lines:
    """Join statements of multiple lines into 1 line.  i.e. a vector terminates with a ;, but the microcodes, label, and tset arguements
could be on 1 line and the channel data could be on the next line."""

    def __init__(self, all_lines, termination_char=';', joint=' '):
        self.all_lines=[ a_row for a_row in all_lines]
        self.termination = termination_char
        self.joint = joint
        self.g = m_grep(self.all_lines)
        self.g.grep(self.termination)
        self.join_lines(self.all_lines, self.g)


    def join_lines(self, all_lines, g, joint=None):
        if not joint: joint = self.joint
        aRange = xrange(g.pattern_count)
        bList, start_line = [], 0
        for i in aRange:
            end_line = int(float(g.coordinates[i]))
            bList.append(joint.join(all_lines[start_line:end_line]))
            start_line = end_line
        all_lines.__delslice__(0, len(all_lines))
        for line in bList:
            all_lines.append(line)


class FileStats(object):
    """Determine if namespace passed in is a file or directory.
    TimeStamp(): return time stamp of namespace creation
    self.dir: directory path of namespace
    self.file: leaf name with directory path removed"""
    
    month_lookup_table = {'Jan':1, 'Feb':2, 'Mar':3, 'Apr':4, 'May':5, 'Jun':6,
     'Jul':7, 'Aug':8, 'Sep':9, 'Oct':10, 'Nov':11, 'Dec':12}

    def __init__(self, namespace=None, ref_path=''):
        self.namespace, self.ref_path = namespace, ref_path 
        self.get_file_info()

    def get_file_info(self):
        if self.namespace != None:
            self.nm = self.namespace
        else:
            self.nm = ''
        self.nm_stats = commands.getoutput('ls -ld --time-style=long-iso '+self.nm).split()
        self.file = os.path.basename(self.nm)
        self.dir = os.path.dirname(self.nm)
        if self.dir == '': self.dir = '.' #same directory as python shell instance
        self.file_exists = os.path.exists(self.nm)
        if len(self.ref_path)>0 and self.is_path_relative():
           self.make_absolute_path(self.ref_path) 

    def make_absolute_path(self, ref_path):
        self.dir = os.path.join(ref_path, self.dir)
        self.dir = os.path.normpath(self.dir)

    def is_path_relative(self):
        if os.path.isabs(self.dir):
            self.path_is_relative=False
        else:
            self.path_is_relative=True

    def _Month2Number(self, month_key):
        return(self.month_lookup_table[month_key])

    def TimeStamp(self):
        if not self.file_exists:
            return(-99990101.120090001)
        year, month, day = self.nm_stats[5].split('-')
        year, month, day = int(year), int(month), int(day)
        creation_time = int(self.nm_stats[6].replace(':',''))
        if 100*month+day > 100*self._Month2Number(commands.getoutput('date +"%b"'))+int(commands.getoutput('date +"%d"')):
                year = year-1
        timestamp = float(10000.*year+100.*month+1.*day+creation_time/10000.)
        return(timestamp)


class FileUtils(FileStats):
    """a_file = FileUtils(file_name)
    File operations such as is_file, is_path_relative, make_absolute_path, append_to_file
    File info such as timestamps, dir path and filename"""

    def __init__(self, file_name, do_read=False):
        super(FileUtils, self).__init__(file_name)
        self._open_file_function, self.contents = open, []
        if do_read: self.read_from_file()
        else: self.eval_file_size()

    def eval_file_size(self):
        #if commands.getoutput('file '+file_name).find('gzip') == -1 or self.file.find('gz') == -1:
        self.file_size = None
        s = SysCommand('file %s'%self.nm)
        self.file_is_gzipped = in_list(s.output,'gzip compressed data') or in_list(self.nm,'gzi?p?$')
        if not self.file_is_gzipped:
            if self.is_file():
                stat = os.stat(self.nm)
                self.file_size = int(stat.st_size)
            self._open_file_function = open
        else:
            if self.is_file():
                s = SysCommand('gzip -l %s'%self.nm)
                self.gzip_file_info = dict([(a_key, a_value) for a_key, a_value in zip(s.output[0].split(), s.output[-1].split())])
                self.file_size = int(self.gzip_file_info['uncompressed'])
            self._open_file_function = gzip.open

    def make_absolute_path(self, ref_path='./'):
        self.dir = os.path.abspath(ref_path)
        return(self.dir)

    def is_path_relative(self):
        if os.path.isabs(self.dir):
            self.path_is_relative=False
        else:
            self.path_is_relative=True
        return(self.path_is_relative)

    def is_file(self):
        self.file_exists = os.path.isfile(self.dir+os.sep+self.file)
        return self.file_exists

    def _open_file(self, file_name, file_mode):
        self.eval_file_size()
        if ( self.file_is_gzipped and  (file_mode == 'r' or file_mode == 'w' or file_mode == 'a') ): file_mode = '%sb'%file_mode
        return(self._open_file_function(file_name, mode=file_mode))

    def append_to_file(self, aList):
        self.write_to_file(aList,'ab' if self.file_is_gzipped else 'a')

    def write_to_file(self, aList, file_mode='w', offset=-1):
        file_mode_arg = '%sb'%file_mode[0] if self.file_is_gzipped else '%s'%file_mode[0]
        try:
            self.fh = self._open_file(self.nm, file_mode) #open(self.nm, mode=file_mode)
            if offset>-1: self.fh.seek(offset)
            self.fh.writelines(self.add_cr_iter(string_cast_iter(aList))) #each member in aList must have <CR> on the end
            self.fh.close()
            return(0)
        except IOError:
            print 'Ooops, this file: %s\n doesn\'t appear to be writable:\n%s '%(self.nm, sys.exc_info() [1])
            return(-1)

    def read_from_file(self, is_binary=False, offset=-1):
        try:
            mode = 'rb' if is_binary else 'r'
            self.fh = self._open_file(self.nm, mode) #open(self.nm, mode='r')
            if offset>-1: self.fh.seek(offset)
            self.contents = self.fh.readlines()
            self.fh.close()
            return(0)
        except IOError:
            print 'Ooops, this file: %s\n doesn\'t appear to exist:\n%s '%(self.nm, sys.exc_info() [1])
            return(-1)

    def add_cr(self, aList):
        if type(aList) == type('a_string'):
            if aList[-1] != '\n': aList = aList+'\n'
        else:
            aRange = xrange(len(aList))
            a_iter = iter(aList)
            try:
                b_iter = ( '%s%s'%(a_line,'' if a_line.find('\n')>-1 else '\n') for a_line in a_iter)
                #b_iter = ( '%s\n'%a_line if len(a_line)>0 else '' for a_line in a_iter)
                for i in aRange: aList[i] = b_iter.next()
            except IndexError: # might be a blank line, ''
                print 'index is: ', i
                print 'aList[i]: ', aList[i]
                raise
            except StopIteration: # iteration may not have been generated
                print 'File: %s:\n+++ Index: %d\n+++ NumLines: %s'%(self.nm, i, len(aRange))
                print '++++++ Contents: %d'%(aList[i])
                raise

    def add_cr_iter(self, a_iter):
        for a_line in a_iter:
            if len(a_line)>0:
                if a_line[-1] != '\n': yield a_line+'\n'
                else: yield a_line
            else: yield '\n'


class m_sort:
    """m_sort: init with a list of strings where fields are seperated by some delimeter.
use sort_by to sort by one or more fields, specify fields in array, delim defaults to space and joint defaults to ":"
look at sorted for results
usage:
   u = m_sort(a_list)
   u.sort_by(fields=[0], delim=' ', joint=':', do_reverse=[False], a_list=None)
u.sortList is the sorted list"""

    def __init__(self, a_list):
        self.List = a_list

    def sort_by(self, fields=[0], delim='\s+', joint=':', do_reverse=[False], a_list=None, IncludeEmpties = True):
        if not a_list: a_list = self.List
        self.sortList = [ my_split(aRow, delim, IncludeEmpties)  for aRow in a_list ]
        self.unSorted = copy.deepcopy(self.sortList)
        self.sortList = [ [aMember.strip() for aMember in aRow] for aRow in self.sortList ]
        self.sortList = [ [ self.CastToNumber(aMember) if i in fields else aMember for i, aMember in enumerate(aRow) ] for aRow in self.sortList ]
        self.fields, self.do_reverse = fields, do_reverse
        if type(self.do_reverse) != type([False]): self.do_reverse = [self.do_reverse]
        if len(self.fields) > len(self.do_reverse): 
            num_fields, num_bools = len(self.fields), len(self.do_reverse)
            self.do_reverse += [ False for a_field in self.fields[num_bools:] ]
        self.fields.reverse()
        self.do_reverse.reverse()
        #a_field = self.fields[0]
        #a_reverse = self.do_reverse[0]
        #self.sortList.sort(lambda x, y: cmp(x[a_field], y[a_field]), reverse=a_reverse)
        for a_field, a_reverse in zip(self.fields, self.do_reverse):
            try:
                self.sortList = sorted(self.sortList, key= itemgetter(a_field), reverse=a_reverse)
            except IndexError:
                print 'Field: %d, DoReverse: %s'%(a_field, a_reverse)
                raise
        self.sortList = [ joint.join(aRow) for aRow in [ [string_cast(a_cell) for a_cell in a_row] for a_row in self.sortList] ]

    def CastToNumber(self, a_string):
        f, a_value = GetBaseType(a_string)
        return a_value

    def old_sort_by(self, fields=[0], delim='\s+', joint=':', do_reverse=[False]):
        self.sortList = [ my_split(aRow, delim) for aRow in self.List ]
        self.unSorted = copy.deepcopy(self.sortList)
        self.sortList = [ [aMember.strip() for aMember in aRow] for aRow in self.sortList ]
        self.fields = fields
        if len(self.fields)!= len(do_reverse): self.do_reverse = [ False for a_field in self.fields ]
        else: self.do_reverse = do_reverse
        self.fields.reverse()
        self.do_reverse.reverse()
        a_field = self.fields[0]
        a_reverse = self.do_reverse[0]
        self.sortList.sort(lambda x, y: cmp(x[a_field], y[a_field]), reverse=a_reverse)
        fRange = range(len(self.fields)-1)
        for index in fRange:
            a_field, next_field, a_reverse, next_reverse = self.fields[index], self.fields[index+1], self.do_reverse[index], self.do_reverse[index+1]
            colList = [ aRow[a_field] for aRow in self.sortList ] 
            self.sortDict = dict([(aRow, []) for aRow in sort_unique(colList)])
            aRange = range(len(colList))
            NullThis = [ self.sortDict[colList[i]].append(i) for i in aRange ]
            for aKey in self.sortDict:
                start_index, stop_index = self.sortDict[aKey][0], self.sortDict[aKey][-1]+1
                if stop_index-start_index>1:
                    self.sortList.sort(lambda x, y: cmp(x[next_field], y[next_field]), reverse=next_reverse)
        self.sortList = [ joint.join(aRow) for aRow in self.sortList ]


class Scramble:
    """Pass in a list like: aList = ['Vil', 'Vih', 'Vol', 'Voh', 'Iol', 'Ioh', 'Vref', 'ClampLo', 'ClampHi']
and a sequence like: aSeq = [0, 1, 2, 3, 7, 8, 6, 4, 5]
and scramble the list to get: ['Vil', 'Vih', 'Vol', 'Voh', 'ClampLo', 'ClampHi', 'Vref', 'Iol', 'Ioh']
Handy for things like resorting a list of lists... see m_sort
usage: s = Scramble(aList, aSeq) -> s.scrambled
"""

    def __init__(self, a_list, list_sequence):
        if type(a_list) == type([]):
            self.a_list = a_list
        elif type(a_list) == type(""):
            self.a_list = list(a_list) #[a_list]
        self.list_seq = list_sequence
        self.map_dict = dict([ (i, self.list_seq[i]) for i in range(len(self.list_seq))])
        self.scrambled = self.reSort(self.a_list, self.list_seq, self.map_dict)

    def reSort(self, a_list, list_sequence, map_dict):
        ld = list_dimensions(a_list)
        if len(ld)==1:
            scrambled = do_scramble(a_list, map_dict)
        elif len(ld)==2: #only handles 2 dimensional array for now
            scrambled = [ do_scramble(a_row, map_dict) for a_row in a_list ]
        else:
            # need a recursive function to dive down into an array of greater than 2 dimensions
            for a_row in a_list:
                scrambled = []
        return(scrambled)

    def old_reSort(self):
        aRange = range(len(self.list_seq))
        for i in aRange:
            assert len(self.a_list[i]) >= len(self.list_seq),'index: '+str(i)+': a_list length:'+str(len(self.a_list))+' and list_seq:'+str(len(self.list_seq))+' must be lists of same size'
        self.scrambled = [ [a_line[self.map_dict[i]] for i in aRange] for a_line in self.a_list ]


class DeScramble(object):
    """Scramble and DeScramble are pretty much the same thing, use ManipulateList to avoid confusion.
    Pass in a jumbled list, like: aList = ['Vil', 'Vih', 'Vol', 'Voh', 'ClampLo', 'ClampHi', 'Vref', 'Iol', 'Ioh'], with a
sequence like: aSeq = [0, 1, 2, 3, 7, 8, 6, 4, 5]
that would corrspond to the new list order: ['Vil', 'Vih', 'Vol', 'Voh', 'Iol', 'Ioh', 'Vref', 'ClampLo', 'ClampHi']
usage: d = DeScramble(aList, aSeq) -> d.unscrambled is resorted sequence of aList
"""

    def __init__(self, scrambled_list, list_sequence):
        self.s_list = scrambled_list
        self.list_seq = list_sequence
        self.map_dict = self.descramble(self.s_list, self.list_seq)

    def descramble(self, s_list, list_seq):
        ld = list_dimensions(s_list)
        map_dict = dict([(i, j) for i, j in enumerate(list_seq)])
        if len(ld)==1: self.unscrambled = shuffle(s_list, map_dict, list_seq)
        elif len(ld)==2: self.unscrambled = [ shuffle(a_row, map_dict, list_seq) for a_row in s_list ]
        else: self.unscrambled = []
        return map_dict


class ManipulateList(DeScramble):
    """Set of routines to manipulate a list object, such as changing the list sequence, i.e.
A=[[1, 2, 3, 4], [4, 5, 6, 7], ['Boo'], [8, 9, 10]]
aSeq = [2, 3, 0, 1]
m = ManipulateList(A, aSeq)
The resorted list is m.new_list = [['Boo'], [8, 9, 10], [1, 2, 3, 4], [4, 5, 6, 7]]
"""

    def __init__(self, original_list, new_list_sequence):
        super(ManipulateList, self).__init__(original_list, new_list_sequence)
        self.new_list = self.unscrambled


class FractionalApproximation:
    """Use method of continued fractions to arrive at a ratio of two integers that arrives at a very close approximation.
For example, pi can be represented as 22/7, with an error of -.00126 or 355/113, with an error of -.266e-6.
In short, pass in the value to be approximated and the number of iterations, typically, 3 is a good place to start.
The current error, numerator and denominator, and the approximated value can be accessed in the class."""

    def __init__(self, a_value, iterations=3):
        self.value, self.iterations = a_value, iterations
        self.eval_integers(a_value, iterations)
        self.eval_fraction()
        self.approx_value = self.numerator/float(self.denominator)
        self.error = a_value - self.approx_value

    def display(self):
        PrettyPrint('%d/%d at approx value %f with error %f'%(self.numerator, self.denominator, self.approx_value, self.error))


    def eval_integers(self, a_value, iterations):
        aRange, self.n, self.r = range(iterations), [], [a_value]
        for i in aRange:
            self.n.append(round(self.r[-1]))
            error = self.r[-1] - self.n[-1]
            try:
                self.r.append(1/error)
            except ZeroDivisionError:
                #print "error: %f r: %d n: %d i: %d"%(error, self.r[-1], self.n[-1], i)
                break


    def eval_fraction(self):
        aRange, self.numerator, self.denominator = range(len(self.n)-1), 1, self.n[-1]
        aRange.reverse()
        for i in aRange:
            prev_numerator = self.numerator 
            self.numerator = self.denominator
            self.denominator = self.n[i]*self.denominator + prev_numerator
        self.numerator, self.denominator = int(abs(self.denominator)), int(abs(self.numerator))


class SpecialFormat:
    """specify specific breaks for formatting tables, such as one copied from a
pdf file, i.e.:
ADDRESS R/W REGISTER DESCRIPTION
0x00 R Latched fault register 1, global and channel fault
0x01 R Latched fault register 2, dc offset and overcurrent detect
0x02 R Latched fault register 3, load diagnostics
0x03 R Latched fault register 4, load diagnostics
0x04 R External status register 1, temperature and voltage detect
0x05 R External status register 2, Hi-Z and low-low state
0x06 R External status register 3, mute and play modes
0x07 R External status register 4, load diagnostics
0x08 R/W External control register 1, channel gain select
0x09 R/W External control register 2, dc offset reduction and current-limit select
0x0A R/W External control register 3, switching frequency and clip pin select
0x0B R/W External control register 4, load diagnostic, master mode select
0x0C R/W External control register 5, output state control
0x0D R/W External control register 6, output state control
0x0E R/W External control register 7, dc detect level select
0x0F R/W External control register 8, dc detect level select
turns into,
ADDRESS:R/W:REGISTER DESCRIPTION
0x00:R:Latched fault register 1, global and channel fault
0x01:R:Latched fault register 2, dc offset and overcurrent detect
0x02:R:Latched fault register 3, load diagnostics
0x03:R:Latched fault register 4, load diagnostics
0x04:R:External status register 1, temperature and voltage detect
0x05:R:External status register 2, Hi-Z and low-low state
0x06:R:External status register 3, mute and play modes
0x07:R:External status register 4, load diagnostics
0x08:R/W:External control register 1, channel gain select
0x09:R/W:External control register 2, dc offset reduction and current-limit select
0x0A:R/W:External control register 3, switching frequency and clip pin select
0x0B:R/W:External control register 4, load diagnostic, master mode select
0x0C:R/W:External control register 5, output state control
0x0D:R/W:External control register 6, output state control
0x0E:R/W:External control register 7, dc detect level select
0x0F:R/W:External control register 8, dc detect level select

Syntax:
SpecialFormat(a_list, column_list, split_on=None, joint_char=':', a_pattern='')"""

    def __init__(self, a_list, column_list, split_on=None, joint_char=':', a_pattern=''):
        if type(a_list) == type('a_string'):
            self.a_list = [a_list]
        else:
            self.a_list = a_list
        self.column_list = column_list
        self.formatted_list = self.split_a_list(split_on)
        self.formatted_list = self.break_out_columns(self.formatted_list, column_list, joint_char)
        if len(a_pattern)>0: self.formatted_list = self.break_on_pattern(self.formatted_list, a_pattern, joint_char)

    def split_a_list(self, split_on):
        if type(split_on) == None:
            b_list = [ a_line.split() for a_line in self.a_list ]
        else:
            #b_list = self.my_split(self.a_list)
            b_list = [ my_split(a_line, split_on) for a_line in self.a_list ]
        return(b_list)

    def my_split(self, a_string, delim='\s*', skip_empty_members=False):
        search_pattern = re.compile(delim)
        m = re.split(search_pattern, a_string)
        if len(m)>0:
            if skip_empty_members: a_list = [ a_string for a_string in m if len(a_string)>0 ]
            else: a_list = [ a_string for a_string in m ]
            return(a_list)
        else:
            return(a_string)

    def break_out_columns(self, a_list, column_list, joint_char):
        columnRange = range(len(column_list))
        listRange = range(len(a_list))
        c_list = [[] for a_line in a_list]
        last_split = 0
        for i in columnRange:
            for j in listRange:
                sub_list = ' '.join(a_list[j][last_split:column_list[i]]) #for a_line in a_list[j][:column_list[i]]]
                c_list[j] += [sub_list]
            last_split = column_list[i] #+1
        if column_list[-1] < len(a_list[0]):
            for j in listRange:
                c_list[j] += [' '.join(a_list[j][column_list[-1]:])]
        c_list = [ joint_char.join(a_line) for a_line in c_list ]
        return(c_list)

    def break_on_pattern(self, a_list, a_pattern, joint=':'):
        g = m_grep(a_list)
        g.grep(a_pattern)
        aRange = range(g.pattern_count)
        b_list = [ a_list[i].replace(g.m_groups[i], g.m_groups[i]+joint) for i in aRange ]
        return(b_list)


class CollapseBlocks(CaptureBlocks):
    """CollapseBlocks is a better (hopefully) utility than Join_M_Lines, it inherits CaptureBlocks, so the init is the same.
       Think of the start_block, end_block, and start_phrase to divide up the blocks: i.e.
       Pin { Name = OUT3_P; XCoord=(0, 0); Shape = 0; PinType = IOType; 
           Connection[0]; { TestCh[1] = 78; TesterCh[2] = 79; TesterCh[3] = 80; TesterCh[4]=81; }
       }
       so, block_start = "Pin {", block_stop = "}", start_phrase = "{"
       After the init, invoke self.join_lines(joint="") to get:
       Pin { Name = OUT3_P; XCoord = (0, 0); Shape = 0; PinType = IOType;Connection[0] { TesterCh[1] = 78; TesterCh[2] = 79; TesterCh[3] = 80; TesterCh[4] = 81; }}
       """

    def __init__(self, all_lines, block_start='{', block_stop = '}', start_phrase=''):
        super(CollapseBlocks, self).__init__(all_lines, block_start, block_stop, start_phrase)

    def join_lines(self, joint=""):
        aRange = range(len(self.start_pts))
        a_list = [ joint.join(self.all_lines[self.start_pts[i]:self.end_pts[i]]) for i in aRange ]
        aRange.reverse()
        for i in aRange:
            self.all_lines.__delslice__(self.start_pts[i], self.end_pts[i])
            try:
                self.all_lines.insert(self.start_pts[i], a_list[i])
            except IndexError:
                if self.start_pts[i]>=len(self.all_lines): self.all_lines.append(a_list[i])
                else: raise


def file_edit(data_obj, grep_regex_list=[], sub_regex_list=[], apply_fixes=False, tmp_file='/tmp/tmp_file_edit.txt', debug=False):
    """data_obj: FileUtils, file or gzip.GzipFile obj """
    if isinstance(data_obj, FileUtils):
        if cmp(data_obj.contents, []): data_obj.read_from_file()
        a_iter, a_size, file_name = iter(data_obj.contents), get_list_size(data_obj.contents), data_obj.nm
    elif isinstance(data_obj, gzip.GzipFile) or isinstance(data_obj, file):
        file_name = data_obj.filename if isinstance(data_obj, gzip.GzipFile) else data_obj.name
        f = FileUtils(file_name)
        data_obj_initial_offset = 0
        a_size = f.file_size - data_obj_initial_offset
        if isinstance(data_obj, gzip.GzipFile): 
           data_obj.rewind()
        data_obj.seek(data_obj_initial_offset) #seek back to data_obj_initial_offset 
        a_iter = read_lines_iter(data_obj, offset=data_obj_initial_offset)
    mm, fh = reset_mmap(None, FileUtils(tmp_file), a_iter, True)
    gm = mmap_re(mm)
    for a_grep, a_sub in zip(grep_regex_list, sub_regex_list):
        if mm.in_map(a_grep, offset=0):
            gm.sub(a_grep, a_sub, offset=0)
            gm.clear_cache()
    #write changes back to a_file
    if apply_fixes:
        bob = mm.close(), fh.close()
        mm, fh = reset_mmap(None, FileUtils(file_name), a_iter, True)
        mm.write_lines(gm.allLines)
        bob = mm.close(), fh.close()
    else:
        if debug: print 'changes not applied, chkout %s'%tmp_file
    return gm


class FileEdit:
    """Need to make an edit or two to one or more files?  a = FileEdit(file_list) then a.sub('OldPattern','NewPattern')
    do help on re module for more info on regexp and sub functionality.
    """

    def __init__(self, file_list):
        if type(file_list) == type("a_string"): self.file_list = [file_list]
        else: self.file_list = file_list
        self.file_index_list = range(len(self.file_list))
        self.file_utils = [FileUtils(a_file) for a_file in self.file_list]
        self.m_re = [ m_re([]) for file_index in self.file_index_list ]
        self.initialize()

    def initialize(self):
        for f, g in zip(self.file_utils, self.m_re):
            if f.is_file():
                f.read_from_file()
                g.allLines = [ a_line.rstrip() for a_line in f.contents ]
            else: setattr(f,'contents', [])
        self.clear_cache()

    def clear_cache(self):
        for g in self.m_re: g.clear_cache()

    def display_pattern_count(self):
        PrettyPrint(self.stats_list)

    def display_lines(self):
        self.dlist = [ '\n'.join(['File: %s'%f.nm]+['<T> %s'%a_row for a_row in self._global_lines_dict[f.nm]]) for f in self.file_utils if self._global_lines_dict.has_key(f.nm)]
        PrettyPrint(self.dlist)

    def display_m_groups(self):
        self.dlist = [ '\n'.join(['<F%04d>: %s'%(find_index(self.file_list, f.nm), f.nm)]+['   <F%04d> %s'%(find_index(self.file_list, f.nm), a_row) for a_row in self._global_m_groups_dict[f.nm]]) for f in self.file_utils if self._global_m_groups_dict.has_key(f.nm)]
        PrettyPrint(self.dlist)

    def _pattern_count(self):
        self.stats_list = [ "index: %d, file: %s, pattern_count: %d"%(i, self.file_utils[i].nm, self.m_re[i].pattern_count) \
        for i in self.file_index_list if self.m_re[i].pattern_count>0 ]
        self._global_pattern_count_dict = dict([(f.nm, g.pattern_count) for f, g in zip(self.file_utils, self.m_re) if g.pattern_count>0 ])

    def _coordinates(self):
        self.stats_dict = dict( [ (self.file_utils[i].nm, self.m_re[i].coordinates) for i in self.file_index_list ])
        self._global_coordinates_dict = dict([ (f.nm, g.coordinates) for f, g in zip(self.file_utils, self.m_re) if g.pattern_count>0 ])

    def _lines(self):
        self.stats_dict = dict( [ (self.file_utils[i].nm, self.m_re[i].lines) for i in self.file_index_list ])
        self._global_lines_dict = dict([ (f.nm, string_replace(g.lines,'\n','')) for f, g in zip(self.file_utils, self.m_re) if g.pattern_count>0 ])
        self._global_lines_list = []
        for a_file in self.file_list: self._global_lines_list += self._global_lines_dict[a_file] if self._global_lines_dict.has_key(a_file) else []

    def _m_groups(self):
        self._global_m_groups_dict = dict([ (f.nm, g.m_groups) for f, g in zip(self.file_utils, self.m_re) if g.pattern_count>0 ])
        self._global_m_groups_list = []
        for a_file in self.file_list: self._global_m_groups_list += self._global_m_groups_dict[a_file] if self._global_m_groups_dict.has_key(a_file) else []

    def _populate_results(self):
        self._pattern_count()
        self._lines()
        self._m_groups()
        self._coordinates()

    def sub(self, pattern_list, replc_list):
        """Pass in a list of patterns to search for and change to the list of repacement text.  i.e. ['foo','ocho'] for pattern and 
           ['bar','cinco'] for replc, does the following substitutions:
                  foo -> bar
                  ocho -> cinco
        """
        if type(pattern_list) == type("a_string"): pattern_list = [pattern_list]
        if type(replc_list) == type("a_string"): replc_list = [replc_list]
        assert len(pattern_list) == len(replc_list), 'number of elements in pattern_list (%d) and replc_list (%d) must be the same.\n'%(len(pattern_list), len(replc_list))
        aRange = range(len(pattern_list))
        for j in aRange:
            a_pattern, a_replc = pattern_list[j], replc_list[j]
            self.grep(a_pattern)
            for i in self.file_index_list:
                if self.m_re[i].pattern_count>0:
                    self.m_re[i].sub(a_pattern, a_replc)
                    self.file_utils[i].write_to_file(self.file_utils[i].contents)
        self._populate_results()

    def grep(self, pattern):
        for i in self.file_index_list:
            self.m_re[i].clear_cache()
            self.m_re[i].grep(pattern)
        self._populate_results()


class m_re_multi:
    """Pass in *args, where you'd have multiple instances of m_re, i.e.
    G = m_re_multi(g, b, r) where: g=m_re(a_list), b=m_re(b_list), r=m_re(c_list)"""

    def __init__(self,*args):
        self.m_table = [g for g in args ]
        self.m_results = [ [] for i in self.m_table ]

    def grep(self, pat_string):
        for g in self.m_table: g.grep(pat_string)
        return

    def get_lines(self):
        for i, g in enumerate(self.m_table): self.m_results[i] = g.lines
        return(self.m_results)

    def get_pattern_count(self):
        for i, g in enumerate(self.m_table): self.m_results[i] = g.pattern_count
        return(self.m_results)

    def get_line_indices(self):
        for i, g in enumerate(self.m_table): self.m_results[i] = [ int(float(a_num)-1) for a_num in g.coordinates] 
        return(self.m_results)

    def sub(self, query_pattern, sub_pattern):
        for g in self.m_table: g.sub(query_pattern, sub_pattern)
        return

    def clear_cache(self):
        for g in self.m_table: g.clear_cache()
        return


class TableManipulation:
    """TableManipulation, add/remove columns and/or rows from an array that would represent a table grid, or a 2 dimensional
       array.
       t = TableManipulation(a_list, a_delimeter)"""

    def __init__(self, a_list, a_delim=','):
        self.table_array = a_list
        self.delimeter = a_delim
        self.set_params()

    def set_params(self):
        if cmp(self.table_array, []) != 0:
            self.num_rows, self.num_cols = len(self.table_array), 0
            if type(self.table_array[0]) != type([]):
                self.table_array = [ a_line.split(self.delimeter) for a_line in self.table_array ]
            self.num_cols = len(self.table_array[0])
        else: self.num_cols, self.num_rows = 0, 0

    def add_column(self, a_list, index=-1):
        if self.num_cols == 0: self.table_array = a_list
        else:
            if len(a_list)>self.num_rows: 
                for i in xrange(len(a_list)-self.num_rows): self.table_array.append(['' for j in xrange(self.num_cols)])
                self.num_rows = len(a_list)
	    if len(a_list)<self.num_rows: col_list = a_list + ['' for i in xrange(self.num_rows-len(a_list))]
	    else: col_list = a_list
            aRange = range(self.num_rows) 
            if index == -1:
                for i in aRange: self.table_array[i].append(col_list[i])
            else:
                for i in aRange: self.table_array[i].insert(index, col_list[i])
        self.set_params()

    def add_row(self, a_list, index=-1):
        if index == -1:
            self.table_array.append(a_list)
        else:
            self.table_array.insert(index, a_list)
        self.set_params()


class ConvertTime:
    time_struct = namedtuple('time_struct','tm_year tm_mon tm_mday tm_hour tm_min tm_sec tm_wday tm_yday tm_isdst') #copy of time.struct_time

    def __init__(self):
        pass
    @classmethod

    def StructTimeToSeconds(self, time_struct=None):
        if not time_struct: time_struct = localtime()
        return mktime(time_struct)
    @classmethod

    def StringToStructTime(self, a_string='20110502153044'):
        """Populate struct_time object from a string containing year, month, day, hours, minutes, and seconds, or more specifically:
        a_string = yyyymmddhhmmss"""
        num_digits_seq, a_iter, pack_format = [ 4, 2, 2, 2, 2, 2 ], iter(list(a_string)),'i'*9
        date_list = [ int(''.join([a_iter.next() for i in xrange(num_digits)])) for num_digits in num_digits_seq ]
        date_list += [ 0, 0, 0 ] #filler for tm_wkday, tm_yday, tm_isdst, don't care in this case
        packed_list = pack(pack_format,*date_list) #probably not necessary, just getting the hang of pack and unpack from the struct module
        return( self.time_struct._make(unpack(pack_format, packed_list)) )


class GetTimeStamp:

    def __init__(self, total_time):
        delta = total_time
        incr = [ 24*60*60, 60*60, 60, 1] 
        aRange = range(len(incr))
        days, hours, minutes, seconds = 0, 0, 0, 0 
        self.time_stamp = [ days, hours, minutes, seconds ] 
        self.time_string = ['Days:','Hours:','Minutes:','Seconds:']
        for i in aRange:
            if int(delta/incr[i])>0: 
                self.time_stamp[i] = int(delta/incr[i])
                self.time_string[i] = '%s %d '%(self.time_string[i], self.time_stamp[i])
                delta -= self.time_stamp[i]*incr[i]
            else: 
                self.time_stamp[i]=0
                self.time_string[i]=''
        self.time_string = ''.join(self.time_string)


class SysCommand:

    def __init__(self, cmd=''):
        pipe = os.popen('{ '+cmd+';} 2>&1', 'r') 
        self.output = [ a_line.strip() for a_line in pipe.read().splitlines() ] 
        self.sts = pipe.close()


class GetFileListing:
    """
    deprecated, really only useful in linux system, use "get_file_listing" instead
    """

    def __init__(self, file_pattern='', ls_opts=''): 
        self.cmd = ' '.join(['ls', ls_opts, file_pattern])
        self.sys_cmd = SysCommand(self.cmd)
        self.output = self.sys_cmd.output


def get_file_listing(dir_path_list=None, file_pattern="*.*", do_recursive=True):
    """
    Get file listing based on dir_path_list and file_pattern
    :param dir_path_list:
    :param file_pattern:
    :param do_recursive:
    :return:
    """
    #TODO: add handler for recursive function in following sub directories out of dir_path
    file_list = []
    dir_path_list = dir_path_list or [] if not isinstance(dir_path_list,str) else [dir_path_list]
    for a_path in dir_path_list:
        for root, dirs, files in os.walk(a_path):
            if len(files) > 0:
                file_list += [os.path.join(root, a_file) for a_file in fnmatch.filter(files, file_pattern)]
    return file_list


class TranslateAliases:

    def __init__(self, input_codes, output_codes):
        self.input_codes = input_codes
        self.output_codes = output_codes
        self.trans_table = string.maketrans(self.input_codes, self.output_codes)


    def do_translation(self, channel_data):
        self.channel_data = channel_data
        if type(channel_data) == type('a_string'):
            self.channel_data = self.channel_data.translate(self.trans_table)
        else:    
            self.channel_data = [ line.translate(self.trans_table) \
              for line in self.channel_data ]
        return(self.channel_data)


class safe: # the decorator
    """usage: 
        @safe

        def bad():
            1/0"""

    def __init__(self, function):
        self.function = function

  
    def __call__(self, *args):
        try:
            return self.function(*args)
        except Exception, e:
            # make a popup here with your exception information.
            # might want to use traceback module to parse the exception info
            print "Uh Oh, safe Error: %s" % (e)
            exc_type, exc_value, exc_traceback = sys.exc_info()
            traceback.print_exc()


class Profiler:

    def __init__(self):
        self.reset_time_parameters()

    def snap(self):
        self.prev_snap_time = self.snap_time
        self.snap_time = time() 
        self.snap_interval = self.snap_time - self.prev_snap_time
        return(self.snap_interval)

    def get_overall_elapsed_time(self, start_time=None):
        if start_time==None: start_time = self.profiler_start_time
        self.snap()
        self.overall_elapsed_time = self.snap_time - start_time
        return(self.overall_elapsed_time)

    def get_elapsed_time(self):
        self.snap()
        return(self.snap_interval)

    def reset_time_parameters(self):
        self.snap_interval = 0.0
        self.elapsed_time = 0.0
        self.overall_elapsed_time = 0.0
        self.profiler_start_time = time()
        self.snap_time = self.profiler_start_time


class CmpOperators(object):
    """CmpOperators: container class for various comparison methods """

    def __init__(self):
        return
    @classmethod

    def contains(self, v1, v2):
        if v1 in v2:
            return True
    @classmethod

    def contains_regexp(self, v1, v2):
        pat_v1 = re.compile(v1)
        if pat_v1.search(v2):
            return True
    @classmethod

    def excludes(self, v1, v2):
        if not v1 in v2:
            return True
    @classmethod

    def excludes_regexp(self, v1, v2):
        pat_v1 = re.compile(v1)
        if not pat_v1.search(v2):
            return True
    @classmethod

    def equals(self, v1, v2):
        if v1==v2:
            return True
    @classmethod

    def notequals(self, v1, v2):
        if v1!=v2:
            return True
    @classmethod

    def greaterthan(self, v1, v2):
        if v2>v1:
            return True
        return False
    @classmethod

    def lessthan(self, v1, v2):
        if v2<v1:
            return True
        return False
    @classmethod

    def startswith(self, v1, v2):
        if v2.startswith(v1):
            return True
    @classmethod

    def endswith(self, v1, v2):
        if v2.endswith(v1):
            return True
    @classmethod

    def haslength(self, v1, v2):
        if len(v2)>v1:
            return True


class grep_iterator:
    #"""Experimental, playing around with iterators and generators"""

    def __init__(self, a_pattern='', do_match=True):
        self.search_pattern, self.line_counter = re.compile(a_pattern), -1 
        self.FilterFunc = ifilter if do_match else self.__filter_out__

    def grep(self, a_iter, a_pattern=None, do_match=None):
        if a_pattern != None: self.search_pattern = re.compile(a_pattern)
        if do_match != None:
            self.FilterFunc = ifilter if do_match else self.__filter_out__
        self.line_counter = -1
        for a_line in self.FilterFunc(self.__search_function__, a_iter):
            yield self.line_counter, a_line, len(a_line)

    def __filter_out__(self, search_func, a_iter):
        for a_line in a_iter:
            if not search_func(a_line): yield a_line

    def __search_function__(self, a_line=''):
        self.line_counter+=1
        return(self.search_pattern.search(a_line))


def reset_mmap(mmap_obj, f, a_list=None, get_newline_offsets=False):
    a_list_iter = a_list
    if not a_list: # a_list = [] or None
        f.read_from_file()
        a_iter, sum_iter = tee(iter([a_row for a_row in f.contents]), 2)
    elif isinstance(a_list, list): 
        a_list_iter = iter(a_list)
        a_iter, sum_iter = tee(a_list_iter, 2)
        f.write_to_file('bogus')
    else:
        a_iter, sum_iter = tee(a_list_iter, 2)
        f.write_to_file('bogus')
    fh = f._open_file(f.nm,'r+')
    mm_kwargs = dict([('fileno', fh.fileno()),('length', f.file_size)])
    mmap_obj = mmap_utils(**mm_kwargs)
    mmap_obj.resize(sum(len(a_line) for a_line in sum_iter))
    mmap_obj.write_lines(a_iter, offset=0)
    if get_newline_offsets: mmap_obj.get_newline_offsets()
    return mmap_obj, fh


def read_lines_iter(fh, length=0, offset=-1): 
    file_obj = fh #.myfileobj if isinstance(fh, gzip.GzipFile) else fh
    file_obj_offset = offset if offset>-1 else file_obj.tell()
    if isinstance(file_obj, gzip.GzipFile): 
        file_obj.myfileobj.seek(0, 2)
        file_obj_size = file_obj.myfileobj.tell()
        file_obj.rewind()
    else:
        file_obj.seek(0, 2)
        file_obj_size = file_obj.tell()
    file_obj_length = length if length>0 else file_obj_size
    file_obj.seek(file_obj_offset)
    try: 
        file_obj_tell = file_obj_offset 
        while file_obj_tell<file_obj_length: 
            a_line = file_obj.next()
            file_obj_tell += len(a_line)
            yield a_line
    except Exception, e:
        pass


def anon_mmap(data_obj=None, length=0, offset=-1):
    #get a_iter and a_size
    if isinstance(data_obj, mmap.mmap): 
        start = offset if offset>-1 else data_obj.tell()
        stop = length if length>0 else data_obj.map_size
        a_iter, a_size = data_obj.read_lines_iter(stop, start), stop-start
    elif isinstance(data_obj, FileUtils):
        if cmp(data_obj.contents, [])==0: data_obj.read_from_file()
        newline_offsets = [0]
        for a_row in data_obj.contents: newline_offsets.append(newline_offsets[-1]+len(a_row))
        start = 0 if offset<0 else search_rcrsv(newline_offsets, offset)
        stop = len(data_obj.contents) if length==0 else search_rcrsv(newline_offsets, length)
        a_slice = slice(start, stop)
        a_iter, a_size = iter(data_obj.contents[a_slice]), get_list_size(data_obj.contents[a_slice])
    elif isinstance(data_obj, gzip.GzipFile) or isinstance(data_obj, file):
        file_name = data_obj.filename if isinstance(data_obj, gzip.GzipFile) else data_obj.name
        f = FileUtils(file_name)
        data_obj_initial_offset = offset if offset>-1 else data_obj.tell()
        a_size = f.file_size - data_obj_initial_offset
        data_obj_length = length if length>0 else a_size
        if isinstance(data_obj, gzip.GzipFile): 
           data_obj.rewind()
        data_obj.seek(data_obj_initial_offset) #seek back to data_obj_initial_offset 
        a_iter = read_lines_iter(data_obj, length=data_obj_length, offset=data_obj_initial_offset)
    elif isinstance(data_obj, str) or isinstance(data_obj, list): 
        data_obj_offset = offset if offset>-1 else 0
        data_obj_length = length if length>0 else sum(len(a1) for a1 in data_obj)
        a_iter = iter( a1 for a1 in data_obj[data_obj_offset:data_obj_length] )
        a_size = sum(len(a1) for a1 in data_obj[data_obj_offset:data_obj_length]) 
    elif isinstance(data_obj, type(iter(i for i in xrange(2)))):
        data_obj_copy, sum_iter = tee( iter(a1 for a1 in data_obj), 2)
        data_obj_list = list(data_obj_copy)
        data_obj_offset = offset if offset>-1 else 0
        data_obj_length = length if length>0 else sum(len(a1) for a1 in sum_iter)
        a_iter, a_size = iter(a1 for a1 in data_obj_list[data_obj_offset:data_obj_length]), data_obj_length
    else:
        data_obj_length = length if length>0 else sum(len(a1) for a1 in data_obj)
        a_iter, a_size = iter(u'\x00' for i in xrange(data_obj_length)), data_obj_length
    mm = mmap_utils(fileno=-1, length=a_size)
    mm.write_lines(a_iter, offset=0)
    mm.get_newline_offsets()
    return mm


class mmap_utils(mmap.mmap):
    """class wrapper for mmap.mmap
    typical arguements passed in as a dict: {'fileno':,'length':}
    setup by the following:
    fh = open(a_file, mode='+r')
    mm = mmap_utils(**{'fileno':fh.fileno(),'length':os.path.getsize(fh.name)}) """

    def __init__(self,**kwargs):
        self.__set_attributes__()
        self.__match_up_kwargs__(kwargs)
        super(mmap_utils, self).__init__(self.fileno, self.length, self.flags, self.prot, self.access, self.offset)

    def __set_attributes__(self):
        """if access specified, then flags and prot should be set to None 
        map_reference can be a FileUtils object or list, comes into play if fileno = -1"""
        self.attributes_dict = {
            'fh':{'attribute':'fh','default':None},
            'fileno':{'attribute':'fileno','default':-1},
            'length':{'attribute':'length','default':0},
            'flags':{'attribute':'flags','default':mmap.MAP_SHARED},
            'prot':{'attribute':'prot','default':mmap.PROT_READ | mmap.PROT_WRITE},
            'access':{'attribute':'access','default':None},
            'offset':{'attribute':'offset','default':0},
            'map_reference':{'attribute':'map_reference','default':None},
            'map_size':{'attribute':'map_size','default':None},
            'pm':{'attribute':'pm','default':Profiler()},
            'pm_info':{'attribute':'pm_info','default':[]},
            'backed_up':{'attribute':'backed_up','default':False}
        }
        for a_dict in self.attributes_dict.itervalues(): setattr(self, a_dict['attribute'], a_dict['default'])

    def __match_up_kwargs__(self, kwargs):
        special_conditions_check = {\
           'access':['flags','prot'],\
           'map_reference':'fileno'\
        }
        for a_key, a_value in kwargs.iteritems(): 
           if a_value: 
               if self.attributes_dict.has_key(a_key): 
                   setattr(self, self.attributes_dict[a_key]['attribute'], a_value)
        self.map_size = self.length
        if self.map_reference: 
           a_dict = self.attributes_dict['fileno']
           setattr(self, a_dict['attribute'], None)
        if self.access:
           for attribute in special_conditions_check['access']: 
               a_dict = self.attributes_dict[attribute]
               setattr(self, a_dict['attribute'], None)

    def copy_from_list(self, a_list, offset=-1):
        if offset>-1: self.seek(offset)
        for a_row in add_cr_iter(a_list): self.write(a_row)

    def __backup__(self, make_backup=True):
        if make_backup: 
            self.__backup_map__ = mmap.mmap(-1, self.map_size)
            while self.__backup_map__.tell() != self.map_size: self.__backup_map__.write(self.readline())
            self.seek(0)
            self.__backup_map__.seek(0)
            self.backed_up = True

    def write_from_offset(self, a_line, offset=-1):
        if offset>-1: self.seek(offset)
        self.write(a_line)

    def write_lines(self, string_array=None, offset=-1):
        self.size()
        if offset>-1:self.seek(offset)
        for a_string in string_array: self.write(a_string)
        self.seek(0 if offset==-1 else offset)

    def readline_from_offset(self, offset=-1):
        self.size()
        if offset>-1: self.seek(offset)
        return(self.readline())

    def read_from_offset(self, num_bytes=-1, offset=-1):
        'if num_bytes<0, read till EOF, seek(offset) if offset>-1'
        self.size()
        if offset>-1: self.seek(offset)
        self.read(num_bytes)

    def read_lines_iter(self, length=0, offset=-1):
        self.size()
        if length<=0: length = self.map_size
        if offset>-1:self.seek(offset)
        while self.tell() < length: yield self.readline()

    def get_newline_offsets(self):
        self.size()
        self.seek(0)
        num_iterators = 2
        a_iter, offsets_iter = iscatter(self.__get_newline_offsets__(self.tell()), num_iterators)
        self.num_lines, self.newline_offsets = sum(a_iter), list(offsets_iter)
        self.newline_offsets_hash_table = dict([(offset, i) for i, offset in enumerate(self.newline_offsets)])
        self.seek(0)

    def __get_newline_offsets__(self, starting_position=0):
        position = starting_position
        while position < self.map_size:
            position = self.tell()
            self.readline()
            yield 1, position

    def get_offset(self, position=None, offset=0):
       """get offset value from newline_offsets list, use offset to shift offset position
       i.e. mm.in_map(a_str, offset=0) is true, but mm.tell() is on the next line, so get the line with a_str,
       offset needs to be -1"""
       return get_newline_offset(self, position, offset)

    def size(self):
        current_position = self.tell()
        self.seek(0, os.SEEK_END)
        size = self.tell()
        if size != self.map_size: self.map_size = size
        self.seek(current_position if current_position<=self.map_size else 0)
        return(size)

    def keep_in_list(self, a_pattern, length=0, offset=-1):
        self.size()
        if offset>-1: self.seek(offset)
        if length<=0: length = self.map_size
        num_iterators = 3
        g = grep_iterator(a_pattern, do_match=True)
        self.g_coordinates_iter, self.g_lines_iter, g_lengths_iter = iscatter(g.grep(\
            self.read_lines_iter(length=length, offset=offset)), num_iterators)
        self.g_lines_size = sum(g_lengths_iter)

    def remove_from_list(self, a_pattern, length=0, offset=-1):
        self.size()
        if offset>-1: self.seek(offset)
        if length<=0: length = self.map_size
        num_iterators = 3
        g = grep_iterator(a_pattern, do_match=False)
        self.g_coordinates_iter, self.g_lines_iter, g_lengths_iter = iscatter(g.grep(\
            self.read_lines_iter(length=length, offset=offset)), num_iterators)
        self.g_lines_size = sum(g_lengths_iter)

    def replace_in_list(self, a_pattern, sub_pattern, length=0, offset=-1):
        self.size()
        if offset>-1: self.seek(offset)
        if length<=0: length = self.map_size
        num_iterators = 2
        self.g_lines_iter, g_lengths_iter = iscatter(sub_iterator(self.read_lines_iter(length=length, offset=offset), \
            a_pattern, sub_pattern), num_iterators)
        self.g_lines_size = sum(g_lengths_iter)

    def in_map(self, a_pattern, length=0, offset=-1):
        if offset>-1: self.seek(offset)
        if length<=0: length = self.map_size
        self.size()
        search_pattern = re.compile(a_pattern)
        for a_line in self.read_lines_iter(length=length, offset=offset):
            if search_pattern.search(a_line): return True
        return False

    def sort_by(self, fields=[0], delim='\s+', joint=':', do_reverse=[False], IncludeEmpties=True, offset=-1, length=-1, WriteBack=True):
        self.pm.snap()
        start_time, self.pm_info = self.pm.snap_time, []
        self.size()
        self.sortList = list(self.__split_strip_and_cast__(self.read_lines_iter(length=length if length>0 else 0, offset=offset if offset > 0 else 0), fields, delim, IncludeEmpties))
        self.pm_info.append(' + sort_by: split, strip, and cast: %f'%self.pm.snap())
        # -- self.sortList = [ my_split(aRow, delim, IncludeEmpties)  for aRow in self.read_lines_iter(offset if offset > 0 else 0) ]
        # -- self.pm_info.append(' + sort_by: split: %f'%self.pm.snap())
        # -- self.sortList = [ [aMember.strip() for aMember in aRow] for aRow in self.sortList ]
        # -- self.pm_info.append(' + sort_by: strip: %f'%self.pm.snap())
        # -- self.sortList = [ [ self.CastToNumber(aMember) for aMember in aRow ] for aRow in self.sortList ]
        # -- self.pm_info.append(' + sort_by: cast: %f'%self.pm.snap())
        if type(do_reverse) != type([False]): do_reverse = [do_reverse]
        if len(fields) > len(do_reverse): 
            num_fields, num_bools = len(fields), len(do_reverse)
            do_reverse += [ False for a_field in fields[num_bools:] ]
        fields.reverse()
        do_reverse.reverse()
        self.pm_info.append(' + sort_by: setup fields and do_reverse lists: %f'%self.pm.snap())
        for a_field, a_reverse in zip(fields, do_reverse):
            try:
                self.sortList = sorted(self.sortList, key= itemgetter(a_field), reverse=a_reverse)
                self.pm_info.append(' + sort_by: ++ sort on field: %d: %f'%(a_field, self.pm.snap()))
            except IndexError:
                print 'Field: %d, DoReverse: %s'%(a_field, a_reverse)
                raise
        self.pm_info.append(' + sort_by: finished sorted on all fields: %f'%self.pm.snap())
        self.sortList = [ joint.join(aRow) for aRow in iter( (string_cast(a_cell) for a_cell in a_row) for a_row in self.sortList) ]
        self.pm_info.append(' + sort_by: reconstitute row_list to row_string: %f'%self.pm.snap())
        if WriteBack: 
            self.write_lines(add_cr_iter(self.sortList), offset if offset > 0 else 0)
            self.pm_info.append(' + sort_by: write back to mmap_obj: %f'%self.pm.snap())
        self.pm_info.append(' + sort_by: sort done: %f'%(self.pm.snap_time-start_time))

    def __split_strip_and_cast__(self, a_iter, fields, delimeter=';', IncludeEmpties=True):
        for a_row in a_iter:
            yield [self.CastToNumber(aMember.strip()) if i in fields else aMember.strip() for i, aMember in enumerate(my_split(a_row, delimeter, IncludeEmpties)) ]

    def CastToNumber(self, a_string, num_type_keys='Dec Hex Binary Octal Float'.split()):
        f, a_value = GetBaseType(a_string, num_type_keys)
        return a_value


class mmap_re(m_re):

    def __init__(self, a_map):
        self.allLines = list(a_map.read_lines_iter(offset=0))
        self.a_map = a_map
        self.__special_init__()
        self.clear_cache()

    def apply_changes(self, length=-1, offset=0):
        new_size = sum( len(a_row) for a_row in self.allLines)
        self.a_map.resize(new_size)
        self.a_map.map_size = new_size
        self.a_map.write_lines(self.allLines, 0)
        self.a_map.seek(0)
        self.__special_init__()

    def __special_init__(self, offset=0):
        self.a_map.get_newline_offsets()
        if offset>-1: self.a_map.seek(offset)
        self.aRange = xrange(len(self.a_map.newline_offsets))

    def get_all_lines(self):
        a_list = list(self.a_map.read_lines_iter(offset=0))
        self.a_map.seek(0)
        return(a_list)

    def grep(self, pattern, length=-1, offset=-1):
        if length<0: 
            length=self.a_map.map_size
            stop_index = len(self.a_map.newline_offsets)
        else: stop_index = find_index(self.a_map.newline_offsets, length)
        if offset<0: offset = self.a_map.tell() 
        if self.a_map.in_map(pattern, length, offset):
            start_index = find_index(self.a_map.newline_offsets, offset)
            self.aRange = xrange(start_index, stop_index)
            self.a_map.seek(offset)
            self.pattern_count=0
            self.coordinates=[]
            self.lines=[]
            self.search_pattern=re.compile(pattern)
            m_iter = self._process_m(self.m_findall(self.search_pattern, start_index, self.a_map, length))
            for m, m_groups, a_line, coordinates, pattern_count in m_iter:
                self.m = m
                self.m_groups += m_groups
                self.lines.append(a_line)
                self.coordinates += coordinates
                self.pattern_count += pattern_count
        if offset>-1: self.a_map.seek(offset)

    def sub(self, pattern, replc, length=-1, offset=-1):
        if length<0: length = self.a_map.map_size
        if offset<0: offset = self.a_map.tell()
        self.grep(pattern, length, offset) #get pattern_count and coordinates
        self.subRange = unique_sub_list([ int(float(a_coord)) for a_coord in self.coordinates ])
        for i in self.subRange:
            self.m = re.sub(self.search_pattern, replc, self.allLines[i])
            if self.m != self.allLines[i]:
                self.allLines[i] = self.m
        if self.pattern_count>0: self.apply_changes()
        elif offset>-1: self.__special_init__(offset)
        else: pass

    def m_findall(self, a_pattern, start_index=0, a_map=None, length=-1):
       if length<0: length = a_map.map_size
       row = start_index
       while a_map.tell() != length:
           a_line = a_map.readline()
           m = a_pattern.findall(a_line)
           row += 1
           if len(m)>0:
               yield (row-1, m, a_line)


class InfiniteCounter:

    def __init__(self, start=0):
        self.cur = start

    def __iter__(self):
        return(self)

    def next(self):
        self.cur += 1
        return self.cur


class PersistentDict(dict):
    """ Created by Raymond Hettinger on Wed, 4 Feb 2009 (MIT), pulled down from code.activestate.com, 
    dbdict: a dbm based on a dict subclass.

    Persistent dictionary with an API compatible with shelve and anydbm.

    The dict is kept in memory, so the dictionary operations run as fast as
    a regular dictionary.

    Write to disk is delayed until close or sync (similar to gdbm's fast mode).

    Input file format is automatically discovered.
    Output file format is selectable between pickle, json, and csv.
    All three serialization formats are backed by fast C implementations.

    """

    def __init__(self, filename, flag='c', mode=None, format='pickle', *args, **kwds):
        self.flag = flag                    # r=readonly, c=create, or n=new
        self.mode = mode                    # None or an octal triple like 0644
        self.format = format                # 'csv', 'json', or 'pickle'
        self.filename = filename
        if flag != 'n' and os.access(filename, os.R_OK):
            fileobj = open(filename, 'rb' if format=='pickle' else 'r')
            with fileobj:
                self.load(fileobj)
        dict.__init__(self, *args, **kwds)

    def sync(self):
        'Write dict to disk'
        if self.flag == 'r':
            return
        filename = self.filename
        tempname = filename + '.tmp'
        fileobj = open(tempname, 'wb' if self.format=='pickle' else 'w')
        try:
            self.dump(fileobj)
        except Exception:
            os.remove(tempname)
            raise
        finally:
            fileobj.close()
        shutil.move(tempname, self.filename)    # atomic commit
        if self.mode is not None:
            os.chmod(self.filename, self.mode)

    def close(self):
        self.sync()

    def __enter__(self):
        return self

    def __exit__(self, *exc_info):
        self.close()

    def dump(self, fileobj):
        if self.format == 'csv':
            csv.writer(fileobj).writerows(self.items())
        elif self.format == 'json':
            json.dump(self, fileobj, separators=(',', ':'))
        elif self.format == 'pickle':
            pickle.dump(dict(self), fileobj, 2)
        else:
            raise NotImplementedError('Unknown format: ' + repr(self.format))

    def load(self, fileobj):
        # try formats from most restrictive to least restrictive
        for loader in (pickle.load, json.load, csv.reader):
            fileobj.seek(0)
            try:
                return self.update(loader(fileobj))
            except Exception:
                pass
        raise ValueError('File not in a supported format')


class NewLogger(object):
    """
    Helper class for logging
    """

    default_log_format = "%(levelname)s::%(asctime)s:: %(message)s"
    default_date_format = "%m/%d/%Y %H:%M:%S"

    def __init__(self, logger_name="default_logger", file_name=None, stream=sys.stdout,
                 file_log_level=logging.DEBUG, console_log_level=logging.INFO,
                 reset_logger=True):
        if reset_logger:
            self.reset_logging()
        self.file_name = os.path.abspath(file_name)
        self.logger = self.setup_logging(logger_name, file_name, stream, file_log_level,
                                         console_log_level)
        self.handlers = self.logger.handlers

    @staticmethod
    def reset_logging():
        """
        clear out logging root
        :return:
        """
        if logging.root:
            del logging.root.handlers[:]

    @staticmethod
    def setup_logging(logger_name, fn, stdout, flog_level, clog_level,
                      log_format=default_log_format, date_format=default_date_format):
        """
        Create logger and setup handlers for log file and stdout, which defaults to console (sys.stderr)
        :rtype : logging object
        :param logger_name:
        :param fn:
        :param stdout:
        :param flog_level:
        :param clog_level:
        :return logger:
        """
        logger = logging.getLogger()
        logger.setLevel(logging.DEBUG)
        formatter = logging.Formatter(fmt=log_format,
                                      datefmt=date_format)

        # create file handler
        fh = logging.FileHandler(filename=fn, mode="w")
        fh.setLevel(flog_level)
        fh.setFormatter(formatter)

        # create stream handler, default is console
        ch = logging.StreamHandler(stream=stdout)
        ch.setLevel(clog_level)
        ch.setFormatter(formatter)
        # add handlers to logger
        logger.addHandler(fh)
        logger.addHandler(ch)
        return logger

