import util
from util import CmpOperators, copy
import csv
from Tkinter import *
import tkFont
import Pmw
from tkintertable import Dialogs,Tables_IO
from tkintertable.Tables import TableCanvas
from tkintertable.TableModels import TableModel
from tkintertable.Filtering import FilterBar
#useful debug functions for Tkinter debug
def FontInfo(a_font='TkDefaultFont'):
    a_dict = tkFont.Font(font=a_font).configure()
    return( [ 'Attribute: %s, Value: %s'%(a_key,a_value) for a_key,a_value in a_dict.iteritems() ])
def dump_attributes(widget=None):
    util.PrettyPrint(['Key: %s, Value: %s'%(a_key,widget[a_key]) for a_key in widget.keys()])
def dump_bindings(widget=None):
    bindings = set()
    for cls in widget.bindtags():
        bindings |= set(widget.bind_class(cls)) # s |= t means: update set s, adding elements from t
    return(bindings)
#generic type functions for text and listbox widgets
def append_to_list_box(list_box,a_list):
    for a_line in a_list: list_box.insert(END,a_line)
def clear_list_box(list_box=None):
    list_box.delete(0,"end")
def fill_list_box(list_box=None,a_list=[]):
    clear_list_box(list_box)
    for a_line in a_list: list_box.insert(END,a_line)
def clear_text_box(text_box=None):
    text_box.delete('1.0','end')
def append_to_text_box(text_box=None,a_list=[],text_tag=None):
    if type(a_list) == type('a_string'): a_list = [a_list]
    add_cr(a_list)
    for a_line in a_list: text_box.insert('end',a_line,text_tag)
    text_box.see('end')
def delete_from_list_box(list_box=None):
    'delete selection from list_box'
    a_list = list(list_box.get(0,'end'))
    index_list = [ int(i) for i in list(list_box.curselection()) ]
    selection_list = [a_list.pop(i) for i in util.my_reverse_in_place(index_list)]
    fill_list_box(list_box,a_list)
    list_box.select_set(index_list[0])
def add_to_list_box(list_box=None,a_list=[]):
    append_to_list_box(list_box,a_list)
def move_up_in_list_box(list_box=None):
    a_list = list(list_box.get(0,'end'))
    index_list = [ int(i) for i in list(list_box.curselection()) ]
    selected_list = [ a_list[i] for i in index_list ]
    new_i = util.shift_element(a_list,index_list[0])
    fill_list_box(list_box,a_list)
    list_box.select_set(new_i)
def move_down_in_list_box(list_box=None):
    a_list = list(list_box.get(0,'end'))
    index_list = [ int(i) for i in list(list_box.curselection()) ]
    selected_list = [ a_list[i] for i in index_list ]
    new_i = util.shift_element(a_list,index_list[0],-1)
    fill_list_box(list_box,a_list)
    list_box.select_set(new_i)
def get_selection(list_box):
    index_list = list_box.curselection()
    selection_list = [ list_box.get(i) for i in index_list ]
    return(selection_list)
def selection_index_list(list_box):
    return( [ int(i) for i in list(list_box.curselection()) ] )
def add_cr(a_list):
    if type(a_list) == type('a_string'):
        if a_list[-1] != '\n': a_list += '\n'
    else:
        aRange = range(len(a_list))
        for i in aRange:
            try:
                if a_list[i] == '': a_list[i]='\n'
                elif a_list[i][-1] != '\n': a_list[i] += '\n'
            except IndexError: # might be a blank line, ''
                print 'index is: ',i
                print 'a_list[i]: ',a_list[i]
                raise
def set_button_state(conditional=True,button=None):
    if not button: pass
    else:
        if conditional: button.configure(state='normal')
        else: button.configure(state='disabled')
