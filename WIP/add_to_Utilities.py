"""
jk 20140325: staging area for generic utility methods, eventually moved into SVN/Python_Tools/utilities/Utilities.py after
    chk_out
"""
import os, re, sys
import gzip, commands
from operator import itemgetter

#handy lambdas
resort_list = lambda a_list, sort_by_fields=itemgetter(0), key_func=lambda x:x : \
    sorted(a_list,key=lambda x:sort_by_fields(key_func(x)))

get_cr = lambda a_str: re.search(re.compile('$\r?\n'),a_str)

# '''Used in pretty_format, check for carriage return at EOL, return the _sre.SRE_Match obj or None'''
strip_tw = lambda a_str: '%s%s'%(a_str.rstrip(),get_cr(a_str).group() if get_cr(a_str) else '')


def string_cast(a_list):
    '''cast elements from list to string'''
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

def my_split(a_string,delim='\s*', include_empties=False):
    search_pattern = re.compile(delim)
    m = re.split(search_pattern,a_string)
    if len(m)>0:
        if not include_empties: a_list = [ a_string for a_string in m if len(a_string)>0 ]
        else: a_list = [ a_string for a_string in m ]
        return(a_list)
    else:
        return(a_string)

def find_block(m_groups,start_clause,stop_clause,index_offset=0):
    found = False
    # chk_list = [ 1 if cmp(a_cell,start_clause)==0 else -1 for a_cell in m_groups ]
    chk_list = [1 if start_clause == a_cell else -1 for a_cell in m_groups]
    chk_sum = [chk_list[0]]
    for a_num in chk_list[1:]: chk_sum.append(a_num+chk_sum[-1])
    start_index,stop_index = find_index(chk_sum,'^1\\b'),find_index(chk_sum,'^0\\b')
    start_index = (start_index+index_offset) if start_index>-1 else -1
    stop_index = (stop_index+index_offset) if stop_index>-1 else -1
    return start_index,stop_index

def find_blocks(m_groups,start_clause,stop_clause,offset=0):
    # start_stop_iter = find_blocks_iter(m_groups,start_clause,stop_clause,offset)
    # return(list(start_stop_iter))
    start_pts,stop_pts = [],[]
    [(start_pts.append(start_pt),stop_pts.append(stop_pt))for start_pt,stop_pt in find_blocks_iter(m_groups,start_clause,stop_clause,offset)]
    return (start_pts,stop_pts)

def find_blocks_iter(m_groups,start_clause,stop_clause,offset=0):
    current_offset = offset
    start,stop = -1,-1
    while current_offset < len(m_groups):
        start,stop = find_block(m_groups[current_offset:],start_clause,stop_clause,current_offset)
        if start>-1 and stop>-1: current_offset = stop+1
        else: current_offset = len(m_groups)
        yield (start,stop)

def grep_list(a_list, search_param):
    '''Only grep on string types, will handle a list of multitype, but
    only operate on indices of string type'''
    out=[]
    str_type = type("a_str")
    if type(a_list) == str_type: a_list = [a_list]
    for a_value in a_list:
        if type(a_value) == str_type:
            m = re.search(search_param, a_value)
            if m != None: out.append(a_value)
    return(out)

def grep(*matches):
    """
    Returns a generator function that operates on an iterable:
        filters items in the iterable that match any of the patterns.

        match: a callable returning a True value if it matches the item

    snippet:
    import re
    input = [r'alpha\n', 'beta\n', 'gamma\n', 'delta\n']
    list(grep(re.compile('b').match)(input))
    ['beta\n']
    """
    def _do_grep_wrapper(*matches):
        def _do_grep(lines):
            for line in lines:
                for match in matches:
                    if match(line):
                        yield line
                        break
        return _do_grep
    return _do_grep_wrapper(*matches)

def in_string(a_str, search_param):
    if not isinstance(a_str, str): a_str = string_cast(a_str)
    if not isinstance(search_param, str): search_param = string_cast(search_param)
    #a_iter = re.finditer(re.compile(search_param), a_str)
    #return len([m for m in a_iter if m])>0
    return True if re.search(re.compile(search_param), a_str) else False

