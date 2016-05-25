from Tkinter import *
import util
import random
from get_file_tree import *
# handle objects of same name
# add obj_type to window, add obj_type filter
# implement delete command for both sides
# implement Fold, Find, Sort, Filter, Move, Delete functions 
def testEvObjectManagerGUI():
    root = Tk()
    root.withdraw()
    app = EvObjectManagerGUI(root)
    app.go()

def testselectEvRefFileGUI():
    root = Tk()
    root.withdraw()
    app = selectEvRefFileGUI(root)
    app.go()

class EvObjectManagerGUI(Toplevel):
    Version = '0.1'

    def __init__(self, master=None):
        self.toplevel= Toplevel(master)
        self.createWidgets()

    def go(self):
        self.toplevel.title("Just GUI")
        self.toplevel.grab_set()
        self.toplevel.focus_set()
        self.toplevel.wait_window()

    def version_info(self):
        a_string = '''Version: %s EvObjectManager: Not fully functional,....
	working parts: 
	       Move Selected -> add selected objects from import window to loaded evObj File container
	       Save Changes -> append moved objects to respective evObj Reference Files
	coming soon:
	       Filter by Obj Type
	       Delete Objects from imported list_box or loaded objects
	       Import more evObjects
	       ''' % self.Version
	print a_string

    def delete_selected(self):
	pass
    
    def move_selected(self):
	pass

    def clear_selected(self):
	pass

    def clear_all(self):
	pass

    def save_changes(self):
	pass

    def exit_app(self):
	self.toplevel.destroy()

    def _create_clear_import_mb(self):
	self.clear_import_mb.add_command(label="All", command=self.clear_all)
	self.clear_import_mb.add_command(label="Selected", command=self.clear_selected)

    def _create_filter_ev_mb(self):
	pass

    def _create_menu_bar(self, root):
        # create menubar
        self.menubar = Menu(self.toplevel)
        # add evaprog_mb to menubar
        self.ev_ops_mb = Menu(self.menubar)
        self.filter_ev_mb = Menu(self.ev_ops_mb)
        self.clear_import_mb = Menu(self.ev_ops_mb)
        self.menubar.add_cascade(label="Operations", menu=self.ev_ops_mb)
        # create evaprog_mb for menubar 
        self.ev_ops_mb.add_cascade(label="Filter Ev Objects", menu=self.filter_ev_mb)
        self.ev_ops_mb.add_cascade(label="Clear Import", menu=self.clear_import_mb)
        self.ev_ops_mb.add_command(label="Move Selected", command=self.move_selected)
        self.ev_ops_mb.add_command(label="Delete Selected", command=self.delete_selected)
        self.ev_ops_mb.add_separator()
        self.ev_ops_mb.add_command(label="Save Changes", command=self.save_changes)
        self.ev_ops_mb.add_command(label="Exit", command=self.exit_app)
        # create help_mb for menubar 
        helpmenu = Menu(self.menubar)
        helpmenu.add_command(label="About", command =self.version_info)
        # add help_mb to menubar
        self.menubar.add_cascade(label="Help", menu=helpmenu)

    def _create_left_pane(self,root):
	self.left_frame = Frame(root, name="left_frame")
        self.left_frame_title = Label(self.left_frame,text="Ev Object Tree",anchor=NW)
        # build list box
	self.ev_list_box = Listbox(self.left_frame,width=60, height=30, selectmode='extended')
        self.left_frame_title.grid(row=0, column=0, sticky=NW)
        self.ev_list_box.grid(row=1, column=0, sticky=NW)
        self.ev_list_box.columnconfigure(0,weight=1)
        self.ev_list_box.rowconfigure(1,weight=2)
        #tie scrollbar to list_box
        yScroll = Scrollbar(self.left_frame, orient=VERTICAL)
        yScroll.grid(row=1, column=1, sticky=N+S)
        xScroll = Scrollbar(self.left_frame, orient=HORIZONTAL)
        xScroll.grid(row=2, column=0, sticky=E+W)
        self.ev_list_box.configure(yscrollcommand=yScroll.set, xscrollcommand=xScroll.set)
        yScroll.configure(command=self.ev_list_box.yview)
        xScroll.configure(command=self.ev_list_box.xview)
        # set frame into parent window grid
        self.left_frame.grid(row=1, column=0, sticky=NW)
        self.left_frame.columnconfigure(0, weight=1, minsize=300)
        #self.left_frame.rowconfigure(1,weight=1)

    def _create_right_pane(self,root):
	self.right_frame = Frame(root, name="right_frame")
        self.right_frame_title = Label(self.right_frame,text="Objects for Import",anchor=NW)
        self.right_frame_title.grid(row=0,column=0,sticky=NW)
        # build list box
	self.import_list_box = Listbox(self.right_frame, width=60, height=30, selectmode='extended')
        self.right_frame_title.grid(row=0, column=0, sticky=NW)
        self.import_list_box.grid(row=1, column=0, sticky=NW)
        self.import_list_box.columnconfigure(0,weight=1)
        self.import_list_box.rowconfigure(1,weight=2)
        #tie scrollbar to list_box
        yScroll = Scrollbar(self.right_frame, orient=VERTICAL)
        yScroll.grid(row=1, column=1, sticky=N+S)
        xScroll = Scrollbar(self.right_frame, orient=HORIZONTAL)
        xScroll.grid(row=2, column=0, sticky=E+W)
        self.import_list_box.configure(yscrollcommand=yScroll.set, xscrollcommand=xScroll.set)
        yScroll.configure(command=self.import_list_box.yview)
        xScroll.configure(command=self.import_list_box.xview)
        # set frame into parent window grid
        self.right_frame.grid(row=1,column=1, sticky=NW)
        self.right_frame.columnconfigure(0, weight=1, minsize=300)

    def createWidgets(self):
        self.menu_frame = Frame(self.toplevel,name="menu_frame")
        self.menu_frame.grid(row=0, columnspan=2)
        self._create_menu_bar(self.menu_frame)
        self._create_clear_import_mb()
        self._create_filter_ev_mb()
        self._create_left_pane(self.toplevel)
        self._create_right_pane(self.toplevel)
	self.toplevel.configure(menu=self.menubar)

