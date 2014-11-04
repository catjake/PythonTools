import commands,string,shelve,re,sys,os,threading,time
import util
import ev_get_object
from time import sleep, time, ctime
from ev_get_object import *
#for debug stuff
TimeStamp = '20130816:1302:10'

class EnvisionTree:
    Version = '1.1_20130816:1302:10'
    def __init__(self,eva_prog,eva_path,verbose=False):
        self.__set_attributes__(eva_prog,eva_path,verbose)
    def __set_attributes__(self,eva_prog,eva_path,verbose):
        self.eva=eva_prog
        self.eva_path=eva_path
        # open a persistant storage holder
        self.pdb=shelve.open(eva_path+os.sep+eva_prog.split('.')[0]+'.dbm')
        self.dbm_file = eva_path+os.sep+eva_prog.split('.')[0]+'.dbm'
        self.ev_handle=GetEvObjects(self.pdb)
        self.extern_path=self.eva_path
        self.file_list=[]
        self.ev_object_listing=[]
        self.ev_file_reference={}
        self.all_lines=[]
        self.current_file='file_name_with_path'
        self.file_stats_listing=[]
        self.TESTER = 'FX1'
        self.has_TESTER_var()
        self.verbose = verbose
    def _read_file(self):    
        try:
            filehandle = open(self.current_file, 'r')
            fileContents = filehandle.readlines()
            filehandle.close()
        # if not, display usage and exit
        except:
            self.stdout_func('%s%s%s'%(self.current_file, ":", sys.exc_info() [1]))
            fileContents=[]
        return(fileContents)
    def has_TESTER_var(self):
        if commands.getoutput('echo $TESTER'):
            self.TESTER = commands.getoutput('echo $TESTER')
            self.stdout_func(self.TESTER)
            return True
        else:
            return False
    def  fill_in_TESTER_var(self,dir_path):
        pat = re.compile('(\${?TESTER}?)')
        m = re.search(pat,dir_path)
        if m != None:
            return dir_path.replace(m.group(1),self.TESTER)
        else:
            return dir_path
    def _update_ev_file_reference(self,file_name,object_list):
        self.ev_file_reference[file_name]=[]
        for obj in object_list:
            try:
                self.ev_file_reference[file_name].append(obj.split(':')[-1])
            except AttributeError:
                self.stdout_func('%s%s%s'%(file_name,': ', obj))
                raise
    def _get_extern_stats(self,extern_listing):
        '''extern_listing is a list of strings, looking for Path and File parameters '''
        PathName, FileName, self.is_ev_file = '', '', False
        g = util.m_grep(extern_listing)
        g.grep('(File|Path)')
        path_index, file_index = util.find_index(g.m_groups,'Path'), util.find_index(g.m_groups,'File')
        if path_index > -1: PathName = g.lines[path_index].split('"')[1]+os.sep
        FileName = PathName+g.lines[file_index].split('"')[1]
        self.is_ev_file = len(util.grep_list(os.path.splitext(FileName)[1],'(?:ev|un)[ao]')) > 0
        return(FileName)
    def _get_externs(self):
        '''Parse through envision files to find external reference files.
         In the process, load all envision objects into a persistant data base.'''
        external_ref_list = util.keep_in_list(self.pdb.iterkeys(),'ExternalRef')
        for eachKey in external_ref_list:
            extern_file = self._get_extern_stats(''.join(self.pdb[eachKey]).strip().split(';'))
            #print "EnvisionTree._get_externs: file= %s"%extern_file
            if self.is_ev_file and (extern_file not in self.file_list):
                self.file_list.append(extern_file)
    def get_file_tree(self):
        '''The main workhorse from get_file_tree.py:  Fills data base with envision
        objects from eva_file passed in, or looks for all eva's and builds a database
        for each one.'''
        done = 0  #used as boolean to determine when all ev files have been parsed
        index = 0 #used to track external references
        self.extern_file_list=[]
        self.ref_path_list=[]
        log_string=""
        self.file_list.append(self.eva_path+os.sep+self.eva)
        self.ref_path = self.eva_path
        self.ref_path_list.append(self.ref_path)
        while not done:
            log_str =""
            a_file_list = self.file_list
            index+=1
            bob=len(self.file_list)
            self.current_file = self.file_list[index-1]
            #check for TESTER environment variable, can set from EvaProg menu, defaults to FX1
            if self.current_file.find('TESTER'):
                self.current_file = self.fill_in_TESTER_var(self.current_file)
            check_file = util.FileUtils(self.current_file)
            if len(check_file.file) > 0:
                log_str ="file is: "+check_file.file+" index is: "+str(index)+" file list length is "+str(bob)
                if check_file.is_path_relative():
                    is_a_file=False
                    i = 0
                    rel_dir = check_file.dir
                    while not is_a_file:
                        check_file.dir = rel_dir #reset relative path on each pass
                        if i < len(self.ref_path_list):
                            abs_path = check_file.make_absolute_path(self.ref_path_list[i])
                        else: 
                            self.stdout_func('%s%s%s'%("File: ",check_file.file," does not exist"))
                            break
                        if check_file.is_file(): is_a_file=True
                        else: i+=1
                    if is_a_file:
                        self.current_file = abs_path+os.sep+check_file.file
                        # update reference path for any extern refs that use relative path from file referenced
                        if abs_path not in self.ref_path_list:
                            self.ref_path_list.append(abs_path)
                if check_file.is_file():
                    self.all_lines = self._read_file()
                    #self.ev_handle.ev_stuff_object('^[A-Z][A-Za-z_]+\s+',self.all_lines)
                    self.stdout_func('checked file is: %s'%check_file.nm)
                    self.ev_handle.ev_stuff_object('^\s*(?:__)?[A-Z]\w+\s+.*{',self.all_lines)
                    command_str='grep "^_*ExternalRef" %s | wc -l'%self.current_file
                    self._update_ev_file_reference(self.current_file, self.ev_handle.object_listing)
                    has_external_ref = int(commands.getoutput(command_str))
                    self.extern_file_list.append(self.current_file)
            else:
                has_external_ref = 0
            if has_external_ref:
                log_str = log_str+" with "+str(has_external_ref)+" external refs"
                self._get_externs()
            self.stdout_func(log_str)
            if len(log_str)>0:
                self.file_stats_listing.append(log_str)
            if index==len(self.file_list): done=1
        self.access_count = self.ev_handle.access_count
        self.file_stats_listing.append( "access instance ev_stuff_object "+str(self.access_count) )
        self.ev_object_listing = self.ev_handle.object_listing #should be same list as pdb.keys()
        self.pdb["KeyListing"] = self.ev_object_listing 
        self.pdb["FileStatsLog"] = self.file_stats_listing
        self.pdb["ev_file_reference"] = self.ev_file_reference
        self.pdb.close()
    def stdout_func(self,a_list=[]):
        if self.verbose: PrettyPrint(a_list)
        else: pass