def in_list(a_list, search_param):
    '''usage: in_list(aList, regexp) "is regexp in list" is more flexible than "is obj in list"'''
    #g = m_re(a_list)
    #g.grep(search_param)
    #return(g.pattern_count>0)
    if not isinstance(search_param, str): search_param = string_cast(search_param)
    if isinstance(a_list, str): return in_string(a_list, search_param)
    else: a_iter = ( '%s'%a_line for a_line in a_list )
    return (in_iter(a_iter, '%s'%search_param).next())

def in_iter(a_iter, search_param):
    search_pattern = re.compile(search_param)
    found_pattern = False
    for a_line in a_iter:
        if search_pattern.search(a_line):
            found_pattern = True
            break
    yield found_pattern

def find_index(aList, search_param):
    '''usage: index = find_index(aList, search_param) 
    where: aList is a list and search_param is a string expression
           index is the first occurrence of the search_param found in the list
           starting from left to right'''
    ListCopy, SearchParam = string_cast(aList), re.compile(string_cast(search_param))
    if type(ListCopy) == type('a_string'): ListCopy = [ListCopy]
    for a_value in ListCopy:
        m = SearchParam.search(a_value)
        if m != None:
            return(ListCopy.index(a_value))
    return(-1)

def keep_in_list_coordinates(a_list, a_pattern):
    '''grep -l a_pattern: return indices of matching elements in a_list as a new list '''
    search_pattern = re.compile(a_pattern)
    full_line_range = xrange(len(a_list))
    new_list =list( (i for i, a_line in zip(full_line_range, a_list) if search_pattern.search(a_line)) )
    return(new_list)


def replace_in_list(a_list, a_pattern, sub_pattern):
    """
    do re.sub across all elements in a list and return a new list
    """
    search_pattern = re.compile(a_pattern)
    line_range = xrange(len(a_list))
    a_iter = (search_pattern.sub(sub_pattern, a_line) for a_line in a_list )
    return([ a_iter.next() for i in line_range ])

def keep_in_list(a_list, a_pattern):
    '''grep a_pattern: return matching elements in a_list as a new list '''
    search_pattern = re.compile(a_pattern)
    new_list = list( (a_line for a_line in a_list if search_pattern.search(a_line)) )
    return(new_list)

def remove_from_list(a_list, a_pattern):
    '''grep -v a_pattern: return non-matching elements in a_list as a new list '''
    search_pattern = re.compile(a_pattern)
    new_list = list( (a_line for a_line in a_list if not search_pattern.search(a_line)) )
    return(new_list)

def unique_sub_list(a_list):
    """
    From a_list, return all unique elements in ascending order found in a new list
    """
    return(list(iter_unique_members(a_list)))

def sort_unique(a_list):
    """
    From a_list, return all unique elements, sorted in a new list
    """
    return(sorted(unique_sub_list(a_list)))

def iter_unique_members(a_iter):
    """
    Engine for unique_sub_list
    """
    members = []
    for a_element in a_iter:
        if not a_element in members: 
            members.append(a_element)
            yield a_element

def pretty_format(a_list, delimeter=':', joint='', do_left_just=True, do_rstrip=False):
    '''pretty_format(a_list[, delimeter=':', joint='', do_left_just=True, do_rstrip=False])
delimeter: default ':', can use regex, the parameter for splitting the line in a_list
joint: default '', the parameter for joining back the reformatted line in a_list
do_left_just: default True, left justify each column, if False, then right justify
do_rstrip: default False, strip all trailing whitespace and append CR if found per line in a_list
Usage: pretty_list = pretty_format(a_list, ':', ':', do_rstrip=True)
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
 '''
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
    if do_rstrip:
        c_list = [ strip_tw(a_row) for a_row in c_list ]
    return c_list

def mk_vertical(a_list, seperator=''):
    '''mk_vertical(a_list[, seperator=''])
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
'''
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

def force_column_width(a_list, num_per_row, delimeter=', ', prefix=''):
    '''limit the number of elements in a list to a set number per row, i.e.
    from a pinlist, just print up to 12 pins per row'''
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

def _list_copy(srcList, destList, overwrite=0):
    '''usage: _list_copy(srcList, destList[, overwrite] where: overwrite defaults to 0, append items from srcList to destList if not
already in destList'''
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
    '''usage: _list_intersect(srcList, destList) update destList with the intersection of itself and srcList'''
    diffList = list(set(destList).difference(set(srcList)))
    _list_reduce(diffList, destList)