# tkintertable related classes and functions
class mTableModel(TableModel):
    Version = '0.5'
    TimeOfInstance = util.GetTheLocalTime()
    funcs = {'contains':CmpOperators.contains,'excludes':CmpOperators.excludes,'=':CmpOperators.equals, \
        '!=':CmpOperators.notequals,'>':CmpOperators.greaterthan,'<':CmpOperators.lessthan, \
        'starts with':CmpOperators.startswith, 'ends with':CmpOperators.endswith, \
        'has length':CmpOperators.haslength}
    floatops = ['=','!=','>','<']
    def __init__(self, newdict=None, rows=None, columns=None):
        TableModel.__init__(self,newdict,rows,columns)
        self.use_regexp_filter = BooleanVar()
    def setupModel(self, newdict, rows=None, columns=None):
        """Create table model"""
        if newdict != None:
            self.data = copy.deepcopy(newdict)
            for k in self.keywords:
                if self.data.has_key(k):
                    self.__dict__[self.keywords[k]] = self.data[k]
                    del self.data[k]
            #read in the record list order
            if self.data.has_key('reclist'):
                temp = self.data['reclist']
                del self.data['reclist']
                self.reclist = temp
            else:
                self.reclist = self.data.keys()
        else:
            #just make a new empty model
            self.createEmptyModel()

        if not set(self.reclist) == set(self.data.keys()):
            print 'reclist does not match data keys'
        #restore last column order
        if hasattr(self, 'columnOrder') and self.columnOrder != None:
            self.columnNames=[]
            for i in self.columnOrder.keys():
                self.columnNames.append(self.columnOrder[i])
                i += 1
        self.defaulttypes = ['text', 'number']
        #setup default display for column types
        self.default_display = {'text' : 'showstring',
                                'number' : 'numtostring'}
        #set default sort order as first col
        if len(self.columnNames)>0:
            self.sortkey = self.columnNames[0]
        else:
            self.sortkey = None
        #add rows and cols if they are given in the constructor
        if newdict == None:
            if rows != None:
                self.autoAddRows(rows)
            if columns != None:
                self.autoAddColumns(columns)
        self.filteredrecs = None
        self.sortedrecs=None
        return
    def filterBy(self, filtercol, value, op='contains', userecnames=False, progresscallback=None):
        "Filter recs according to one column"
        from util import CmpOperators
        funcs = self.funcs
        # see if we're using regexp filter search
        funcs['contains'] = CmpOperators.contains_regexp if self.use_regexp_filter.get() else CmpOperators.contains
        funcs['excludes'] = CmpOperators.excludes_regexp if self.use_regexp_filter.get() else CmpOperators.excludes
        floatops = self.floatops
        func = funcs[op]
        data = self.data
        names=[]
        model_reclist = self.reclist if not self.sortedrecs else self.sortedrecs
        for rec in model_reclist:
            if data[rec].has_key(filtercol):
                #try to do float comparisons if required
                if op in floatops:
                    try:
                        item = float(data[rec][filtercol])
                        v=float(value)
                        if func(v, item) == True:
                            names.append(rec)
                        continue
                    except:
                        pass
                if filtercol == 'name' and userecnames == True:
                    item = rec
                else:
                    item = str(data[rec][filtercol])
                if func(value, item):
                    names.append(rec)
        return names
    def getFilteredCells(self):
        '''Return a dict of the form rowname: list of filtered cell contents
          Useful for a simple table export for example'''
        records = dict( [ (row,[ self.getValueAt(row,col) for col in xrange(len(self.columnNames)) ]) \
            for row in xrange(len(self.filteredrecs)) ])
        return records