class EvObjectManager(EvObjectManagerGUI):
    Version = '0.3'
    ev_header = 'enVision:"bl8:R10.4:S2.0";'

    def __init__(self,ev_file_ref, ev_obj_dict, import_file_ref={}, import_obj_dict={}):
	EvObjectManagerGUI.__init__(self)
        self.made_changes = False
	self.ev_file_ref=ev_file_ref
	self.ev_obj_dict = ev_obj_dict
	self.import_file_ref = import_file_ref
	self.import_obj_dict = import_obj_dict
	self.import_key_list=[]
	self.transfer_objects=[]
	self.changes_dictionary={}
	self.file_changes_dict={}
	self.populate_list_boxes()

    def populate_list_boxes(self):
	self.ev_formatted_list= self.dict_2_list(self.ev_file_ref)
	self.populate_list_box(self.ev_list_box, self.ev_formatted_list)
        if len(self.import_file_ref)>0:
	    self.import_formatted_list= self.dict_2_list(self.import_file_ref)
	    self.populate_list_box(self.import_list_box,self.import_formatted_list)
    
    def populate_list_box(self, listBox, aList):
	listBox.delete(0,END)
	for aLine in aList:
	    listBox.insert(END,aLine)

    def dict_2_list(self,aDict):
	"expecting only strings for dictionary key and value(s)"
	aList=[]
	spacer='|------> '
	ListOfKeys = aDict.keys()
        EvaIndex = util.find_index(ListOfKeys,'eva')
	if EvaIndex >= 0:
	    EvaKey = ListOfKeys.pop(EvaIndex)
            aList.append('+ '+EvaKey)
            spacer = '|-----> '
            for value in aDict[EvaKey]:
	        aList.append(spacer+value)
	spacer='    |-----> '
	for aKey in ListOfKeys:
	    aList.append('   ++ '+aKey)
            for value in aDict[aKey]:
	        aList.append(spacer+value)
	return(aList)

    def _transfer_all_objects(self,aList):
	for aKey in aList:
	    self.transfer_objects.append(self.import_obj_dict[aKey])

    def _is_reference_file(self,FileName):
	self.a_file = util.FileUtils(FileName)
        return self.a_file.is_file()

    def update_change_dictionary(self,aList):
        self.changes_dictionary.clear()
	key_name = "a_string"
        fd = selectEvRefFile(self.ev_file_ref.keys())
        self.ev_obj_file = fd.go(title="Select Ev File")
        if len(self.ev_obj_file)>0:
	    if not self.changes_dictionary.has_key(self.ev_obj_file):
	        self.changes_dictionary[self.ev_obj_file] = []
	    util._list_copy(aList,self.changes_dictionary[self.ev_obj_file])
            #add appropriate items to self.ev_file_ref and self.ev_obj_dict dictionaries
            #remove appropriate items from self.import_obj_dict and self.import_file_ref dictionaries, then repopulate the list_boxes
            util._list_copy(self.changes_dictionary[self.ev_obj_file],self.ev_file_ref[self.ev_obj_file])
            for refFile in self.import_file_ref:
	        util._list_reduce(self.changes_dictionary[self.ev_obj_file],self.import_file_ref[refFile])

            for objFile in self.changes_dictionary:
	        for ev_obj in self.changes_dictionary[objFile]:
		    key_name = ev_obj
		    if self.ev_obj_dict.has_key(ev_obj): #multiple ev objects of same name
			key_name +="_"+str(random.randint(100,10000))
		    self.ev_obj_dict[key_name] = self.import_obj_dict.pop(ev_obj)

            print "import_file_ref: ",self.import_file_ref
            print "changes_dict: ",self.changes_dictionary
            self.populate_list_boxes()
            if not self.file_changes_dict.has_key(self.ev_obj_file):
		self.file_changes_dict[self.ev_obj_file] = self.changes_dictionary[self.ev_obj_file]
	    else:
	        util._list_copy(self.changes_dictionary[self.ev_obj_file],self.file_changes_dict[self.ev_obj_file])
            

    def append_to_file(self,aFile,aList):
	fh = util.FileUtils(self.ev_obj_file)
        fh.append_to_file(aList)
        aList=[]

    def delete_selected(self):
