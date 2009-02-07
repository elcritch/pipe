#!/usr/bin/env python
# encoding: utf-8
# sys and os contain system classes such as stdin
##files trace.dat
import sys, os, re

# Globals
inst = []
Mem = []
PC = 0
cycles = {}

class Instruction:
    """implements a simple instruction"""
    num = -1
    def __init__(self, line):
        self.line = line.strip()
        
        # split command and registers
        line = line.split()
        self.opcode = line[0]
        regs = ''.join(line[1:]).split(',')
        self.regs = regs
        self.id = Instruction.num = Instruction.num + 1
        self.rs = self.rt = self.rd = None
        self.parse_options(regs)
    
    def set_type(self,opcode):
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
        # R opcode (6)  rs (5)  rt (5)  rd (5)  shamt (5)   funct (6)
        # I opcode (6)  rs (5)  rt (5)  immediate (16)
        # J opcode (6)  address (26)
        if len(regs) == 1:
            if match_reg:      self.rs = regs[0]
            elif match_const:  self.imm = regs[0]
            else: raise ValueError()
        elif len(regs) == 2:
            self.rs = regs[0]
            if match_reg:         self.rt = regs[1]
            elif match_const_reg: self.rt, self.imm = match_const_reg.groups()
            else: raise ValueError()
            
        elif len(regs) == 3:
            self.rs = regs[0]
            self.rt = regs[1]
            if match_reg:      self.rd = regs[2]
            elif match_const:  self.imm = regs[2]
            elif match_branch: self.rd, self.branch = match_branch.groups()
            else: raise ValueError()
        
    def __repr__(self):
        return "<CMD: %s ID: %d> "%(self.opcode, self.id)
    def __str__(self):
        attrs = [ nm for nm in dir(self) if not nm.startswith("_")]
        s = "INST:\n"
        s += ''.join([ '\t%s:\t%s\n'%(a,getattr(self,a)) for a in attrs])
        return str(s)


class Latch:
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
        else:
            return None
            
    def __setattr__(self, item, value):
        """overrides accessing object attributes"""
        if self.__dict__.has_key(item): # normal attributes are handled normally
            dict.__dict__[item] = value
        else:
            self.attr[item] = value

    def __repr__(self):
        s = "Stage: "
        for n in self.attr:
            s+= "%s:%s "%(n,self.attr[n].__repr__())
        return s
    def __str__(self):
        return self.__repr__()
    def opcode(self):
        if self.IR: return self.attr['IR'].opcode
        else: return None


IF_ID = Latch()
ID_EX = Latch()
EX_MEM = Latch()
MEM_WB = Latch()
PipeLine = [ IF_ID, ID_EX, EX_MEM, MEM_WB ]
PipeLineNames = ['IF_ID','ID_EX','EX_MEM','MEM_WB']
StageNames = [ 'stage_WB','stage_MEM','stage_EX','stage_ID','stage_IF',]

header = """
cycle    IF    ID    EX   MEM    WB  FADD  FMUL  FDIV   FWB
----- ----- ----- ----- ----- ----- ----- ----- ----- -----
"""

def config():
    global PipeLine, PipeLineNames, cycles
    fl = open('config.txt','r')
    for dat in fl.readlines():
        op, cy = [ s.strip() for s in dat.split(':') ]
        cycles[op] = int(cy)
    fl.close()
    
    for line in sys.stdin.readlines():
        ist = Instruction(line)
        # print "inst", ist
        Mem.append(ist)
    
def reset(name):
    latch = Latch()
    globals()[name] = latch
    PipeLine[PipeLineNames.index(name)] = latch

def main():
    global PipeLine, PipeLineNames
    config()
    print "mem", Mem
    print "PC", PC
    print
    print "PipeLine"
    
    # iteratePipeLine() # we just copy the values?
    for i,inst in enumerate(Mem):
        for stage in StageNames: globals()[stage]()
        
        print " ========================== Cycle =========================="
        for i,stage in enumerate(PipeLine):
            print PipeLineNames[i].ljust(7), stage
        
        output = str(PC).rjust(5)
        for name in PipeLineNames:
            stage = globals()[name]
            output += ' '+str(stage.IR.id).rjust(5) if stage.IR else ' '*5
        print header,
        print output
    


def stage_IF():
    global Mem, PC, IF_ID # we must tell python they're global vars
    reset('IF_ID')
    IF_ID.IR = Mem[PC]
    PC = PC+1
    if hasattr(EX_MEM.opcode,'branch') and EX_MEM.cond:
        IF_ID.NPC = EX_MEM.ALUOutput
        # TODO: book uses bitwise '&'?
    else:
        # we are referencing list index as memory addressess
        IF_ID.NPC = PC+1 

def stage_ID():
    reset('ID_EX')
    if ID_EX.IR:
        ID_EX.A = IF_ID.IR.rs
        ID_EX.B = IF_ID.IR.rt
        ID_EX.Imm = IF_ID.IR.imm
    ID_EX.NPC = IF_ID.NPC
    ID_EX.IR = IF_ID.IR
    
def stage_EX():
    reset('EX_MEM')
    if ID_EX.opcode() in ('load', 'store'):
        EX_MEM.IR = ID_EX.IR
        EX_MEM.ALUOutput = ""
        EX_MEM.B = ID_EX.B
    elif ID_EX.opcode() == 'branch':
        EX_MEM.ALUOutput =  ID_EX.NPC + int(ID_EX.Imm) << 2
        EX_MEM.cond = ID_EX.A == None
    elif hasattr(ID_EX,'IR'):
        EX_MEM.IR = ID_EX.IR
        EX_MEM.ALUOutput = ""
    else: raise "ERROR"
        
    
def stage_MEM():
    reset('MEM_WB')
    if EX_MEM.opcode() in ('load', 'store'):
        MEM_WB.IR = EX_MEM.IR
    elif hasattr(EX_MEM,'IR'):
        MEM_WB.IR = EX_MEM.IR
        MEM_WB.ALUOutput = EX_MEM.ALUOutput
    else:
        pass
    
def stage_WB():
    
    if MEM_WB.opcode() in ('load', 'store'):
        pass
    elif hasattr(ID_EX,'IR'):
        pass
    else: 
        raise "ERROR"
    
def iteratePipeLine():
    """
    This function just passes along the Latch objects, setting up 
    the new global latch names from the pipes. A bit of a hack, but it makes
    copying the book easier.
    """
    global PipeLine
    # get 4 first elements and add new Latch to beginning
    PipeLine = [Latch()]+PipeLine[:-1]
    # iterate over pipe names, setting the new value for it from the pipe array
    for i, sn in enumerate(PipeLineNames):
        globals()[sn] = PipeLine[i]



if __name__ == '__main__':
    """ Runs the program. If we don't parse the input we throw an error."""
    try:
        main()
    except (ValueError), exc:
        print "Incorrect input format."
        print exc