def _list_add(srcList, destList):
    '''usage: _list_add(srcList, destList) append items from srcList that are not in destList'''
    a_dict = dict([(a, i) for i, a in enumerate(srcList)])
    i_dict = dict([(i, a) for a, i in a_dict.iteritems() ])
    a_set = set(srcList)
    for a in destList: a_set.discard(a)
    diffList = [ i_dict[a_] for a_ in sorted(a_dict[a] for a in a_set) ]
    destList += diffList

def _list_reduce(srcList, destList):
    '''usage: _list_reduce(srcList, destList) Remove items (all occurences) from destList that are in srcList'''
    a_dict = dict([(a, i) for i, a in enumerate(destList)])
    i_dict = dict([(i, a) for a, i in a_dict.iteritems() ])
    a_set = set(destList).intersection(set(srcList))
    for a_ in reversed(sorted(a_dict[a] for a in a_set)): destList.pop(a_)

def _dictionary_copy(srcDict, destDict):
    '''usage: _dictionary_copy(srcDict, destDict) add dictionary key:value pairs that aren't present in destDict from srcDict'''
    for aKey in srcDict:
        try:
            destDict.update({aKey:srcDict[aKey].copy()}) # dicts, sets
        except AttributeError:
            try:
                destDict.update({aKey:srcDict[aKey][:]}) # list, tuples, strings, unicode
            except TypeError:
                destDict.update({aKey:srcDict[aKey]}) # ints

def _dictionary_reduce(srcDict, destDict):
    '''usage: _dictionary_reduce(srcDict, destDict) reduce key value list from destDict that are in srcDict'''
    list_type = type([1, 2, 34])
    for aKey in srcDict:
        if destDict.has_key(aKey):
            _list_reduce(srcDict[aKey], destDict[aKey])
            if type(destDict[aKey]) == list_type and destDict[aKey] == []:
                destDict.__delitem__(aKey)

class FileStats(object):
    '''Determine if namespace passed in is a file or directory.
    TimeStamp(): return time stamp of namespace creation
    self.dir: directory path of namespace
    self.file: leaf name with directory path removed'''
    
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
        creation_time = int(self.nm_stats[6].replace(':', ''))
        if 100*month+day > 100*self._Month2Number(commands.getoutput('date +"%b"'))+int(commands.getoutput('date +"%d"')):
                year = year-1
        timestamp = float(10000.*year+100.*month+1.*day+creation_time/10000.)
        return(timestamp)

class FileUtils(FileStats):
    '''a_file = FileUtils(file_name)
    File operations such as is_file, is_path_relative, make_absolute_path, append_to_file
    File info such as timestamps, dir path and filename'''
    def __init__(self, file_name, do_read=False):
        super(FileUtils, self).__init__(file_name)
        self._open_file_function, self.contents = open,[]
        if do_read: self.read_from_file()
        else: self.eval_file_size()
    def eval_file_size(self):
        #if commands.getoutput('file '+file_name).find('gzip') == -1 or self.file.find('gz') == -1:
        self.file_size = None
        s = SysCommand('file %s'%self.nm)
        self.file_is_gzipped = in_list(s.output, 'gzip compressed data') or in_list(self.nm, 'gzi?p?$')
        if not self.file_is_gzipped:
            if self.is_file():
                stat = os.stat(self.nm)
                self.file_size = int(stat.st_size)
            self._open_file_function = open
        else:
            if self.is_file():
                try:
                    s = SysCommand('gzip -l %s'%self.nm)
                    self.gzip_file_info = dict([(a_key, a_value) for a_key, a_value in zip(s.output[0].split(), s.output[-1].split())])
                    self.file_size = int(self.gzip_file_info['uncompressed'])
                except:
                    print 'Uh oh, this was only tested in linux, may not work in microsoft windows, probably a gzip issue'
                    raise
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
        self.write_to_file(aList, 'ab' if self.file_is_gzipped else 'a')
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
                b_iter = ( '%s%s'%(a_line, '' if a_line.find('\n')>-1 else '\n') for a_line in a_iter)
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

