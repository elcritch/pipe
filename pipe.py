#!/usr/bin/env python

# sys and os contain system classes such as stdin
import sys, os, re
##files trace.dat 
inst = []
Mem = []
PC = 0

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
   
        match_reg = re.match("^([A-Za-z]\d{1,2})$",regs[-1])
        match_const_reg = re.match("(-{0,1}[\w\d]+)\((\w+)\)",regs[-1])
        match_const = re.match("((?:L\d+)|(?:\d+))$",regs[-1])
        match_branch = re.match("(\w+):([TF])",regs[-1])

        if len(regs) == 1:
            if match_reg:      self.rs = regs[0]
            elif match_const:  self.imm = regs[0]
            else: raise ValueError()
        elif len(regs) == 2:
            if match_reg:         self.rt = regs[1]
            elif match_const_reg: self.rt, self.imm = match_const_reg.groups()
            else: raise ValueError()
            
        elif len(regs) == 3:
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
            s+= "'%s':%s"%(n,self.attr[n].__repr__())
        return s
    def __str__(self):
        return self.__repr__()
    


IF_ID = Latch()
ID_EX = Latch()
EX_MEM = Latch()
MEM_WB = Latch()
PipeLine = [ IF_ID, ID_EX, EX_MEM, MEM_WB ]
PipeLineNames = ['IF_ID','ID_EX','EX_MEM','MEM_WB']

def main():
    global PipeLine, PipeLineNames
    for line in sys.stdin.readlines():
        ist = Instruction(line)
        # print "inst", ist
        Mem.append(ist)
    
    print "mem", Mem
    print "PC", PC
    print
    print "Pipe PipeLine"
    # iteratePipeLine()
    stage_IF()
    stage_ID()
    stage_EX()
    stage_MEM()
    stage_WB()

    for i,stage in enumerate(PipeLine):
        print PipeLineNames[i].ljust(6),stage
    
def stage_IF():
    global Mem, PC # we must tell python they're global vars
    IF_ID.IR = Mem[PC]
    if hasattr(EX_MEM.opcode,'branch') and EX_MEM.cond:
        IF_ID.NPC = PC = EX_MEM.ALUOutput
        # TODO: book uses bitwise '&'?
    else:
        # we are referencing list index as memory addressess
        IF_ID.NPC = PC = PC+1 

def stage_ID():
    pass
    
def stage_EX():
    pass
    
def stage_MEM():
    pass
    
def stage_WB():
    pass
    
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




