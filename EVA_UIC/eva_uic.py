#!/usr/bin/env python
import os,sys,traceback
from Tkinter import *
import tkFont
from mFileDialog import create_selectDialog, create_selectDirectory,question, message
from get_file_tree import *
from ev_object_manager import EvObjectManager
import util
from time import time
# ****************************************************************************************
# To Do:
# add history bar to "Where Used" entry
# add a 'copy' function to the text display window.
# ****************************************************************************************
# 20121030 - put in hooks for unison file analysis

def test():
    app = EvaApplication()
    app.go()
class SelectAFile:
    def __init__(self,title='Select A File',file_pattern=".*\..*",start_path=os.getcwd(),grab_set=True):
        self.file_pattern, self.a_file = file_pattern, None
        self.do_selection(title,start_path,file_pattern,grab_set)
    def do_selection(self,window_title='Select A File',start_path=os.getcwd(),file_pattern=".*\..*",grab_set=True):
        self.create_tk_root()
        self.app = create_selectDialog(self.root)
        self.a_file = self.app.go(title=window_title,startPath=start_path,pattern=file_pattern,grab_set=grab_set)
    def create_tk_root(self):
        self.root = Tk()
        self.root.withdraw()
class SelectADirectory:
    def __init__(self,title='Select A Directory',file_pattern=".*\..*",start_path=os.getcwd(),grab_set=True):
        self.file_pattern, self.a_path,self.start_path = file_pattern, None,start_path
        self.do_selection(title,start_path,file_pattern,grab_set)
    def do_selection(self,window_title='Select A Directory',start_path=os.getcwd(),file_pattern=".*\..*",grab_set=True):
        self.create_tk_root()
        self.app = create_selectDirectory(self.root)
        self.a_path = self.app.go(title=window_title,startPath=start_path,pattern=file_pattern,grab_set=grab_set)
    def create_tk_root(self):
        self.root = Tk()
        self.root.withdraw()
