import util
import random
import mmap,os,re
from mmap import ACCESS_READ,ACCESS_COPY,ACCESS_WRITE
import tkFont
from GUI.my_tkinter import append_to_list_box,fill_list_box,append_to_text_box,delete_from_list_box, \
    add_to_list_box,move_up_in_list_box, move_down_in_list_box,get_selection,add_cr,selection_index_list, \
    set_button_state
'''
reload(da)
r = util.FileUtils('/tmp/tim')
t = da.EnvisionAsciiDlogAnalysis('/tmp/bob')
t.BuildStatsTable(test_list,4)  # 4 is the number of sites
r.write_to_file(util.pretty_format(t.PrintRecords(test_list),'\t',''))

a = da.PrepAsciiDlogFile('/tmp/bob')
t = da.TestAnalysis(a.test_records,5.,90.,[3,4,5,6])

'''
#helper classes/functions
class CreateDlogChunksByTestRunIndex(object):
    '''take a file list of ascii dlogs, break each file down into chunks by test run index
    return the start and stop offset(s) of TRI for each file
    Note: TRI or tri is short for test run index'''
    pm = util.Profiler()
    def __init__(self,file_list,test_line_pattern='^Test_No\.',tri_start_device_results_pattern='^Device\s+Results:'):
        self.pm_info = []
        self.pm.snap()
        loop_start_time = self.pm.snap_time
        self.file_list = [file_list] if isinstance(file_list,str) else file_list
        self.test_line_pattern,self.tri_start_device_results_pattern = test_line_pattern,tri_start_device_results_pattern
        self.LoopThruFiles(self.file_list)
        self.pm_info.append(' + Total Processing Time: %f'%(self.pm.snap_time-loop_start_time))

    def LoopThruFiles(self,file_list):
        self.mmap_dict = {}
        for a_file in file_list:
            a_dict = {'mmap_obj':None,'tri_offsets':[]}
            f = util.FileUtils(a_file)
            fh = f._open_file(a_file,'r+')
            a_dict.update({'mmap_obj':util.mmap_utils(**dict([('fileno',fh.fileno()),('length',f.file_size),('access',mmap.ACCESS_READ)]))})
            self.pm_info.append(' + Initialize mmap_obj for %s: %f'%(a_file,self.pm.snap()))
            start_offsets,stop_offsets = self.SplitDlogByTestRunIndex(a_dict['mmap_obj'],self.test_line_pattern,self.tri_start_device_results_pattern)
            a_dict.update({'tri_offsets':[(start,stop) for start,stop in zip(start_offsets,stop_offsets)]})
            self.pm_info.append(' + Get TRI offsets for %s: %f'%(a_file,self.pm.snap()))
            self.mmap_dict.update({a_file:a_dict})
    def SplitDlogByTestRunIndex(self,mm,test_line_pattern='^Test_No\.',tri_start_device_results_pattern='^Device\s+Results:'):
        mm.get_newline_offsets()
        end_pts_offsets,start_pts_offsets = [],[]
        if  mm.in_map(tri_start_device_results_pattern,offset=0):
            next_offset = mm.newline_offsets[mm.newline_offsets_hash_table[mm.tell()]-1]
            while mm.tell()<mm.map_size:
                current_offset = next_offset
                if mm.in_map('%s|^\s*$'%test_line_pattern,offset = current_offset):
                    end_offset = mm.newline_offsets[mm.newline_offsets_hash_table[mm.tell()]-1]
                else:
                    end_offset = mm.newline_offsets[-1]
                end_pts_offsets.append(end_offset)
                #look ahead for next TRI
                if mm.in_map(tri_start_device_results_pattern,offset=end_offset):
                    next_offset = mm.newline_offsets[mm.newline_offsets_hash_table[mm.tell()]-1]
                    # make sure we have test(s) before next_offset
                    if mm.in_map(test_line_pattern,offset=end_offset): mm.seek(next_offset)
                    else: mm.seek(0,os.SEEK_END) #redundant, should already be there....
        else:
            end_pts_offsets.append(mm.newline_offsets[-1])
        start_pts_offsets = [0]+[end_offset for end_offset in end_pts_offsets[:-1] ] if len(end_pts_offsets)>1 else [0]
        return(start_pts_offsets,end_pts_offsets)


def SplitDlogByTestRunIndex(dlog_file,dest_path='/tmp'):
    pm = util.Profiler()
    pm.snap()
    start_time = pm.snap_time
    f = util.FileUtils(dlog_file)
    fh = f._open_file(dlog_file,'r+')
    cm_kwargs = dict([('fileno',fh.fileno()),('length',f.file_size),('access',mmap.ACCESS_READ)])
    map_copy = util.mmap_utils(**cm_kwargs)
    print ' + Initializing mmap object of dlog file: %f'%pm.snap()
    map_copy.get_newline_offsets()
    print ' + Getting newline offsets from master dlog file: %f'%pm.snap()
    map_copy.keep_in_list('^Device\s+Results:',offset=0)
    print ' + Grepped out Device Results to TRI stops: %f'%pm.snap()
    end_pts_offsets = []
    for i in map_copy.g_coordinates_iter:
        map_copy.seek(map_copy.newline_offsets[i])
        pattern_found,a_pattern = False,'^Test_No\.|^\s*$'
        while map_copy.tell()<map_copy.map_size and not pattern_found:
            pattern_found = util.in_list(map_copy.readline(),a_pattern)
        if pattern_found: end_pts_offsets.append(map_copy.tell())
    start_pts_offsets = [0]+end_pts_offsets[:-1]
    end_pts_offsets[-1] = map_copy.newline_offsets[-1]
    print ' + Determined start and stop offsets of master dlog file: %f'%pm.snap()
    #break up the dlog by test run
    a_path,base_file = os.path.split(dlog_file)
    for i,start,stop in zip(util.InfiniteCounter(),start_pts_offsets,end_pts_offsets):
        map_copy.seek(start)
        a_list = []
        while map_copy.tell() < stop:
            a_list.append(map_copy.readline())
        f = util.FileUtils('/tmp/%s_TRI_%03d%s'%\
            ('.'.join(base_file.split('.')[:-1]),\
            i,'%s'%('.%s'%base_file.split('.')[-1] if util.find_index(base_file,'.')>-1 else '')))
        f.write_to_file('bogus')
        fh = f._open_file(f.nm,'r+')
        mm = util.mmap_utils(**{'fileno':fh.fileno(),'length':f.file_size})
        mm.resize(sum(len(a_row) for a_row in a_list))
        mm.write_lines(a_list,offset=0)
        mm.flush()
        mm.close()
        fh.close()
        print ' ++ Finished working on file index TRI: %d, time elapsed: %f'%(i,pm.snap())
    print ' + Total processing time: %f'%(pm.snap_time - start_time)


def iter_insert_blanks(a_iter,a_pattern=''):
    for a_line in a_iter:
        if util.in_list(a_line,a_pattern):
            yield ['\n',a_line]
        else: yield a_line


def get_span_brackets(span_line,search_exp='-\s',offset=-1):
    '''get the bracket pts of a string based on a search expression
    i.e. span_line = "--------  ---  ----  ----  ------------------            ----------------\n"
    would return a tuple set: [(0, 8), (8, 13), (13, 19), (19, 25), (25, 45), (45, 74)]'''
    cb = util.m_re(span_line)
    cb.grep(search_exp)
    start_pts = [0]+[int(a_coord.split('.')[-1])+offset+len(a_group) for a_coord,a_group in zip(cb.coordinates[:-1],cb.m_groups) ]
    end_pts = [int(a_coord.split('.')[-1])+offset+len(a_group) for a_coord,a_group in zip(cb.coordinates[:-1],cb.m_groups) ]+[len(span_line)]
    return zip(start_pts,end_pts)


def check_dlog_record_fits_header_span(dlog_line,header_span_list,dlog_field_boundry_exp='\w\s',span_boundry_exp='\s-'):
    '''Determine, which header_span the dlog_record fits, if any. 
    Return the matching header_span, the index of the header_span_list'''
    dline_brackets = get_span_brackets(dlog_line,dlog_field_boundry_exp)
    # move start_pt at beginning of first letter for each section of dlog_line
    for i,(start,end) in zip(util.InfiniteCounter(start=0),dline_brackets[1:]):
        m = re.match(re.compile('^\s+'),dlog_line[start:end])
        if m: dline_brackets[i] = (start+m.end(),end)
    fit_found = False
    for i,header_span in enumerate(header_span_list):
        span_brackets = get_span_brackets(header_span,span_boundry_exp)
        if brackets_line_up(dline_brackets,span_brackets): 
            fit_found = True
            break
    return ('',-1) if not fit_found else (header_span,i)


def replace_leading_whitespace(a_line,new_str='S'):
    '''Replace leading white space with new_str, for each space'''
    lw = re.match(re.compile('^\s+'),a_line)
    if lw: #replace leading whitespace of a_line with 'S'
        prefix = re.sub(re.compile('\s'),'S',lw.group())
        a_line = prefix+a_line[len(prefix):]
    return a_line


def brackets_line_up(a_brackets_set,b_brackets_set,last_bracket_chk_start_boundry=True):
    '''See if a_brackets_set fits within b_brackets_set, for last bracket_set, check the start boundry
    only since the end boundry is the end of the line.  Disable that condition by setting 
    last_bracket_chk_start_boundry = False'''
    a_fits_b = lambda a1,a2,b1,b2 : (a1>=b1 and a1<=b2) and (a2>=b1 and a2<=b2) 
    if len(a_brackets_set)<len(b_brackets_set):
        new_a_brackets_set,new_b_brackets_set = [],[]
        for i,(a1,a2) in enumerate(a_brackets_set):
            for j,(b1,b2) in enumerate(b_brackets_set):
                if a_fits_b(a1,a2,b1,b2):
                    new_a_brackets_set.append((a1,a2))
                    new_b_brackets_set.append((b1,b2))
                    break
        if last_bracket_chk_start_boundry and (i==len(a_brackets_set)-1 and j==len(b_brackets_set)-1):
            new_a_brackets_set.append(a_brackets_set[-1])
            new_b_brackets_set.append(b_brackets_set[-1])
        a_brackets_set,b_brackets_set = new_a_brackets_set,new_b_brackets_set
    chk_each_fits = [ a_fits_b(a_start,a_stop,b_start,b_stop) for (a_start,a_stop),(b_start,b_stop) in zip(a_brackets_set,b_brackets_set) ]
    if last_bracket_chk_start_boundry and not chk_each_fits[-1]: 
        chk_each_fits[-1] = a_brackets_set[-1][0] >= b_brackets_set[-1][0]
    return min(chk_each_fits) and max(chk_each_fits)


