# jk 20140313: removed tkintertable stuff and replaced pyExcelerator with xlwt
import add_to_Utilities as util
from xlwt import Workbook, Font, Borders, Alignment, XFStyle
class ConvertCsv2Xls(object):
    attributes_dict = { \
        'Self':{'font': 'Font', 'borders':'Borders', 'alignment':'Alignment', 'style':'XFStyle'}, \
        'Font':{'font.name':'Arial', 'font.color_index':0x08, 'font.bold':False, 'font._weight':0x0190}, \
        'Borders':{'borders.left':0,'borders.right':0,'borders.top':0,'borders.bottom':0}, \
        'Alignment':{'alignment.horz':Alignment.HORZ_CENTER,'alignment.vert':Alignment.VERT_CENTER}, \
        'Style':{'style.font':'font','style.borders':'borders','style.alignment':'alignment'}, \
        'Args':['file_name','csv_source','worksheet_titles','pm','pm_info','max_word_width']\
    }
    kwargs_dict = {\
        'font.name':{'attribute':'font.name','default':'Arial'}, \
        'font.color_index':{'attribute':'font.color_index','default':0x08}, \
        'font.bold':{'attribute':'font.bold','default':False}, \
        'font._weight':{'attribute':'font._weight','default':0x0190}, \
        'borders.left':{'attribute':'borders.left','default':0}, \
        'borders.right':{'attribute':'borders.right','default':0}, \
        'borders.top':{'attribute':'borders.top','default':0}, \
        'borders.bottom':{'attribute':'borders.bottom','default':0}, \
        'alignment.horz':{'attribute':'alignment.horz','default':Alignment.HORZ_CENTER}, \
        'alignment.vert':{'attribute':'alignment.vert','default':Alignment.VERT_CENTER} \
    }
    def __init__(self,file_name='',csv_source=[],worksheet_titles=[],max_word_width=122,**kwargs):
        self.__set_attribute_defaults__(*[file_name,csv_source,worksheet_titles,util.Profiler(),[],max_word_width])
        self.__match_up_kwargs__(kwargs)
        self.generate_workbook(*self.setup_csv_source(self.csv_source,self.worksheet_titles,self.file_name))
    def __set_attribute_defaults__(self,*args):
        for attribute,a_value in self.attributes_dict['Self'].iteritems(): setattr(self,attribute,eval('%s()'%a_value))
        for attribute,a_value in self.attributes_dict['Font'].iteritems(): 
            self_attribute,sub_attribute = attribute.split('.')
            setattr(eval('self.%s'%self_attribute),sub_attribute,a_value)
        for attribute,a_value in self.attributes_dict['Borders'].iteritems():
            self_attribute,sub_attribute = attribute.split('.')
            setattr(eval('self.%s'%self_attribute),sub_attribute,a_value)
        for attribute,a_value in self.attributes_dict['Alignment'].iteritems():
            self_attribute,sub_attribute = attribute.split('.')
            setattr(eval('self.%s'%self_attribute),sub_attribute,a_value)
        for attribute,a_value in self.attributes_dict['Style'].iteritems():
            self_attribute,sub_attribute = attribute.split('.')
            setattr(eval('self.%s'%self_attribute),sub_attribute,a_value)
        for attribute,arg in zip(self.attributes_dict['Args'],args): setattr(self,attribute,arg)
    def __match_up_kwargs__(self,kwargs):
        for a_key,a_value in kwargs.iteritems():
            if a_value:
                attribute = self.kwargs_dict[a_key]['attribute']
                if self.attributes_dict['Font'].has_key(attribute): 
                    self_attribute,sub_attribute = attribute.split('.')
                    setattr(eval('self.%s'%self_attribute),sub_attribute,a_value)
                if self.attributes_dict['Borders'].has_key(attribute):
                    self_attribute,sub_attribute = attribute.split('.')
                    setattr(eval('self.%s'%self_attribute),sub_attribute,a_value)
                if self.attributes_dict['Alignment'].has_key(attribute):
                    self_attribute,sub_attribute = attribute.split('.')
                    setattr(eval('self.%s'%self_attribute),sub_attribute,a_value)
        for attribute,a_value in self.attributes_dict['Style'].iteritems():
            self_attribute,sub_attribute = attribute.split('.')
            setattr(eval('self.%s'%self_attribute),sub_attribute,eval('self.%s'%a_value))
    def setup_csv_source(self,csv_source=None,worksheet_titles=[],file_name=None):
        self.pm.snap()
        if isinstance(worksheet_titles,str): 
            if not file_name: file_name = '%s.xls'%worksheet_titles
            worksheet_titles = [worksheet_titles]
        if not file_name: file_name = self.file_name
        if isinstance(csv_source,util.FileEdit): #util.FileEdit instance
            csv_source_list = [ [a_row.rstrip() for a_row in f.contents] for f in csv_source.file_utils ]
        elif isinstance(csv_source,list):
            if isinstance(csv_source[0],list): 
                if isinstance(csv_source[0][0],list):
                    csv_source_list = [ [','.join(a_row) for a_row in a_table] for a_table in csv_source ]
                else: csv_source_list = csv_source
            else: pass
        else: csv_source_list,worksheet_titles = [],[]
        # work on iteration throught csv_source_list and worksheet_titles
        # account for a mismatch in quantity between worksheet_titles and csv_source_list, i.e. a default enum 
        # for any missing worksheet titles.....
        if len(csv_source_list) != len(worksheet_titles):
            if len(csv_source_list)>len(worksheet_titles):
                worksheet_titles += [ 'Sheet%03d'%i for i in xrange(len(worksheet_titles),len(csv_source_list)) ]
            else: worksheet_titles = worksheet_titles[:len(csv_source_list)]
        self.pm_info.append(' + setup_cvs_source; %f'%self.pm.snap())
        return csv_source_list,worksheet_titles,file_name
    def generate_workbook(self,*args):
        self.pm.snap()
        start_time = self.pm.snap_time
        delimeter = ','
        if len(args)==3: 
            csv_source_list,worksheet_titles,file_name = args
        else:
            csv_source_list,worksheet_titles,file_name = self.csv_source,self.worksheet_titles,self.file_name
        self.wb = Workbook()
        self.ws_list = [ self.wb.add_sheet(ws_title) for ws_title in worksheet_titles ]
        self.pm_info.append(' + setup workbook; %f'%self.pm.snap())
        for csv_source,ws_title,ws in zip(csv_source_list,worksheet_titles,self.ws_list):
            for a_row,row_length,a_line in zip(xrange(len(csv_source)),iter(len(sub_line.split(delimeter)) for sub_line in csv_source),iter( sub_row.rstrip().split(delimeter) for sub_row in csv_source )):
                for a_col,a_cell in zip(xrange(row_length),a_line): ws.write(a_row,a_col,a_cell,self.style)
            self.__auto_scale_column_width__(csv_source,ws,max_word_width=self.max_word_width)
            self.pm_info.append(' ++ generated worksheet %s; %f'%(ws_title,self.pm.snap()))
        self.wb.save(file_name)
        self.pm_info.append(' + saved workbook file; %f'%self.pm.snap())
        self.pm_info.append(' + total time to generate workbook; %f'%(self.pm.snap_time-start_time))
    def __auto_scale_column_width__(self,a_table,ws,delimeter=',',base_word_width=8,pixel_scale_factor=260,max_word_width=122):
        max_width = max_word_width*pixel_scale_factor
        num_cols = max(len(a_row.split(delimeter)) for a_row in a_table)
        col_widths = [base_word_width*pixel_scale_factor for i in xrange(num_cols)]
        for a_line in iter(a_row.split(delimeter) for a_row in a_table):
            for i,a_cell in zip(util.InfiniteCounter(start=-1),a_line):
                if len(a_cell)*pixel_scale_factor > col_widths[i]: col_widths[i] = len(a_cell)*pixel_scale_factor 
        col_widths = [a_width if a_width <= max_width else max_width for a_width in col_widths]
        for i,w in enumerate(col_widths): ws.col(i).width = w