class mTableCanvas(TableCanvas):
    Version = '0.5.2'
    TimeOfInstance = util.GetTheLocalTime()
    def __init__(self, parent=None, model=None, width=None, height=None, rows=10, cols=5, **kwargs):
        TableCanvas.__init__(self,parent,mTableModel(rows=rows,columns=cols) if not model else model, \
            width,height,rows,cols,**kwargs)
        self.is_sorted = False
    def createfromDict(self, data):
        """Attempt to create a new model/table from a dict"""
        try:
            namefield=self.namefield
        except:
            namefield=data.keys()[0]
        self.model = mTableModel()
        self.model.importDict(data, namefield=namefield)
        self.model.setSortOrder(0,reverse=self.reverseorder)
        return
    def new(self):
        """Clears all the data and makes a new table"""
        from Dialogs import MultipleValDialog
        mpDlg = MultipleValDialog(title='Create new table',
            initialvalues=(10, 4),
            labels=('rows','columns'),
            types=('int','int'),
            parent=self.parentframe)
        if mpDlg.result == True:
            rows = mpDlg.results[0]
            cols = mpDlg.results[1]
            model = mTableModel(rows=rows,columns=cols)
            self.updateModel(model)
        return
    def importTable(self):
        """Import from csv file"""
        from Tables_IO import TableImporter
        importer = TableImporter()
        importdialog = importer.import_Dialog(self.master)
        self.master.wait_window(importdialog)
        model = mTableModel()
        model.importDict(importer.data)
        self.updateModel(model)
        return
    def createFilteringBar(self, parent=None, fields=None):
        'Executed from Right-Click Menu:: Filter Records in Table Widget: Add a filter frame'
        if parent == None:
            parent = Toplevel()
            parent.title('Filter Records')
            x,y,w,h = self.getGeometry(self.master)
            parent.geometry('+%s+%s' %(x,y+h))
        if fields == None:
            fields = self.model.columnNames
        self.filterframe = mFilterFrame(parent,fields,self.doFilter,self.closeFilterFrame,x,y+h)
        self.filterframe.pack()
        self.model.use_regexp_filter = self.filterframe.use_regexp
        return parent
    def create_mtablesFilteringBar(self,parent=None,fields=None,additional_tables=[]):
        'Add a filter frame'
        if parent == None:
            parent = Toplevel()
            parent.title('Filter Records')
            x,y,w,h = self.getGeometry(self.master)
            parent.geometry('+%s+%s' %(x,y+h))
        if fields == None:
            fields = self.model.columnNames
        self.filterframe = mtables_FilterFrame(parent,fields,additional_tables,self.doFilter,self.close_mtablesFilterFrame,x,y+h)
        self.filterframe.pack()
        self.model.use_regexp_filter = self.filterframe.use_regexp
        return parent
    def doFilter(self, event=None):
        '''Filter the table display by some column values.
        We simply pass the model search function to the the filtering
        class and that handles everything else.
        See filtering frame class for how searching is done.
        '''
        if self.model==None:
            return
        names = self.filterframe.doFiltering(searchfunc=self.model.filterBy)
        #create a list of filtered recs
        self.model.filteredrecs = names
        self.filtered = True
        self.redrawTable()
        return
    def do_mtablesFilter(self, event=None):
        '''Filter the table display by some column values.
        We simply pass the model search function to the the filtering
        class and that handles everything else.
        See filtering frame class for how searching is done.
        '''
        self.doFilter()
        for a_table in self.filterframe.additional_tables:
            if a_table.model == None:
                return
            else:
                names = a_table.filterframe.doFiltering(searchfunc=a_table.model.filterBy)
        if self.model==None:
            return
        names = self.filterframe.doFiltering(searchfunc=self.model.filterBy)
        #create a list of filtered recs
        self.model.filteredrecs = names
        self.filtered = True
        self.redrawTable()
        return
    def show_mtablesFilteringBar(self,additional_tables=[]):
        if not hasattr(self, 'filterwin') or self.filterwin == None:
            self.filterwin = self.create_mtablesFilteringBar(additional_tables=additional_tables)
            self.filterwin.protocol("WM_DELETE_WINDOW", self.close_mtablesFilterFrame)
        else:
            self.filterwin.lift()
        return
    def close_mtablesFilterFrame(self):
        """Callback for closing filter frame"""
        if self.filterwin:
            self.filterwin.destroy()
            self.filterwin = None
        #self.showAll()
        #for a_table in self.filterframe.additional_tables: a_table.showAll()
        return
    def exportTable(self, filename=None):
        """Do a simple export of the cell contents to csv"""
        exporter = mTableExporter()
        exporter.ExportTableData(self)
        return
    def createSortMap(self, names, sortkey, reverse=0):
        "Create a sort mapping for given list"
        recdata = [ self.getRecordAttributeAtColumn(recName=rec, columnName=sortkey) for rec in names ]
        #try create list of floats if col has numbers only
        try:
            recdata = [ util.CastToNumber(a_cell) for a_cell in recdata ]
        except:
            pass
        smap = zip(names, recdata)
        #sort the mapping by the second key
        smap = sorted(smap, key=operator.itemgetter(1), reverse=reverse)
        #now sort the main reclist by the mapping order
        sortmap = map(operator.itemgetter(0), smap)
        return sortmap
    def setSortOrder(self, columnIndex=None, columnName=None, reverse=0):
        '''Changes the order that records are sorted in, which will
           be reflected in the table upon redrawing'''
        if columnName != None and columnName in self.columnNames:
            self.sortkey = columnName
        elif columnIndex != None:
            self.sortkey = self.getColumnName(columnIndex)
        else:
            return
        self.reclist = self.createSortMap(self.reclist, self.sortkey, reverse)
        if self.filteredrecs != None:
            self.filteredrecs = self.createSortMap(self.filteredrecs, self.sortkey, reverse)
        return
    def doSortOrder(self,sortkeys=[],do_reverse_list=[0]):
        '''Front end for sorting the table based on one or more column names as the sort keys'''
        self.is_sorted=True
        if len(sortkeys) > len(do_reverse_list):
            num_fields,num_bools = len(sortkeys),len(do_reverse_list)
            do_reverse_list += [ 0 for a_field in sortkeys[num_bools:] ]
        sort_fields, do_reverse_list = reversed(sortkeys),reversed(do_reverse_list) 
        model_reclist = self.model.reclist if not self.filtered else self.model.filteredrecs
        self.model.sortedrecs = [ a_rec for a_rec in model_reclist ]
        #make sortmap
        for sort_field,do_reverse in zip(sort_fields,do_reverse_list):
            self.model.sortedrecs = self.model.createSortMap(self.model.sortedrecs,sort_field,do_reverse)
        # -- hack --, first row not visible, so duplicate row inserted for reclist
        self.resyncTableData(self.model.sortedrecs)
        if self.filtered: 
            self.model.filteredrecs = self.model.sortedrecs
        else: 
            self.model.reclist = self.model.sortedrecs
        self.redrawTable()
    def resyncTableData(self,records_list):
        '''-- hack --, first row not visible, so duplicate row inserted for reclist, after a sort and/or
        filter operation, one or more sets of duplicate pairs may exist.  This function eliminates the pair(s)
        and keeps the first row visible'''
        table_data,col_names = self.model.getData(), [a_col for a_col in self.model.columnNames if cmp(a_col,'BlankCol')!= 0 ]
        chk_list = [ ','.join([table_data[a_row][a_col] for a_col in col_names]) \
            for a_row in records_list ]
        resynced_records_list,resynced_data_list = [],[]
        for i,a_record in zip(records_list,chk_list):
            if not a_record in resynced_data_list:
                resynced_data_list.append(a_record)
                resynced_records_list.append(i)
        util._list_intersect(resynced_records_list,records_list)
        records_list.insert(0,records_list[0])
    def redrawVisible(self, event=None, callback=None):
        """Redraw the visible portion of the canvas"""
        model = self.model
        self.rows = self.model.getRowCount()
        self.cols = self.model.getColumnCount()
        if self.cols == 0 or self.rows == 0:
            self.delete('entry')
            self.delete('rowrect')
            self.delete('currentrect')
            return
        self.tablewidth = (self.cellwidth) * self.cols
        self.configure(bg=self.cellbackgr)
        self.setColPositions()
        #are we drawing a filtered subset of the recs?
        if self.filtered == True and self.model.filteredrecs != None:
            self.rows = len(self.model.filteredrecs)
            # -- hack, first row not visible for sorted and/or filtered recs
            self.model.filteredrecs = [self.model.filteredrecs[0]] + util.unique_sub_list(self.model.filteredrecs[1:])
            self.delete('colrect')
        self.rowrange = range(0,self.rows)
        self.configure(scrollregion=(0,0, self.tablewidth+self.x_start,
                self.rowheight*self.rows+10))
        x1, y1, x2, y2 = self.getVisibleRegion()
        startvisiblerow, endvisiblerow = self.getVisibleRows(y1, y2)
        self.visiblerows = range(startvisiblerow, endvisiblerow)
        startvisiblecol, endvisiblecol = self.getVisibleCols(x1, x2)
        self.visiblecols = range(startvisiblecol, endvisiblecol)
        self.drawGrid(startvisiblerow, endvisiblerow)
        align = self.align
        self.delete('fillrect')
        for row in self.visiblerows:
            if callback != None:
                callback()
            for col in self.visiblecols:
                colname = model.getColumnName(col)
                bgcolor = model.getColorAt(row,col, 'bg')
                fgcolor = model.getColorAt(row,col, 'fg')
                text = model.getValueAt(row,col)
                self.drawText(row, col, text, fgcolor, align)
                if bgcolor != None:
                    self.drawRect(row,col, color=bgcolor)
        #self.drawSelectedCol()
        self.tablecolheader.redraw()
        self.tablerowheader.redraw(align=self.align, showkeys=self.showkeynamesinheader)
        #self.setSelectedRow(self.currentrow)
        self.drawSelectedRow()
        self.drawSelectedRect(self.currentrow, self.currentcol)
        #print self.multiplerowlist
        if len(self.multiplerowlist)>1:
            self.tablerowheader.drawSelectedRows(self.multiplerowlist)
            self.drawMultipleRows(self.multiplerowlist)
            self.drawMultipleCells()
        return
    def showAll(self):
        "reset filtered records, show all records"
        self.model.filteredrecs = None
        self.filtered = False
        if self.is_sorted: self.model.reclist = self.model.sortedrecs
        self.redrawTable()
        return
    def unsortAll(self):
        "reset sorted records, put records back in original sequence order"
        tm = self.getModel()
        unsorted_reclist = sorted(tm.data.iterkeys()) if not self.filtered else sorted(tm.filteredrecs)
        if not self.filtered: tm.reclist = [ a_rec for a_rec in unsorted_reclist ]
        else: tm.filteredrecs = [ a_rec for a_rec in unsorted_reclist ]
        self.model.sortedrecs=None
        self.is_sorted=False
        self.redrawTable()
        pass
    def resetAll(self):
        '''Put data set back to original in the table, clearing out all sorted and/or filtered results '''
        if not hasattr(self,'filterwin'): self.filterwin = None
        if self.filterwin: 
            self.closeFilterFrame() #close_mtablesFilterFrame
        if self.filtered:
            self.showAll()
            #for a_table in self.filterframe.additional_tables: a_table.showAll()
        if self.is_sorted:
            self.unsortAll()
        pass