#dlog specific classes
class PrepAsciiDlogFile(object):
    '''Prep one or more ascii dlog file for analysis by splitting out the fields, enter the ascii dlog file list as first argument 
      i.e. a = PrepAsciiDlogFile(file_list,(start,stop),delimeter,keep_fails)
      where: file_list is a list of one or more ascii output dlog files
             start,stop defaults to (0,-1), is a tuple, with a start and stop pair indices that are applied to all files 
                in the file list, usually only set this for a single file of interest, or where you may have an interest 
                of 1 out of multiple test runs in the file
             delimeter defaults to "|", another good choice would be "," for csv format and easy import to a spreadsheet app
             keep_fails defaults to False, which skips all failing records.  Set to True to keep all records'''
    site_specific_result_header='Test_No.    P/F  Site  Minimum        Measured       Maximum        Pin_Name               Test_Description'
    site_specific_result_span='----------  ---  ----  -------------  -------------  -------------  ---------------------  --------------------------------------------------'
    pm = util.Profiler()

    def __init__(self,file_list,start_stop=(0,-1),delimeter=',',test_num_iter=10,keep_fails=False,stdout=None):
        '''Useful debug trick, pass in file_list as []'''
        self.Delimeter, self.keep_fails, self.test_num_iter = delimeter, keep_fails, test_num_iter
        self.file_list = [file_list] if isinstance(file_list,str) else file_list
        self.stdout = stdout
        self.stdout_function = self.pretty_print_wrapper if not stdout else self.append_to_console
        self.pm_info = []
        self.pm.snap()
        start_time = self.pm.snap_time
        if len(self.file_list)>0:
            self.TestDlogDict = self.PopulateTestDict(self.file_list)
        self.pm.snap()
        self.pm_info.append('Finshed building TestDlogDict: %f'%(self.pm.snap_time - start_time))
        self.stdout_function(self.pm_info[-1])

    def Reformat(self,mm,l_start,l_stop,delimeter='|'):
        self.pm.snap()
        test_dict = {}
        mm.keep_in_list('^Test_No\.',length=l_stop,offset=l_start)
        start_tri = mm.newline_offsets_hash_table[l_start]
        stop_tri = mm.newline_offsets_hash_table[l_stop] - start_tri
        start_indices = list(mm.g_coordinates_iter) #local indices for this test run index block (tri)
        start_pts = [mm.newline_offsets[i+start_tri] for i in start_indices]
        end_indices = [ a_num for a_num in start_indices[1:] ] + [stop_tri-1] #local indices for this test run index block (tri)
        end_pts = [ mm.newline_offsets[i+start_tri] for i in end_indices ]
        c_list, b_list = [],[]
        self.pm_info.append(' ++ Reformat: + Getting start and stop pts for subsections: %f'%self.pm.snap())
        subsection_start_time = self.pm.snap_time
        #toi = util.keep_in_list_coordinates(a_list,'FBS_ML_PBIST1P_FMAX_F').pop() #toi = test of interest
        #start,stop = [ (start,stop) for start,stop in zip(start_pts,end_pts) if start<=toi and stop>=toi ].pop()
        #bak_a_list = [ a_row for a_row in a_list ]
        # arg_list = [ (start,stop) for start,stop in zip(start_pts,end_pts) ]
        # start,stop = arg_list[0]
        for start,stop in zip(start_pts,end_pts):
            loop_start_time = self.pm.snap_time
            header = mm.readline_from_offset(start)
            field_span = mm.readline()
            sub_b_list = list(mm.read_lines_iter(length=stop))
            field_span_brackets = get_span_brackets(field_span,'-[\s$]')
            self.pm_info.append(' ++ Reformat: ++ loop %d-%d: Field start and stop pts: %f'%(start,stop,self.pm.snap()))
            g_iter = util.grep_iterator()
            g_coordinates_iter,g_lines_iter,g_lengths_iter = util.iscatter(g_iter.grep(iter(sub_b_list),'^\s*\d+\s+(?:\*?F\*?|P)?\s+\d+\s+',True),3)
            g_lines = util.keep_in_list(sub_b_list,'^\s*\d+\s+(?:\*?F\*?|P)?\s+\d+\s+')
            self.pm_info.append(' ++ Reformat: ++ loop %d-%d: Setup and Grep out dlog lines from subsection: %f'%(start,stop,self.pm.snap()))
            field_span_slices = [slice(a,b) for a,b in field_span_brackets[:-1]]+[slice(field_span_brackets[-1][0],-1)]
            sub_c_list = [ delimeter.join([a_line[a_slice] for a_slice in field_span_slices ]) for a_line in g_lines ]
            sub_b_list = [ ['%s'%a_field.strip() for a_field in util.my_split(a_line,delimeter)] for a_line in sub_c_list ]
            #knock off lines that don't start with a valid test number... i.e. if you have something like:
            #  3    771770    70    7b11d7  0019  0000  0000    0xfffe
            #  4771770771770    707b11d77b11d7  0019  0000  0000    0xfffe
            #  Running Test Number 0x80120400 
            #  Running Test Number PMEX 0x80120400
            sub_b_list = [ a_row for a_row in sub_b_list if not util.in_list(a_row[0].strip(),'[^\d]') ]
            self.pm_info.append(' ++ Reformat: ++ loop %d-%d: Filter out invalid dlog lines: %f'%(start,stop,self.pm.snap()))
            b_list += sub_b_list
            c_list += sub_c_list
            self.pm_info.append(' ++ Reformat: ++ loop %d-%d: Loop Finished: %f'%(start,stop,self.pm.snap_time-loop_start_time))
        self.pm_info.append(' ++ Reformat: + Done looping through and formatting dlog subsections: %f'%(self.pm.snap_time-subsection_start_time))
        # specific with respect to LTXC ascii dlog format
        # -- bak_b_list = [ a_line for a_line in b_list ]
        # -- b_list = [ a_line for a_line in bak_b_list ]
        subsection_start_time = self.pm.snap_time # -- delete line? or reset profile parameter
        # site results not merged yet, every dlog record has following uniform format:
        #Name :Test_No. :P/F:Site:Minimum:Maximum:Result:Pin_Name:Test_Description
        #Field:0        :1  :2   :3      :4      :5     :6       :7
        test_number_field_value,site_field_value,result_field_value,pin_field_value,comment_field_start = 0,2,4,6,7
        lower_limit_field_value,upper_limit_field_value = 3,5
        #append test number to comment
        b_list = [ a_row[:pin_field_value]+ \
            [a_row[pin_field_value] if len(a_row[pin_field_value])>0 else '']+[ \
            '%s TestNumber->%s'%('->'.join([ a_param for a_param in a_row[comment_field_start:]]),\
            a_row[test_number_field_value])] \
            for a_row in b_list ]
        comment_field_value = comment_field_start # lumped pin field with test description field
        m = util.mmap_utils(**{'fileno':-1,'length':sum(len('%s\n'%';'.join(a_row)) for a_row in b_list)})
        m.write_lines(iter('%s\n'%';'.join(a_row) for a_row in b_list))
        m.sort_by(fields=[site_field_value,test_number_field_value,comment_field_value,pin_field_value],delim=';', joint=delimeter,offset=0,WriteBack=False)
        sorted_b_list = [ a_row.rstrip().split(delimeter) for a_row in m.sortList ]
        self.pm_info.append(' ++ Reformat: + Sort based on site,test num, and description: %f'%(self.pm.snap_time-subsection_start_time))
        # dlog sorted by site, test number, and then test description
        # break up into dict per site, look for duplicate test numbers
        subsection_start_time = self.pm.snap_time # -- delete line? or reset profile parameter
        site_dict = dict( [ (a_site,[]) for a_site in \
            util.sort_unique([ int(a_row[2]) for a_row in sorted_b_list])])
        site_list = [ a_site for a_site in sorted(site_dict.iterkeys()) ]
        coordinates_list=[]
        start_index = 0
        for a_site in site_list[1:]:
            next_site_index = util.find_index(m.sortList[start_index:],'^\d+%s(?:P|\*F\*)%s%d'%(delimeter,delimeter,a_site))
            coordinates_list.append((start_index,next_site_index+start_index if next_site_index > -1 else -1))
            start_index = next_site_index+start_index if next_site_index > -1 else -1
        coordinates_list.append((start_index,len(m.sortList)))
        for a_site,start_stop in zip(site_list,coordinates_list): 
            start,stop = start_stop
            site_dict.update({a_site:sorted_b_list[start:stop]})
        self.pm.snap()
        self.pm_info.append(' ++ Reformat: + Create site dict, key for each site with results list: %f'%(self.pm.snap_time-subsection_start_time))
        self.pm_info.append(' ++ Reformat: INFO:: + Site Dict: NumSites: %d'%len(site_dict.keys()))
        bob = [ self.pm_info.append(' ++ Reformat: INFO:: ++ Site Dict: Site %d: NumTests %d'%(a_site,len(results_list))) for a_site,results_list in site_dict.iteritems() ]
        # now look for duplicate test numbers before merging site results
        subsection_start_time = self.pm.snap_time # -- delete line? or reset profile parameter
        duplicate_numbers,test_numbers = [],[]
        for a_site,results_list in site_dict.iteritems():
            self.pm.snap()
            loop_start = self.pm.snap_time
            site_test_numbers = [ int(a_row[0]) for a_row in results_list ]
            site_duplicate_numbers = util.sort_unique([ a_num for a_num,next_num in zip(site_test_numbers[:-1],site_test_numbers[1:]) if (next_num-a_num)==0])
            duplicate_numbers += [ a_num for a_num in site_duplicate_numbers if not a_num in duplicate_numbers ]
            test_numbers += [ a_num for a_num in site_test_numbers if not a_num in test_numbers ]
        duplicate_numbers = sorted(duplicate_numbers)
        test_numbers = sorted(test_numbers)
        self.pm.snap()
        self.pm_info.append(' ++ Reformat: + Generate test number list and duplicates: %f'%(self.pm.snap_time-subsection_start_time))
        #have test_numbers sorted, and a list of duplicate test numbers, if any
        duplicates_start_time = self.pm.snap_time
        if len(duplicate_numbers)>0:
            # make a list without the duplicate test number(s)
            t_list = [ int(a_num) for a_num in test_numbers if a_num not in duplicate_numbers ]
            self.pm_info.append(' ++ Reformat: ++ Generate t_list, without the duplicates: %f'%self.pm.snap())
            num_iter = self.test_num_iter #int( (max(t_list)-min(t_list) )/( len(t_list) )/10 )
            #num_iter -= num_iter %10
            self.pm_info.append(' ++ Reformat: ++ Setup m_re for grepping off test numbers: %f'%self.pm.snap())
            for a_num in duplicate_numbers:
                loop_duplicate_numbers_start_time = self.pm.snap_time
                index_list = util.keep_in_list_coordinates(['%d'%i for i in test_numbers],'\\b%d\\b'%a_num)
                self.pm_info.append(' ++ Reformat: +++ Grep duplicate number, %d: %f'%(int(a_num),self.pm.snap()))
                a_test_number = a_num
                t_list.append(int(a_test_number))
                new_test_numbers = self.MakeDifferentTestNumber(a_num,[i for i in test_numbers],index_list[1:],num_iter) 
                self.pm_info.append(' ++ Reformat: +++ MakeDifferentTestNumber: %f'%self.pm.snap())
                # need to implement the number change for each site's results_list in site_dict
                for a_site,results_list in site_dict.iteritems():
                    site_loop_time = self.pm.snap_time
                    if len(new_test_numbers)>0 and util.in_list([';'.join(a_row) for a_row in results_list ],'^%d;'%a_test_number):
                        sub_b_list = [';'.join(a_row) for a_row in results_list ]
                        g_coordinates = util.keep_in_list_coordinates(sub_b_list,'^%d;'%a_test_number)
                        for i,a_coordinate in enumerate(g_coordinates[1:]):
                            results_list[a_coordinate][test_number_field_value] = '%d'%int(new_test_numbers[i])
                            results_list[a_coordinate][-1] += ' DUPE%04d:%d'%(i+1,int(a_test_number))
                            self.pm_info.append(' ++ Reformat: +++++ Implement NewTestNumber %d: %f'%(int(new_test_numbers[i]),self.pm.snap()))
                        site_dict.update({a_site:results_list})
                    else: self.pm.snap()
                    self.pm_info.append(' ++ Reformat: ++++ Processed TestNumberChange Site %d: %f'%(a_site,self.pm.snap_time-site_loop_time))
                self.pm_info.append(' ++ Reformat: +++ Implement TestNumberChange: %f'%(self.pm.snap_time-loop_duplicate_numbers_start_time))
        self.pm.snap()
        self.pm_info.append(' ++ Reformat: + Processed through duplicates: %f'%(self.pm.snap_time-duplicates_start_time))
        new_b_list, new_c_list = [], []
        for a_site,results_list in site_dict.iteritems(): 
            new_c_list += [ delimeter.join(a_row) for a_row in results_list ]
            # -- new_b_list += results_list #really for debug, can pull out
        m = util.mmap_utils(**{'fileno':-1,'length':sum(len('%s\n'%a_row) for a_row in new_c_list)})
        m.write_lines(util.add_cr_iter(new_c_list))
        m.sort_by(fields=[test_number_field_value,site_field_value],delim=delimeter,joint=delimeter,offset=0,WriteBack=False)
        new_b_list = [ a_row.rstrip().split(delimeter) for a_row in m.sortList ]
        new_test_numbers = util.sort_unique([ int(a_row[0]) for a_row in new_b_list ])
        self.pm_info.append(' ++ Reformat: + Sort by test number, then site: %f'%self.pm.snap())
        #group tests by number, to merge site results to single record
        coordinates_list=[]
        start_index = 0
        for a_num in new_test_numbers[1:]:
            next_index = util.find_index(m.sortList[start_index:],'^%d'%a_num)
            coordinates_list.append((start_index,next_index+start_index if next_index > -1 else -1))
            start_index = next_index+start_index if next_index > -1 else -1
        coordinates_list.append((start_index,len(m.sortList)))
        self.pm_info.append(' ++ Reformat: + Merge site results to single record: %f'%self.pm.snap())
        #initialize test_dict
        record_fields = 'Test_No. Minimum Maximum Pin_Name Test_Description'.split() 
        record_indices = [test_number_field_value,lower_limit_field_value,upper_limit_field_value,pin_field_value,comment_field_value]
        result_fields = [ 'Site%d'%a_site for a_site in site_list ]
        test_dict = dict([ (a_num,dict([(a_field,'') for a_field in iter(record_fields+result_fields)])) for a_num in new_test_numbers ])
        self.pm_info.append(' ++ Reformat: + Initialize test_dict: %f'%self.pm.snap())
        #build TestDlogDict
        for a_num,start_stop in zip(new_test_numbers,coordinates_list): 
            start,stop = start_stop
            results_list = new_b_list[start:stop]
            record_dict = dict([ ('Site%d'%int(a_row[site_field_value]),a_row[result_field_value]) for a_row in results_list ])
            record_dict.update(dict([(a_field,results_list[0][i]) for a_field,i in zip(record_fields,record_indices)]))
            test_dict[a_num].update(record_dict)
        self.pm_info.append(' ++ Reformat: + Populate test_dict: %f'%self.pm.snap())
        #flatten out to b_list
        all_record_fields = 'Test_No. Minimum Maximum'.split() + result_fields + ' Pin_Name Test_Description'.split() 
        b_list = [ [test_dict[a_num][a_field] for a_field in all_record_fields] for a_num in new_test_numbers ]
        header = '  :  '.join(['Test_No.  ','Minimum  ','Maximum  ']+['Site%s    '%a_site for a_site in site_list]+['Pin_Name    ','Test_Description    '])
        for i,a_row in enumerate(b_list):
            for j,a_field in enumerate(a_row):
                if len(a_field)==0: b_list[i][j] = '    '
        c_list = util.pretty_format([header]+[ ' : '.join(['%s'%a_field for a_field in a_row]) for a_row in b_list ],' : ',delimeter,do_rstrip=True)
        self.pm_info.append(' ++ Reformat: + Generate list of reformatted dlog: %f'%self.pm.snap())
        test_dict.update({'DlogKeys':[ a_field.strip() for a_field in util.my_split(header,'  :  ')]})
        self.pm_info.append(' ++ Reformat: + Update test_dict DlogKeys: %f'%self.pm.snap())
        test_dict.update({'TestNumberKeys':[ int(a_num) for a_num in new_test_numbers ]})
        self.pm_info.append(' ++ Reformat: + Update test_dict TestNumberKeys: %f'%self.pm.snap())
        test_dict.update({'TestNumberAndCommentTable':sorted([ '%s:%s'%(a_num,a_comment) for a_num,a_comment in \
            zip([ x.split(delimeter)[0].strip() for x in c_list[1:] ],[y.split(delimeter)[-1].strip() for y in c_list[1:]]) ],key=lambda a:int(a.split(':')[0]))})
        self.pm_info.append(' ++ Reformat: + Update test_dict TestNumberAndCommentTable: %f'%self.pm.snap())
        self.pm_info.append(' ++ Reformat: + Update test_dict keys with DlogKeys,TestNumberKeys, and TestNumberAndCommentTable: %f'%self.pm.snap())
        return(test_dict,c_list)

    def _defunct_MergeSiteResults(self,d_list,test_number_dict,field_index_dict,site_list):
        '''d_list: list of lists, each row split for the number of fields in field_index_dict
           field_index_dict: dict of field_key:index_value from original header in data log'''
        test_number_field_value = field_index_dict[field_index_dict.keys()[util.find_index(field_index_dict.keys(),'Test\w*N\w*')]]
        site_field_value = field_index_dict[field_index_dict.keys()[util.find_index(field_index_dict.keys(),'\\bSite\\b')]] 
        result_field_value = field_index_dict[field_index_dict.keys()[util.find_index(field_index_dict.keys(),'\\bMeas\w*')]] 
        min_field_value = field_index_dict[field_index_dict.keys()[util.find_index(field_index_dict.keys(),'\\bMin\w*')]] 
        max_field_value = field_index_dict[field_index_dict.keys()[util.find_index(field_index_dict.keys(),'\\bMax\w*')]] 
        comment_field_value = field_index_dict[field_index_dict.keys()[util.find_index(field_index_dict.keys(),'\\b(Comment|\w*Description)\w*')]] 
        pin_field_value = field_index_dict[field_index_dict.keys()[util.find_index(field_index_dict.keys(),'\\bPin\w*')]] 
        field_sequence = [test_number_field_value,min_field_value,max_field_value]
        comments_sequence = [comment_field_value]
        b_list = []
        for a_test_number,row_indices in test_number_dict.iteritems(): #row_indices is for multisite
            # -- a_dict = dict([ (i,dict([ (a_key,d_list[i][field_index_dict[a_key]]) for a_key in field_index_dict.keys() if not util.in_list(a_key,'P/F') ])) for i in row_indices ])
            first_row = d_list[row_indices[0]] #first active site for this dlog record
            if len(first_row)-1 == comment_field_value: row_comments_index_sequence = comments_sequence
            else: row_comments_index_sequence = comments_sequence+range(comment_field_value+1,len(first_row))
            a_dict = dict([ (i, \
                dict([ (a_key,d_list[i][field_index_dict[a_key]]) for a_key in field_index_dict.keys() \
                if not util.in_list(a_key,'P/F') and not util.in_list(a_key,'\\b(Comment|\w*Description)\w*|\\bPin\w*') ])) \
                for i in row_indices ])
            active_sites = [ a_dict[a_key]['Site'] for a_key in row_indices ]
            result_dict = dict([ ('Site%s'%a_site,'  ') for a_site in site_list ])
            result_dict.update(dict([('Site%s'%sub_row[site_field_value].strip(),sub_row[result_field_value].strip()) for sub_row in [d_list[i] for i in row_indices] ]) )
            # put it all together: [ test_number,lower_limit,upper_limit ] + [ measured values by site ] + [ Pin Value and Test Description(s) ]
            a_row_pin = first_row[pin_field_value] if len(first_row[pin_field_value]) > 0 else 'NullPin'
            a_row_comment = '|'.join([ first_row[a_index] for a_index in row_comments_index_sequence if len(first_row[a_index])>0 ])
            a_row = [first_row[a_field] for a_field in field_sequence]+[ result_dict['Site%s'%a_site] for a_site in site_list] + [a_row_pin,a_row_comment]
            b_list.append(a_row)
        return(b_list)

    def MakeDifferentTestNumber(self,dupe_num,number_list,index_list,num_iter):
        '''dupe_num: duplicated number
        number_list: current set of existing numbers
        index_list: line numbers of dupe_num
        num_iter: step size for changing test number'''
        new_numbers = []
        int_num_list = [int(a_num) for a_num in number_list]
        int_num = int(dupe_num)
        for i in index_list:
            #new_num = int_num + num_iter
            #while util.in_list(number_list,'%d'%new_num): new_num += num_iter
            new_num = self.__in_list__(int_num_list,int_num,num_iter)
            number_list[i] = '%d'%new_num
            int_num_list[i] = new_num
            new_numbers.append('%d'%new_num)
        return(new_numbers)

    def __in_list__(self,number_list,a_num,num_iter):
        '''Recursive function to generate new number not already in number_list'''
        if a_num in number_list:
            a_num = self.__in_list__(number_list,a_num+num_iter,num_iter)
        return a_num

    def GetTest(self,test_number,dlist):
        g_lines = util.keep_in_list(dlist,'^\s*%d\\b'%int(test_number))
        return( g_lines )

    def PopulateTestDict(self,file_list,start_stop=(0,-1)):
        self.pm_info = []
        test_dict = {}
        start,stop = start_stop
        self.F = CreateDlogChunksByTestRunIndex(file_list) #[ util.FileUtils(a_file) for a_file in file_list ]
        self.pm_info += [ ' ++ CreateDlogChunksByTRI: %s'%a_line for a_line in self.F.pm_info ]
        test_run_index = 0
        self.pm.snap()
        # -- file_index,f = 0,self.F[0]
        # -- if True:
        for file_index,a_file in enumerate(file_list):
            self.stdout_function('Processing file: %s, at %s'%(a_file,util.GetTheLocalTime()))
            file_loop_start_time = self.pm.snap_time
            tmp_file = os.path.join('/tmp',os.path.basename(a_file))
            a_file_mm,f = self.F.mmap_dict[a_file]['mmap_obj'],util.FileUtils(tmp_file)
            for sub_file_start_offset,sub_file_end_offset in self.F.mmap_dict[a_file]['tri_offsets']:
                loop_start_time,preformat_start_time  = self.pm.snap_time,self.pm.snap_time
                f.write_to_file(a_file_mm.read_lines_iter(sub_file_end_offset,sub_file_start_offset))
                self.pm_info.append(' + Generate tmp dlog file for offsets %d-%d: %f'%(sub_file_start_offset,sub_file_end_offset,self.pm.snap()))
                self.stdout_function(self.pm_info[-1])
                mm,fh = self.PreFormat(f)
                self.pm_info.append(' + PreFormat Dlog: %f'%(self.pm.snap_time-preformat_start_time))
                self.stdout_function(self.pm_info[-1])
                mm.keep_in_list('^\s*--+(?:\s+-+)+\s*$',offset=0)
                g_coordinates = [ mm.newline_offsets[a_num-1] for a_num in mm.g_coordinates_iter]
                all_headers = [ mm.readline_from_offset(a_num) for a_num in g_coordinates ]
                all_spans = [ mm.readline_from_offset(a_num+1) for a_num in g_coordinates ]
                self.pm_info.append(' + Get all dlog headers: %f'%self.pm.snap())
                self.stdout_function(self.pm_info[-1])
                #remove bogus headers
                all_headers = util.remove_from_list(all_headers,'(\s+\%\s+|^P/F\s+)') #remove bogus headers
                self.pm_info.append(' + Remove bogus headers: %f'%self.pm.snap())
                self.stdout_function(self.pm_info[-1])
                end_run_expression = '^Device\s+Results:$'
                found_in_file = mm.in_map(end_run_expression,offset=0)
                # since a_file broken down into chunks for each test run, l_start,l_stop need only be set once
                if found_in_file: 
                    start_run_expression = '^%s\s+%s\s+%s'%tuple(['%s'%a_field for a_field in all_headers[0].split()[:3]])
                    mm.seek(0)
                    found_start,found_end = mm.in_map(start_run_expression),False
                    if found_start:
                        l_start = mm.get_offset(offset=-1)
                        found_end = mm.in_map(end_run_expression)
                    if not found_end:
                        mm.seek(0,os.SEEK_END)
                    else:
                        found_start,found_end = False,False
                    l_stop = mm.get_offset(offset=-1)
                    get_summary = True
                else: start_pts,stop_pts, get_summary = [mm.newline_offsets[start]],[mm.newline_offsets[stop]],False
                self.pm_info.append(' + Determine start,stop pts for dlog subsections: %f'%self.pm.snap())
                if not get_summary: partial_list = mm.read_lines_iter(length=l_stop,offset=l_start)
                else: 
                    found_end_of_summary = mm.in_map('%s|%s'%(start_run_expression,'^\s*$'),offset=l_stop)
                    if found_end_of_summary: 
                        summary_stop = mm.get_offset(offset=-1)
                        partial_list = list(mm.read_lines_iter(length=summary_stop,offset=l_stop))
                    else: partial_list = list(mm.read_lines_iter(offset=l_stop))
                summary_dict,site_list=self.GetSummary(partial_list,get_summary)
                summary_dict.update({'Start':a_file_mm.newline_offsets_hash_table[sub_file_start_offset+l_start],'Stop':a_file_mm.newline_offsets_hash_table[sub_file_end_offset],\
                    'File':a_file, 'SiteList':site_list})
                self.pm_info.append(' + GetSummary for testrun: %f'%self.pm.snap())
                try:
                    reformat_start_time = self.pm.snap_time
                    #work on this one next, 20130429 23:33
                    a_dict,self.dlist = self.Reformat(mm,l_start,l_stop,self.Delimeter)
                    self.pm_info.append(' + Reformat dlist: %f'%(self.pm.snap_time-reformat_start_time))
                    self.stdout_function(self.pm_info[-1])
                    #close tmp file mmap and file handle objects
                    bob = mm.close(),fh.close()
                except IndexError:
                    print "File: %s"%f.nm
                    raise
                test_dict[test_run_index] = a_dict
                test_dict[test_run_index].update({'Summary':summary_dict})
                test_run_index += 1
                self.pm_info.append(' + Update TestDlogDict: %f'%self.pm.snap())
            self.pm_info.append('- Finished Processing file: %s, in %f'%(f.nm,self.pm.snap_time-file_loop_start_time))
            self.stdout_function('- Finished Processing file: %s, in %f\n  at %s'%(f.nm,self.pm.snap_time-file_loop_start_time,util.GetTheLocalTime()))
        return (test_dict)

    def PreFormat(self,f):
        self.pm_info = []
        preformat_start_time = self.pm.snap_time
        fh = f._open_file(f.nm,'r+')
        cm_kwargs = dict([('fileno',fh.fileno()),('length',f.file_size),('access',ACCESS_READ)])
        map_copy = util.mmap_utils(**cm_kwargs)
        # ascii dlog variations, could have whitespace at start of dlog, or not.... also Test_No. could be Test No.
        # remove most lines from preformat, write to new mmap_utils object, and close map_copy
        search_list = ['(?:Test[_\s]No\.|--+)\s+(?:P/F|--+)\s+(?:Site|--+)\s+(?:Ovrd|--+)?\s*(?:Result Description|Minimum|Pattern|--+|\s+)\s+(?:Test Description|Measured|Count|--+).*$', \
            '\s+\d+\s+(?:\s+|P|\*?F\*?|\d+)\s+(?:OVRD)?\s*(?:\s+|[\d\w\.\-]+)\s+.*$', \
            '\s+\d+\s+(?:P|\*?F\*?)\s+\d+\s+(?:OVRD)?\s*\w+\s+\d+', \
            'Device\s+Results:$', \
            '\s+(?:--+|Site|\d+)\s+(?:--+|Device\s+ID|\d+)\s+(?:--+|X\s+Coord|\s+)\s+(?:--+|Y\s+Coord|\s+)\s+.*$', \
            '(?:\s+Name|\s+\w+|--+)\s+(?:FL_TestNum|0x\d+|--+)\s+(?:Site|\d+|\w*SITE\w*|--+)\s+(?:Value|[\w\d\.]+|--+)$' 
        ]
        map_copy.keep_in_list('^\s*(%s)'%'|'.join(search_list),offset=0)
        list_size = map_copy.g_lines_size
        map_copy.close()
        fh.close()
        self.pm_info.append(' ++ Preformat: + Search for all valid dlog lines: %f'%self.pm.snap())
        self.stdout_function(self.pm_info[-1])
        mm,fh = util.reset_mmap(None,util.FileUtils('/tmp/%s'%(util.os.path.basename(f.nm))),\
            map_copy.g_lines_iter,True)
        self.pm_info.append(' ++ Preformat: + New copy of dlog in /tmp dir: %f'%self.pm.snap())
        self.stdout_function(self.pm_info[-1])
        # crop everything at top of file preceding the first "Test_No. P/F" line, using 
        # first_test_header_offset 
        assert mm.in_map('^\s*Test[\s_]No\.\s+P/F\s+Site',offset=0), \
            'Oh no, looks like %s does not have the expected dlog format'%os.path.basename(f.nm)
        first_test_header_offset = mm.get_offset(offset=-1)
        # insert a blank line in front of each header line up to test run summary
        self.pm.snap()
        a_pattern = '|'.join(['^\s*(?:Test[_\s]No\.)\s+(?:P/F)\s+(?:Site)\s+(?:Ovrd)?\s*(?:Result Description|Minimum|Pattern|\s+)\s+(?:Test Description|Measured|Count).*$','^Device\s+Results:'])
        end_run_expression,end_run_offset = '^Device\s+Results:$',mm.map_size
        if mm.in_map(end_run_expression,offset=0): end_run_offset = mm.get_offset(offset=-1)
        b_list = util.recursive_flatten(iter_insert_blanks(mm.read_lines_iter(length=end_run_offset,\
            offset=first_test_header_offset),a_pattern))
        #account for leading white space and/or spaces in the header names, i.e. Test No. -> Test_No.
        start_here = util.find_index(b_list,'^\s*Test[\s_]No\.\s+P/F\s+Site')
        b_list = [a[0] for a in util.sub_iterator(b_list[start_here:],'(?P<pre>Test|Result|Pin) (?P<post>No\.|Description|Name)','\g<pre>_\g<post>')]
        b_list = [a[0] for a in util.sub_iterator(b_list,'\s\*F\*\s','  F  ')]
        b_list = [a[0] for a in util.sub_iterator(b_list,'^\s*(?P<id>(?:Test_No\.|--+).+)$','\g<id>')]
        b_list = [a[0] for a in util.sub_iterator(b_list,'^\s*(?P<id>\d+\s+(?:P|\*F\*|\d+)?\s*(?:OVRD\s+)?(?:\s+|[\d\w\.\-]+)\s*)',' \g<id>')]
        #account for scan pattern fail, lump pins, P/F results of signal header with test description
        scan_pattern_header = '^\s*Test_No\.\s+P/F\s+Site\s+Pattern\s+Count\s+ScanVec:Bit\s+Test_Description\s+pins\s+'
        shortened_header = '(?P<id>^\s*Test_No\.\s+P/F\s+Site\s+Pattern\s+Count\s+ScanVec:Bit\s+Test_Description)\s+pins\s+.+$'
        scan_pattern_span = '^(?P<pre>(?:-+\s+){6})(?P<desc>-+)(?P<pin_info>(?:\s+-+){2})$'
        indices = util.keep_in_list_coordinates(b_list,scan_pattern_header)
        # bak_b_list = [ a_row for a_row in b_list ]
        for i in indices:
            b_list[i] = re.sub(re.compile(shortened_header),'\g<id>',b_list[i])
            b_list[i+1] = re.sub(re.compile(scan_pattern_span),'\g<pre>\g<desc>',b_list[i+1])
        scan_pattern_dlog = '(?P<id>^\s*{test_num}{ws}{fail}{ws}{site}{ws}{pattern}{ws}{count}{ws}{scan_vec_bit}{ws}{test_desc}){ws}(?P<fpins>{num_pins}){ws}.+$'.format(test_num='\d+',ws='\s+',fail='F',site='\d+',pattern='[\w\+]+',count='\d+',scan_vec_bit='[\w:\d\s]+',test_desc='[\w/:]+',num_pins='\d+')
        indices = util.keep_in_list_coordinates(b_list,scan_pattern_dlog)
        for i in indices: b_list[i] = re.sub(re.compile(scan_pattern_dlog),'\g<id>/NumFailPins_\g<fpins>',b_list[i])
        #concat test run summary if applicable:
        if end_run_offset<mm.map_size: b_list += ['\n']+list(mm.read_lines_iter(offset=end_run_offset))
        self.pm_info.append(' ++ Preformat: + grep on header line, calculate new size with blank line inserts: %f'%self.pm.snap())
        mm.close(),fh.close()
        mm,fh = util.reset_mmap(mm,f,b_list,True)
        self.pm_info.append(' ++ Preformat: + Stick blank lines between certain headers and device summary: %f'%self.pm.snap())
        # format for pattern/functional tests
        # -- bak_a_list = list(mm.read_lines_iter(offset=0))
        # -- mm.close(),fh.close()
        # -- mm,fh = util.reset_mmap(mm,f,bak_a_list,True)
        #Get all headers and spans, filter out "invalid" dlog lines, i.e. ' 11  1       OOOOA       6 VVVV_  C  2P_ R'
        #line up test number with first span field, should shift dlog record in line with header_span
        #check down to test run summary: 'Device Results:'
        end_run_expression,end_run_offset = '^Device\s+Results:$',mm.map_size
        if mm.in_map(end_run_expression,offset=0): end_run_offset = mm.get_offset(offset=-1)
        mm.keep_in_list('^\s*--+(?:\s+-+)+\s*$',length=end_run_offset,offset=0)
        g_coordinates,all_spans = [ mm.newline_offsets[a_num-1] for a_num in mm.g_coordinates_iter],list(mm.g_lines_iter)
        all_headers = [ mm.readline_from_offset(a_num) for a_num in g_coordinates ]
        header_set,span_set = util.unique_sub_list(all_headers),util.unique_sub_list(all_spans)
        sub_dlog_records_start,sub_dlog_records_end = [mm.get_offset(a_num,2) for a_num in g_coordinates],[a_num-1 for a_num in g_coordinates[1:]]+[mm.get_offset(position=end_run_offset,offset=-1)]
        invalid_dlog_line_str = 'Invalid Dlog Record:%s'%util.GetTheLocalTime()
        for sub_start,sub_end in zip(reversed(sub_dlog_records_start),reversed(sub_dlog_records_end)):
            start_index,end_index = mm.newline_offsets_hash_table[sub_start],mm.newline_offsets_hash_table[sub_end]
            field_span = mm.readline_from_offset(mm.newline_offsets[start_index-1])
            d_list,tn = list(mm.read_lines_iter(sub_end,sub_start)),re.match(re.compile('^--+'),field_span.split()[0])
            test_number_span,span_size = tn.group(),tn.end()
            for i,(j,a_line) in zip(xrange(start_index,end_index+1),enumerate(d_list)):
                m = re.match(re.compile('^\d+'),a_line.lstrip())
                if m:
                    test_number_field = m.group()
                    spacer = ' '*(span_size-m.end()) if m.end()<span_size else ''
                    s_line = '%s%s'%(spacer,a_line.lstrip())
                a_span,span_index = check_dlog_record_fits_header_span(replace_leading_whitespace(\
                    util.sub_iterator([s_line.rstrip()],\
                    '(?P<pre>\w)[\s/](?P<post>\w)','\g<pre>_\g<post>').next()[0],\
                    'S'),span_set,'\w\s','\s-')
                if span_index<0: #try a different field_boundry_expression
                    a_span,span_index = check_dlog_record_fits_header_span(replace_leading_whitespace(\
                        util.sub_iterator([s_line.rstrip()],\
                        '(?P<pre>\w)[\s/](?P<post>\w)','\g<pre>_\g<post>').next()[0],\
                        'S'),span_set,'\w(?:\s|$)','\s-')
                if span_index>-1:
                    m = re.match(re.compile('^\s*\d{4,}\s+'),a_line)
                    if not m: span_index=-1
                b_list[i] = '%s sub_start=%d, sub_end=%d, i=%d, j=%d\n%s%s'%(invalid_dlog_line_str,\
                    sub_start,sub_end,i,j,s_line,a_line) if span_index<0 else s_line
        bob = mm.close(),fh.close()
        mm,fh = util.reset_mmap(mm,f,util.remove_from_list(b_list,invalid_dlog_line_str),True)
        self.pm_info.append(' ++ Preformat: + Remove invalid dlog lines: %f'%self.pm.snap())
        # check for functional test dlog records, reformat
        found_in_list = mm.in_map('^Test_No\.\s+.*\s+(?:Pattern|Result_Description)\s+',offset=0)
        self.pm_info.append(' ++ Preformat: + Determine if functional patterns are in dlog: %f'%self.pm.snap())
        if found_in_list:
            first_pattern_header_line = mm.readline_from_offset(mm.get_offset(offset=-1))
            trans_result_dict = {'':'1', 'P':'1', 'F':'0', '*F*':'0'}
            start_expression = '^%s\s+%s\s+%s\s+%s'%tuple(['%s'%a_field for a_field in first_pattern_header_line.split()[:4] ])
            self.pm.snap()
            mm.keep_in_list(start_expression,offset=0)
            start_indices = list(mm.g_coordinates_iter)
            start_pts = [ mm.newline_offsets[i] for i in start_indices]
            end_pts,end_indices = [],[]
            for a_pt in start_pts:
                found_blank_line = mm.in_map('^$',offset=a_pt)
                #end_indices.append(util.find_index(mm.newline_offsets,mm.tell())-1)
                end_pts.append(mm.get_offset(offset=-1))
                end_indices.append(mm.newline_offsets_hash_table[end_pts[-1]])
            self.pm_info.append(' ++ Preformat: + CaptureBlocks for functional pattern tests: %f'%self.pm.snap())
            self.stdout_function(self.pm_info[-1])
            reformat_functional_patterns_start = self.pm.snap_time
            chk_start_stop_list,chk_list = [],['index:loop_time:start:stop:compare']
            arg_list = [ (index,start,stop,start_offset,stop_offset) for index,start,stop,start_offset,stop_offset in zip(xrange(len(start_pts)),reversed(start_indices),reversed(end_indices),\
                reversed(start_pts),reversed(end_pts)) ]
            modified_sections_list = []
            a_list = list(mm.read_lines_iter(offset=0))
            for index,start,stop,start_offset,stop_offset in arg_list:
                self.pm.snap()
                loop_start_time = self.pm.snap_time
                header = mm.readline_from_offset(start_offset)
                span = mm.readline()
                b_list = list(mm.read_lines_iter(length = stop_offset,offset=mm.tell()))
                dline_brackets = get_span_brackets(span,'-[\s|$]')
                slice_list = [ slice(a,b) for a,b in dline_brackets[:-1] ] + [slice(dline_brackets[-1][0],-1)]
                pattern_field_index = util.find_index(header.split(),'\\b(?:Pattern|Result_Description)\\b')
                field_index_dict = dict([ (i,a_field) for i,a_field in enumerate(header.split()[:pattern_field_index]) if not util.in_list(a_field,'\\bOvrd(?i)\\b') ])
                meas_key = field_index_dict.keys()[ util.find_index( ['%s:%s'%(a_key,a_value) for a_key,a_value in field_index_dict.iteritems()],'P/F') ]
                comment_index_dict = dict([ (i,a_field) for i,a_field in enumerate(header.split()[pattern_field_index:],pattern_field_index) ])
                self.pm_info.append(' ++ Preformat: ++ Break out the sub start/stop pts, and generate the field_index_dict: %f'%self.pm.snap())
                modified_sections_list.append( \
                    util.pretty_format([' : '.join(self.site_specific_result_header.split()), \
                    ' : '.join(self.site_specific_result_span.split())]+[' : '.join( \
                    [' %s '%a_row[a_key].strip() for a_key in util.my_sort_in_place(field_index_dict.iterkeys()) ] + \
                    ['1',trans_result_dict[a_row[meas_key].strip()],'1','    '] + \
                    [' '.join([ '%s->%s'%(comment_index_dict[a_key],a_row[a_key].strip()) for a_key in util.my_sort_in_place(comment_index_dict.iterkeys()) if len(a_row[a_key].strip())>0 ])] ) \
                    for a_row in [[a_line[a_slice] for a_slice in slice_list] for a_line in b_list if util.in_list(a_line,'\s*\d+\s+(?:\*?F\*?|P)?\s+\d+\s+(?:OVRD\s+)?')] ], ' : ','  ') \
                    )
                self.pm_info.append(' ++ Preformat: ++ Generate reformatted list: %f'%self.pm.snap())
                if len(modified_sections_list[-1])>0: a_list[start:stop] = list(util.add_cr_iter(modified_sections_list[-1]))
                self.pm_info.append(' ++ Preformat: ++ Put in reformatted dlog stuff: %f'%self.pm.snap())
                self.pm_info.append(' ++ Preformat: ++ Done with loop section %d - %d: %f'%(start,stop,(self.pm.snap_time-loop_start_time)))
                chk_start_stop_list.append((index,start,stop)) #cmp(chk_start_stop_list,arg_list)
                chk_list.append('%d:%f:%d:%d:%s'%(index,self.pm.snap_time-loop_start_time,start,stop,'Equal' if (stop-start)==len(modified_sections_list) else 'NotEqual'))
            bob = mm.close(),fh.close()
            mm,fh = util.reset_mmap(mm,f,a_list,get_newline_offsets=True)
            self.pm_info.append(' ++ Preformat: + Finished reformatting functional pattern sections: %f'%(self.pm.snap_time-reformat_functional_patterns_start))
            self.stdout_function(self.pm_info[-1])
        self.pm_info.append(' ++ Preformat: + Finished: %f'%(self.pm.snap_time - preformat_start_time))
        return(mm,fh)

    def GetSummary(self,a_list,get_summary):
        if get_summary: return(self._doGetSummary(a_list))
        else:
            g = util.m_re(a_list)
            g.grep('^--+[\s$]+')
            all_headers = [ a_list[i] for i in [ int(float(a_coord)-2) for a_coord in g.coordinates ] ]
            possible_headers = util.unique_sub_list(all_headers)
            b = util.m_re(possible_headers)
            b.grep('  Site  ')
            if b.pattern_count > 0:
                chk_coordinates = util.unique_sub_list([ int(a_coord.split('.')[-1]) for a_coord in b.coordinates ])
                if len(chk_coordinates) == 1: 
                    site_index = util.find_index(possible_headers[0].split(),'Site')
                    b.clear_cache()
                    b.grep('\s+\d+\s+\*?[FP]?\*?\s+\d+\s+')
                    return({'NoSummary'},util.sort_unique([a_line.split()[site_index] for a_line in b.lines ]) )
                else: 
                    site_indices = [ util.find_index(a_line.split(),'Site') for a_line in  possible_headers ]
                    header_dict = dict([ (a_header,site_index) for a_header,site_index in zip(possible_headers,site_indices) ])
                    site_list = []
                    for a_header in possible_headers:
                        site_index = header_dict[a_header]
                        b = util.CaptureBlocks(a_list,'^%s\s+%s\s+%s'%tuple(a_header.split()[:3]),'^$')
                        for sub_start,sub_stop in zip(b.start_pts+2,b.end_pts):
                            bob = [ site_list.append(a_line.split()[site_index]) for a_line in a_list[sub_start:sub_stop] \
                                  if a_line.split()[site_index] not in site_list ]
                    return({'NoSummary'},util.sort_unique([a_line.split()[site_index] for a_line in b.lines ]) )

    def _doGetSummary(self,a_list):
        '''a_list is a partial list of a particular dlog run, starting from Device Results:
            looking for the next blank line, or eof'''
        summary_dict ={}
        g = util.m_re(a_list)
        g.grep('^$')
        #if g.pattern_count > 0: b = util.m_re([ a_line for a_line in a_list[:int(float(g.coordinates[0]))]])
        #else: b = util.m_re([a_line for a_line in a_list])
        b = util.m_re(a_list[:int(float(g.coordinates[0])) if g.pattern_count>0 else len(a_list) ])
        b.grep('^\s*(\d+)')
        site_list = b.m_groups
        summary_list = b.lines
        b.clear_cache()
        b.grep('^\s*--+')
        try:
            field_span_line = b.allLines[int(float(b.coordinates[0])-1)]
            field_keys_line = b.allLines[int(float(b.coordinates[0])-2) ]
            field_span_line = '-'*field_span_line.find('-')+field_span_line[field_span_line.find('-'):]
            field_span_brackets = get_span_brackets(field_span_line,'\s-')
            field_keys = [ field_keys_line[i:j].strip() for i,j in field_span_brackets ]
            summary_dict.update(dict([(i,dict([(a_field,a_summary[i:j].strip()) for a_field,(i,j) in zip(field_keys,field_span_brackets)])) for i,a_summary in enumerate(summary_list) ]))
        except IndexError:
            print 'a_list:\n%s'%'\n'.join(a_list)
            print 'allLines:\n%s'%'\n'.join(b.allLines)
            print 'coordinates:\n%s'%', '.join(b.coordinates)
            print 'site_list: %s'%', '.join(site_list)
            print 'summary_list:\n%s'%'\n'.join(summary_list)
            raise
        return(summary_dict,site_list)

    def pretty_print_wrapper(self,a_list=[]):
        util.PrettyPrint(a_list)

    def append_to_console(self,a_list=[],text_tag=None):
        self.stdout.update_idletasks()
        append_to_text_box(self.stdout,a_list,text_tag)
        self.stdout.update_idletasks()


