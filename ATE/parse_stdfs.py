import util
import dlog_analysis as da
import sys
import commands
import os
import time

# get file list of stdf's, we're looking for *.std, *.stdf, *.std.gz, *.stdf.gz
# process the stdfs, create dlist and flist, die id records and fail logs respectively
class ProcessStdfs:
    '''batch process stdf files that have been converted to ascii with stdf2atdf.py'''
    def __init__(self,dir_path_list=["./"], file_pattern='*.atd*', doRecursive=False, x_loc=0,y_loc=0,w_loc=0):
        self.stdf_files = util.get_file_listing(dir_path_list, file_pattern, doRecursive)
        self.stdf_dict = {}
        self.parse_them(x_loc,y_loc,w_loc)
        
    def parse_them(self,x_loc=0,y_loc=0,w_loc=0):
        for a_file in self.stdf_files:
            print('Working on %s, started at %s'%(a_file,time.asctime()))
            snap = time.time()
            self.stdf = da.ParseStdf(a_file,x_loc,y_loc,w_loc)
            self._write_to_file(a_file.split('.')[0]+'.dlist',self.stdf.DieIdList)
            self.determine_die_id_fails(a_file)
            self._write_to_file(a_file.split('.')[0]+'.flist',self.stdf.FailLogList)
            d = util.GetTimeStamp(time.time()-snap)
            print('Done, finished at %s'%time.asctime())
            print('Finished processing in %s'%d.time_string)
            self.stdf_dict[a_file] = self.stdf

    def determine_die_id_fails(self,stdf_file):
        list_seq = [5,6,0,1,2,3]
        m = util.m_sort(self.stdf.DieIdList)
        m.sort_by(list_seq,'[:\|]')
        m.sortList.reverse()
        die_id_list = [ ' '.join(a_line[:3]) for a_line in [ a_record.split(':') for a_record in m.sortList ] if int(a_line[5])!=1 ]
        self.stdf.GetFailLogList(die_id_list)

    def _write_to_file(self,a_file,a_list):
        f = util.FileUtils(a_file)
        f.write_to_file(a_list)


'''
import parse_stdfs as ps
x_loc,y_loc,w_loc = '70063 70064 70066'.split() # FT1
x_loc,y_loc,w_loc = '10063 10064 10066'.split() # FT2
file_pattern = './ATDF/*.atd*'
p = ps.ProcessStdfs(file_pattern,x_loc,y_loc,w_loc)

#insert die id at the front of each line in dlist and flist
d = util.GetFileListing('*.*list','-1')
file_list = d.sys_cmd.output
for a_file in file_list:
    f=util.FileEdit(a_file)
    f.sub('(?P<id>^\d)',f.file_list[0].split('_')[4]+':\g<id>')

#concate it all together
d = ps.SysCommand('find . -name "*.dlist" -exec cat {} >> BigDlist \;' )
d = ps.SysCommand('find . -name "*.flist" -exec cat {} >> BigFlist \;' )

#get the first fails lined up
f = util.FileUtils('BigFlist')
f.read_from_file()

a_list = util.sort_unique([ ':'.join(util.my_split(a_line,'[:\|]')[:4]) for a_line in f.contents ])
g = util.m_re(f.contents)
b_list=[]
for a_record in a_list:
    g.grep(a_record)
    b_list.append(f.contents[int(float(g.coordinates[0]))-1])
    g.clear_cache()

f = util.FileUtils('FirstFails')
f.write_to_file(b_list)

# format with 1 leading 0 for dlist, sort by die_id
f = util.FileEdit(file_list)
f.sub('(?P<head>[:\|])(?P<id>\d)(?P<tail>[:\|])','\g<head>0\g<id>\g<tail>')
for index in f.file_index_list:
    blah = f.file_utils[index].read_from_file()
    m = util.m_sort([ a_line.strip() for a_line in f.file_utils[index].contents ])
    m.sort_by([1,2,3],'[:\|]')
    blah = f.file_utils[index].write_to_file(m.sortList)

# build up stats table
a = p.stdf
die_id_list = [ ' '.join(util.my_split(a_line,'[:\|]')[:3]) for a_line in a.DieIdList ]
test_list = '10653 10654 10655 10656'.split()
c_list = a.GenerateDlogRecordDict(die_id_list,test_list)
g = util.m_re(c_list)
g.grep(':10653:')

t = da.TestAnalysis(g.lines,0.0049,0.090,[5],':')
    
f_list = []
for a_die in die_id_list:
    g.grep(a_die+'[:\|]')
    if g.pattern_count > 0: f_list = f_list + g.lines
  
#generate a histogram....
import numpy as np
import matplotlib.mlab as mlab
import matplotlib.pyplot as plt
results_list = t.Results[0]
plt.figure(1)
n, bins, patches = plt.hist(results_list,50, (0.005,0.090), normed=1, facecolor='green', alpha=0.75)
mu = t.ResultsDict['Avg']
sigma = t.ResultsDict['StdDev']
y = mlab.normpdf(bins,mu,sigma)
l = plt.plot(bins,y,'r--',linewidth=1)
plt.xlabel('THDN, OUT1')
plt.ylabel('Probability')
plt.title(r'$\mathrm{Histogram\ of\ THDN:}\ \mu=0.018784,\ \sigma=0.00319$')
plt.axis('auto')
plt.grid(True)
plt.show()

'''
