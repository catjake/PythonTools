#! /usr/bin/env python
# -*- python -*-
'''envision2unison.py, keezel, 20131101
required modules:
    util,Envision2Unison,mFileDialog
    os,re,sys,optparse

snippet for test from python interpreter:
import envision2unison as e2u
e2u.test()
args_passed_in,resolved_args_dict = e2u.parse_arguments()
doc = e2u.ConvertEnvision2Unison(**resolved_args_dict)
#gui driven
doc = e2u.ConvertEnvision2Unison()
doc = e2u.ConvertEnvision2Unison(ev_patterns_path='../EvoPatterns',ev_files_path='../Evos',dest_toplevel_dir='./UnisonTopLevel')
#step-by-step
doc = e2u.ConvertEnvision2Unison(debug=True)
doc = e2u.ConvertEnvision2Unison(debug=True,ev_patterns_path='../J750AsciiPatterns',ev_files_path='../Evos',dest_toplevel_dir='./UnisonTopLevel')
#parameter assignments
if True:
    DestTopLevelDir,EvFilesPath,SkipEvFiles,EvPatternsPath,SkipEvPatterns = doc.dest_toplevel_dir,doc.ev_files_path,\
        doc.skip_ev_files,doc.ev_patterns_path,doc.skip_ev_patterns
if True: #steps from a to z
    doc.__setup_dest_directory_tree__(doc.dest_toplevel_dir,doc.ev_files_path,doc.skip_ev_files,doc.ev_patterns_path,doc.skip_ev_patterns)
    doc.__check_ev_paths__(doc.ev_files_path,doc.skip_ev_files,doc.ev_patterns_path,doc.skip_ev_patterns)
    doc.DoTheConversion()
# def __setup_dest_directory_tree__(self,DestTopLevelDir,EvFilesPath,SkipEvFiles,EvPatternsPath,SkipEvPatterns):
        mk_paths_absolute = lambda path_list:[os.path.realpath(a_path) for a_path in path_list]
        set_path_attribute = lambda orig_path_list,attribute: (False \
            if not max(os.path.isabs(a_path) for a_path in orig_path_list) else True)
        set_path_attribute = lambda orig_path_list,attribute: (False,None) \
            if not max(os.path.isabs(a_path) for a_path in orig_path_list) else \
            (True,setattr(doc,attribute,mk_paths_absolute(orig_path_list)))
        if isinstance(EvFilesPath,str): EvFilesPath = EvFilesPath.split(',')
        if isinstance(EvPatternsPath,str): EvPatternsPath = EvPatternsPath.split(',')
        if not len(DestTopLevelDir)>0:
            setattr(doc,'dest_toplevel_dir', doc.__selection_dialog__(SelectADirectory,\
                'Select Toplevel Dest Directory',\
                '\w+\.una$',\
                'Please select the toplevel directory\ndestination for the generated unison files'))
            DestTopLevelDir = doc.dest_toplevel_dir
            if not os.path.isabs(DestTopLevelDir): 
                DestTopLevelDir = os.path.realpath(DestTopLevelDir)
                setattr(doc,'dest_toplevel_dir',DestTopLevelDir)
        if not len(EvFilesPath)>0 and not SkipEvFiles:
            setattr(doc,'ev_files_path',doc.__selection_dialog__(SelectDirectories,'Select EvFiles Paths',\
                doc.EvFileExpr,\
                'Please select the directory paths\nof the envision files (Not Patterns) to convert'))
            EvFilesPath = doc.ev_files_path
            if set_path_attribute(EvFilesPath,'ev_files_path')[0]: EvFilesPath = doc.ev_files_path
        if not len(EvPatternsPath)>0 and not SkipEvPatterns:
            setattr(doc,'ev_patterns_path',doc.__selection_dialog__(SelectDirectories,'Select EvPatterns Paths',\
                doc.EvPatternExpr,\
                'Please select the directory paths\nof the envision patterns to convert'))
            EvPatternsPath = doc.ev_patterns_path
            if set_path_attribute(EvPatternsPath,'ev_patterns_path')[0]: EvPatternsPath = doc.ev_patterns_path
        if not os.path.exists(DestTopLevelDir): os.makedirs(DestTopLevelDir)
        CommonPrefix,DestSubDirDict = os.path.commonprefix(EvFilesPath+EvPatternsPath),{}
        for a_dir in EvFilesPath+EvPatternsPath:
            sub_dir = os.path.join(DestTopLevelDir,re.sub(re.compile('^\.*/'),'',a_dir.replace(CommonPrefix,'')))
            if not os.path.exists(sub_dir): os.makedirs(sub_dir)
            DestSubDirDict.update({a_dir:sub_dir})
        setattr(doc,'dest_sub_dir_dict',DestSubDirDict)
#def __selection_dialog__(self,Dialog,Title,FilePattern,Message): 
if True:
    Dialog,Title,FilePattern,Message = DestTopLevel = SelectADirectory,\
        'Select Toplevel Dest Directory','\w+\.una$',\
        'Please select the toplevel directory\ndestination for the generated unison files'
if True:
        message(title='Message',message=Message,geometry='350x80+437+349')
        fd = Dialog(Title,FilePattern)
        #return fd.app.newValue
# def DoTheConversion(self):
if True:
        doc.pm.snap()
        start_time = doc.pm.snap_time
        doc.un_files_list,start_time = [],doc.pm.snap_time
        for ev_file in doc.ev_files_list:
            doc.stdout_function('++ Working on %s:'%ev_file)
            ev_dir,ev_base = os.path.split(ev_file)
            mm,fh = EvFile2Unison(ev_file,os.path.join(doc.dest_sub_dir_dict[ev_dir],\
                re.sub(re.compile('(?P<id>\w+)\.ev(?P<ext>[\w\.]+)'),'\g<id>.un\g<ext>',ev_base)))
            doc.un_files_list.append(fh.name)
            doc.stdout_function('++    done: %f'%doc.pm.snap())
        doc.stdout_function('+ EvFiles Processing time: %f'%(doc.pm.snap_time-start_time))
        doc.un_pattern_list,pat_start_time = [],doc.pm.snap_time
        for ev_pattern in doc.ev_patterns_list:
            doc.stdout_function('++ Working on %s...'%ev_pattern)
            un_pattern = os.path.join(doc.dest_sub_dir_dict[os.path.dirname(ev_pattern)],\
                '%s.uno'%os.path.basename(ev_pattern).split('.')[0])
            doc.un_patterns_list.append(EvPattern2Un(ev_pattern,un_pattern))
            doc.stdout_function('++  done: %f'%doc.pm.snap())
        doc.stdout_function('+ Total Processing time: %f'%(doc.pm.snap_time-start_time))

'''
import util,os,re,sys
import Envision2Unison
from Envision2Unison import unison_header,EvFile2Unison,EvPattern2Un
from mFileDialog import message,SelectADirectory,SelectDirectories
#globals
REV = '0.2.5'
ORIG_DATE = '20131113:1743:46' #latest rev, initial rev 20131101
mandatory_options = [] #'ev_files_path dest_toplevel_dir'.split(), none, so GUI can take over
version = sys.hexversion
prog_description = '''Convert one or more enVision program files into Unison.\n
If no options are used, then envision file selection and destination directory for converted unison files is\n
prompted by GUI's.  Typical options would be the --ev_files_path, --dest_toplevel_dir, and --verbose=True'''
prog_name = 'envision2unison.py'
prog_epilog = '''--ev_files_path can be an absolute or relative path, for multiple directories separated by comma.'''
args_dict = { \
    'debug':{'option':'--debug','help':'special hook for debugging the python script','action':'debug','type':bool,'default':False}, \
    'ev_files_path':{'option':'--ev_files_path','help':'One or more directories of enVision files (not patterns, see ev_patterns_path option) to convert','action':'ev_files_path','type':str,'default':''}, \
    'skip_ev_files':{'option':'--skip_ev_files','help':'Skip over ev file conversion','action':'skip_ev_files','type':bool,'default':False}, \
    'ev_patterns_path':{'option':'--ev_patterns_path','help':'One or more directories, seperated by comma, of enVision patterns to convert','action':'ev_patterns_path','type':str,'default':''}, \
    'skip_ev_patterns':{'option':'--skip_ev_patterns','help':'Skip over ev pattern conversion','action':'skip_ev_patterns','type':bool,'default':False}, \
    'make_skeleton_prog':{'option':'--make_skeleton_prog','help':'NOT Implemented:  Import barebones object types, i.e. adapterboard, spec, mask, levels, etc to facilitate loading a freshly converted program','action':'make_skeleton_prog','type':bool,'default':False}, \
    'dest_toplevel_dir':{'option':'--dest_toplevel_dir','help':'designated toplevel directory for all unison files that are converted from envision','action':'dest_toplevel_dir','type':str,'default':''}, \
    'chk_subdirectories':{'option':'--chk_subdirectories','help':'check subdirectories from ev_patterns_path and ev_files_path','action':'chk_subdirectories','type':bool,'default':False}, \
    'verbose':{'option':'--verbose','help':'print everything under the sun','action':'verbose','type':bool,'default':True} \
}
def test():
    '''ipython --verbose=True --chk_subdirectories=False --dest_toplevel_dir=./UnisonProg --ev_patterns_path=./Patterns --ev_files_path=./,./Prog'''
    sys.argv.append('--ev_files_path=./,./Prog')#abs or rel path of envision files
    sys.argv.append('--ev_patterns_path=./Patterns')#abs or rel path of envision pattern files
    sys.argv.append('--dest_toplevel_dir=./UnisonProg')#Dest of unison files
    sys.argv.append('--chk_subdirectories=False')
    sys.argv.append('--verbose=True')