class mTableExporter:
    def __init__(self):
        "Provides export utility methods for the Table and Table Model classes"
        return
    def ExportTableData(self, table, sep=None):
        "Export table data to a comma separated file"
        parent=table.parentframe
        import tkFileDialog
        filename = tkFileDialog.asksaveasfilename(parent=parent,defaultextension='.csv',
            filetypes=[("CSV files","*.csv")])
        if not filename:
            return
        if sep == None:
            sep = ','
        writer = csv.writer(file(filename, "w"), delimiter=sep)
        model=table.getModel()
        colnames,collabels  = model.columnNames,model.columnlabels
        header_row = [ collabels[c] for c in colnames ]
        recs = model.getAllCells() if not table.filtered else [ [model.data[a_row][c] for c in header_row ] for a_row in model.filteredrecs ]
        #take column labels as field names
        row=[]
        for c in colnames:
            row.append(collabels[c])
        writer.writerow(row)
        for row in sorted(recs.iterkeys()):
            writer.writerow(recs[row])
        return
class SimpleTableExporter:
    def __init__(self):
        "Same base functionality as TableExporter from Tables_IO module, but no GUI frontend"
        pass
    def ExportTableData(self, filename, table, seperator=None):
        "Export table data to a comma separated file"
        sep = ',' if not seperator else seperator
        writer = csv.writer(file(filename, "w"), delimiter=sep)
        model=table.getModel()
        colnames,collabels  = model.columnNames,model.columnlabels
        header_row = [ collabels[c] for c in colnames ]
        recs = model.getAllCells() if not table.filtered else model.getFilteredCells()
        writer.writerow(header_row)
        for a_row in sorted(recs.iterkeys()): writer.writerow(recs[a_row])
        pass
