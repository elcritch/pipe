#!/usr/bin/env python
# encoding: utf-8
# sys and os contain system classes such as stdin
##files trace.dat
import sys, os, re

class Stage:
    """
    This class stores the data in between Stage functions. Attributes
    in this class act as the temporary variables in the 'latches'. To simplify
    programming, this class returns 'None' whenever an attribute hasn't been
    stored. 
    """
    def __init__(self):
        self.__dict__['attr'] = {}
        
    def __getattr__(self, item):
        """this is called if the attribute isn't found in the object"""
        if self.attr.has_key(item):
            return self.attr[item] # we store all new additions in attr dict
        elif self.attr.has_key('IR') and hasattr(self.attr['IR'],item):
            return getattr(self.attr['IR'],item)
        else:
            return None
            
    def __setattr__(self, item, value):
        """overrides accessing object attributes"""
        if self.__dict__.has_key(item): # normal attributes are handled normally
            self.__dict__[item] = value
        else:
            self.attr[item] = value

    def __repr__(self):
        s = "Stage: "
        for n in self.attr:
            s+= "%s:%s "%(n,self.attr[n].__repr__())
        return s
    def __str__(self):
        return self.__repr__()
    # def opcode(self):
        # if self.IR: return self.attr['IR'].opcode
        # else: return None
    def __nonzero__(self):
        return True if self.attr.has_key('IR') else False

class Instruction:
    """implements a simple instruction"""
    num = 0
    def __init__(self, line):
        self.line = line.strip()
        
        # split command and registers
        line = line.split()
        self.opcode = line[0]
        regs = ''.join(line[1:]).split(',')
        self.regs = regs
        self.id = Instruction.num = Instruction.num + 1
        self.rs = self.rt = self.rd = self.imm = None
        self.parse_options(regs)
        self.settype(self.opcode)
    
    def settype(self,opcode):
        """
        • loads and stores (LW, SW, L.S, and S.S) 
        • single cycle arithmetic operations (DADD, DSUB, AND, OR, XOR) 
        • branches (BEQ, BNE) 
        • ﬂoating-point arithmetic operations (ADD.S, SUB.S, MUL.S, DIV.S) 
        • data movement (MOV.S, MFC1, MTC1) 
        • data conversion (CVT.S.W, CVT.W.S) 
        """
        self.float = True if opcode.find('.') >= 0 else False
        self.delay = 1
        
        if opcode in ('LW', 'SW', 'L.S', 'S.S'):
            if opcode.startswith('L'):
                self.type = 'load'
                self.delay = 2
            if opcode.startswith('S'):
                self.type = 'store'
        elif opcode in ('DADD', 'DSUB', 'AND', 'OR', 'XOR'):
            self.type = 'arithmetic'
        elif opcode in ('BEQ', 'BNE'):
            self.type = 'branch'
        elif opcode in ('ADD.S', 'SUB.S', 'MUL.S', 'DIV.S'):
            self.type = 'fp'
        elif opcode in ('MOV.S', 'MFC1', 'MTC1'):
            self.type = 'move'
        elif opcode in ('CVT.S.W', 'CVT.W.S'):
            self.type = 'conversion'
               
    
    def parse_options(self, regs):
        match_reg = re.match("^([A-Za-z]\d{1,2})$",regs[-1])
        match_const_reg = re.match("(-{0,1}[\w\d]+)\((\w+)\)",regs[-1])
        match_const = re.match("((?:L\d+)|(?:\d+))$",regs[-1])
        match_branch = re.match("(\w+):([TF])",regs[-1])
        # Assembly Comment 
        # add # op = 0, shamt= 0, funct= 32 
        # $t0 # rd = 8 
        # $s1 # rs= 17 
        # $s2 # rt= 18 
        if len(regs) == 1:
            if match_reg:      self.rd = regs[0]
            elif match_const:  self.imm = regs[0]
            else: raise ValueError()
        elif len(regs) == 2:
            self.rt = regs[0]
            if match_reg:         self.rs = regs[1]
            elif match_const_reg: self.imm, self.rs = match_const_reg.groups()
            else: raise ValueError()
            
        elif len(regs) == 3:
            self.rd = regs[0]
            self.rs = regs[1]
            if match_reg:      self.rt = regs[2]
            elif match_const:  self.imm = regs[2]
            elif match_branch: self.rt, self.branch = match_branch.groups()
            else: raise ValueError()
        
    def __repr__(self):
        return "<CMD:%s ID:%s RS:%s RT:%s RD:%s IMM:%s> "%\
            (self.opcode, self.id, self.rs, self.rt, self.rd, self.imm)
    def __str__(self):
        attrs = [ nm for nm in dir(self) if not nm.startswith("_")]
        s = "INST:\n"
        s += ''.join([ '\t%s:\t%s\n'%(a,getattr(self,a)) for a in attrs])
        return str(s)

# Globals
inst = []
Mem = []
PC = 0
CYCLE = 0
CONFIG = {}
STALLS = []

