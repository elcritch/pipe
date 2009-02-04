#!/usr/bin/env python

# sys and os contain system classes such as stdin
import sys, os, re

inst = []

class Instruction:
    """implements a simple instruction"""
    def __init__(self, line):
        self.line = line.strip()
        
        # split command and registers
        line = line.split()
        self.cmd = line[0]
        regs = ''.join(line[1:]).split(',')
        self.regs = regs
        
        # just strip the addressing mode, we don't care about actual value?
        match = re.search("\d+\((.+)\)",regs[-1])
        if match:
            regs[-1] = match.groups()[0]
        
        match = re.search("(\w+):([TF])",regs[-1])
        if match:
            self.regs[-1] = match.groups()[0]
            self.branch = True if match.groups()[1] == 'T' else False
        
        # Set inst registers:
        # DR = destination
        # S1 = source register 1
        # S2 = source register 2
        print "regs", regs
        if len(regs) == 2:
            self.DR, self.S1 = regs
        elif len(regs) == 3:
            self.DR, self.S1, self.S2 = regs
        
    def __str__(self):
        attrs = [ nm for nm in dir(self) if not nm.startswith("_")]
        s = "INST:\n" 
        s += ''.join([ '\t%s:\t%s\n'%(a,getattr(self,a)) for a in attrs])
        return str(s)




def main():
    for line in sys.stdin.readlines():
        ist = Instruction(line)
        print "inst", ist
        inst.append(ist)





if __name__ == '__main__':
    try:
        main()
    except (ValueError), exc:
        print "Incorrect input format."
        print exc