def parse_arguments():
    type_cast = lambda a_type,a_value:a_type(a_value)
    positional_arguments = mandatory_options
    optional_arguments = 'dest_toplevel_dir make_skeleton_prog verbose chk_subdirectories ev_files_path ev_patterns_path verbose debug'.split()
    resolved_args_dict = dict([ (a_key,None) for a_key in args_dict.iterkeys() ])
    usage_string = '%s %s'%(prog_name,' '.join(positional_arguments))
    from optparse import OptionParser #handler for args from sys.argv
    parser = OptionParser(usage=usage_string, description=prog_description, \
        version="%s Rev: %s, %s"%(prog_name,REV,ORIG_DATE))
    for a_arg in sorted(args_dict.iterkeys()):
        a_dict = args_dict[a_arg]
        if util.in_list(a_dict['option'],'^--\w+'):
            if a_dict['type'] == type(True): 
                parser.add_option(a_dict['option'],dest=a_dict['action'],help=a_dict['help'],default=a_dict['default'])
            elif not a_dict['type']:
                parser.add_option(a_dict['option'],dest=a_dict['action'],help=a_dict['help'],default=a_dict['default'])
            else:
                parser.add_option(a_dict['option'],dest=a_dict['action'],type=a_dict['type'],help=a_dict['help'],default=a_dict['default'])
    (options,args) = parser.parse_args()
    args_passed_in = [ (a_key,resolved_args_dict.update({a_key:arg}))[0] for a_key,arg in zip(positional_arguments,args) ]
    args_passed_in += [ (a_key,resolved_args_dict.update(\
        {a_key:type_cast(args_dict[a_key]['type'],eval('options.%s'%args_dict[a_key]['action']))})\
        )[0] for a_key in optional_arguments if eval('options.%s'%args_dict[a_key]['action']) ]
    # need to reset any args that are "None" to their default value in args_dict
    for a_key in args_dict.iterkeys():
        if resolved_args_dict.has_key(a_key):
            if resolved_args_dict[a_key] == None and not args_dict[a_key]['default'] == None:
                resolved_args_dict.update({a_key:args_dict[a_key]['default']})
    if len(args_passed_in)>0 and len(mandatory_options)>0:
        chk_options_list = [ a_option in args_passed_in for a_option in mandatory_options ]
    else: chk_options_list = [True]
    if not min(chk_options_list):
        parser.print_help()
        sys.exit(-2)
    return (args_passed_in,resolved_args_dict)
