#! /usr/bin/env python
# -*- python -*-

import os,sys,re,string
from util import _list_add

py2 = py30 = py31 = False
version = sys.hexversion
if version >= 0x020600F0 and version < 0x03000000 :
    py2 = True    # Python 2.6 or 2.7
    from Tkinter import *
    import ttk
elif version >= 0x03000000 and version < 0x03010000 :
    py30 = True
    from tkinter import *
    import ttk
elif version >= 0x03010000:
    py31 = True
    from tkinter import *
    import tkinter.ttk as ttk
else:
    print ("""
    You do not have a version of python supporting ttk widgets..
    You need a version >= 2.6 to execute PAGE modules.
    """)
    sys.exit()
def vp_start_gui():
    '''Starting point when module is the main routine.'''
    global val, w, root
    root = Tk()
    root.title('vp start gui')
    root.geometry('600x540+650+150')
    set_Tk_var()
    w = mFileDialog (root)
    init()
    root.mainloop()
w = None
def create_selectDialog(root):
    '''Starting point when module is imported by another program.'''
    global w, w_win
    if w: # So we have only one instance of window.
        return
    w = Toplevel (root)
    w.title('selectDialog')
    w.geometry('599x363+613+229')
    set_Tk_var()
    w_win = selectDialog(w)
    init()
    return w_win
def create_loop_m_selectDialog (root):
    '''Starting point when module is imported by another program.'''
    global w, w_win
    if w: # So we have only one instance of window.
        return
    w = Toplevel (root)
    w.title('m_loop_selectDialog')
    w.geometry('600x634+651+178')
    set_Tk_var()
    w_win = loop_m_selectDialog(w)
    init()
    return w_win
def create_selectDirectory(root):
    '''Starting point when module is imported by another program.'''
    global w, w_win
    if w: # So we have only one instance of window.
        return
    w = Toplevel (root)
    w.title('selectDialog')
    w.geometry('599x363+613+229')
    set_Tk_var()
    w_win = selectDirectory(w)
    init()
    return w_win
def create_loop_m_selectDirectory (root):
    '''Starting point when module is imported by another program.'''
    global w, w_win
    if w: # So we have only one instance of window.
        return
    w = Toplevel (root)
    w.title('m_loop_selectDirectory')
    w.geometry('600x634+651+178')
    set_Tk_var()
    w_win = loop_m_selectDirectory(w)
    init()
    return w_win
def destroy_mFileDialog ():
    global w
    w.destroy()
    w = None
def set_Tk_var():
    # These are Tk variables used passed to Tkinter and must be
    # defined before the widgets using them are created.
    global dir_list_box, file_list_box
    dir_list_box = StringVar()
    file_list_box = StringVar()
def init():
    pass
#helper classes, one layer above mFileDialog, i.e. SelectAFile, SelectADirectory, etc
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
        self.file_pattern, self.a_file = file_pattern, None
        self.do_selection(title,start_path,file_pattern,grab_set)
    def do_selection(self,window_title='Select A Directory',start_path=os.getcwd(),file_pattern=".*\..*",grab_set=True):
        self.create_tk_root()
        self.app = create_selectDirectory(self.root)
        self.a_file = self.app.go(title=window_title,startPath=start_path,pattern=file_pattern,grab_set=grab_set)
    def create_tk_root(self):
        self.root = Tk()
        self.root.withdraw()
class SelectFiles:
    def __init__(self,title='Select Files',file_pattern=".*\..*",start_path=os.getcwd(),grab_set=True):
        self.title, self.file_pattern, self.file_list = title, file_pattern, []
        self.m_files_selection(title,start_path,file_pattern,grab_set)
    def m_files_selection(self,window_title='Select Files',start_path=os.getcwd(),file_pattern=".*\..*",grab_set=True):
        self.create_tk_root()
        self.app = create_loop_m_selectDialog(self.root)
        self.app.ok_button.configure(text='AddFile(s)')
        self.app.newValue = self.file_list
        self.app.display_selected_files(self.file_list)
        self.file_list = self.app.go(title=window_title,startPath=start_path,pattern=file_pattern,grab_set=grab_set)
    def create_tk_root(self):
        self.root = Tk()
        self.root.withdraw()