#use .curselection() to get tuple of selected lines
#use .delete(first, last=None) to wipe out each line, in reverse
	pass
    
    def move_selected(self):
    #can only be done from import list box, add members to ev_obj_dict, if file selected, move all members of
    #said file to ev_obj_dict, then add selected file to ev_file_reference
	self.transfer_objects=[]
        import_index_list = self.import_list_box.curselection()
        for i in import_index_list:
            currentObject = self.import_formatted_list[int(i)].split(' ')[-1]
	    self.import_key_list.append(currentObject)
	    if self._is_reference_file(currentObject):
		self._transfer_all_objects(self.import_file_ref[currentObject])
            else:
	        self.transfer_objects.append(currentObject)
        self.update_change_dictionary(self.transfer_objects)
        print "file_changes_dict: ",self.file_changes_dict

    def save_changes(self):
	for aFile in self.file_changes_dict:
	    for evObj in self.file_changes_dict[aFile]:
	        aList = self.ev_obj_dict[evObj][-1]
                self.append_to_file(aFile,aList)
        self.made_changes = True
        self.exit_app()

    def clear_selected(self):
#remove selected objects from import list
	pass

    def clear_all(self):
#remove all objects from import list
	pass

    def go(self):
        self.toplevel.title("EvObjectManager")
        self.toplevel.grab_set()
        self.toplevel.focus_set()
        self.toplevel.wait_window()