class mFilterFrameFunctions(object):
    def __init__(self,fields=None,callback=None):
        self.fields = fields
        self.filters = []
        self.resultsvar = IntVar(value=-999,name='results_found')
    def doFiltering(self, searchfunc, filters=None):
        '''Filter recs by several filters using user provided search function.
        Provides a list of tuples with filter values'''
        F=[]
        for f in self.filters:
            F.append(f.getFilter())
        sets = []
        for f in F:
            col, val, op, boolean = f
            names = searchfunc(col, val, op)
            sets.append((set(names), boolean))
        names = sets[0][0]
        for s in sets[1:]:
            b=s[1]
            if b == 'AND':
                names = names & s[0]
            elif b == 'OR':
                names = names | s[0]
            elif b == 'NOT':
                names = names - s[0]
        names = list(names)
        self.updateResults(len(names))
        return names
    def updateResults(self, i):
        self.resultsvar.set(i)
        return
class mFilterFrame(Frame,mFilterFrameFunctions):
    master_height = 80
    master_width = 600
    first_level_height = 40
    filter_height = 40
    def __init__(self, parent, fields, callback=None, closecallback=None,parent_x=0,parent_y=0):
        '''Create a filtering gui frame
        Callback must be some method that can accept tuples of filter
        parameters connected by boolean operators  '''
        Frame.__init__(self, parent)
        mFilterFrameFunctions.__init__(self,fields,callback)
        self.parent = parent
        self.callback = callback
        self.closecallback = closecallback
        self.master_x,self.master_y = parent_x, parent_y
        self.create_frames(self.parent)
        self.create_buttons()
        self.create_labels_and_chk_boxes()
        self.addFilterBar()
        self.parent.geometry('%dx%d+%d+%d'%(self.master_width,self.master_height+self.filter_height*len(self.filters),self.master_x,self.master_y))
        return
    def create_frames(self,root):
        self.ButtonsFrame = Frame(root,borderwidth="0",relief="groove",takefocus="0")
        self.ButtonsFrame.place(x=0,y=0,height=self.first_level_height,relwidth=0.4)
        self.LabelsAndChkButtonsFrame = Frame(root,relief="groove",takefocus="0")
        self.LabelsAndChkButtonsFrame.place(relx=0.405,y=0,height=self.first_level_height,relwidth=0.5)
        self.FiltersFrame = Frame(root,relief="groove",takefocus="0")
        self.FiltersFrame.place(x=0,y=self.first_level_height+2,relwidth=0.995)
    def create_buttons(self):
        self.GoButton=Button(self.ButtonsFrame,text='Go', command=self.callback,bg='lightblue')
        self.GoButton.grid(row=0,column=0,sticky='news',padx=2,pady=2)
        self.AddFilterButton=Button(self.ButtonsFrame,text='+Add Filter', command=self.addFilterBar)
        self.AddFilterButton.grid(row=0,column=1,sticky='news',padx=2,pady=2)
        self.CloseButton=Button(self.ButtonsFrame,text='Close', command=self.close)
        self.CloseButton.grid(row=0,column=2,sticky='news',padx=2,pady=2)
    def create_labels_and_chk_boxes(self):
        self.resultsvar = IntVar(self.LabelsAndChkButtonsFrame,-999,'results_found')
        self.use_regexp = BooleanVar(self.LabelsAndChkButtonsFrame,True,'use_regexp')
        self.FoundLabel = Label(self.LabelsAndChkButtonsFrame,text='found:')
        self.FoundLabel.grid(row=0,column=0,sticky='nes')
        self.ResultsFoundLabel = Label(self.LabelsAndChkButtonsFrame,textvariable=self.resultsvar)
        self.ResultsFoundLabel.grid(row=0,column=1,columnspan=2,sticky='news',padx=2,pady=2)
        self.RegexpChkButton = Checkbutton(self.LabelsAndChkButtonsFrame,text="UseRegexp",variable=self.use_regexp,onvalue=True,offvalue=False)
        self.RegexpChkButton.grid(row=0,column=3,sticky='nes',padx=2,pady=2)
    def addFilterBar(self):
        'Add filter'
        index = len(self.filters)
        f=mFilterBar(self.FiltersFrame, self, index, self.fields)
        self.filters.append(f)
        f.grid(row=index+1,column=0,columnspan=5,sticky='news',padx=2,pady=2)
        self.parent.geometry('%dx%d'%(self.master_width,self.master_height+self.filter_height*index))
        return
    def close(self):
        'Close frame and do stuff in parent app if needed'
        self.closecallback()
        self.destroy()
        return