class SelectDirectories:
    def __init__(self,title='Select Directories',file_pattern=".*\..*",start_path=os.getcwd(),grab_set=True):
        self.title, self.file_pattern, self.dir_list = title, file_pattern, []
        self.m_files_selection(title,start_path,file_pattern,grab_set)
    def m_files_selection(self,window_title='Select Directories',start_path=os.getcwd(),file_pattern=".*\..*",grab_set=True):
        self.create_tk_root()
        self.app = create_loop_m_selectDirectory(self.root)
        self.app.ok_button.configure(text='AddDir(s)')
        self.app.newValue = self.dir_list
        self.app.display_selected_directories(self.dir_list)
        self.dir_list = self.app.go(title=window_title,startPath=start_path,pattern=file_pattern,grab_set=grab_set)
    def create_tk_root(self):
        self.root = Tk()
        self.root.withdraw()
#base mFileDialog classes
class mFileDialog_gui(object):
    Version = '1.0.5'
    def __init__(self, master=None):
        # Set background of toplevel window to match
        # current style
        style = ttk.Style()
        theme = style.theme_use()
        default = style.lookup(theme, 'background')
        master.configure(background=default)
        self.toplevel= master
        self.createWidgets()
    def createWidgets(self):
        self._make_the_frames(self.toplevel)
        self._make_dir_tree_panel(self.toplevel)      #row 0, columnspan=2
        self._make_Dir_Panel(self.toplevel) #row 1, column 0
        self._make_File_Panel(self.toplevel)#row 1, column 1
        self._make_selection_box(self.toplevel) #row 2
        self._make_buttons(self.toplevel)   #row 3
    def _make_the_frames(self,root):
        #the dir_tree_frame
        self.TFrame1 = ttk.Frame (root)
        self.TFrame1.place(relx=0.0,rely=0.0,relheight=0.12,relwidth=0.99) #relheight ~0.08
        self.TFrame1.configure(relief=GROOVE)
        self.TFrame1.configure(borderwidth="2")
        self.TFrame1.configure(relief="groove")
        #the dir_panel_frame
        self.TFrame2 = ttk.Frame (root)
        self.TFrame2.place(relx=0.02,rely=0.14,relheight=0.56,relwidth=0.48) #relheight=~0.38
        self.TFrame2.configure(relief=GROOVE)
        self.TFrame2.configure(borderwidth="2")
        self.TFrame2.configure(relief="groove")
        #the file_panel_frame
        self.TFrame3 = ttk.Frame (root)
        self.TFrame3.place(relx=0.52,rely=0.14,relheight=0.56,relwidth=0.48) #relheight=~0.38
        self.TFrame3.configure(relief=GROOVE)
        self.TFrame3.configure(borderwidth="2")
        self.TFrame3.configure(relief="groove")
        #the select_box_frame
        self.TFrame4 = ttk.Frame (root)
        self.TFrame4.place(relx=0.0,rely=0.72,relheight=0.12,relwidth=0.99) #relheight = ~0.08
        self.TFrame4.configure(relief=GROOVE)
        self.TFrame4.configure(borderwidth="2")
        self.TFrame4.configure(relief="groove")
        #the button_frame
        self.TFrame5 = ttk.Frame (root)
        self.TFrame5.place(relx=0.0,rely=0.85,relheight=0.12,relwidth=0.99) #relheight = ~0.08
        self.TFrame5.configure(relief=GROOVE)
        self.TFrame5.configure(borderwidth="2")
        self.TFrame5.configure(relief="groove")
    def _make_dir_tree_panel(self,root):
        #the menu button
        self.dir_tree_mb = ttk.Menubutton(self.TFrame1)
        self.dir_tree_mb.place(relx=0.02,rely=0.22,relheight=0.56,relwidth=0.77)
        self.dir_tree_menu = Menu(self.dir_tree_mb,tearoff=0)
        self.dir_tree_mb.configure(menu=self.dir_tree_menu)
        self.dir_tree_mb.configure(takefocus="")
        self.dir_tree_mb.configure(text='''Dir History''')
    def _make_Dir_Panel(self,root):
        #the dir list box
        self.dir_list_box = ScrolledListBox (self.TFrame2)
        self.dir_list_box.place(relx=0.0,rely=0.0,relheight=1.01,relwidth=1.01)
        self.dir_list_box.configure(selectbackground="#c4c4c4")
        self.dir_list_box.configure(listvariable=dir_list_box)
    def _make_File_Panel(self,root):
        #the file list box
        self.file_list_box = ScrolledListBox (self.TFrame3)
        self.file_list_box.place(relx=0.0,rely=0.0,relheight=1.01,relwidth=1.01)
        self.file_list_box.configure(selectbackground="#c4c4c4")
        self.file_list_box.configure(listvariable=file_list_box)
    def _make_selection_box(self,root):
        #the selection entry and label
        self.selection_label = ttk.Label (self.TFrame4)
        self.selection_label.place(relx=0.02,rely=0.22,height=17,width=67)
        self.selection_label.configure(relief="flat")
        self.selection_label.configure(text='''Selection:''')
        self.selection_entry = ttk.Entry (self.TFrame4)
        self.selection_entry.place(relx=0.13,rely=0.44,relheight=0.42
                ,relwidth=0.75)
        self.selection_entry.configure(takefocus="")
        self.selection_entry.configure(cursor="xterm")
    def _make_buttons(self,root):
        #the buttons
        #ok button
        self.ok_button = ttk.Button (self.TFrame5)
        self.ok_button.place(relx=0.32,rely=0.22,height=26,width=83)
        self.ok_button.configure(takefocus="")
        self.ok_button.configure(text='''ok''')
        #cancel/done/quit button
        self.cancel_button = ttk.Button (self.TFrame5)
        self.cancel_button.place(relx=0.52,rely=0.22,height=26,width=83)
        self.cancel_button.configure(takefocus="")
        self.cancel_button.configure(text='''done''')
    def go(self):
        self.newValue = None
        self.toplevel.title("Select a File")
        self.toplevel.grab_set()
        self.toplevel.focus_set()
        self.toplevel.wait_window()
        return self.newValue