class selectEvRefFileGUI(Toplevel):
    Version = '0.1'

    def __init__(self, title="Just GUI", pattern="*\.ev[ao]$", master=None):
        self.toplevel= Toplevel(master)
        self.createWidgets()

    def createWidgets(self):
	self._make_EvRef_Panel(self.toplevel) #row 0
        self._make_selection_box(self.toplevel) #row 1
	self._make_buttons(self.toplevel) #row 2

    def _make_selection_box(self,root):
	self.selection_panel = Frame(root, name="selection_panel")
        #make the selection label
	self.selection_label = Label(self.selection_panel, text="Selection:")
	self.selection_label.grid(row=0, column=0, sticky=W)
        #make the selection entry box
        self.selection_entry = Entry(self.selection_panel, background='white', width=40)
	self.selection_entry.grid(row=1, columnspan=4, sticky=W+E)
        # set frame into parent window grid
        self.selection_panel.grid(row=1, columnspan=4)

    def ok_command(self):
	pass

    def cancel_command(self):
	self.toplevel.destroy()

    def _make_buttons(self,root):
	self.button_panel = Frame(root, name="button_panel")
        #make the buttons
        self.ok_button = Button(self.button_panel, text="ok", width=8, command=self.ok_command)
	self.ok_button.grid(row=0, column=0)
        self.cancel_button = Button(self.button_panel, text="cancel", width=8, command=self.cancel_command)
	self.cancel_button.grid(row=0, column=1)
        # set frame into parent window grid
        self.button_panel.grid(row=2, columnspan=3)
        self.button_panel.columnconfigure(0, weight=1) 

    def _make_EvRef_Panel(self,root):
	self.ev_ref_panel = Frame(root, name="ev_ref_panel")
        # build list box
	self.ev_ref_list_box = Listbox(self.ev_ref_panel, width=40, selectmode='single')
        self.ev_ref_list_box.grid(row=0, column=0, sticky=NW)
        #tie scrollbar to list_box
        yScroll = Scrollbar(self.ev_ref_panel, orient=VERTICAL)
        yScroll.grid(row=0, column=1, sticky=N+S)
        xScroll = Scrollbar(self.ev_ref_panel, orient=HORIZONTAL)
        xScroll.grid(row=1, column=0, sticky=E+W)
        self.ev_ref_list_box.configure(yscrollcommand=yScroll.set, xscrollcommand=xScroll.set)
        yScroll.configure(command=self.ev_ref_list_box.yview)
        xScroll.configure(command=self.ev_ref_list_box.xview)
        # set frame into parent window grid
        self.ev_ref_panel.grid(row=0, column=0, sticky=NW)
        self.ev_ref_panel.columnconfigure(0, weight=1) 

    def go(self):
        self.toplevel.title("Just GUI")
        self.toplevel.grab_set()
        self.toplevel.focus_set()
        self.toplevel.wait_window()

class selectEvRefFile(selectEvRefFileGUI):

    def __init__(self,aList=[]):
        selectEvRefFileGUI.__init__(self)
        self._define_panel_events()
        self.ev_file_list = aList
        self.populate_ev_ref_list_box(self.ev_file_list)

    def populate_ev_ref_list_box(self, aList):
        self.ev_ref_list_box.configure(selectmode='single')
	self.list_box_contents=[]
	self.ev_ref_list_box.delete(0,END)
        util.my_sort(aList)
	for aLine in aList:
	    self.list_box_contents.append(aLine)
	    self.ev_ref_list_box.insert(END,aLine)

    def _define_panel_events(self):
	btags = self.ev_ref_list_box.bindtags() 
        self.ev_ref_list_box.bindtags(btags[1:] + btags[:1])
        self.ev_ref_list_box.bind('<ButtonRelease-1>', self.files_select_event)
        self.ev_ref_list_box.bind('<Double-ButtonRelease-1>', self.files_double_event)
        btags = self.toplevel.bindtags()
        self.toplevel.bindtags(btags[1:] + btags[:1])
        self.toplevel.bind('<Return>',self.global_ok_command)

    def ok_command(self):
        self.newValue = self.get_selection()
	self.toplevel.destroy()

    def global_ok_command(self,event):
	self.ok_command()

    # set the file selection value
    def set_selection(self, file):
        self.selection_entry.delete('0', END)
        self.selection_entry.insert('0', file)

    # get the file selection value
    def get_selection(self):
        return self.selection_entry.get()

    # on clicking the file list
    def files_select_event(self, event):
        self.set_selection(self.ev_ref_list_box.get('active'))

    # on double clicking the file list
    def files_double_event(self, event):
        self.ok_command()

    def go(self, title="Choose EvRef File to move evObjects into"):
        self.newValue = None
        self.toplevel.title(title)
        self.toplevel.grab_set()
        self.toplevel.focus_set()
        self.toplevel.wait_window()
        return self.newValue