class SysCommand:
    def __init__(self, cmd=''):
        pipe = os.popen('{ '+cmd+';} 2>&1', 'r') 
        self.output = [ a_line.strip() for a_line in pipe.read().splitlines() ] 
        self.sts = pipe.close()

class m_grep(object):
    '''usage: 
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
    Note: back-slashes need to be doubled for compiled expresion, i.e \b -> \\b '''
    
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
        a_string, col_list = a_line,[]
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
        '''Pass in a list which may consist of strings and/or tuples.  Expand out each tuple to list element members. '''
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
        '''clear all grep results for this instance of my_grep'''
        self.m, self.coordinates, self.m_groups, self.lines, self.pattern_count=[],[],[],[], 0

class m_re(m_grep):
    '''wrapper class for re, some useful functions like replacing a pattern
       with a replacement, i.e. "_C84" -> "_relay", i.e. a_string = "NSTANDBY_C91+NSTANDBY_C92+A_BYP_C4+PVDD_CAP_C26", so,
       the search_pattern=re.compile('(?P<id>\w+)C\d+') and replacement string would be '\g<id>relay', thus the
       result would be "NSTANDBY_relay+NSTANDBY_relay+A_BYP_relay+PVDD_CAP_relay"
       or change upper case to lower case
    '''
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