class mFileDialog(mFileDialog_gui):
    def __init__(self,master=None):
        mFileDialog_gui.__init__(self,master)
        self._define_panel_event()
        self.cancel_button.configure(command=self.cancel_command)
        self.ok_button.configure(command=self.ok_command)
    def _define_panel_event(self):
        btags = self.file_list_box.bindtags() 
        self.file_list_box.bindtags(btags[1:] + btags[:1])
        self.file_list_box.bind('<ButtonRelease-1>', lambda e :self.files_select_event())
        self.file_list_box.bind('<Double-ButtonRelease-1>', lambda e :self.files_double_event())
        self.file_list_box.bind_all('<Destroy>', lambda e: self.cancel_command())
        btags = self.dir_list_box.bindtags()
        self.dir_list_box.bindtags(btags[1:] + btags[:1])
        self.dir_list_box.bind('<ButtonRelease-1>', lambda e :self.subDirectory_select_event())
        btags = self.selection_entry.bindtags()
        self.selection_entry.bindtags(btags[1:] + btags[:1])
        self.selection_entry.bind('<Return>',lambda e :self.global_ok_command())
    def cancel_command(self):
        self.update_command()
        destroy_mFileDialog()
    def update_command(self):
        pass #self.toplevel.update_idletasks()
    def ok_command(self):
        self.newValue = self.get_selection()
        self.update_command()
        destroy_mFileDialog()
    def global_ok_command(self):
        self.ok_command()
    # refresh the display when there are user initiated selections
    def refreshDisplay(self, pathString):
        self.myDirectory = os.path.abspath(pathString) if not os.path.isabs(pathString) else pathString
        myList = self.parseDirectory(self.myDirectory)
        self.dir_tree_mb.configure(text = myList[0])
        self.dir_tree_menu.delete(0, END)
        for i in myList[1:]:
            self.dir_tree_menu.add_command(label = i, command = self.evaluateDirectory)
        try:
            names = os.listdir(self.myDirectory)
        except os.error:
            self.toplevel.bell()
            return
        names.sort()
        if (self.myDirectory == os.sep) or (not os.sep in self.myDirectory):
            subdirs = []
        else:
            subdirs = [os.pardir]
        matchingfiles = []
        for name in names:
            fullname = os.path.join(self.myDirectory, name)
            if os.path.isdir(fullname) and name[0] != '.':
               subdirs.append(name)
            elif name[0] != '.':
                matchingfiles.append(name)
        self.dir_list_box.delete(0, END)
        for name in subdirs:
            self.dir_list_box.insert(END, name)
        self.file_list_box.delete(0, END)
        if cmp(self.file_pattern,''): 
            pattern=re.compile(self.file_pattern)
        else:
            pattern=re.compile('.*\..*|\..*')
        for name in matchingfiles:
          m=re.search(pattern,name)
          if m != None:
              self.file_list_box.insert(END, name)
        self.set_selection('')
    # parse the directory for the directory menu
    def parseDirectory(self, directoryString):
        if directoryString == os.sep:
            return [directoryString]
        if not os.sep in directoryString:
            return [directoryString]
        myList = []
        myString = ''
        myElements = string.split(directoryString, os.sep)
        for element in myElements:
            myString = myString + element
            if element == '':
                myString = os.path.normpath(myString + os.sep)
                myPost = ''
            else:
                myPost = os.sep
            myList.append(myString)
            myString = myString + myPost
        myList.reverse()
        return myList
    # process the current directory string  
    def evaluateDirectory(self):
        self.refreshDisplay(self.dir_tree_menu.entrycget(ACTIVE, 'label'))
    # set the file selection value
    def set_selection(self, a_file_selection):
        '''Can be one or more files currently selected '''
        self.selection_entry.delete('0', END)
        self.selection_entry.insert('0', a_file_selection)
    # get the file selection value
    def get_selection(self):
        return self.selection_entry.get()
    # on clicking the subdirectory list
    def subDirectory_select_event(self):
        subdir = self.dir_list_box.get('active')
        self.refreshDisplay(os.path.normpath(os.path.join(self.myDirectory, subdir)))
    # on clicking the file list
    def files_select_event(self):
        self.set_selection(self.file_list_box.get('active'))
    # on double clicking the file list
    def files_double_event(self):
        self.ok_command()
    def go(self, title = 'file dialog', startPath = os.getcwd(), pattern='',grab_set=True):
        self.newValue = None
        self.file_pattern = pattern
        self.toplevel.title(title)
        if os.path.isfile(startPath):
            startPath, myFile = os.path.split(startPath)
            self.refreshDisplay(startPath)
            self.set_selection(myFile)
        else:
            self.refreshDisplay(startPath)
        if grab_set and self.toplevel.winfo_viewable():
            self.toplevel.grab_set()
        self.toplevel.focus_set()
        self.toplevel.wait_window()
        return self.newValue
