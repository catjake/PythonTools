# -*- coding: utf-8 -*-
import util, os, re, sys
from xlrd import open_workbook, USE_MMAP, cellname
# from pyExcelerator import parse_xls
import unicodedata

utf_8_map = {
    u"\u2019":  u"'", u"\u2018":  u"'", u"\u201c":  u'"', u"\u201d":  u'"', u"\u2026": u'…',
    u"\u2103":u'℃'
}
utf_map = dict([(ord(k),ord(v)) for k,v in utf_8_map.iteritems()])


def unicode_info(a):
    '''Handy for special unicode characters like the HELLO ELLIPSIS u'…' '''
    cat, name = unicodedata.category(a),unicodedata.name(a)
    encode_type = unicodedata.lookup(name)
    return cat,name,encode_type


class Xls2Csv(object):
    kwargs =  {"filename": None, "logfile": sys.stdout, "verbosity": 0, "use_mmap": USE_MMAP,
               "file_contents": None, "encoding_override": None, "formatting_info": False,
               "on_demand": False, "ragged_rows": False}

    def __init__(self, **kwargs):
        for arg, value in self.kwargs.iteritems():
            if arg in kwargs:
                self.kwargs[arg] = kwargs[arg]
        self.wb = open_workbook(**self.kwargs)

    def get_contents(self, sheet_obj, skip_if_empty=True):
        sheet_contents = {}
        for row in xrange(sheet_obj.nrows):
            for col in xrange(sheet_obj.ncols):
                if sheet_obj.cell(row, col).value or not skip_if_empty:
                    sheet_contents[cellname(row, col)] = sheet_obj.cell(row, col).value
        return sheet_contents


def parse_xls(fn, encoding):
    pass


class oldConvertXls2Csv(object):
    '''encodings: refer to ImportXLS.py in the pyExcelerator package, default is "cp437", which is #IBM PC CP-437 (US)
    file_name needs to be an excel file.  This class converts each worksheet to a csv list, which can be written to 
    a file <worksheet_title>.csv'''
    pm = util.Profiler()
    def __init__(self,file_name,encoding='utf_8',generate_csv_files=True,dest_dir='/tmp'):
        self.file_name,self.encoding,self.dest_dir = file_name,encoding,dest_dir
        self.pm_info = []
        self.pm.snap()
        self.wb_list = parse_xls(self.file_name,self.encoding)
        self.pm_info.append(' + Parse xls file-> %s: %f'%(self.file_name,self.pm.snap()))
        self.wb_dict = self.__wb_list_2_dict__(self.wb_list)
        self.pm_info.append(' + Build wb_dict {sheet_name:[sheet_contents.csv]}: %f'%self.pm.snap())
        if generate_csv_files:
            self.GenerateCsvFiles(self.wb_dict,self.dest_dir)
            self.pm_info.append(' + Generate Csv files: %f'%self.pm.snap())
        else: pass
    def GenerateCsvFiles(self,wb_dict,dest_dir='/tmp'):
        for a_sheet,a_list in wb_dict.iteritems():
            mm,fh = util.reset_mmap(None,util.FileUtils(os.path.join(dest_dir,util.sub_iterator(['%s.csv'%a_sheet],'[\(\)\-\s]','_').next()[0])),util.add_cr_iter(a_list))
            bob = (mm.close(),fh.close())
    def __wb_list_2_dict__(self,wb_list):
        wb_dict = {}
        try:
            for i, (a_sheet, a_dict) in enumerate(wb_list):
                wb_dict[a_sheet.encode("cp437")] = self.__break_down_sheet_contents__(a_dict)
        except Exception:
            print("SheetName: {0}, index: {1}".format(a_sheet,i))
            raise
        return wb_dict
    def __get_cell_contents__(self,a_value,encode_val='utf_8'):
        if isinstance(a_value,(str,unicode)):
            if isinstance(a_value,unicode) and len(a_value)>0:
                a_string = a_value.replace(u'\u2026','...').replace(u'\u2103','C').translate(utf_map).encode('utf_8','ignore')
            else: a_string = a_value
            if re.search(re.compile('"'),a_string): a_string = re.sub(re.compile('"'),'""',a_string)
            if re.search(re.compile(','),a_string): a_string = '"%s"'%a_string
        else: a_string = str(a_value)
        try:
            encoded_string = a_string.encode(encode_val)
        except UnicodeDecodeError:
            encoded_string = a_value.encode('ascii','ignore')
        return encoded_string
    def __break_down_sheet_contents__(self,a_dict):
        rows = util.sort_unique([a for a,b in sorted(a_dict.iterkeys())])
        row_by_col = dict([(a_row,[]) for a_row in xrange(max(rows)+1) ])
        for row,col in sorted(a_dict.iterkeys()): row_by_col[row].append(col)
        col_range = lambda col_list: xrange(max(col_list)+1 if len(col_list)>0 else 0)
        get_cell = lambda a_dict,a_key,encode_val='utf_8': self.__get_cell_contents__(a_dict[a_key],encode_val) if a_dict.has_key(a_key) else ''
        try:
            return [ ','.join([get_cell(a_dict,(row,a_col)) for a_col in col_range(row_by_col[row])]) for row in sorted(row_by_col.iterkeys()) ]
        except Exception:
            print("Oooops, what do we have:\nrow: {0}, col: {1}\n{2}".format(row,a_col,a_dict[(row,a_col)]))
            raise

#convert wb_list to dictionary structured by:
# wb_dict = {sheet_name_0:{ rows = [row_list], row_by_col:{ 0:[cols],1:[cols],....}},
#    sheet_name_1:{ rows = [row_list], row_by_col:{ 0:[cols],1:[cols],....}},...}
def test(file_name):
    wb = Xls2Csv(file_name)