class ConvertEnvision2Unison:
    EvPatternExpr='\\b\w+\.evo(?:.gz)?$'
    EvFileExpr='\\b\w+\.ev[ao]$'
    def __init__(self,**kwargs):
        self.__set_attribute_defaults()
        self.__match_up_kwargs(kwargs)
        if self.debug: pass
        else:
            self.__setup_dest_directory_tree__(self.dest_toplevel_dir,self.ev_files_path,self.skip_ev_files,self.ev_patterns_path,self.skip_ev_patterns)
            if not self.__check_ev_paths__(self.ev_files_path,self.skip_ev_files,self.ev_patterns_path,\
                self.skip_ev_patterns): pass
            else: self.DoTheConversion()
        pass
    def DoTheConversion(self):
        self.pm.snap()
        start_time = self.pm.snap_time
        self.un_files_list,start_time = [],self.pm.snap_time
        for ev_file in self.ev_files_list:
            self.stdout_function('++ Working on %s:'%ev_file)
            ev_dir,ev_base = os.path.split(ev_file)
            mm,fh = EvFile2Unison(ev_file,os.path.join(self.dest_sub_dir_dict[ev_dir],\
                re.sub(re.compile('(?P<id>\w+)\.ev(?P<ext>[\w\.]+)'),'\g<id>.un\g<ext>',ev_base)))
            self.un_files_list.append(fh.name)
            self.stdout_function('++    done: %f'%self.pm.snap())
        self.stdout_function('+ EvFiles Processing time: %f'%(self.pm.snap_time-start_time))
        self.un_pattern_list,pat_start_time = [],self.pm.snap_time
        for ev_pattern in self.ev_patterns_list:
            self.stdout_function('++ Working on %s...'%ev_pattern)
            un_pattern = os.path.join(self.dest_sub_dir_dict[os.path.dirname(ev_pattern)],\
                '%s.uno'%os.path.basename(ev_pattern).split('.')[0])
            self.un_patterns_list.append(EvPattern2Un(ev_pattern,un_pattern))
            self.stdout_function('++  done: %f'%self.pm.snap())
        self.stdout_function('+ Total Processing time: %f'%(self.pm.snap_time-start_time))
    def __check_ev_paths__(self,EvFilesPath,SkipEvFiles,EvPatternsPath,SkipEvPatterns):
        ev_files_list,ev_patterns_list = [],[]
        if self.chk_subdirectories:
            __get_dir_contents__ = lambda a_dir:util.SysCommand('find %s'%a_dir)
        else:
            __get_dir_contents__ = lambda a_dir:util.GetFileListing(os.path.join(a_dir,'*.*'),'-1')
        get_files = lambda search_expr,a_dir: util.keep_in_list(__get_dir_contents__(a_dir).output,search_expr)
        if not SkipEvFiles:
            ev_files_list = util.unique_sub_list(util.flatten_list(\
                [get_files(self.EvFileExpr,a_dir) for a_dir in EvFilesPath]))
            if len(ev_files_list)>0: setattr(self,'ev_files_list',ev_files_list)
        if not SkipEvPatterns:
            ev_patterns_list = util.unique_sub_list(util.flatten_list(\
                [get_files(self.EvPatternExpr,a_dir) for a_dir in EvPatternsPath]))
            if len(ev_patterns_list)>0: setattr(self,'ev_patterns_list',ev_patterns_list)
        return ((len(ev_files_list)+len(ev_patterns_list))>0)
    def __setup_dest_directory_tree__(self,DestTopLevelDir,EvFilesPath,SkipEvFiles,EvPatternsPath,SkipEvPatterns):
        '''Check for the destination directory and ev files/patterns paths, if one or more 
        are empty, run the file dialog gui to fill those in.  Also generate dest_sub_dir_dict, 
        to be used for populating the top level destination directory'''
        mk_paths_absolute = lambda path_list:[os.path.realpath(a_path) for a_path in path_list]
        set_path_attribute = lambda orig_path_list,attribute: ((None,False) \
            if max(os.path.isabs(a_path) for a_path in orig_path_list) else
            setattr(self,attribute,mk_paths_absolute(orig_path_list)),True)
        set_path_attribute = lambda orig_path_list,attribute: (False,None) \
            if not max(os.path.isabs(a_path) for a_path in orig_path_list) else \
            (True,setattr(self,attribute,mk_paths_absolute(orig_path_list)))
        if isinstance(EvFilesPath,str): EvFilesPath = EvFilesPath.split(',')
        if isinstance(EvPatternsPath,str): EvPatternsPath = EvPatternsPath.split(',')
        if not len(DestTopLevelDir)>0:
            setattr(self,'dest_toplevel_dir', self.__selection_dialog__(SelectADirectory,\
                'Select Toplevel Dest Directory',\
                '\w+\.una$',\
                'Please select the toplevel directory\ndestination for the generated unison files'))
            DestTopLevelDir = self.dest_toplevel_dir
            if not os.path.isabs(DestTopLevelDir): 
                DestTopLevelDir = os.path.realpath(DestTopLevelDir)
                setattr(self,'dest_toplevel_dir',DestTopLevelDir)
        if not len(EvFilesPath)>0 and not SkipEvFiles:
            setattr(self,'ev_files_path',self.__selection_dialog__(SelectDirectories,'Select EvFiles Paths',\
                self.EvFileExpr,\
                'Please select the directory paths\nof the envision files (Not Patterns) to convert'))
            EvFilesPath = self.ev_files_path
            if set_path_attribute(EvFilesPath,'ev_files_path')[0]: EvFilesPath = self.ev_files_path
        if not len(EvPatternsPath)>0 and not SkipEvPatterns:
            setattr(self,'ev_patterns_path',self.__selection_dialog__(SelectDirectories,'Select EvPatterns Paths',\
                self.EvPatternExpr,\
                'Please select the directory paths\nof the envision patterns to convert'))
            EvPatternsPath = self.ev_patterns_path
            if set_path_attribute(EvPatternsPath,'ev_patterns_path')[0]: EvPatternsPath = self.ev_patterns_path
        if not os.path.exists(DestTopLevelDir): os.makedirs(DestTopLevelDir)
        SubDirs,DestSubDirDict = self.__get_dest_sub_dirs__(EvFilesPath+EvPatternsPath),{}
        for a_dir,sub_dir in zip((EvFilesPath+EvPatternsPath),SubDirs):
            sub_dir_path = os.path.join(DestTopLevelDir,sub_dir)
            if not os.path.exists(sub_dir_path): os.makedirs(sub_dir_path)
            DestSubDirDict.update({a_dir:sub_dir_path})
        setattr(self,'dest_sub_dir_dict',DestSubDirDict)
    def __get_dest_sub_dirs__(self,path_list):
        chk_list = [ [j for j in xrange(len(path_list)) if j!=i] for i,a_path in enumerate(path_list) ]
        common_index = min(\
            min(\
            max(j for j,a_dir,b_dir in zip(util.InfiniteCounter(start=-1),a_path.split('/'),path_list[i].split('/')) \
            if cmp(b_dir,a_dir)==0 ) \
            for i in a_range )\
            for a_range,a_path in zip(chk_list,path_list) )
        ci = common_index+1
        tree = '/'.join(path_list[0].split('/')[:ci])+'/'
        branches = util.unique_sub_list([a_path.replace(tree,'').split('/')[0] for a_path in path_list])
        return util.flatten_list([[a_path.replace(tree,'') for a_path in path_list \
            if cmp(a_branch,a_path.split('/')[ci]) == 0] for a_branch in branches])
    def __selection_dialog__(self,Dialog,Title,FilePattern,Message):
        message(title='Message',message=Message,geometry='350x80+437+349')
        fd = Dialog(Title,FilePattern,start_path=self.__cwd__)
        self.__cwd__ = fd.app.myDirectory
        fd.app.toplevel.update_idletasks()
        return fd.app.newValue
    def __set_attribute_defaults(self):
        self.attributes_dict = { \
            '__cwd__':{'attribute':'__cwd__','default':os.getcwd()}, \
            'debug':{'attribute':'debug','default':False}, \
            'ev_files_path':{'attribute':'ev_files_path','default':[]}, \
            'skip_ev_files':{'attribute':'skip_ev_files','default':False}, \
            'ev_patterns_path':{'attribute':'ev_patterns_path','default':[]}, \
            'skip_ev_patterns':{'attribute':'skip_ev_patterns','default':False}, \
            'dest_toplevel_dir':{'attribute':'dest_toplevel_dir','default':''}, \
            'make_skeleton_prog':{'attribute':'make_skeleton_prog','default':False}, \
            'chk_subdirectories':{'attribute':'chk_subdirectories','default':False}, \
            'verbose':{'attribute':'verbose','default':True}, \
            'dest_sub_dir_dict':{'attribute':'dest_sub_dir_dict','default':[]}, \
            'ev_files_list':{'attribute':'ev_files_list','default':[]}, \
            'ev_patterns_list':{'attribute':'ev_patterns_list','default':[]}, \
            'un_files_list':{'attribute':'un_files_list','default':[]}, \
            'un_patterns_list':{'attribute':'un_patterns_list','default':[]}, \
            'pm':{'attribute':'pm','default':util.Profiler()}, \
            'pm_info':{'attribute':'pm_info','default':[]}}
        for a_dict in self.attributes_dict.itervalues(): setattr(self,a_dict['attribute'],a_dict['default'])
    def __match_up_kwargs(self,kwargs):
        for a_key,a_value in kwargs.iteritems():
            if self.attributes_dict.has_key(a_key) and a_value: 
                if util.in_list(a_key,'\\bev_(?:patterns|dir)_path\\b'): # directory listing attribute type
                    setattr(self,self.attributes_dict[a_key]['attribute'],a_value.split(','))
                else:
                    setattr(self,self.attributes_dict[a_key]['attribute'],a_value)
    def stdout_function(self,a_list=[],append_to_pm_info=True):
        if isinstance(a_list,str): a_list = [a_list]
        if not self.verbose: stdout_function = self.null_console_output
        else: stdout_function = self.print_wrapper
        stdout_function(a_list)
        if append_to_pm_info: self.pm_info += a_list
    def null_console_output(self,a_list=[]):
        pass
    def print_wrapper(self,a_list=[]):
        util.PrettyPrint(a_list)
def main():
    args_passed_in,resolved_args_dict = parse_arguments()
    try:
        doc = ConvertEnvision2Unison(**resolved_args_dict)
    except Exception, e:
        print "Uh Oh, safe Error: %s"%(e)
        exc_type,exc_value,exc_traceback = sys.exc_info()
        traceback.print_exc()
if __name__ == "__main__":
    main()