class TestAnalysis:
    ''' Pass in a list of the dlog test results, i.e. 79303, the limits list [lo,hi], and result fields [site1,site2,...], 
    and delimeter ('|' is default)'''
    def __init__(self,a_list,lo_limit=-2e32,hi_limit=2e32,result_fields=[2],delimeter='|'):
        if type(a_list) == type('a_string'): a_list = [a_list]
        self.Dlist, self.NumResults = [ a_line.split(delimeter) for a_line in a_list], [ 0 ]*len(result_fields)
        self.Site, self.SiteRange = [ a_site for a_site in result_fields ], range(len(result_fields))
        self.Results = [ [] ] *len(result_fields)
        self.MergedResults = []
        for a_site in self.SiteRange:
            try:
                self.NumResults[a_site] = sum([ 1 for a_line in self.Dlist if len(a_line[self.Site[a_site]])>0 ]) 
                self.Results[a_site] = [ float(a_line[self.Site[a_site]].split()[0]) for a_line in self.Dlist if len(a_line[self.Site[a_site]])>0 ]
                self.MergedResults += self.Results[a_site]
            except IndexError:
                print 'site field: %d\n%s'%(a_site,a_line)
                break
            except ValueError:
                print 'site field: %d\n%s'%(a_site,a_line)
                break
        self.LoLimit,self.HiLimit = lo_limit, hi_limit
        self.GetStats()
    def _calcStats(self,results,LoLimit, HiLimit):
        NumResults = len(results)
        aRange = range(NumResults)
        self.ResultsDict = {'Avg':0, 'Cpk':0, 'Cpl':0, 'Cph':0, 'StdDev':0, 'Max':0, 'Min':0, 'Range':0}
        self.ResultsDict['Min'], self.ResultsDict['Max'], self.ResultsDict['Avg'] = min(results), max(results), sum(results)/NumResults
        self.ResultsDict['Range'] = self.ResultsDict['Max']-self.ResultsDict['Min']
        self.ResultsDict['StdDev'] = pow( sum([pow(a_result-self.ResultsDict['Avg'],2) for a_result in results])/NumResults,0.5)
        cp_results_list = []
        if LoLimit:
            self.ResultsDict['Cpl'] = (self.ResultsDict['Avg'] - LoLimit)/(3*self.ResultsDict['StdDev']+1e-12)
            cp_results_list.append(self.ResultsDict['Cpl'])
        if HiLimit:
            self.ResultsDict['Cph'] = (HiLimit - self.ResultsDict['Avg'])/(3*self.ResultsDict['StdDev']+1e-12)
            cp_results_list.append(self.ResultsDict['Cph'])
        self.ResultsDict['Cpk'] = min(cp_results_list) if len(cp_results_list)>0 else 0
        return self.ResultsDict
    def GetStats(self):
        self.Avg,self.Min,self.Max  = [ 0 for a_site in self.SiteRange ],[ 0 for a_site in self.SiteRange ],[ 0 for a_site in self.SiteRange ]
        self.StdDev, self.Cpk, self.Cpl, self.Cph = [ 0 for a_site in self.SiteRange ],[ 0 for a_site in self.SiteRange ],\
            [ 0 for a_site in self.SiteRange ],[ 0 for a_site in self.SiteRange ]
        for a_site,num_site_results in zip(self.SiteRange,self.NumResults):
            if num_site_results>0:
                site_field, aRange = self.Site[a_site], range(self.NumResults[a_site]) 
                aDict = self._calcStats(self.Results[a_site],self.LoLimit,self.HiLimit)
                self.Min[a_site], self.Max[a_site], self.Avg[a_site] = aDict['Min'],aDict['Max'],aDict['Avg']
                self.StdDev[a_site],self.Cpl[a_site],self.Cph[a_site],self.Cpk[a_site] = aDict['StdDev'],aDict['Cpl'],aDict['Cph'],aDict['Cpk']
    def GetMergedStats(self):
        aDict, self.SiteAvgDelta = self._calcStats(self.MergedResults,self.LoLimit,self.HiLimit), [ 0 for a_site in self.SiteRange ]
        self.MergeAvg, self.MergeMin, self.MergeMax, self.MergeStdDev = aDict['Avg'],aDict['Min'],aDict['Max'],aDict['StdDev']
        self.MergeCpl, self.MergeCph, self.MergeCpk = aDict['Cpl'],aDict['Cph'],aDict['Cpk']
        for a_site in self.SiteRange:
            self.SiteAvgDelta[a_site] = self.MergeAvg-self.Avg[a_site]