class selectDialog(mFileDialog):
    def __init__(self,master=None):
        mFileDialog.__init__(self,master)
        self.cancel_button.configure(text="cancel")
    def ok_command(self):
        self.myFile = os.path.join(self.myDirectory, self.get_selection())
        self.newValue = None
        if os.path.isfile(self.myFile): self.newValue = self.myFile
        self.cancel_command()
class loop_m_selectDialog(mFileDialog):
    def __init__(self,master=None):
        mFileDialog.__init__(self,master)
        self.newValue = []
        self.file_list_box.configure(selectmode='extended')
        self.cancel_button.configure(text="done")
    def createWidgets(self):
        self._make_the_frames(self.toplevel)
        self._make_dir_tree_panel(self.toplevel)      #row 0
        self._make_Dir_Panel(self.toplevel) #row 1, column 0
        self._make_File_Panel(self.toplevel)#row 1, column 1
        self._make_selection_box(self.toplevel) #row 2
        self._make_buttons(self.toplevel)   #row 3
        self._make_FileList_Panel(self.toplevel) #row 4
    def _make_the_frames(self,root):
        #the dir_tree_frame
        self.TFrame1 = ttk.Frame (root)
        self.TFrame1.place(relx=0.0,rely=0.0,relheight=0.08,relwidth=0.99) #relheight ~0.08
        self.TFrame1.configure(relief=GROOVE)
        self.TFrame1.configure(borderwidth="2")
        self.TFrame1.configure(relief="groove")
        #the dir_panel_frame
        self.TFrame2 = ttk.Frame (root)
        self.TFrame2.place(relx=0.02,rely=0.09,relheight=0.38,relwidth=0.48) #relheight=~0.38
        self.TFrame2.configure(relief=GROOVE)
        self.TFrame2.configure(borderwidth="2")
        self.TFrame2.configure(relief="groove")
        #the file_panel_frame
        self.TFrame3 = ttk.Frame (root)
        self.TFrame3.place(relx=0.52,rely=0.09,relheight=0.38,relwidth=0.48) #relheight=~0.38
        self.TFrame3.configure(relief=GROOVE)
        self.TFrame3.configure(borderwidth="2")
        self.TFrame3.configure(relief="groove")
        #the select_box_frame
        self.TFrame4 = ttk.Frame (root)
        self.TFrame4.place(relx=0.0,rely=0.48,relheight=0.08,relwidth=0.99) #relheight = ~0.08
        self.TFrame4.configure(relief=GROOVE)
        self.TFrame4.configure(borderwidth="2")
        self.TFrame4.configure(relief="groove")
        #the button_frame
        self.TFrame5 = ttk.Frame (root)
        self.TFrame5.place(relx=0.0,rely=0.57,relheight=0.08,relwidth=0.99) #relheight = ~0.08
        self.TFrame5.configure(relief=GROOVE)
        self.TFrame5.configure(borderwidth="2")
        self.TFrame5.configure(relief="groove")
        #the text_window_frame
        self.TFrame6 = ttk.Frame (root)
        self.TFrame6.place(relx=0.0,rely=0.67,relheight=0.32,relwidth=0.99) #relheight = ~0.32
        self.TFrame6.configure(relief=GROOVE)
        self.TFrame6.configure(borderwidth="2")
        self.TFrame6.configure(relief="groove")
    def _make_FileList_Panel(self,root):
        #the text window for file list display
        self.text_window = ScrolledText (self.TFrame6)
        self.text_window.place(relx=0.0,rely=0.0,relheight=1.01,relwidth=1.01)
        self.text_window.configure(selectbackground="#c4c4c4")
    def ok_command(self):
        sub_list = self.get_selection()
        for i in xrange(len(sub_list)):
            sub_list[i] = os.path.join(self.myDirectory, sub_list[i])
        self.newValue += sub_list
        self.display_selected_files(self.newValue)
    def get_selection(self):
        index_list, file_list = self.file_list_box.curselection(),[]
        file_list = [ self.file_list_box.get(i) for i in index_list ]
        for i in index_list: self.file_list_box.selection_clear(i)
        return(file_list)
    def display_selected_files(self,file_list):
        self.text_window.delete('0.0','end')
        for a_file in file_list: self.text_window.insert('end','%s\n'% a_file)
    def go(self, title = 'file dialog', startPath = os.getcwd(), pattern='',grab_set=True):
        self.file_pattern = pattern
        self.toplevel.title(title)
        if os.path.isfile(startPath):
            startPath, myFile = os.path.split(startPath)
            self.refreshDisplay(startPath)
            self.set_selection(myFile)
        else:
            self.refreshDisplay(startPath)
        if grab_set and self.toplevel.winfo_viewable():
            self.toplevel.grab_set()
        self.toplevel.focus_set()
        self.toplevel.wait_window()
        self.update_command()
        return self.newValue
