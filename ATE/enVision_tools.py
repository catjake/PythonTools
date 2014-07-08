import re
import copy
import util
import string

'''AdapterBoard <adapter_name> {
    Pin { Name= <pin_name>; Ppid= "<ppid>"; XCoord= (<int>, <int>); Shape=16; PinType=<pintype>;
        Connection[0] { TesterCh[1] = <resource>; [TesterCh[2] = <resource>;..TesterCh[N]=<resource>; }
    }
    ...
    [MaxSite = <num_sites>;]
}

SignalHeader <Scan_SH_Name> {
    evSegmentName = "<Scan_SH_Name>_Seg";
    Signals {
        <Pin_Name> { Scan, ScanLength = <ScanChainLength>, Fill = <default_alias, <Fill>; }
        <Pin_Name> { Scan, ScanLength = <ScanChainLength>, Fill = <default_alias, <Fill>; }
        <Pin_Name> { Scan, ScanLength = <ScanChainLength>, Fill = <default_alias, <Fill>; }
        <Pin_Name> { Scan, ScanLength = <ScanChainLength>, Fill = <default_alias, <Fill>; }
        <Pin_Name> { Scan, ScanLength = <ScanChainLength>, Fill = <default_alias, <Fill>; }
        <Pin_Name> { Scan, ScanLength = <ScanChainLength>, Fill = <default_alias, <Fill>; }
        ....
        ....
    }
}
where:
    Pin_Name = pin resource from AdapterBoard/SignalHeader
    ScanChainLength = Num of bits in scan chain
    default_alias = alias character used by compiler to fill chain when not at ScanChainLength
    Fill = 2 choices -> PreFill, PostFill, where Pre fills at beggining of scan chain, and post at the end of scan chain

Use GenSigHeader(pin_list) to create signal headers

PatternSequence <PatSeq_Name> {
    Thread[0]=<thread_name>;
    Thread[1]=<thread_name>;
    ...
    Thread[N]=<thread_name>;
    Zipper = Zipper {
        Row { <PatGrp>, <WFT_Reference_Name> = { <WaveformTable> } }
        Row { <PatGrp>, <WFT_Reference_Name> = { <WaveformTable> } }
        ...
    }
}
where: 
    PatGrp = PatternGroup for signal header used for parallel vectors in pattern
    WFT_Reference_Name = somewhat arbitrary, references WaveformTable(s), called into Waveform field in pattern
    thread_name = Thread composed of rows of action sequences and pattern labels which define pattern execution order and conditions
    
Use GenPatternSequence to create pattern sequence object.  Put in space holder for thread(s) and set WaveformTable Name and reference.

Pattern <Pattern_Name> {
Type <Pattern_Type>;

"<Comment Line Only>"
$Label
*<ChannelData>* WFT_Ref SignalHeader; < <Microcode> > "<Comments>" 
*<ChannelData>* WFT_Ref SignalHeader; < <Microcode> > "<Comments>" 
*<ChannelData>* WFT_Ref SignalHeader; < <Microcode> > "<Comments>" 
...
}
where: 
    Pattern_Name = evo FileName
    Pattern_Type = CPM or DPM
    WFT_Ref = WaveformTable Reference
    SignalHeader = list of pins that correspond to the ChannelData
    ChannelData = stream of alias characters

Use GenPattern to create pattern object.  Pass in Pattern_Name, Pattern_Type, SignalHeader_Name, and massaged vector field data

PatternMap <pattern_map_name> {
    [DefaultSourcePath = <string>;]
    [DefaultBinaryPath = <string>;]
    [DefaultPatternGroup = <string>;]
    Pattern <name> {
        File <filename1>[, <filename2>..<filenameN>];
        [Path <sourcepath1[, <sourcepath2>..<sourcepathN>];]
        [CachePath <cachepath1>[, <cachepath2>..<cachepathN>];]
        [Group <patterngroup>;]
        [evRemove <boolean>;]
    }
    ...
}

Use GenPatternMap to creat pattern map object.  Pass in Pattern_Map_Name, DefaultSourcePath, DefaultBinaryPath, 
    DefaultPatternGroup when creating class instance.  Use gen_pattern_entry to create pattern statement and pass in
    filename_list, pathname_list, cachepath_list, groupname, and evRemove (default is False) 

WaveformTable Cell Drive states:
    DriveOn, DriveHigh, DriveLow, DriveData, DriveDataNot, DriveOff, DriveHighIfOne, DriveLowIfZero, DriveHighIfZero,
    DriveLowIfOne, EdgeMarker, PeriodMarker
WaveformTable Cell Compare states:
    CompareData, CompareFloat, CompareFloatNot, CompareOpenData, CompareOpenDataNot, CompareOpenFloat, CompareOpenFloatNot,
    CompareClose, CompareHighIfOne, CompareLowIfZero, CompareHighIfZero, CompareLowIfOne, EdgeMarker, PeriodMarker

WaveformTable <WFT_Name> {
    Period "<period_value>";
    Cell "<cell_name>" <OXBI.aliases> PinGrp/Pins {
        [Inherit <cell_name>._<OXBI.half>_<OXBI.half>;] # such as Inherit z8600_pats__z8600_pats._2_3;
        [Data <OXBI.states>
        [Drive {
            [EntryState <drive_state>]
            Waveform { <drive_state> [@ "<time_value>"]; [<drive_state> @ <time_set> [-> <time_expression>;] }
        } ]
        [Compare {
            [Data <OXBI.states>;]
            Waveform {<compare_state> [@ "<time_value>"]; [<compare_state>....]}
        } ]
where: 
    drive_state/compare_state: a valid WaveformTable Cell state, such as DriveOn, DriveState, CompareOn, etc.
    time_value: some float value, can be a scalar or expression
    time_set: D0, D1, D2, D3
    time_expression: like time_value, except scalars are in quotes, i.e. T0 + "0nS"
    OXBI.states: out_lo/out_hi mask_lo/mask_hi bi_lo/bi_hi in_lo/in_hi -> 0/1/2/3/4/5/6/7
    OXBI.aliases: alphanumeric/[alphanumeric], i.e. r/R, M/
    OXBI.half: OXBI.state, i.e. 2 or 3, etc.
examples: 
    rz drive waveform -> EntryState DriveOn; Waveform { DriveLow; DriveData; DriveLow; }
    nrz drive waveform -> EntryState DriveOn; Waveform { DriveData; }

WaveformTable TDLScanPatGrp TDLScanPatGrp {
    Cell "TDLScanPatGrp.Pins" d PatSrcOther {
        Data 3 Other;
        Color 6;
        Drive {
            Waveform { DriveOff; }
        }
    }
    Cell "TDLScanPatGrp.Pins" s ScanInAlias {
        Data 3 Serial;
        Color 5;
        Drive {
            Waveform { DriveOff; }
        }
    }
    Cell "TDLScanPatGrp.Pins" q ScanOutAlias {
        Data 3 Serial;
        Color 8;
        Drive {
            Waveform { DriveOff; }
        }
    }
    Cell "TDLScanPatGrp.Pins" - HoldState {
        Data 6;
        Color 3;
        Drive {
            Waveform { }
        }
    }
    Inherit TDLStdPatGrp__TDLStdPatGrp;
}

Levels <LevelName> {
    [Comment = "relevant description here";]
    Column[0] {
        LevelsColumnType = <evSeqPowerType|evPowerType|evDigitalType|evDCTestType|evCalibrationType>
        Title= <title_name>
        Group= Expr { String = "<pingrp/pin combination>"; }
        ExecSeq = Expr { String = "<expression/value of integer type>";}
'''
#globals
ev_header= 'enVision:"bl8:R14.2.1.WW20060502:S3.6"; /* 5.7 */'
disclaimer='''/* ***************************************************************************************************************
generated by rddt -> really don't do teradyne.... seriously though, there's a high probability that
something wasn't quite converted over properly. If you find a bug, send me a test case, a dump from the console if 
there is one, and other relevant info to help me hone into the problem.  My e-mail is bill_keezel@ltx.com and I'll
glady welcome any feedback, questions, or comments along with any problems in converting the pattern(s).

In the event that this is a scan pattern, look for 'SCAN_SETUP' in the comments, this is the vector that would 
run in the background, which better be a background vector in the "new" evo.  For pin_mode scenarios, especially 
if a pin was in dual mode, the comments section  would have the pin name, mode, and the 2 alias characters, i.e. 11.  
If the two aliases are different, such as 10, then the format in the waveform table will need to be modified accordingly, 
actually, the format will probably have to be modified anyway since set pin tset statement for specifying the pin format 
may not match the pin mode declaration from the pin list field of the vector in the tp.  Lastly, on the topic of SCAN, 
only the DPM evo is created, it may have to be massaged to be compliant with scan autogen.

For mix signal, look in the comments for ac hdw names and ac op codes, these are clues as to when a digitizer is triggered
for a capture, or an awg is triggered to source a segment, or dsp send is shifted (D+) or dpro capture is started or stopped
.... well, hopefully from the comments one can ascertain the instrumentation being used and how and when.

-Bill Keezel, 2006-08-10
***************************************************************************************************************** */  '''
class GenAdapterBoard:
    '''Pass in DIB name and device object like the one generated from rddt.PinMap_Cat2Env.
Use gen_pintypes() and gen_adapter_board() to create pintypes and adapterboard '''
    def __init__(self,adapter_board_name, device):
        self.board_name = adapter_board_name
        self.device= device
        self.device_list = []

    def gen_pintypes(self):
        for aPinType in self.device.pintype_dict['KeyOrder']:
            self.device_list.append('PinType %s {'% (aPinType))
            for aField in self.device.pintype_dict[aPinType]['KeyOrder']:
                self.device_list.append('    %s = %s;' % (aField, self.device.pintype_dict[aPinType][aField]) )
            self.device_list.append('}')
            self.device_list.append('')

    def gen_adapter_board(self):
        self.device_list.append('AdapterBoard %s {'% (self.board_name))
        for aPin in self.device.adapter_board['KeyOrder']:
            pin_params = self.device.adapter_board[aPin]
            pin_name, ppid, xcoord, shape, pintype = \
                aPin, pin_params['Ppid'],pin_params['XCoord'], pin_params['Shape'], pin_params['PinType']
            PinStatement='    Pin { Name= %s; Ppid= "%s"; XCoord= %s; Shape=%s; PinType=%s;\n'% (pin_name,ppid,xcoord,shape,pintype)
            PinStatement +='        Connection[0] { '
            site = 1
            for resource in pin_params['TesterCh']:
                PinStatement += 'TesterCh[%d] = %s;'% (site, resource)
            PinStatement += '}\n    }\n'
            self.device_list += PinStatement.splitlines()
        if self.device.num_sites > 1: 
            self.device_list.append('    MaxSite = %d;' % (self.device.num_sites)) 
        self.device_list.append('}')
        self.device_list.append('')