class EnvisionAsciiDlogAnalysis(PrepAsciiDlogFile):
    def __init__(self,file_list,start_stop=(0,-1),delimeter=',',test_num_iter=10,keep_fails=False,skip_device_id=False,\
        device_id_dict={'device_id_x':'DIEID_WAFERX_Value','device_id_y':'DIEID_WAFERY_Value',\
        'device_id_w':'DIEID_WAFERNUM_Value','DeviceIdAttributes':'device_id_x device_id_y device_id_w'.split(),\
        'DeviceIdTableKeys':':'.join( 'u,x,y,w,test_run_index,a_site,sbin_name,hbin,file,start_pt,end_pt'.split(',') )},\
        stdout=None):
        super(EnvisionAsciiDlogAnalysis,self).__init__(file_list,start_stop,delimeter,test_num_iter,keep_fails,stdout)
        self.device_id_dict = device_id_dict
        dev_id_attr_key,dev_id_table_keys = 'DeviceIdAttributes','DeviceIdTableKeys'
        if len(file_list)>0:
            self.__set_device_id_attributes__(self.device_id_dict,dev_id_attr_key,dev_id_table_keys)
            if not skip_device_id:
                self.DeviceIdTableDict,self.DeviceIdTableList = self.BuildDeviceIdTable(self.TestDlogDict,\
                    device_id_dict,dev_id_attr_key)
                self.pm_info.append(' + Generate DeviceIdTable: %f'%self.pm.snap())
    def __set_device_id_attributes__(self,device_id_dict,device_id_attr_key='DeviceIdAttributes',\
        device_id_table_keys='DeviceIdTableKeys'):
        for device_id_attr in device_id_dict[device_id_attr_key]: 
            setattr(self,device_id_attr,device_id_dict[device_id_attr])
        setattr(self,'device_id_table_dict_keys',device_id_dict[device_id_table_keys])
    def BuildLimitsTable(self,limitDict):
        pass
    def BuildStatsTable(self,test_list,num_sites):
        self.TestStatsDict = {}
        for test_num in test_list:
            self.test_records = self.GetTest(test_num)
            if len(self.test_records)>0:
                a_record = self.test_records[0].split(self.Delimeter)
                test_num = a_record.pop(0)
                test_comment = a_record.pop()
                test_pin = a_record.pop()
                num_params = len(a_record)
                num_limits = num_params-num_sites
                Limits = [float(a_record[0].split()[0]),float(a_record[1].split()[0])]  #hard coding for now....
                LoLimit, HiLimit = Limits #hard coding for now, assuming hi and lo are always there.....
                ResultFields = range(len(Limits)+1,len(Limits)+1+num_sites)
                t = TestAnalysis(self.test_records,LoLimit,HiLimit,ResultFields)
                self.TestStatsDict[test_num] = { 'Pin':test_pin, 'Comment':test_comment, 'Avg':t.Avg, 'StdDev':t.StdDev, 'Cpk':t.Cpk, 'Limits':Limits }
    def PrintRecords(self,test_list):
        a_list = ['test_num:site:comment/pin\tavg\tstd_dev\tcpk']
        for test_num in test_list:  a_list+=self.GetRecord(test_num)
        return a_list
    def GetRecord(self,test_num):
        site_list = range(len(self.TestStatsDict[test_num]['Avg']))
        a_dict = self.TestStatsDict[test_num]
        return [ '%s:s%02d:%s/%s\t%7.4f\t%7.4f\t%7.4f'\
            %(test_num,i+1,a_dict['Comment'],a_dict['Pin'],a_dict['Avg'][i],a_dict['StdDev'][i],a_dict['Cpk'][i])\
            for i in site_list ]
    def BuildDeviceIdTable(self,test_dlog_dict,device_id_dict,device_id_attr_key='DeviceIdAttributes',\
      device_id_table_dict_keys=None):
        '''Create Device Id Table to allow cross reference for a specific unit, useful for 
        correlation, grr, etc.
        device_id_dict: dictionary with key entry search expressions tied to test records in test_dlog_dict'''
        if device_id_table_dict_keys is None: device_id_table_dict_keys = self.device_id_table_dict_keys
        device_id_list = [device_id_table_dict_keys]
        num_device_id_table_fields,num_attr_keys  = len(device_id_list[0].split(':')),len(device_id_dict[device_id_attr_key])
        header_bin_keys = ['SW Bin No.','HW Bin No.']
        zipper_set = [(u,tri,test_dlog_dict[tri]) for u,tri in enumerate(util.my_sort_in_place(test_dlog_dict.iterkeys()))]  #unit_num,test_run_index,t_dict
        if num_attr_keys>0:
            for u,test_run_index,t_dict in zipper_set:
                g = util.m_re(t_dict['TestNumberAndCommentTable'])
                g.grep('\\b(%s)\\b'%'|'.join([device_id_dict[attr_key] for attr_key in device_id_dict[device_id_attr_key]]))
                test_number_dict={}
                for key_name in util.sort_unique([a_line.split(':')[-1] for a_line in g.lines]):
                    num_list = [ int(a_num) for a_num in [ a_row.split(':')[0] for a_row in util.keep_in_list(g.lines,key_name) ] ]
                    test_number_dict.update({key_name:num_list})
                site_list = [ int(a_site) for a_site in t_dict['Summary']['SiteList'] ]
                # device_id_param_keys, is the key order for the device id search expression(s) in device_id_list
                device_id_param_keys = [g.lines[util.search_rcrsv(g.m_groups,device_id_dict[regex_key])].split(':')[-1] \
                    for regex_key in device_id_dict[device_id_attr_key]]
                site_dict = dict([(a_site,dict([(a_key,'') for a_key in device_id_param_keys])) for a_site in site_list])
                for a_key in device_id_param_keys:
                    for a_num in test_number_dict[a_key]:
                        for a_site in site_list:
                            if len(t_dict[int(a_num)]['Site%d'%a_site].strip())>0:
                                site_dict[a_site].update({a_key:t_dict[a_num]['Site%d'%a_site]})
                                continue
                device_id_list += [ '%s:%s'%(u,':'.join(
                    [site_dict[a_site][a_key] for a_key in device_id_param_keys ]+\
                    ['%d'%test_run_index,'%s'%a_site] +\
                    [t_dict['Summary'][i][header_bin_key] for header_bin_key in header_bin_keys ] + \
                    [t_dict['Summary']['File'].split('/')[-1],'%d'%t_dict['Summary']['Start'],'%d'%t_dict['Summary']['Stop'] ]))
                    for i,a_site in enumerate(site_list) ]
        else:
            num_attr_keys = 2 #force to 2, for tri and site
            device_id_list = [':'.join(device_id_table_dict_keys.split(':')[:3]+device_id_table_dict_keys.split(':')[1:])]
            for u,test_run_index,t_dict in zipper_set:
                device_id_param_keys,site_list = 'tri site'.split(),\
                    [int(a_site) for a_site in t_dict['Summary']['SiteList']]
                #site_dict = {SITE:{}}
                site_dict = dict([(a_site,\
                    dict([(device_id_param,device_id_value) for device_id_param,device_id_value in \
                    zip(device_id_param_keys,[test_run_index,a_site])])
                    ) for a_site in site_list])
                device_id_list += [ '%s:%s'%(u,':'.join(
                    ['%d'%site_dict[a_site][a_key] for a_key in device_id_param_keys ]+\
                    ['%d'%test_run_index,'%s'%a_site] +\
                    [t_dict['Summary'][i][header_bin_key] for header_bin_key in header_bin_keys ] + \
                    [t_dict['Summary']['File'].split('/')[-1],'%d'%t_dict['Summary']['Start'],'%d'%\
                    t_dict['Summary']['Stop'] ]))
                    for i,a_site in enumerate(site_list) ]
        #bak_device_id_list = [a_row for a_row in device_id_list] #backup
        #device_id_list = [a_row for a_row in bak_device_id_list] #restore
        device_id_list = [ a_line for a_line in device_id_list if len(''.join(a_line.split(':')[1:num_attr_keys+1]))>=num_attr_keys ]
        #u:len(<device_attr_key_list>):+1:+1:+1:+1:+1:+1
        gen_col_list = lambda num_attr_keys:([1] if num_attr_keys>0 else [])\
            +range(num_attr_keys+1,num_device_id_table_fields)
        s = util.SpecialFormat(device_id_list,gen_col_list(num_attr_keys),':',',')
        #s.formatted output: u,x y w,test_run_index,a_site,sbin_name,hbin.....
        #colum list starts at first device_id_attribute, "x"->col 1, and spans x y w, so the range
        #picks up after 1+num_attr_keys and goes out to num_device_id_table_fields, thus
        #col_list = [1, 4, 5, 6, 7, 8, 9, 10]
        #where x y w are device_id_attributes
        #renumber u
        get_starting_device_id_table_field = lambda num_attr_fields: 2 if num_attr_fields>0 else 1
        field_start = get_starting_device_id_table_field(num_attr_keys)
        #arg_list = [ (i,a_line) for i,a_line in enumerate([util.my_split(a_row,',') for a_row in s.formatted_list[1:]]) ]
        b_list = [[' '.join(['%d'%i,(a_line[1] if field_start>1 else '')])]+a_line[field_start:] for i,a_line in enumerate([util.my_split(a_row,',') for a_row in s.formatted_list[1:]])] 
        #replace u with i enumerator, then concatenate a_line[1] (device id attr fields) and a_line[2:], the rest of 
        #device_id_table_fields
        #sample output: fields: ['u x y w','test_run_index','a_site','sbin_name',....'start_pt','end_pt']
        #[['0 1 11 22', '0', '1', '1', '1', 'BlizC11RPCQuadSite.txt', '1', '7344'],\
        # ['1 11 11 10', '0', '2', '1', '1', 'BlizC11RPCQuadSite.txt', '1', '7344'],\
        # ['2 18 20 11', '0', '3', '1', '1', 'BlizC11RPCQuadSite.txt', '1', '7344'],\
        # ['3 2 12 22', '0', '4', '1', '1', 'BlizC11RPCQuadSite.txt', '1', '7344']]
        #
        b_list.insert(0,s.formatted_list[0].split(','))
        device_id_list = [ ':'.join(' '.join(a_row).split()) for a_row in [ a_row for a_row in b_list ] ]
        device_id_table_keys = b_list.pop(0)[get_starting_device_id_table_field(num_attr_keys):] #test_run_index,a_site,sbin_name......
        device_id_dict = dict([ (device_id_key,dict([ (table_key, a_value) for table_key, a_value in zip(device_id_table_keys,a_row) ]))\
            for device_id_key,a_row in zip([ ':'.join(x[0].split()) for x in b_list],[y[1:] for y in b_list] ) ])
        return(device_id_dict,device_id_list)
    def __build_die_id_table__(self,test_dlog_dict,die_id_x,die_id_y,die_id_wafer):
        '''Sanity Check: Older method, tied to die id parameters from a typical TI app'''
        die_id_list = [self.device_id_table_dict_keys]
        num_die_id_table_fields = len(die_id_list[0].split(':'))
        header_bin_keys = ['SW Bin No.','HW Bin No.']
        zipper_set = [(u,tri,test_dlog_dict[tri]) for u,tri in enumerate(util.my_sort_in_place(test_dlog_dict.iterkeys()))]  #unit_num,test_run_index,t_dict
        for u,test_run_index,t_dict in zipper_set:
            g = util.m_re(t_dict['TestNumberAndCommentTable'])
            g.grep('\\b%s\\b'%'|'.join([die_id_x,die_id_y,die_id_wafer]))
            test_number_dict={}
            for key_name in util.sort_unique([a_line.split(':')[-1] for a_line in g.lines]):
                num_list = [ int(a_num) for a_num in [ a_row.split(':')[0] for a_row in util.keep_in_list(g.lines,key_name) ] ]
                test_number_dict.update({key_name:num_list})
            site_list = [ int(a_site) for a_site in t_dict['Summary']['SiteList'] ]
            fnd_die_id_x = g.lines[util.find_index(g.m_groups,'X(?i)')].split(':')[-1]
            fnd_die_id_y = g.lines[util.find_index(g.m_groups,'Y(?i)')].split(':')[-1]
            fnd_die_id_w = g.lines[util.find_index(g.m_groups,'NUM(?i)')].split(':')[-1]
            die_id_param_keys = [fnd_die_id_x,fnd_die_id_y,fnd_die_id_w]
            site_dict = dict([(a_site,dict([(a_key,'') for a_key in die_id_param_keys])) for a_site in site_list])
            for a_key in die_id_param_keys:
                for a_num in test_number_dict[a_key]:
                    for a_site in site_list:
                        if len(t_dict[int(a_num)]['Site%d'%a_site].strip())>0:
                            site_dict[a_site].update({a_key:t_dict[a_num]['Site%d'%a_site]})
                            continue
            die_id_list += [ '%s:%s'%(u,':'.join(
                [site_dict[a_site][a_key] for a_key in die_id_param_keys ]+\
                ['%d'%test_run_index,'%s'%a_site] +\
                [t_dict['Summary'][i][header_bin_key] for header_bin_key in header_bin_keys ] + \
                [t_dict['Summary']['File'].split('/')[-1],'%d'%t_dict['Summary']['Start'],'%d'%t_dict['Summary']['Stop'] ]))
                for i,a_site in enumerate(site_list) ]
        die_id_list = [ a_line for a_line in die_id_list if len(''.join(a_line.split(':')[1:4]))>=3 ]
        s = util.SpecialFormat(die_id_list,[1,4,5,6,7,8,9,10],':',',')
        #renumber u
        b_list = [[' '.join(['%d'%i,a_line[1]])]+a_line[2:] for i,a_line in enumerate([util.my_split(a_row,',') for a_row in s.formatted_list[1:]])]
        b_list.insert(0,s.formatted_list[0].split(','))
        die_id_list = [ ':'.join(' '.join(a_row).split()) for a_row in [ a_row for a_row in b_list ] ]
        die_id_table_keys = b_list.pop(0)[2:]
        die_id_dict = dict([ (die_id_key,dict([ (table_key, a_value) for table_key, a_value in zip(die_id_table_keys,a_row) ]))\
            for die_id_key,a_row in zip([ ':'.join(x[0].split()) for x in b_list],[y[1:] for y in b_list] ) ])
        return(die_id_dict,die_id_list)
    def GenerateDlogTable(self, test_dict, delimeter=None):
        '''Pass in TestDlogDict[index], get a nice printable list back that's comma delimited and easy to read '''
        if not delimeter: delimeter = self.Delimeter
        # dlist = ['    ,   '.join(test_dict['DlogKeys'])]+\
            # ['%d , %s'%(a_test_number,'  ,  '.join([ \
            # '%s'%test_dict[int(a_test_number)][a_field] for a_field in test_dict['DlogKeys'][1:] ]) ) \
            # for a_test_number in util.my_sort_in_place(test_dict['TestNumberKeys']) ]
        return ( util.pretty_format( \
            ['    ,   '.join(test_dict['DlogKeys'])]+
            ['%d , %s'%(a_test_number,'  ,  '.join([ \
            '%s'%test_dict[int(a_test_number)][a_field] for a_field in test_dict['DlogKeys'][1:] ]) ) \
            for a_test_number in util.my_sort_in_place(test_dict['TestNumberKeys']) ], \
            ' , ', ',',do_rstrip=True)
            )
    def _append_to_console(self):
        pass