class mtables_FilterFrame(mFilterFrame):
    Version = 'class:mtables_FilterFrame:20130323_0.5.1'
    master_height = 80
    master_width = 600
    first_level_height = 40
    filter_height = 40
    def __init__(self, parent, fields, additional_tables=[], callback=None, closecallback=None,parent_x=0,parent_y=0):
        '''Create a filtering gui frame, apply filtering across multiple tables from one gui interface
        Callback must be some method that can accept tuples of filter
        parameters connected by boolean operators  '''
        mFilterFrame.__init__(self,parent,fields,callback,closecallback,parent_x,parent_y)
        #self.parent = parent
        self.additional_tables = additional_tables
        #self.callback = callback
        #self.closecallback = closecallback
        #self.master_x,self.master_y = parent_x, parent_y
        #self.create_frames(self.parent)
        #self.create_buttons()
        #self.create_labels_and_chk_boxes()
        #self.addFilterBar()
        #self.parent.geometry('%dx%d+%d+%d'%(self.master_width,self.master_height+self.filter_height*len(self.filters),self.master_x,self.master_y))
        return
    def create_labels_and_chk_boxes(self):
        self.resultsvar = IntVar(self.LabelsAndChkButtonsFrame,-999,'results_found')
        self.use_regexp = BooleanVar(self.LabelsAndChkButtonsFrame,True,'use_regexp')
        self.apply_to_all = BooleanVar(self.LabelsAndChkButtonsFrame,True,'apply_to_all')
        self.FoundLabel = Label(self.LabelsAndChkButtonsFrame,text='found:')
        self.FoundLabel.grid(row=0,column=0,sticky='nes')
        self.ResultsFoundLabel = Label(self.LabelsAndChkButtonsFrame,textvariable=self.resultsvar)
        self.ResultsFoundLabel.grid(row=0,column=1,columnspan=2,sticky='news',padx=2,pady=2)
        self.RegexpChkButton = Checkbutton(self.LabelsAndChkButtonsFrame,text="UseRegexp",variable=self.use_regexp,onvalue=True,offvalue=False)
        self.RegexpChkButton.grid(row=0,column=3,sticky='nes',padx=2,pady=2)
        self.ApplyToAllChkButton = Checkbutton(self.LabelsAndChkButtonsFrame,text="ApplyToAllTabs",variable=self.apply_to_all,onvalue=True,offvalue=False)
        self.ApplyToAllChkButton.grid(row=0,column=4,sticky='nes',padx=2,pady=2)
    def doFiltering(self, searchfunc,filters=None):
        names = self._doFiltering(searchfunc,filters)
        for a_table in self.additional_tables:
            a_table.model.use_regexp_filter = self.use_regexp
            a_table.filterframe = mFilterFrameFunctions(fields=a_table.model.columnNames,callback=a_table.doFilter)
            a_table.filterframe.filters = self.filters
            a_table.doFilter()
        return names
    def _doFiltering(self, searchfunc, filters=None):
        """Filter recs by several filters using user provided search function.
        Provides a list of tuples with filter values"""
        F=[]
        for f in self.filters:
            F.append(f.getFilter())
        sets = []
        for f in F:
            col, val, op, boolean = f
            names = searchfunc(col, val, op)
            sets.append((set(names), boolean))
        names = sets[0][0]
        for s in sets[1:]:
            b=s[1]
            if b == 'AND':
                names = names & s[0]
            elif b == 'OR':
                names = names | s[0]
            elif b == 'NOT':
                names = names - s[0]
        names = list(names)
        self.updateResults(len(names))
        return names