class selectDirectory(mFileDialog):
    def __init__(self,master=None):
        mFileDialog.__init__(self,master)
        self.cancel_button.configure(text="cancel")
    def ok_command(self):
        self.set_selection()
        self.newValue = self.get_selection()    
        self.cancel_command()
    # set the file selection value
    def set_selection(self,a_file=''):
        self.selection_entry.delete('0', END)
        self.selection_entry.insert('0', self.myDirectory)
class loop_m_selectDirectory(mFileDialog):
    def __init__(self,master=None):
        mFileDialog.__init__(self,master)
        self.newValue = []
        self.cancel_button.configure(text="done")
    def createWidgets(self):
        self._make_the_frames(self.toplevel)
        self._make_dir_tree_panel(self.toplevel)      #row 0
        self._make_Dir_Panel(self.toplevel) #row 1, column 0
        self._make_File_Panel(self.toplevel)#row 1, column 1
        self._make_selection_box(self.toplevel) #row 2
        self._make_buttons(self.toplevel)   #row 3
        self._make_DirList_Panel(self.toplevel) #row 4
    def _make_the_frames(self,root):
        #the dir_tree_frame
        self.TFrame1 = ttk.Frame (root)
        self.TFrame1.place(relx=0.0,rely=0.0,relheight=0.08,relwidth=0.99) #relheight ~0.08
        self.TFrame1.configure(relief=GROOVE)
        self.TFrame1.configure(borderwidth="2")
        self.TFrame1.configure(relief="groove")
        #the dir_panel_frame
        self.TFrame2 = ttk.Frame (root)
        self.TFrame2.place(relx=0.02,rely=0.09,relheight=0.38,relwidth=0.48) #relheight=~0.38
        self.TFrame2.configure(relief=GROOVE)
        self.TFrame2.configure(borderwidth="2")
        self.TFrame2.configure(relief="groove")
        #the file_panel_frame
        self.TFrame3 = ttk.Frame (root)
        self.TFrame3.place(relx=0.52,rely=0.09,relheight=0.38,relwidth=0.48) #relheight=~0.38
        self.TFrame3.configure(relief=GROOVE)
        self.TFrame3.configure(borderwidth="2")
        self.TFrame3.configure(relief="groove")
        #the select_box_frame
        self.TFrame4 = ttk.Frame (root)
        self.TFrame4.place(relx=0.0,rely=0.48,relheight=0.08,relwidth=0.99) #relheight = ~0.08
        self.TFrame4.configure(relief=GROOVE)
        self.TFrame4.configure(borderwidth="2")
        self.TFrame4.configure(relief="groove")
        #the button_frame
        self.TFrame5 = ttk.Frame (root)
        self.TFrame5.place(relx=0.0,rely=0.57,relheight=0.08,relwidth=0.99) #relheight = ~0.08
        self.TFrame5.configure(relief=GROOVE)
        self.TFrame5.configure(borderwidth="2")
        self.TFrame5.configure(relief="groove")
        #the text_window_frame
        self.TFrame6 = ttk.Frame (root)
        self.TFrame6.place(relx=0.0,rely=0.67,relheight=0.32,relwidth=0.99) #relheight = ~0.32
        self.TFrame6.configure(relief=GROOVE)
        self.TFrame6.configure(borderwidth="2")
        self.TFrame6.configure(relief="groove")
    def _make_DirList_Panel(self,root):
        #the text window for dir list display
        self.text_window = ScrolledText (self.TFrame6)
        self.text_window.place(relx=0.0,rely=0.0,relheight=1.01,relwidth=1.01)
        self.text_window.configure(selectbackground="#c4c4c4")
    def ok_command(self):
        _list_add([self.myDirectory],self.newValue)
        self.display_selected_directories(self.newValue)
    def display_selected_directories(self,dir_list):
        self.text_window.delete('0.0','end')
        for a_dir in dir_list: self.text_window.insert('end','%s\n'% a_dir)
    def go(self, title = 'dir dialog', startPath = os.getcwd(), pattern='',grab_set=True):
        self.file_pattern = pattern
        self.toplevel.title(title)
        if os.path.isfile(startPath):
            startPath, myFile = os.path.split(startPath)
            self.refreshDisplay(startPath)
            self.set_selection(myFile)
        else:
            self.refreshDisplay(startPath)
        if grab_set and self.toplevel.winfo_viewable():
            self.toplevel.grab_set()
        self.toplevel.focus_set()
        self.toplevel.wait_window()
        self.update_command()
        return self.newValue