class CaptureBlocks(object):
    '''usage: c = CaptureBlocks(all_lines,block_start_string,block_stop_string,start_phrase)
Use escape character \ for special characters, like *, (, and ), when doing this,
set start_phrase to appropriate value, such as ( or if blocking out preproccessor statements, like
#if 0, then 0, or in the case of a field entry, like vector (...., then set start_phrase to vector.
start_phrase should be a substring of block_start'''
    def __init__(self,all_lines, block_start='{', block_stop = '}', start_phrase=''):
        self.all_lines = all_lines
        self.start_pts, self.end_pts = [], []
        if start_phrase == '': start_phrase = block_start.replace('\\','')
        self.block_start, self.block_stop, self.start_phrase = block_start, block_stop, start_phrase
        self.g = m_grep(self.all_lines)
        if block_start == '/\*':
            self.comment_block(self.all_lines, self.block_start,self.block_stop)
        else:
            self.capture_block(self.all_lines, self.block_start, self.block_stop, start_phrase)
    def comment_block(self,all_lines,block_start='/\*', block_stop='\*/',start_phrase='/*'):
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
            Null = [ (self.g.m_groups.pop(index),self.g.coordinates.pop(index)) for index in indices ]
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
                        print "g.pattern_count: ",self.g.pattern_count," i: ",i," closed: ", closed," start_phrase: ", start_phrase
                        print "last start_pt: ",self.start_pts[-2]," and stop_pt: ",self.end_pts[-1]
                        print "current start_pt: ",self.start_pts[-1]
                        if (i-1) in range(len(g.coordinates)) and (i-1) in range(len(g.m_groups)):
                            print g.coordinates[i-1],': ',g.m_groups[i-1]
                        # index -1, skips escape character, \, needed for grep function
                        closed = 0
                        i = self.g.pattern_count
                self.end_pts.append(int(float(self.g.coordinates[i])) )
            i += 1
    def specific_block(self,block_start,block_stop,start_phrase):
        self.g.clear_cache()
        self.g.grep(block_start)
        self.end_pts, self.start_pts = [], [ int(float(i))-1 for i in self.g.coordinates ]
        for start_pt in self.start_pts:
            closed,i = self.all_lines[start_pt].count(start_phrase), start_pt
            while closed != 0:
                i += 1
                try:
                    closed += self.all_lines[i].count(start_phrase) - self.all_lines[i].count(block_stop)
                except IndexError:
                    print "Exceeded last line of file"
            self.end_pts.append(i+1)
    def capture_block(self,all_lines,block_start='{', block_stop='}',start_phrase='{'):
        self.g.clear_cache()
        self.start_pts, self.end_pts = [], []
        if in_list(all_lines,block_start) and in_list(all_lines,block_stop):
            self.g.grep('(%s|%s|%s)'%(block_start,block_stop,start_phrase))
            search_start_pattern = re.compile(block_start)
            search_stop_pattern = re.compile(block_stop)
            start_stop_iter = self._process_engine(all_lines,self.g,search_start_pattern,search_stop_pattern,start_phrase)
            for start,stop in start_stop_iter:
                self.start_pts.append(start)
                self.end_pts.append(stop)
        else:
            pass
    def _process_engine(self,all_lines,g,search_start_pattern,search_stop_pattern,start_phrase):
        '''yield: start_pt and end_pt, '''
        i=0
        while i < self.g.pattern_count:
            start_pt, end_pt = None,None
            m = search_start_pattern.search(g.m_groups[i])
            if m != None:
                closed = g.m_groups[i].count(m.group())
                start_pt = int(float(g.coordinates[i]))-1
                while closed != 0:
                    i += 1  # what happens if block_start and block_stop are on the same line?
                    try:
                        m_stop = re.search(search_stop_pattern,self.g.m_groups[i])
                        #closed += self.g.m_groups[i].count(start_phrase) - self.g.m_groups[i].count(block_stop.replace('\\',''))
                        closed += g.m_groups[i].count(start_phrase)
                        if m_stop != None: closed -= g.m_groups[i].count(m_stop.group())
                    except IndexError:
                        print "g.pattern_count: ",g.pattern_count," i: ",i," closed: ", closed," start_phrase: ", start_phrase
                        print "current start_pt: ",start_pt
                        if (i-1) in range(len(g.coordinates)) and (i-1) in range(len(g.m_groups)):
                            print g.coordinates[i-1],': ',g.m_groups[i-1]
                        # index -1, skips escape character, \, needed for grep function
                        closed = 0
                        i = self.g.pattern_count
                end_pt = int(float(g.coordinates[i] if i in xrange(len(g.coordinates)) else -1))
                yield (start_pt,end_pt)
            i += 1
    def old_capture_block(self,all_lines,block_start='{', block_stop='}',start_phrase='{'):
        self.g.clear_cache()
        self.start_pts, self.end_pts = [], []
        self.g.grep('('+block_start+'|'+block_stop+'|'+start_phrase+')')
        search_start_pattern = re.compile(block_start)
        search_stop_pattern = re.compile(block_stop)
        i = 0
        while i < self.g.pattern_count:
            m = re.search(search_start_pattern,self.g.m_groups[i])
            if m != None:
                closed = self.g.m_groups[i].count(m.group())
                self.start_pts.append(int(float(self.g.coordinates[i]))-1 )
                while closed != 0:
                    i += 1  # what happens if block_start and block_stop are on the same line?
                    try:
                        m_stop = re.search(search_stop_pattern,self.g.m_groups[i])
                        #closed += self.g.m_groups[i].count(start_phrase) - self.g.m_groups[i].count(block_stop.replace('\\',''))
                        closed += self.g.m_groups[i].count(start_phrase)
                        if m_stop != None: closed -= self.g.m_groups[i].count(m_stop.group())
                    except IndexError:
                        print "g.pattern_count: ",self.g.pattern_count," i: ",i," closed: ", closed," start_phrase: ", start_phrase
                        print "last start_pt: ",self.start_pts[-2]," and stop_pt: ",self.end_pts[-1]
                        print "current start_pt: ",self.start_pts[-1]
                        print self.g.coordinates[i-1],': ',self.g.m_groups[i-1]
                        raise
                        # index -1, skips escape character, \, needed for grep function
                self.end_pts.append(int(float(self.g.coordinates[i])) )
            i += 1


class GetFileListing:
    def __init__(self,file_pattern='', ls_opts=''):
        self.cmd = ' '.join(['ls',ls_opts,file_pattern])
        self.sys_cmd = SysCommand(self.cmd)
        self.output = self.sys_cmd.output


class Profiler:
    def __init__(self):
        self.reset_time_parameters()

    def snap(self):
        self.prev_snap_time = self.snap_time
        self.snap_time = time()
        self.snap_interval = self.snap_time - self.prev_snap_time
        return(self.snap_interval)

    def get_overall_elapsed_time(self,start_time=None):
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


class InfiniteCounter:
    def __init__(self,start=0):
        self.cur = start

    def __iter__(self):
        return(self)

    def next(self):
        self.cur += 1
        return self.cur