class ParseStdf:
    '''Pass in parsed ascii stdf file, using stdf2atdf and x_loc, y_loc, and wfr_loc test numbers.'''
    def __init__(self,stdf_file,x_loc,y_loc,w_loc):
        self.DieIdList, self.FailLogList = [],[]  # initialize as empty lists
        self.f = util.FileUtils(stdf_file)
        self.f.read_from_file()
        self.c = util.CaptureBlocks(self.f.contents,'Pir:1\|\d','Prr:1\|\d','Pir:')
        self.num_records = int(self.f.contents[self.c.end_pts[-1]-1].split('|')[9])
        self.num_test_runs = len(self.c.end_pts)
        self.GetFullTestList()
        self.x_loc, self.y_loc, self.w_loc = x_loc,y_loc,w_loc
        self.GetDieIdList()

    def GetFullTestList(self):
        g = util.m_re(self.f.contents)
        g.grep('Ptr:\d+\|')
        if g.pattern_count>0: 
            self.full_test_list = [ a_num.strip() for a_num in util.sort_unique(g.m_groups)]
            self.test_limits_dict= {}
            for a_line in g.lines:
                test_num = util.my_split(a_line,'[:\|]')[1].strip()
                if not self.test_limits_dict.has_key(test_num):
                    comment,blah1,blah2,blah3,blah4,low_limit,high_limit,units = util.my_split(a_line,'[\|:]',True)[7:15]
                    self.test_limits_dict[test_num] = { 'LowerLimit': low_limit, 'UpperLimit':high_limit, 'Units':units, 'Comment':comment }

    def GetDieIdList(self):
        self.DieIdList=[]
        aRange = range(self.num_test_runs)
        for i in aRange:
            rec_start,rec_stop = self.c.start_pts[i],self.c.end_pts[i]
            g = util.m_grep(self.f.contents[rec_start:rec_stop])
            g.grep('Prr:')
            siteRange = [ int(a_line.split(':')[-1].split('|')[1]) for a_line in g.lines ]
            g.clear_cache()
            record_range='%d:%d'%(rec_start,rec_stop)
            for a_site in siteRange:
                SiteNum='%d'%(a_site)
                self.die_id_test_num_pattern = '('+'|'.join([self.x_loc+'\|\d+\|'+SiteNum+'\|\d+\|\d+\|[\d\.]+',\
                    self.y_loc+'\|\d+\|'+SiteNum+'\|\d+\|\d+\|[\d\.]+',\
                    self.w_loc+'\|\d+\|'+SiteNum+'\|\d+\|\d+\|[\d\.]+'])+')'
                g.grep('Ptr:'+self.die_id_test_num_pattern) 
                if g.pattern_count > 0:
                    die_id = ':'.join([ str(int(float(a_line.split('|')[-1]))) for a_line in g.m_groups ])
                else:
                    die_id = '0:0:0'
                g.clear_cache()
                g.grep('Prr:\d+\|'+SiteNum+'\|\d+\|\d+\|\d+\|\d+\|[\d\-]+\|[\d\-]+\|\d+\|\d+')
                try:
                    Head,SiteNum,PassFail,NumTests,HardBin,SoftBin,Xcoord,Ycoord,TestTime,PartId=g.m_groups[0].split('|')
                except IndexError:
                    print 'DieId: %s, SiteNum: %s, RecStart: %d, RecStop: %d'%(die_id,SiteNum,rec_start,rec_stop)
                    raise
                part_id = ':'.join([PartId,NumTests,HardBin,SoftBin,SiteNum])        
                g.clear_cache()
                self.DieIdList.append('|'.join([die_id,part_id,record_range]))

    def GetFailLogList(self,die_id_list):
        '''Generates a fail log listing for one or more die id.  Where die_id_list is a list 
        of one or more die id strings that are space delimited,
        i.e. [ '12 24 3', '2 7 12',...] '''
        if type(die_id_list) == type('a_string'):
            die_id_list = [ die_id_list ]
        self.FailLogList = []
        for a_line in die_id_list:
            x,y,w = a_line.split()
            self.FailLogList += self.GetAFailLog(x,y,w)

    def GetAFailLog(self,x_loc,y_loc,w_loc):
        b_list = []
        g = util.m_grep(self.DieIdList)
        g.grep(':'.join([x_loc,y_loc,w_loc]))
        if g.pattern_count>0:
            for a_line in g.lines:
                DieId = a_line.split('|')[0]
                SiteNum = a_line.split('|')[1].split(':')[-1]
                DeviceId = a_line.split('|')[1].split(':')[0]
                rec_start,rec_stop = a_line.split('|')[-1].split(':')
                rec_start,rec_stop = int(rec_start),int(rec_stop)
                b = util.m_grep(self.f.contents[rec_start:rec_stop])
                b.grep('Ptr:\d+\|\d\|'+SiteNum+'\|\d\d+')
                for a_dlog in b.lines:
                    b_list.append(('|'.join([DieId,DeviceId,a_dlog.strip()])))
        return(b_list)

    def GetDieIdRecord(self,die_id_list):
        '''Return a list of one or more die id records, pull from DieIdList, so need to run GetDieIdList first.  Need to pass in a string with 3 coordinates, 'x y w', or a list of lists, i.e. ['x1 y1 w1', 'x2 y2 w2'....]'''
        b_list = [] 
        for a_die in die_id_list:
            g = util.m_grep(self.DieIdList)
            x,y,w = a_die.split()
            g.grep('\\b'+x+'\\b:\\b'+y+'\\b:\\b'+w+'\\b')
            b_list = b_list + g.lines
        return b_list

    def GetDlogRecord(self,x_loc,y_loc,w_loc,test_list):
        '''Get the dlog record(s) for a single die id device based on the test numbers passed in the test_list argument'''
        if type(test_list) == type('a_string'):
            test_list = [ test_list ]
        b_list = []
        g = util.m_grep(self.DieIdList)
        g.grep(':'.join([x_loc,y_loc,w_loc]))
        if g.pattern_count>0:
            a_line = g.lines[0]
            DieId = a_line.split('|')[0]
            SiteNum = a_line.split('|')[1].split(':')[-1]
            rec_start,rec_stop = a_line.split('|')[-1].split(':')
            rec_start,rec_stop = int(rec_start),int(rec_stop)
            b = util.m_grep(self.f.contents[rec_start:rec_stop])
            for a_test in test_list:
                 b.grep('Ptr:'+a_test+'\|\d\|'+SiteNum+'\|\d+')
                 b_list=b_list+b.lines
                 b.clear_cache()
            return b_list
        return []

    def GenerateDlogRecordDict(self,die_id_list,test_list):
        '''Create a dictionary with test data for multiple devices, that can be ported to the TestAnalysis class, returns a list that can be used for this'''
        #make a dictionary, store limits and results for a set of tests
        a_list = [ self.GetDlogRecord(a_die.split()[0],a_die.split()[1],a_die.split()[2],test_list) for a_die in die_id_list ]
        #['Ptr', '10068', '1', '0', '129', '0', '1.51064316611e-08', 'Leakage_IHIL_Test nstandby 46.a28', '14', '9', '9', '9', '-1.50000005306e-07', '1.00000001169e-07', 'A', '%f', '%f', '%f', '\n']
        list_seq = [1,3,6,7,12,13,14] 
        self.DlogRecordDict= dict([ (util.my_split(a_line,'[:\|]')[1],{'DieId':[':'.join(die_id_list[0].split())], 'Site':[util.my_split(a_line,'[:\|]')[3]], \
            'Result':[util.my_split(a_line,'[:\|]')[6]], 'Comment':util.my_split(a_line,'[:\|]')[7]}) for a_line in a_list[0] ])
        if len(a_list)>1:
            aRange = range(len(a_list))
            for i in aRange[1:]:
                a_part = a_list[i]
                a_die = ':'.join(die_id_list[i].split())
                for a_record in a_part:
                    a_line = util.my_split(a_record,'[:\|]',True)
                    a_test,a_result,a_site = a_line[1],a_line[6],a_line[3]
                    self.DlogRecordDict[a_test]['Result'].append(a_result)
                    self.DlogRecordDict[a_test]['Site'].append(a_site)
                    self.DlogRecordDict[a_test]['DieId'].append(a_die)
        c_list = []
        for a_test in test_list:
            aRange = range(len(self.DlogRecordDict[a_test]['Result']))
            self.DlogRecordDict[a_test]['LowerLimit'] = self.test_limits_dict[a_test]['LowerLimit']
            self.DlogRecordDict[a_test]['UpperLimit'] = self.test_limits_dict[a_test]['UpperLimit']
            self.DlogRecordDict[a_test]['Units'] = self.test_limits_dict[a_test]['Units']
            for i in aRange:
                c_list.append(':'.join([self.DlogRecordDict[a_test]['DieId'][i],a_test,self.DlogRecordDict[a_test]['Site'][i], \
                    self.DlogRecordDict[a_test]['Result'][i],self.DlogRecordDict[a_test]['Comment'],self.DlogRecordDict[a_test]['LowerLimit'],\
                    self.DlogRecordDict[a_test]['UpperLimit'],self.DlogRecordDict[a_test]['Units']]))
        return(c_list)