# the question window class
class question:
    def __init__(self, master = None):
        self.top = Toplevel(master)
        self.frame = Frame(self.top)
        self.frame.pack(side = BOTTOM)
        self.yes_button = Button(self.frame, 
                                    text = 'yes', 
                                    command = self.yes)
        self.yes_button.pack(side = LEFT)
        self.no_button = Button(self.frame, 
                                    text = 'no', 
                                    command = self.no)
        self.no_button.pack(side = RIGHT)
        self.label = Label(self.top)
        self.label.pack(side = TOP, 
                       fill = BOTH, 
                       expand = YES)
        self.top.protocol('WM_DELETE_WINDOW', self.no)
    def go(self, title = 'question',message = 'question goes here!',geometry =  '200x100+412+334',grab_set=True):
        self.top.title(title)
        self.top.geometry(geometry)
        self.label.configure(text = message)
        self.booleanValue = None
        if grab_set:
            self.top.grab_set()
        self.top.focus_set()
        self.top.wait_window()
        return self.booleanValue
    def yes(self):
        self.booleanValue = True
        self.top.destroy()
    def no(self):
        self.booleanValue = False
        self.top.destroy()
# the message window class
class message:
    def __init__(self,master = None,title = 'message',message = 'Under construction!',geometry = '150x70+437+349'):
        if not master: 
            master = Tk()
            master.withdraw()
        self.top = Toplevel(master)
        self.top.title(title)
        self.top.geometry(geometry)
        self.ok_button = Button(self.top, text = 'ok', command = self.ok)
        self.ok_button.pack(side = BOTTOM)
        self.label = Label(self.top, text = message)
        self.label.pack(side = TOP, fill = BOTH, expand = YES)
        if self.top.winfo_viewable():
            self.top.grab_set()
        self.top.focus_set()
        self.top.wait_window()
    def ok(self):
        self.top.destroy()