class GenPattern:
    def __init__(self,PatName, PatType, Vector_List,print_disclaimer=False):
        self.pat_name, self.pat_type, self.v_list = PatName, PatType, Vector_List
        self.pattern_list,self.disclaimer = [], disclaimer if print_disclaimer else ''
        self.pattern_wrapper()
        self.fill_out_pattern()
    def __del_add_cr_on_end__(self):
        aRange = range(len(self.pattern_list))
        self.pattern_list = [ self.pattern_list[i]+'\n' for i in aRange]
    def pattern_wrapper(self):
        a_string = '%s\n%s\nPattern %s {\nType %s;\n}'% (ev_header,self.disclaimer,self.pat_name,self.pat_type)
        self.pattern_list = a_string.splitlines()
        self.insert_here = len(self.pattern_list)-1
        self.pattern_list = list(util.add_cr_iter(self.pattern_list))
    def fill_out_pattern(self):
        vRange = range(len(self.v_list))
        for vector in vRange:
            self.pattern_list.insert(self.insert_here+vector, self.v_list[vector])
class GenPatternSequence:
    def __init__(self,PatSeq_Name):
        self.patseq_name = PatSeq_Name
        self.pattern_sequence=[]
        self.pattern_sequence_wrapper()
        
    def pattern_sequence_wrapper(self):
        self.pattern_sequence.append('PatternSequence %s {'% self.patseq_name)
        self.insert_thread_here, self.thread_index = 1, 0
        self.pattern_sequence.append('    Zipper = Zipper {')
        self.insert_zipper_row_here = 2
        self.pattern_sequence.append('    }')
        self.pattern_sequence.append('}')

    def add_thread(self,Thread_List):
        aList = []
        if type(Thread_List) == type('a_string'):
            aList.append(Thread_List)
        else: aList = Thread_List
        aRange = range(len(aList))
        for i in aRange:
            self.pattern_sequence.insert(self.insert_thread_here, \
                    'Thread[%d] = %s;'% self.thread_index, aList[i])
            self.insert_thread_here, self.thread_index = self.insert_thread_here+1, self.thread_index+1
        self.insert_zipper_row += self.insert_thread_here

    def add_zipper_row(self,Zipper_List):
        '''Zipper_List=[(PatGrp, WaveformTable Reference, WaveformTable_List)...]'''
        aList=[]
        if type(Zipper_List) == type(()):
            aList.append(Zipper_List)
        else: aList = Zipper_List
        aRange = range(len(aList))
        for i in aRange:
            self.pattern_sequence.insert(self.insert_zipper_row_here, \
                    '        Row { %s, %s = { %s }}'% aList[i])
            self.insert_zipper_row_here += 1