## Setup Pipe/Stage names as index numbers
PipeLineNames = ['IF','ID','EX','MEM','WB']
for i,nm in enumerate(PipeLineNames): globals()[nm] = i

## Instantiate Pipe
Pipe = [ Stage() for nm in PipeLineNames ]
StageNames = [ 'stage_IF','stage_ID','stage_EX','stage_MEM','stage_WB',]

## Printout header
header = """
cycle    IF    ID    EX   MEM    WB  FADD  FMUL  FDIV   FWB
----- ----- ----- ----- ----- ----- ----- ----- ----- -----
"""

def config():
    global Pipe, PipeLineNames, CONFIG
    fl = open('config.txt','r')
    for dat in fl.readlines():
        op, cy = [ s.strip() for s in dat.split(':') ]
        CONFIG[op] = int(cy)
    fl.close()
    
    for line in sys.stdin.readlines():
        ist = Instruction(line)
        Mem.append(ist)

OUTPUT = ""
def print_cycle():
    global OUTPUT
    # DEBUG print out
    # print " ========================== Cycle =========================="
    # for i,stage in enumerate(Pipe):
        # print PipeLineNames[i].ljust(7), stage
    
    # Print out line of cycles
    OUTPUT += str(CYCLE).rjust(5)
    for stage in Pipe:
        OUTPUT += ' '+str(stage.IR.id).rjust(5) if stage.IR else ' '*6
    
    OUTPUT += '\n'
    # print OUTPUT
    
def main():
    global Pipe, PipeLineNames, CYCLE
    config()
        
    s = Stage()
    if s: print "STAGE"
    else: print "NULL STAGE"
    
    loop = True
    while loop:
        # This shifts the array down, creates empty stage for IF, stalls
        # call function for each stage
        iteratePipeLine()
        controller()
        for stage in StageNames:
            globals()[stage]()
            
        # keep looping while we have commands in the stages
        loop = True in [ True for stage in Pipe if stage.IR ]
        CYCLE += 1        
        
        if loop: print_cycle()
    
    # print "mem", Mem
    print "Pipe"
    print header,
    print OUTPUT

def set_stall(cycles,stage):
    # add a new stall state to the global STALLS list
    # iteratePipeLine takes care of implementing stalls
    STALLS.append({'cycles':cycles,'stage':stage})
     
def stage_IF():
    global Mem, PC
    if not Pipe[IF].IR == 'stall':
        Pipe[IF].IR = Mem[PC] if PC < len(Mem) else None
        PC = PC + 1
    
def stage_ID():
    pass
    
def stage_EX():
    opcode = Pipe[EX].opcode
    irtype = Pipe[EX].type
    if irtype == 'load':
        if (Pipe[EX].rt == Pipe[ID].rs) or \
           (Pipe[EX].rt == Pipe[ID].rt) or \
           (Pipe[EX].rt == Pipe[ID].rs):
            set_stall(cycles=1,stage=EX)
            
    elif irtype == 'store':
        pass
    elif irtype == 'branch':
        pass
        # TODO: branch logic control? Shouldn't this be in ID?
        # EX_MEM.cond = ID_EX.A == None
    elif Pipe[ID].IR:
        pass
    else: pass
    
def stage_MEM():
    pass
    
def stage_WB():
    pass
    
def controller():
    """
    This function just passes along the Latch objects, setting up 
    the new global latch names from the pipes. A bit of a hack, but it makes
    copying the book easier.
    """
    global PC
    
    if STALLS:
        stall = STALLS[-1]
        
        class Stall(Stage): pass
        
        if not stall.has_key('stalled'):
            Pipe[0:stall['stage']] = Pipe[1:stall['stage']+1]
            blank = Stage()
            blank.IR = Stall()
            blank.IR.stall = True
            blank.IR.id = ''
            Pipe[stall['stage']] = blank
            
            print "stall", stall
            PC -= stall['cycles']
            # add these to the stall list, so we can reset them? 
            stall['stalled'] = [ Pipe[i] for i in xrange(stall['stage'])  ]            
            for i in xrange(stall['stage']):
                print "i", i
                Pipe[i].IR._id = Pipe[i].IR.id
                Pipe[i].IR.id = 'stall'
            
        
        if stall['cycles'] == 0:
            print "popping cycles"
            print stall['stalled']
            # restore the names
            for st in stall['stalled']:
                print "st.IR.id", st.IR.id
                print "st.IR._id", st.IR._id
                st.IR.id = st.IR._id 
            STALLS.pop(-1)
        else:
            stall['cycles'] -= 1
        
def iteratePipeLine():
    # Make new pipeline stage
    Pipe.insert(0,Stage())    
    Pipe.pop(-1)



if __name__ == '__main__':
    """ Runs the program. If we don't parse the input we throw an error."""
    try:
        main()
    except (ValueError), exc:
        print "Incorrect input format."
        print exc