#check out Csv2Xls
def test():
    kwargs = dict([ ('font.name','Arial'),('font.color_index',0x08),('font._weight',0x0190) ])
    csv_source = [ a.OutputNoteBookDict[i]['widget'] for i in sorted(a.OutputNoteBookDict.iterkeys()) if i>0 ]
    worksheet_titles = [ a.OutputNoteBookDict[i]['title'] for i in sorted(a.OutputNoteBookDict.iterkeys()) if i>0 ]
    file_name = 'chk_out.xls'
    reload(C2X)
    c = C2X.ConvertCsv2Xls(file_name,csv_source,worksheet_titles,**kwargs)
def chk_setup_csv_source():
    return c.setup_csv_source(c.csv_source,c.worksheet_titles,c.file_name)
def chk_generate_workbook(*args):
    c.generate_workbook(args)
def sandbox():
    #set attributes for workbook
    fnt = Font()
    fnt.name, fnt.colour_index, fnt.bold, fnt._weight = 'Arial',0x08,False,0x0190
    borders = Borders()
    borders.left, borders.right, borders.top, borders.bottom = 0,0,0,0
    al = Alignment()
    al.horz, al.vert = Alignment.HORZ_CENTER,Alignment.VERT_CENTER
    style = XFStyle()
    style.font, style.borders,style.alignment = fnt,borders,al
    # create wb instance
    wb = Workbook()
    #add a sheet for each csv file being imported to excel
    s = util.GetFileListing('Note*.csv')
    csv_files = s.sys_cmd.output
    worksheet_titles = [ ':'.join(a_file.split(':')[1:-2]) for a_file in csv_files ]
    ws_list = [ wb.add_sheet(ws_title) for ws_title in worksheet_titles ]
    F = util.FileEdit(csv_titles)
    for ws,f in zip(ws_list,F.file_utils):
        a_list = [ a_row.rstrip().split(',') for a_row in f.contents ]
        for a_row,a_line in enumerate(a_list):
            for a_col,a_cell in enumerate(a_line): ws.write(a_row,a_col,a_cell,style)

    wb.save('chk_out.xls')