class GenSigHeader:
    '''Generate one or more signal headers, use generate_signal_header to populate signal_header_list
with the following arguements: pin_list, SH_Name, isScanSH, scan_pin_req
where: 
    pin_list: list of pins in signal header, ignored for scan signal header type, see scan_pin_req
    SH_Name: string parameter, signal header name
    isScanSH: defaults to False, boolean parameter that specifies if signal header type is scan
    scan_pin_req=[(pin_name, chain_length, default_alias, fill_option),...]
    DoFractionalBus: defaults to False, only set to True if application will utilize Fractional Bus'''
    def __init__(self):
        self.signal_header_list=[]
    def generate_signal_header(self,pin_list,SH_Name,isScanSH=False,scan_pin_req=None,DoFractionalBus=False):
        self.pins, self.signal_header_name = pin_list, SH_Name
        self.is_scan_SH, self.scan_pin_req = isScanSH, scan_pin_req
        self.signal_header_list.append('SignalHeader %s {' % self.signal_header_name)
        if DoFractionalBus:
            self.signal_header_list.append('    evSegmentName = "%s_Seg";' % self.signal_header_name)
        self.signal_header_list.append('    Signals {')
        if not self.is_scan_SH:
            self.fill_out_signal_header()
        else:
            self.fill_out_scan_signal_header(self.scan_pin_req)
        self.signal_header_list.append('    }')
        self.signal_header_list.append('}')
        self.signal_header_list.append('')

    def fill_out_signal_header(self):
        if len(self.pins) >=12:
            aRange = range(len(self.pins)/12) #put 12 pins across, max.
            for i in aRange:
                self.signal_header_list.append('        %s'% ' '.join(self.pins[i*12:(i+1)*12]))
        else:
            i=-1
        if (len(self.pins) % 12) != 0:
            self.signal_header_list.append('        %s'% ' '.join(self.pins[(i+1)*12:]))

    def fill_out_scan_signal_header(self,scan_pin_req):
        '''scan_pin_req=[(pin_name, chain_length, default_alias, fill_option),...]'''
        aRange = range(len(scan_pin_req))
        for index in aRange:
            self.signal_header_list.append('        %s { Scan, ScanLength = %d, Fill = %s, %s; }'% scan_pin_req[index])