class EvaApplication_gui(Frame): 
    Version = '0.84_20130816:1244:57'
    def __init__(self, master=None, verbose=False):
        Frame.__init__(self, master) 
        self.verbose = verbose
        self.grid(sticky=N+S+W+E)
        self.rowconfigure(0, weight=1)
        self.rowconfigure(1, weight=5) 
        self.columnconfigure(0, weight=1) 
        self.columnconfigure(1, weight=7) 
        self.createWidgets()
        self.set_tags()
    def open_file(self):
        fd = SelectAFile(title="Select Eva File",file_pattern=".*\.(?:ev|un")
        self.eva_file = fd.a_file
        print self.eva_file
    def version_info(self):
        print "Version: "+self.Version+" pre alpha, the horse before the cart, whatever..."
    def _create_menu_bar(self, root):
        # create menubar
        self.menubar = Menu(self)
        # add evaprog_mb to menubar
        self.evaprog_mb = Menu(self.menubar)
        self.filter_ev_mb = Menu(self.evaprog_mb)
        self.ev_tools_mb = Menu(self.evaprog_mb)
        self.menubar.add_cascade(label="EvaProg", menu=self.evaprog_mb)
        # create evaprog_mb for menubar 
        self.evaprog_mb.add_command(label="Open Ev Application", command=self.open_file)
        self.evaprog_mb.add_cascade(label="Filter Ev Objects", menu=self.filter_ev_mb, state=DISABLED)
        self.evaprog_filter_menu_index = 2
        self.evaprog_mb.add_cascade(label="Tools",menu=self.ev_tools_mb, state=DISABLED)
        self.evaprog_mb.add_separator()
        self.evaprog_mb.add_command(label="Exit", command=self.quit)
        # create help_mb for menubar 
        helpmenu = Menu(self.menubar)
        helpmenu.add_command(label="About", command =self.version_info)
        # add help_mb to menubar
        self.menubar.add_cascade(label="Help", menu=helpmenu)
    def _create_left_pane(self,root):
        self.left_frame = Frame(root, name="left_frame")
        self.left_frame_title = Label(self.left_frame,text="Query Results",anchor=NW)
        # build list box
        self.list_box = Listbox(self.left_frame, background='#f8fff0', height=19) #mint greenish, with more grey
        self.left_frame_title.grid(row=0, column=0, sticky=NW)
        self.list_box.grid(row=1, column=0, sticky=NW)
        self.list_box.columnconfigure(0,weight=1)
        self.list_box.rowconfigure(1,weight=2)
        #tie scrollbar to list_box
        yScroll = Scrollbar(self.left_frame, orient=VERTICAL)
        yScroll.grid(row=1, column=1, sticky=N+S)
        xScroll = Scrollbar(self.left_frame, orient=HORIZONTAL)
        xScroll.grid(row=2, column=0, sticky=E+W)
        self.list_box.configure(yscrollcommand=yScroll.set, xscrollcommand=xScroll.set)
        yScroll.configure(command=self.list_box.yview)
        xScroll.configure(command=self.list_box.xview)
        # build 'where used' entry object
        self.where_used_label=Label(self.left_frame,text="Where Used:",anchor=NW)
        self.where_used_label.grid(row=3,column=0,sticky=NW)
        self.where_used_entry=Entry(self.left_frame, background='#ffffff', width=20) #white
        self.where_used_entry.grid(row=4,column=0, columnspan=1, sticky=NW)
        # build 'where used' list box from previous queries
        self.where_used_list_box = Listbox(self.left_frame,background='#dcdcdc', width=20) #gainsboro
        self.where_used_list_box.grid(row=5, column=0, sticky=NW)
        self.where_used_list_box.columnconfigure(0,weight=1)
        self.where_used_list_box.rowconfigure(1,weight=2)
        #tie scrollbar to list_box
        yScroll_where_used = Scrollbar(self.left_frame, orient=VERTICAL)
        yScroll_where_used.grid(row=5, column=1, sticky=N+S)
        xScroll_where_used = Scrollbar(self.left_frame, orient=HORIZONTAL)
        xScroll_where_used.grid(row=6, column=0, sticky=E+W)
        self.where_used_list_box.configure(yscrollcommand=yScroll_where_used.set, xscrollcommand=xScroll_where_used.set)
        yScroll_where_used.configure(command=self.where_used_list_box.yview)
        xScroll_where_used.configure(command=self.where_used_list_box.xview)
        # set frame into parent window grid
        self.left_frame.grid(row=1, column=0, sticky=NW)
        self.left_frame.columnconfigure(0, weight=1, minsize=150)
        self.left_frame.rowconfigure(1,weight=1)
    def _create_right_pane(self,root):
        self.right_frame = Frame(root, name="right_frame")
        self.right_frame_title = Label(self.right_frame,text="Display Contents",anchor=NW)
        self.right_frame_title.grid(row=0,column=0,sticky=NW)
        # build text window
        defaultFont = tkFont.Font(family='Helvetica',size=10)
        self.text_window = Text(self.right_frame, font=defaultFont, background='#fff5ee', width=90) #seashell
        self.text_window.grid(row=1,column=0, sticky=NW)
        #tie scrollbars to text_window
        yScroll = Scrollbar(self.right_frame, orient=VERTICAL)
        yScroll.grid(row=1, column=1, sticky=N+S)
        xScroll = Scrollbar(self.right_frame, orient=HORIZONTAL)
        xScroll.grid(row=2, column=0, sticky=E+W)
        self.text_window.configure(yscrollcommand=yScroll.set, xscrollcommand=xScroll.set)
        yScroll.configure(command=self.text_window.yview)
        xScroll.configure(command=self.text_window.xview)
        # set frame into parent window grid
        self.right_frame.grid(row=1,column=1, sticky=NW)
        self.right_frame.columnconfigure(0, weight=1, minsize=640)
    def set_tags(self):
        standoutFont = tkFont.Font(family='lucidabright',size=13,weight="bold")
        self.text_window.tag_config("standout",foreground='blue',background='#dcdcdc') #gainsboro
        self.text_window.tag_config("standout",font=standoutFont)
        #self.text_window.tag_bind("Enter>", show_hand_cursor)
        #self.text_window.tag_bind("Leave>", show_arrow_cursor)
    def createWidgets(self):
        self.top=self.winfo_toplevel()
        self.menu_frame = Frame(self,name="menu_frame")
        self.menu_frame.grid(row=0, columnspan=2)
        self._create_menu_bar(self.menu_frame)
        self._create_left_pane(self.top)
        self._create_right_pane(self.top)
        self.top.configure(menu=self.menubar)
        self._set_window_exit_protocol()
    def _destroy_command(self):
        try:
            self.quit()
        except Exception, e:
            print 'Hmmm, looks like toplevel widget has already been destroyed, our work here is done....\n    Error: %s' % e
            exc_type,exc_value,exc_traceback = sys.exc_info()
            traceback.print_exc()
    def _set_window_exit_protocol(self,destroy_function=None):
        self.top.protocol("WM_DELETE_COMMAND",self._destroy_command if not destroy_function else destroy_function)
