#!/usr/bin/env python

# sys and os contain system classes such as stdin
import sys, os, re
##files trace.dat 
inst = []
Mem = []
PC = 0

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
   
        match_reg = re.match("^(\w{1}\d{1,2})$",regs[-1])
        match_const_reg = re.match("(-{0,1}[\w\d]+)\((\w+)\)",regs[-1])
        match_const = re.match("((?:L\d+)|(?:\d+))",regs[-1])
        match_branch = re.match("(\w+):([TF])",regs[-1])

        print "matched", [ nm for nm in ['match_reg','match_const','match_const_reg','match_branch'] if locals()[nm] ], regs
        if len(regs) == 1:
            if match_reg:      self.rs = regs[0]
            elif match_const:  self.imm = regs[0]
        elif len(regs) == 2:
            if match_reg:         self.rt = regs[1]
            elif match_const_reg: self.rt, self.imm = match_const_reg.groups()
            
        elif len(regs) == 3:
            if match_reg:      self.rd = regs[2]
            elif match_const:  self.imm = regs[2]
            elif match_branch: self.rd, self.branch = match_branch.groups()
        
    def __repr__(self):
        return "<CMD: %s ID: %d> "%(self.opcode, self.id)
    def __str__(self):
        attrs = [ nm for nm in dir(self) if not nm.startswith("_")]
        s = "INST:\n" 
        s += ''.join([ '\t%s:\t%s\n'%(a,getattr(self,a)) for a in attrs])
        return str(s)


class Latch:
    def __init__(self):
        """docstring for __init__"""
        self.attr = {}
        
    def __getattr__(self, item):
        """Maps values to attributes.
        Only called if there *isn't* an attribute with this name
        """
        try:
            return self.attr[item]
        except KeyError:
            return None
    
    # def __setattr__(self, item, value):
    #     """Maps attributes to values.
    #     Only if we are initialised
    #     """
    #     # this test allows attributes to be set in the __init__ method
    #     if not self.__dict__.has_key('_attrExample__initialised'):  
    #         return dict.__setattr__(self, item, value)
    #     elif self.__dict__.has_key(item):       # any normal attributes are handled normally
    #         dict.__setattr__(self, item, value)
    #     else:
    #         self.__setitem__(item, value)


IF_ID = Latch()
ID_EX = Latch()
EX_MEM = Latch()
MEM_WB = Latch()
Pipes = [ IF_ID, ID_EX, EX_MEM, MEM_WB ]


def main():
    for line in sys.stdin.readlines():
        ist = Instruction(line)
        # print "inst", ist
        Mem.append(ist)
    # Mem = inst
    print "mem", Mem
    print "PC", PC
    # stage_if()
    
def stage_if():
    mem = Mem[PC] 
    IF_ID.IR = mem
    if EX_MEM.opcode.branch and EX_MEM.cond:
        IF_ID.NPC = Mem['PC'] = EX_MEM.ALUOutput
    else:
        Mem['PC']=Mem['PC']+1
    
    print "IF_ID.IR", IF_ID.IR
    
    


if __name__ == '__main__':
    try:
        main()
    except (ValueError), exc:
        print "Incorrect input format."
        print exc