class GenPatGroup:
    '''Generate Pattern Group objects '''
    def __init__(self):
        self.pattern_group_list=[]
    def generate_pattern_group(self,pattern_group_name,sigheader_list):
        if isinstance(sigheader_list,str): sigheader_list = [sigheader_list]
        self.pattern_group_list.append('PatternGroup %s {' % pattern_group_name)
        self.pattern_group_list.append('    SignalHeader %s'% ' '.join(sigheader_list)+';')
        self.pattern_group_list.append('}')
        self.pattern_group_list.append('')

class GenPatternMap:
    def __init__(self, PatternMapName,DefaultSourcePath=None,DefaultBinaryPath=None,DefaultPatternGroup=None):
        self.PM_name = PatternMapName
        self.D_src_path = DefaultSourcePath
        self.D_bin_path = DefaultBinaryPath
        self.D_pat_group = DefaultPatternGroup
        self.pattern_map_wrapper()

    def gen_pattern_entry(self,pattern_name, filename_list, pathname_list=None, 
            cachepath_list=None, groupname=None, evRemove=False):
        if type(filename_list) == type('a_str'):
            filename_list = [filename_list]
        a_list = ['    Pattern %s {'% (pattern_name)]
        a_list.append('        File "%s";'% ('", "'.join(filename_list)) )
        if pathname_list != None:
            a_list.append('        Path "%s";' % ('", "'.join(pathname_list)) )
        if cachepath_list != None:
            a_list.append('        CachePath "%s";' % ('", "'.join(cachepath_list)) )
        if groupname != None:
            a_list.append('        Group "%s";'% (groupname) )
        if evRemove:
            a_list.append('        evRemove "TRUE";')
        a_list.append('    }')
        self.PM_list = self.PM_list[:-1] + a_list + [self.PM_list[-1]]

    def pattern_map_wrapper(self):
        self.PM_list = []
        self.PM_list.append('PatternMap %s {'% (self.PM_name))
        if self.D_src_path != None:
            self.PM_list.append('    DefaultSourcePath = "%s";'% (self.D_src_path))
        if self.D_bin_path != None:
            self.PM_list.append('    DefaultBinaryPath = "%s";'% (self.D_bin_path))
        if self.D_pat_group != None:
            self.PM_list.append('    DefaultPatternGroup = "%s";'% (self.D_pat_group))
        self.PM_list.append('}')