class mFilterBar(Frame):
    'Class providing filter widgets'
    operators = ['contains','excludes','=','!=','>','<','starts with',
                 'ends with','has length']
    booleanops = ['AND','OR','NOT']
    def __init__(self, root, parent, index, fields):
        Frame.__init__(self, root)
        self.root = root
        self.parent=parent
        self.index = index
        self.filtercol=StringVar()
        if 'name' in fields:
            initial = 'name'
        else:
            initial = fields[0]
        filtercolmenu = Pmw.OptionMenu(self,
            labelpos = 'w',
            label_text = 'Column:',
            menubutton_textvariable = self.filtercol,
            items = fields,
            initialitem = initial,
            menubutton_width = 10)
        filtercolmenu.grid(row=0,column=1,sticky='news',padx=2,pady=2)
        self.operator=StringVar()
        operatormenu = Pmw.OptionMenu(self,
            menubutton_textvariable = self.operator,
            items = self.operators,
            initialitem = 'contains',
            menubutton_width = 8)
        operatormenu.grid(row=0,column=2,sticky='news',padx=2,pady=2)
        self.filtercolvalue=StringVar()
        valsbox=Entry(self,textvariable=self.filtercolvalue,width=20,bg='white')
        valsbox.grid(row=0,column=3,sticky='news',padx=2,pady=2)
        valsbox.bind("<Return>", self.parent.callback)
        self.booleanop=StringVar()
        booleanopmenu = Pmw.OptionMenu(self,
            menubutton_textvariable = self.booleanop,
            items = self.booleanops,
            initialitem = 'AND',
            menubutton_width = 6)
        booleanopmenu.grid(row=0,column=0,sticky='news',padx=2,pady=2)
        cbutton=Button(self,text='-', command=self.close)
        cbutton.grid(row=0,column=5,sticky='news',padx=2,pady=2)
        return
    def close(self):
        'Destroy and remove from parent'
        self.parent.filters.remove(self)
        self.destroy()
        return
    def getFilter(self):
        'Get filter values for this instance'
        col = self.filtercol.get()
        val = self.filtercolvalue.get()
        op = self.operator.get()
        booleanop = self.booleanop.get()
        return col, val, op, booleanop