class user_entry_dialog:
    def __init__(self,master=None, title= 'User Input', message= 'Ask question here', geometry = '150x70+437+349'):
        self.top=Toplevel(master)
        self.top.title(title)
        self.top.geometry(geometry)
        self.ok_button = Button(self.top, text = 'ok', command = self.ok)
        self.ok_button.pack(side = BOTTOM)
        self.label = Label(self.top, text = message)
        self.label.pack(side = TOP, fill = BOTH, expand = YES, anchor=NW)
        self.entry = Entry(self.top, background='#ffffff', width=20) #white
        self.entry.pack(side = TOP, fill = X, expand = NO, anchor=NW)
        btags = self.entry.bindtags()
        self.entry.bindtags(btags[1:] + btags[:1])
        self.entry.bind('<Return>',self.ok_event)
    def go(self, title='Enter Information', message='Ask a question', geometry = '150x70+437+349', grab_set=True):
        self.newValue=None
        self.top.title(title)
        self.top.geometry(geometry)
        self.label.configure(text=message)
        if grab_set:
            self.top.grab_set()
        self.top.focus_set()
        self.top.wait_window()
        return self.newVal
    def get_selection(self):
        return self.entry.get()
    def ok_event(self,event):
        self.ok()
    def ok(self):
        self.newVal = self.get_selection()
        self.top.destroy()
# The following code is added to facilitate the Scrolled widgets you specified.
class AutoScroll(object):
    '''Configure the scrollbars for a widget.'''

    def __init__(self, master):
        vsb = ttk.Scrollbar(master, orient='vertical', command=self.yview)
        hsb = ttk.Scrollbar(master, orient='horizontal', command=self.xview)

        self.configure(yscrollcommand=self._autoscroll(vsb),
            xscrollcommand=self._autoscroll(hsb))
        self.grid(column=0, row=0, sticky='nsew')
        vsb.grid(column=1, row=0, sticky='ns')
        hsb.grid(column=0, row=1, sticky='ew')

        master.grid_columnconfigure(0, weight=1)
        master.grid_rowconfigure(0, weight=1)

        # Copy geometry methods of master  (took from ScrolledText.py)
        if py31:
            methods = Pack.__dict__.keys() | Grid.__dict__.keys() \
                  | Place.__dict__.keys()
        else:
            methods = Pack.__dict__.keys() + Grid.__dict__.keys() \
                  + Place.__dict__.keys()

        for meth in methods:
            if meth[0] != '_' and meth not in ('config', 'configure'):
                setattr(self, meth, getattr(master, meth))

    @staticmethod
    def _autoscroll(sbar):
        '''Hide and show scrollbar as needed.'''
        def wrapped(first, last):
            first, last = float(first), float(last)
            if first <= 0 and last >= 1:
                sbar.grid_remove()
            else:
                sbar.grid()
            sbar.set(first, last)
        return wrapped

    def __str__(self):
        return str(self.master)

def _create_container(func):
    '''Creates a ttk Frame with a given master, and use this new frame to
    place the scrollbars and the widget.'''
    def wrapped(cls, master, **kw):
        container = ttk.Frame(master)
        return func(cls, container, **kw)
    return wrapped

class ScrolledText(AutoScroll, Text):
    '''A standard Tkinter Text widget with scrollbars that will
    automatically show/hide as needed.'''
    @_create_container
    def __init__(self, master, **kw):
        Text.__init__(self, master, **kw)
        AutoScroll.__init__(self, master)

class ScrolledListBox(AutoScroll, Listbox):
    '''A standard Tkinter Text widget with scrollbars that will
    automatically show/hide as needed.'''
    @_create_container
    def __init__(self, master, **kw):
        Listbox.__init__(self, master, **kw)
        AutoScroll.__init__(self, master)

if __name__ == '__main__':
    vp_start_gui()