class GenLevels:
    def __init__(self):
        self.levels_list = []

    def generate_levels_object(self,levelsObjDict, levelsName):
        '''levelsObjDict[levelsName] = { 'Comment':<comment_string>, 'KeyOrder':[column sequence], 
0: {'KeyOrder': [param sequence], param0: <param0_value>, param1: <param1_value>..,paramN:<paramN_value>}[,..1:...N:...] }'''
        self.levelsObjDict = levelsObjDict
        self.levels_list.append('Levels %s {'% (levelsName) )
        if self.levelsObjDict[levelsName].has_key('Comment'):
            self.levels_list.append('    Comment= "%s";'% (self.levelsObjDict[levelsName]['Comment']) )
        for aColumn in self.levelsObjDict[levelsName]['KeyOrder']:
            self.levels_list.append('    Column[%d] {'% (aColumn) )
            for aParam in self.levelsObjDict[levelsName][aColumn]['KeyOrder']:
                if aParam == 'Title' or aParam == 'LevelsColumnType':
                    self.levels_list.append('        %s = %s;'% (aParam, self.levelsObjDict[levelsName][aColumn][aParam]) ) 
                elif aParam == 'Params':
                    for lvlParam in self.levelsObjDict[levelsName][aColumn][aParam]['KeyOrder']:
                        self.levels_list.append('        %s = Expr {String="%s";}' \
                            % (lvlParam, self.levelsObjDict[levelsName][aColumn][aParam][lvlParam]) ) 
                else:
                    try:
                        self.levels_list.append('        %s = Expr {String="%s";}' \
                            % (aParam, self.levelsObjDict[levelsName][aColumn][aParam]) ) 
                    except KeyError:
                        print 'aColumn : ',aColumn
                        print 'aParam  : ',aParam
                        print 'LevelName : ', levelsName
                        raise

            self.levels_list.append('    }')
        self.levels_list.append('}')
        self.levels_list.append('')

class GenPinGroup:
    '''Use generate_pingroup to create pingroups.  Pass in pingroup_name and associated list of pins.'''
    def __init__(self):
        self.pingroup_list = []

    def generate_pingroup(self,pingroup_name, pinlist):
        self.pingroup_list.append('PinGroup %s {'% (pingroup_name))
        a_string, spacer = '    Group= Expr { String="', ''
        if len(pinlist) >=12:
            aRange = range(len(pinlist)/12) #put 12 pins across, max.
            for i in aRange:
                a_string += '%s%s\n'% (spacer,'+'.join(pinlist[i*12:(i+1)*12]))
                spacer = '    +'
        else:
            i=-1
        if (len(pinlist) % 12) != 0:
            a_string += '%s%s\n'% (spacer,'+'.join(pinlist[(i+1)*12:]))
        a_string = a_string[:-1] + '"; }'
        self.pingroup_list += a_string.splitlines()
        self.pingroup_list.append('}')
        self.pingroup_list.append('')

