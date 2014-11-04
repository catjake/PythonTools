import util,os,commands
import get_file_tree
from get_file_tree import EnvisionTree
#eva_uic.....
if True:
    #snippet from def open_file(self): -- class EvaApplication_events
    if True:
        a.evaprog_mb.entryconfig(index=a.evaprog_filter_menu_index, state=ACTIVE) #filter_ev_mb
        a.evaprog_mb.entryconfig(index=a.evaprog_filter_menu_index+1, state=ACTIVE) #ev_tools_mb
        a._fill_ev_obj_dict() #each key is a 2 element list
        a.object_types=util.sort_unique(util.split_list(a.ev_object_listing,':'))
        a._create_filter_ev_mb()
        #dump object listing into listbox
        a._fill_list_box(util.split_list(a.ev_object_listing,':',1))

#EnvisionTree breakdown
et = EnvisionTree(a_file,a_dir,verbose=True)
if True:
    #def get_file_tree(self):
    if True:
        '''The main workhorse from get_file_tree.py:  Fills data base with envision
        objects from eva_file passed in, or looks for all eva's and builds a database
        for each one.'''
        done = 0  #used as boolean to determine when all ev files have been parsed
        index = 0 #used to track external references
        et.extern_file_list=[]
        et.ref_path_list=[]
        log_string=""
        et.file_list.append(et.eva_path+os.sep+et.eva)
        et.ref_path = et.eva_path
        et.ref_path_list.append(et.ref_path)
        while not done:
            log_str =""
            a_file_list = et.file_list
            index+=1
            bob=len(et.file_list)
            et.current_file = et.file_list[index-1]
            #check for TESTER environment variable, can set from EvaProg menu, defaults to FX1
            if et.current_file.find('TESTER'):
                et.current_file = et.fill_in_TESTER_var(et.current_file)
            check_file = util.FileUtils(et.current_file)
            if len(check_file.file) > 0:
                log_str ="file is: "+check_file.file+" index is: "+str(index)+" file list length is "+str(bob)
                if check_file.is_path_relative():
                    is_a_file=False
                    i = 0
                    rel_dir = check_file.dir
                    while not is_a_file:
                        check_file.dir = rel_dir #reset relative path on each pass
                        if i < len(et.ref_path_list):
                            abs_path = check_file.make_absolute_path(et.ref_path_list[i])
                        else: 
                            et.stdout_func('%s%s%s'%("File: ",check_file.file," does not exist"))
                            break
                        if check_file.is_file(): is_a_file=True
                        else: i+=1
                    if is_a_file:
                        et.current_file = abs_path+os.sep+check_file.file
                        # update reference path for any extern refs that use relative path from file referenced
                        if abs_path not in et.ref_path_list:
                            et.ref_path_list.append(abs_path)
                if check_file.is_file():
                    et.all_lines = et._read_file()
                    #et.ev_handle.ev_stuff_object('^[A-Z][A-Za-z_]+\s+',et.all_lines)
                    et.stdout_func('checked file is: %s'%check_file.nm)
                    et.ev_handle.ev_stuff_object('^\s*(?:__)?[A-Z]\w+\s+.*{',et.all_lines)
                    command_str='grep "^_*ExternalRef" %s | wc -l'%et.current_file
                    et._update_ev_file_reference(et.current_file, et.ev_handle.object_listing)
                    has_external_ref = int(commands.getoutput(command_str))
                    et.extern_file_list.append(et.current_file)
            else:
                has_external_ref = 0
            if has_external_ref:
                log_str = log_str+" with "+str(has_external_ref)+" external refs"
                et._get_externs()
            et.stdout_func(log_str)
            if len(log_str)>0:
                et.file_stats_listing.append(log_str)
            if index==len(et.file_list): done=1
        et.access_count = et.ev_handle.access_count
        et.file_stats_listing.append( "access instance ev_stuff_object "+str(et.access_count) )
        et.ev_object_listing = et.ev_handle.object_listing #should be same list as pdb.keys()
        et.pdb["KeyListing"] = et.ev_object_listing 
        et.pdb["FileStatsLog"] = et.file_stats_listing
        et.pdb["ev_file_reference"] = et.ev_file_reference
        et.pdb.close()
if True:
    #def _get_externs(self):
    if True:
        '''Parse through envision files to find external reference files.
         In the process, load all envision objects into a persistant data base.'''
        external_ref_list = util.keep_in_list(et.pdb.iterkeys(),'ExternalRef')
        for eachKey in external_ref_list:
            # -- extern_file = et._get_extern_stats(''.join(et.pdb[eachKey]).strip().split(';'))
            # InLine: --**-- begin def _get_extern_stats --**--
            extern_listing = ''.join(et.pdb[eachKey]).strip().split(';')
            PathName, FileName, et.is_ev_file = '', '', False
            g = util.m_grep(extern_listing)
            g.grep('(File|Path)')
            path_index, file_index = util.find_index(g.m_groups,'Path'), util.find_index(g.m_groups,'File')
            if path_index > -1: PathName = g.lines[path_index].split('"')[1]+os.sep
            FileName = PathName+g.lines[file_index].split('"')[1]
            et.is_ev_file = len(util.grep_list(os.path.splitext(FileName)[1],'(?:ev|un)[ao]')) > 0
            extern_file = FileName
            # InLine: --**-- end def _get_extern_stats --**--
            #print "EnvisionTree._get_externs: file= %s"%extern_file
            if et.is_ev_file and (extern_file not in et.file_list):
                et.file_list.append(extern_file)
if True:
    extern_listing = ''.join(et.pdb[eachKey]).strip().split(';')
    #def _get_extern_stats(self,extern_listing):
    if True:
        '''extern_listing is a list of strings, looking for Path and File parameters '''
        PathName, FileName, et.is_ev_file = '', '', False
        g = util.m_grep(extern_listing)
        g.grep('(File|Path)')
        path_index, file_index = util.find_index(g.m_groups,'Path'), util.find_index(g.m_groups,'File')
        if path_index > -1: PathName = g.lines[path_index].split('"')[1]+os.sep
        FileName = PathName+g.lines[file_index].split('"')[1]
        et.is_ev_file = len(util.grep_list(os.path.splitext(FileName)[1],'(?:ev|un)[ao]')) > 0
        return(FileName)
