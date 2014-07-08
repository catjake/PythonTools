#!/usr/bin/env python
import re
import shelve
import util
from util import PrettyPrint
TimeStamp = '20130816:1341:51'
class GetEvObjects(object):
    'Parse through external references (if any) of an envision test program.'
    'Store the objects in persistant container, dbm in this case'
    def __init__(self,pdb):
        self.dbm = pdb
        self.access_count = 0
        self.object_listing=[]
    def _externalRefCase(self,object_contents):
        object_name,object_type="",object_contents[0].split()[0]
        for eachLine in object_contents:
            m_ev_file=re.search('\s+(?:__)?File\s*=\s*\"(.+\.(?:ev|un)o)\"',eachLine)
            m_cad_file=re.search('\s+File\s*=\s*\"(.+\.(?:tp|tmod|mod))\"',eachLine)
            m_evso_file=re.search('\s+File\s*=\s*\"(.+\.[tc][mx][kx])\"',eachLine)
            if m_ev_file != None:
                object_name = '%s:%s'%(object_type,m_ev_file.group(1))
                return(object_name)
            if m_cad_file != None:
                object_name = 'ExternalRef:'+m_cad_file.group(1)
                return(object_name)
            if m_evso_file != None:
                object_name = 'ExternalRef:'+m_evso_file.group(1)
                return(object_name)
    # get object contents and stuff into persistant storage (pdb)
    def ev_stuff_object(self,query,allLines):
        '''critical assumption here is that structure has ObjName and { on same line'''
        util.Strip_C_Comments(allLines)
        ev_obj_capture = util.CaptureBlocks(allLines,block_start='^\s*(?:__)?[A-Z]\w+\s+.*{',block_stop='}',start_phrase='{')
        assert len(ev_obj_capture.start_pts) == len(ev_obj_capture.end_pts), 'In parsing for ev object locations '+ \
            'did not find all pairs of delimeters, missing one or more here'
        aRange = range(len(ev_obj_capture.start_pts))
        for i in aRange:
            start_here, stop_there = ev_obj_capture.start_pts[i], ev_obj_capture.end_pts[i]
            object_and_name = allLines[start_here].split('{')[0]
            object_type = object_and_name.split()[0]
            object_name = ' '.join(object_and_name.split()[1:])
            #object_type,object_name = allLines[start_here].split()[:2]
            if cmp(object_type,'ExternalRef')==0 or cmp(object_type,'__ExternalRef')==0:
                object_name=self._externalRefCase(allLines[start_here:stop_there])
                try:
                    object_name.split(':')
                except AttributeError:
                    print "line range: ",start_here,':',stop_there
                    print "object_name: ",object_name,"\tobject_type: ",object_type
                    for line in allLines[start_here:stop_there]:
                        print line
                    raise
            else: 
                object_name=object_type+':'+object_name
            self.object_listing.append(object_name)
            self.dbm[object_name] = allLines[start_here:stop_there]
    def old_ev_stuff_object(self,query,allLines):
        totalLineCount = len(allLines)-1 
        self.access_count += 1
        pattern=re.compile(query)
        i = 0
        while i < totalLineCount:
            line = allLines[i]
            m=re.search(pattern,line)
            if m != None:
                start_here = i
                object_type,object_name=line.split()[0:2]
                objectOpen=1
                while objectOpen:
                    i += 1
                    try:
                        line = allLines[i]
                    except IndexError:
                        print "at end of file..."
                        i -= 1
                        line = allLines[i]
                    objectOpen += line.count('{') - line.count('}')
                stop_there=i+1
                if cmp(object_type,'ExternalRef')==0:
                    object_name=self._externalRefCase(allLines[start_here:stop_there])
                    try:
                        object_name.split(':')
                    except AttributeError:
                        print start_here,':',stop_there
                        for line in allLines[start_here:stop_there]:
                            print line
                        raise
                else: 
                    object_name=object_type+':'+object_name
                self.object_listing.append(object_name)
                self.dbm[object_name] = allLines[start_here:stop_there]
            i += 1
class GetEvChildren:
    'Build Reference Tree of Envision Objects.'
    'Store object hierarchy in list'

    def __init__(self):
        pass