## I have a working ComboBox which is editable and
## has a button around here some where. I'll keep
## looking for that. In the mean time, this Entry
## subclass shares a StringVar with the menu item
## that are created form input list(s) to achive a
## simple ChoiceBox.
 
class ChoiceBox(Entry):
    '''ComboBox(parent, itemList=[], *args, kwargs)
       A simple ChoiceBox with checked menu items
       itemList may be a mix of list of strings and lists of tuples of (label, list of strings)
       for one level of sub menu items. *args and kwargs are passed to the Entry widget.'''
    def __init__(self, parent, itemList=[], *args, **kwargs):
        Entry.__init__(self, parent, *args, **kwargs)
        self.pyvar = pyvar = StringVar(self)    # this is the sharing mechanism
        self.config(textvariable=pyvar)         # add the StringVar to self.
        self.popup = popup = Menu(self, tearoff=0)
        self.bind("<Button-1>", self.mousedown, add="+")
        for item in itemList:
            if type(item) == tuple:
                submenu = self.GetSubMenu(item[0])
                for subitem in item[1]:
                    self.AddCBMenuItem(submenu, subitem)
            else:
                self.AddCBMenuItem(popup, item)
    def GetSubMenu(self, label):
        menu = Menu(self, tearoff=0)
        self.popup.add_cascade(menu=menu, label=label)
        return menu
    def AddCBMenuItem(self, menu, label):
        menu.add_checkbutton(label=label,
                             command=self.MenuSelect,
                             variable=self.pyvar,   # add the StringVar to a menu.
                             onvalue=label, offvalue='')
    def mousedown(self, event):
        x = event.x_root - event.x
        y = event.y_root -  event.y
        self.popup.post(x, y)
        return 'break'
    def get(self):
        return self.pyvar.get()
    def clear(self):
        self.pyvar.set('')
    def MenuSelect(self):
        pass
# floating_menu
# first attempt at creating class for generating mouse driven events, i.e. M3 brings up a menu of options such as copy, cut
# and paste.  Want a boiler plate to start with, then allow for insertion of custom events as required for the 
# particular app.

class FloatingMenu(Frame): 
    ''' floating_menu
 first attempt at creating class for generating mouse driven events, i.e. M3 brings up a menu of options such as copy, cut
 and paste.  Want a boiler plate to start with, then allow for insertion of custom events as required for the 
 particular app.
    '''
    Version = '0.1'
    def __init__(self, master=None):
        Frame.__init__(self, master) 
        self.grid(sticky=N+S+W+E)
        self.rowconfigure(0, weight=1)
    def _create_menu_bar(self, root):
        # create menubar
        self.menubar = Menu(self)
    def _add_to_menu_bar(self, CommandLabel, Command):
        self.menubar.add_command(label=CommandLabel, command=Command)
def _test_choice_box():
    root = Tk()
##        cb = ChoiceBox(root, [('test', ['one', 'two', 'three'])])
    cb = ChoiceBox(root, ['one', 'two', 'three'])
    cb.pack()
    root.mainloop()
 
if __name__ == '__main__':
    _test_choice_box()