'''
x_loc,y_loc,w_loc = '70063 70064 70066'.split() # FT1
x_loc,y_loc,w_loc = '10063 10064 10066'.split() # FT2
a = da.ParseStdf(a_file_name,x_loc,y_loc,w_loc)
b_list = a.GetDieIdRecord(die_id_list)
a.GetFailLogList(die_id_list)
FailLogList = a.FailLogList

# build up stats table
die_id_list = [ ' '.join(util.my_split(a_line,'[:\|]')[:3]) for a_line in a.DieIdList ]
test_list = '10653 10654 10655 10656'.split()
c_list = a.GenerateDlogRecordDict(die_id_list,test_list)
g = util.m_re(c_list)
g.grep(':10653:')

t = da.TestAnalysis(g.lines,0.0049,0.090,[5],':')

#Part Results Record (Prr)
#Prr:1    |1    |0         |310       |1       |1        |-32768 |-32768 |1942   |1      |         |[]
#    Head |Site |P(0)/F(8) |Num Tests |HardBin | SoftBin |Xcoord |Ycoord |TT(ms) |PartID | PartTxt | PartFix

#To get test result, read back the site, num tests, hard bin, soft bin, and test time(ms):-> fields [1,3,4,5,8]

#Parametric Test Record (Ptr)
#Ptr:70063   |1       |1       |0        |192      |13.0   |X_Loc/NFAULT |        |14      |0        |0        |0        |0.0     |256.0   |     |%9.3f|%9.3f|%9.3f|0.0|0.0a.append(da.ParseStdf(a_file_name,x_loc,y_loc,w_loc))

#    TestNum |HeadNum |SiteNum |TestFlag |ParmFlag |Result |TestTxt      |AlarmId |OptFlag |ResScale |LlmScale |HlmScale |LoLimit |HiLimit |Units|

#To get a result from a particular test, plug in test number and site number, read back Result and Units:-> find record fields[0,2], result field [5,14]
#To get limits, plug in test number and site number, and read back LoLimit and HiLimit (fields [12,13,14]
a.append(da.ParseStdf(a_file_name,x_loc,y_loc,w_loc))

#To get DieId from Fusion: 70063(x), 70064(y), 70066(wfr)
#To get DieId from Iflex: 79466(x), 79467(y), 79469(wfr)

#make a dictionary, store limits and results for a set of tests
a_list = [ a.GetDlogRecord(a_die.split()[0],a_die.split()[1],a_die.split()[2],test_list) for a_die in die_id_list ]
#['Ptr', '10068', '1', '0', '129', '0', '1.51064316611e-08', 'Leakage_IHIL_Test nstandby 46.a28', '14', '9', '9', '9', '-1.50000005306e-07', '1.00000001169e-07', 'A', '%f', '%f', '%f', '\n']
list_seq = [1,3,6,7,12,13,14]

a_dict = dict([ (util.my_split(a_line,'[:\|]')[1],{'Site':[util.my_split(a_line,'[:\|]')[3]], 'Result':[util.my_split(a_line,'[:\|]')[6]],\
 'Comment':util.my_split(a_line,'[:\|]')[7],\
 'Lower':util.my_split(a_line,'[:\|]')[12], 'Upper':util.my_split(a_line,'[:\|]')[13], 'Units':util.my_split(a_line,'[:\|]')[14]})\
 for a_line in a_list[0] ])
test_list = a_dict.keys()
test_list.sort()

for a_part in a_list[1:]:
    for a_record in a_part:
        a_line = util.my_split(a_record,'[:\|]')
        a_test,a_result,a_site = a_line[1],a_line[6],a_line[3]
        a_dict[a_test]['Result'].append(a_result)
        a_dict[a_test]['Site'].append(a_site)

c_list = []
for a_test in test_list:
    aRange = range(len(a_dict[a_test]['Result']))
    for i in aRange:
        c_list.append(':'.join([a_test,a_dict[a_test]['Site'][i],a_dict[a_test]['Result'][i],a_dict[a_test]['Comment'],a_dict[a_test]['Lower'],\
 a_dict[a_test]['Upper'],a_dict[a_test]['Units']]))

# get test record for die id list over multiple lots, i.e. FirstPass, Rescreen, and PostBurninVerify
a = []
die_id_list = ['4 11 11']
x_loc,y_loc,w_loc = '10063 10064 10066'.split() # FT2
#file_list = \'\'\'./STDF/TAIFLEX53-1_TAS5414_COLD_PF118009_1305077_FT2_FIRST_PASS_064839.atd.gz
#... ./STDF/TAIFLEX53-1_TAS5414_COLD_PF118009_1305077_FT2_RESCREEN_AFTER_LOT_CLOSE_111536.atd.gz
#... ./RetestedOnIflex/TAS5414_Cold_Lot1305077_10192011_135446.atd.gz
#... \'\'\'.splitlines()
test_list = ['10653', '10654', '10655', '10656', '10896', '10897', '10898', '10899' ]
record_list = []
    def GenerateDlogRecordDict(self,die_id_list,test_list):
for a_file in file_list:
    a.append(da.ParseStdf(a_file_name,x_loc,y_loc,w_loc))
    record_list.append(a[-1].GenerateDlogRecordDict(die_id_list,test_list))


 '''