class EvaApplication_events(EvaApplication_gui):
    ''' define events for analyzing eva application:
    like listing out all objects such as Levels, Specs, etc.
    where used feature to track object dependencies
    export feature
    '''
    snap = time
    ev_header = 'enVision:"bl8:R10.4:S2.0";'
    
    def __init__(self,verbose=False):
        EvaApplication_gui.__init__(self,verbose=verbose)
        self._initialize()
        self._create_ev_tools_menu()
        self._define_panel_events()
    def _initialize(self):
        self.ev_tree_parse_time = 0.
        self.dbm_file =""
        self.ev_file_reference={}
        self.import_file_reference={}
        self.ev_obj_dict={}
        self.ev_obj_keys=[]
        self.import_obj_dict={}
        self.import_obj_keys=[]
        self.list_box_contents=[]
        self.where_used_list=[]
        self.where_used_str="a_str"
    def _define_panel_events(self):
        btags = self.list_box.bindtags() 
        self.list_box.bindtags(btags[1:] + btags[:1])
        self.list_box.bind('<ButtonRelease-1>', self._display_contents)
        btags = self.text_window.bindtags()
        self.text_window.bindtags(btags[1:] + btags[:1])
        self.text_window.bind('<Control-n>',self.go_to_next)
        self.text_window.bind('<Control-p>',self.go_to_previous)
        self.text_window.bind('<Control-w>',self.where_used_text_window_event)
        btags = self.where_used_entry.bindtags()
        self.where_used_entry.bindtags(btags[1:] + btags[:1])
        self.where_used_entry.bind('<Return>',self.where_used_event)
        #add bindings to select text and do where used.....
        #add bindings for moving selected objects to evo file....
    def where_used_event(self,event):
        self.where_used(self.where_used_entry.get())
    def where_used_text_window_event(self,event):
        self.where_used(self.text_window.selection_get())
    def where_used(self,aString):
        self.where_used_list=[]
        self.where_used_str= aString
        a_list = []
        for objKey in self.ev_obj_keys:
            if util.in_list(self.ev_obj_dict[objKey][1],aString):
                self.where_used_list.append(objKey)
                #now generate contents for list box, and modify _display_contents for where_used clause    
                a_list = self.text_window.get('0.0','end').split('\n')
        util.add_cr(a_list)
        self.update_text_window(a_list)
        self._highlight_where_used_str()
        self._fill_list_box(self.where_used_list)
    def _highlight_where_used_str(self):
        a_list = self.text_window.get('0.0','end').split('\n')
        str_length = len(self.where_used_str)
        g = util.m_grep(a_list)
        g.grep(self.where_used_str)
        if g.pattern_count > 0:
            #print g.m_groups g.coordinates
            self.current_where_used_list = [ int(float(a_coordinate))-1 for a_coordinate in g.coordinates ]
            self.num_lines_where_used_list = len(a_list)
            self.where_used_go_to_next_index = 0
            self.where_used_go_to_prev_index = len(self.current_where_used_list)-1
        for coordinate in g.coordinates:
            a_str = g.m_groups[g.coordinates.index(coordinate)]
            str_length = len(a_str)
            end_pt = str(coordinate[:coordinate.find('.')+1])+ \
            str(int(coordinate[coordinate.find('.')+1:])+str_length)
            self.text_window.tag_add('standout',coordinate,end_pt)
    def _display_contents(self, event):
        display_list = self.ev_obj_dict[self.list_box.get('active')][1]
        self.update_text_window(display_list)
        if cmp(self.where_used_str,'')>0:
            self._highlight_where_used_str()
    def update_text_window(self,a_list):
        self.text_window.delete('0.0','end')
        for aLine in a_list:
            self.text_window.insert('end',aLine)
    def go_to_next(self, event):
        self.text_window.yview_moveto(float(self.current_where_used_list[self.where_used_go_to_next_index])/self.num_lines_where_used_list)
        if self.where_used_go_to_prev_index > 0: self.where_used_go_to_prev_index = self.where_used_go_to_next_index-1 
        else: self.where_used_go_to_prev_index = len(self.current_where_used_list)-1 
        self.where_used_go_to_next_index += 1
        if self.where_used_go_to_next_index>= len(self.current_where_used_list): self.where_used_go_to_next_index = 0
    def go_to_previous(self, event):
        self.text_window.yview_moveto(float(self.current_where_used_list[self.where_used_go_to_prev_index])/self.num_lines_where_used_list)
        if self.where_used_go_to_next_index< len(self.current_where_used_list)-1: self.where_used_go_to_next_index = self.where_used_go_to_prev_index+1
        else: self.where_used_go_to_next_index = 0
        self.where_used_go_to_prev_index -= 1
        if self.where_used_go_to_prev_index < 0: self.where_used_go_to_prev_index = len(self.current_where_used_list)-1
    def _fill_ev_obj_dict(self):
        self.ev_obj_dict={}
        self.ev_obj_keys=[]
        for aKey in self.ev_object_listing:
            self.ev_obj_dict[aKey.split(':')[-1]] = [aKey.split(':')[0], self.pdb[aKey] ]
        self.ev_obj_keys = self.ev_obj_dict.keys()
    def _fill_list_box(self,a_list):
        self.list_box.configure(selectmode='single')
        self.left_frame_title.configure(text='Query Results')
        self.list_box_contents=[]
        self.list_box.delete(0,END)
        util.my_sort(a_list)
        for aLine in a_list:
            self.list_box_contents.append(aLine)
            self.list_box.insert(END,aLine)
    def apply_filter(self):
        update_list=[]
        update_list=self.list_box_contents
        for obj_type in self.object_types:
           if self.show_object[obj_type].get():
               for eachMember in self.obj_cat_list[obj_type]:
                   if eachMember not in self.list_box_contents: update_list.append(eachMember)
           else:
               for eachMember in self.obj_cat_list[obj_type]:
                   if eachMember in self.list_box_contents:
                           update_list.remove(eachMember)
           self._fill_list_box(update_list)
    def _create_ev_tools_menu(self):
        # import/export, with ev_header.
        self.ev_tools_mb.add_command(label="Import", command=self._import_ev_object)
        # read Catalyst tp patterns and convert to enVision
    def _create_filter_ev_mb(self):
        self.show_object={}
        self.obj_cat_list={}
        self.filter_ev_mb.delete(1,END)
        for obj_type in self.object_types:
            self.show_object[obj_type] = IntVar()
            self.obj_cat_list[obj_type] = util.split_list(util.grep_list \
                (self.ev_object_listing,obj_type+':'),':',1)
            self.filter_ev_mb.add_checkbutton(label=obj_type, variable=self.show_object[obj_type], \
                command=self.apply_filter)
    def build_dbm_tree(self):
        a = self.snap()
        self.eva_tree=EnvisionTree(self.eva_file_stats.file,self.eva_file_stats.dir,verbose=self.verbose)
        self.eva_tree.get_file_tree()        
        b = self.snap() 
        self.ev_tree_parse_time = b - a
        self.ev_object_listing = self.eva_tree.ev_object_listing
        self.ev_file_reference = self.eva_tree.ev_file_reference
        self.file_stats_listing = self.eva_tree.file_stats_listing
        self.pdb=shelve.open(self.dbm_file)
        print "Ev App processing time for ",self.eva_file,"\n",self.ev_tree_parse_time," seconds"
    def _update_ev_dictionary(self,objList, ev_obj_dict, ev_obj_keys, pdb):
        for obj in objList:
            aKey = obj.split(':')[-1]
            if not self.ev_obj_dict.has_key(aKey):
                    ev_obj_dict[aKey] = [obj.split(':')[0], pdb[obj] ]
            ev_obj_keys.append(aKey)
    def _import_ev_object(self):
        self.obj_imported=[]
        self.types_imported=[]
        import_dialog= SelectAFile(self,title="Import EvObj", file_pattern=".*\.ev[ao]$")
        self.import_file = import_dialog.a_file
        if len(self.import_file) > 0:
            file_name = util.FileUtils(self.import_file)
            self.import_ev_tree = EnvisionTree(file_name.file,file_name.dir)
            self.import_ev_tree.get_file_tree()
            self.import_file_reference = self.import_ev_tree.ev_file_reference
            pdb = shelve.open(self.import_ev_tree.dbm_file)
            self.import_obj_dict = {}
            for aKey in self.import_ev_tree.ev_object_listing:
                self.import_obj_dict[aKey.split(':')[-1]] = [aKey.split(':')[0], pdb[aKey] ]
            self.import_obj_keys = self.import_obj_dict.keys()
            pdb.close()
            self.obj_manager = EvObjectManager(self.ev_file_reference, self.ev_obj_dict, \
                self.import_ev_tree.ev_file_reference, self.import_obj_dict) 
            self.obj_manager.go()
            #update filter list, if necessary, and update ev_obj_dict
            if self.obj_manager.made_changes:
                ##self._update_ev_dictionary(self.obj_manager.ev_object_listing,self.ev_obj_dict, obj_imported, pdb)
                util._dictionary_copy(self.obj_manager.ev_obj_dict,self.ev_obj_dict)
                for evFile in self.obj_manager.file_changes_dict:
                    for evObj in self.obj_manager.file_changes_dict[evFile]:
                        self.types_imported.append(self.ev_obj_dict[evObj][0])
                        self.obj_imported.append(evObj)
                        self.ev_object_listing.append(self.ev_obj_dict[evObj][0]+':'+evObj)
                util._list_copy(self.obj_imported,self.ev_obj_keys)
                util.sort_unique(self.types_imported)
                util._list_copy(self.types_imported,self.object_types)
                util.my_sort(self.object_types)
                self._create_filter_ev_mb()
                self._fill_list_box(self.obj_imported)
                self.left_frame_title.configure(text='Objects imported')
    def open_file(self):
        try: # try to close dbm file if we're opening another ev application.
            self.dbm_file.close()
        except AttributeError, NameError:
            pass
        fd = SelectAFile(title="Select Eva File",file_pattern=".*\.(?:ev|un)")
        self.eva_file = fd.a_file
        if len(self.eva_file) > 0:
            self._initialize()
            self.eva_file_stats = util.FileUtils(self.eva_file)
            self.dbm_check()
            if not self.use_dbm: # then make one
                self.build_dbm_tree()
            else:
                ask = question()
                a_title="dbm file exists"
                a_message="Overwrite existing file? \nPath: "+self.dbm_file_stats.dir \
                   +"\nFile: "+self.dbm_file_stats.file.split('.')[0]+'.dbm\n'
                build_dbm = ask.go(title=a_title, message=a_message, geometry= '400x200+412+334')
                if build_dbm:
                    os.remove(self.dbm_file)
                    self.build_dbm_tree()
                else:
                    self.pdb=shelve.open(self.dbm_file)
                    self.ev_object_listing = self.pdb["KeyListing"] 
                    self.file_stats_listing = self.pdb["FileStatsLog"]
                    self.ev_file_reference = self.pdb["ev_file_reference"]
        self.evaprog_mb.entryconfig(index=self.evaprog_filter_menu_index, state=ACTIVE) #filter_ev_mb
        self.evaprog_mb.entryconfig(index=self.evaprog_filter_menu_index+1, state=ACTIVE) #ev_tools_mb
        self._fill_ev_obj_dict() #each key is a 2 element list
        self.object_types=util.sort_unique(util.split_list(self.ev_object_listing,':'))
        self._create_filter_ev_mb()
        #dump object listing into listbox
        self._fill_list_box(util.split_list(self.ev_object_listing,':',1))
    def dbm_check(self):
        self.dbm_file = self.eva_file_stats.file.split('.')[0]+'.dbm'
        self.dbm_file = self.eva_file_stats.dir+os.sep+self.dbm_file
        self.dbm_file_stats = util.FileUtils(self.dbm_file)
        if self.dbm_file_stats.file_exists:
            self.use_dbm = self.time_stamp_compare()
        else:
            self.use_dbm = False
    def time_stamp_compare(self):
        if self.dbm_file_stats.TimeStamp() > self.eva_file_stats.TimeStamp():
            return True
        else:
            return False
class EvaApplication(EvaApplication_events):
    ''' wrapper for EvaApplication_gui and EvaApplication_events
    - build dbm database of ev objects
    - based on timestamps of eva and dbm, if built, update dbm
    - '''

    def __init__(self,verbose=False):
        EvaApplication_events.__init__(self,verbose)

    def go(self):
        self.master.title("enVision Offline Analysis")
        self._set_window_exit_protocol()
        self.mainloop()
if __name__=='__main__':
    test()
