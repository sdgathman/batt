#!/usr/bin/python3

import time
import csv
import os.path

class battery(object):
    SYSDIR = '/sys/class/power_supply/'
    CONFDIR = os.path.expanduser('~/.config/battery/')
    LOGFILE = os.path.expanduser('~/.batt')

    def __init__(self):
        self.capacity = -1
        self.current_now = -1
        self.voltage_now = -1
        self.power_now = -1
        self.status = None
        self.energy_full = -1
        self.charge_full = -1
        self.energy_now = -1
        self.charge_now = -1
        self.remaining = 0.0
        self.measured = set()
        self.now = 0.0
        self.name = 'BAT0'
        self.batdir = os.path.join(self.SYSDIR,self.name)
        if not os.path.isdir(self.batdir):
          self.name = 'axp20x-battery'
          self.batdir = os.path.join(self.SYSDIR,self.name)
        self.props = self.getProps()
        self.voltage_max = self.getint('voltage_max',1000000.0)
        if self.voltage_max < 0:
          self.voltage_max = self.getPropint('voltage_max')
        if self.voltage_max < 0:
          self.voltage_max = self.getint('voltage_now',1000000.0)
        self.voltage_min_design = self.getint('voltage_min_design',1000000.0)
        self.voltage_max_design = self.getint('voltage_max_design',1000000.0)
        if self.voltage_max_design < 0:
          self.voltage_max_design = self.voltage_max
        self.charge_full_design = self.getint('charge_full_design',1000.0)
        if self.charge_full_design < 0:
          self.charge_full_design = self.getPropint('charge_full_design')
        self.energy_full_design = self.getint('energy_full_design',1000000.0)
        v = self.voltage_max_design
        if self.energy_full_design > 0 and self.charge_full_design < 0:
          self.charge_full_design = self.energy_full_design * 1000 / v 
        if self.charge_full_design < 0:
          self.charge_full_design = 10000.0
        if self.energy_full_design < 0:
          self.energy_full_design = self.charge_full_design * v / 1000
        self.saveProps()

    def getProp(self,item):
        return self.props.get(item)

    def getPropint(self,item,scale=1,default=-1):
        try:
            v = self.getProp(item)
            return float(v) / scale
        except:
            return default

    def getProps(self):
        conf = os.path.join(self.CONFDIR,self.name)
        d = {}
        try:
            with open(conf) as fp:
                for ln in fp:
                    ln = ln.strip()
                    if ln.startswith('#'): continue
                    k,v = ln.split('=',2)
                    d[k.strip()] = v.strip()
        except: pass
        return d

    def saveProps(self):
        changed = False
        if self.getPropint('voltage_max') < self.voltage_max:
          self.props['voltage_max'] = self.voltage_max
          changed = True
        if self.getPropint('charge_full_design') < self.charge_full_design:
          self.props['charge_full_design'] = self.charge_full_design
          changed = True
        if not changed: return
        conf = os.path.join(self.CONFDIR,self.name)
        try:
            with open(conf,'w') as fp:
                for k,v in self.props.items():
                    fp.write(k+'='+str(v)+'\n')
        except Exception as x:
            print(conf,x)

    def get(self,item):
        try:
            with open(os.path.join(self.batdir,item)) as fp:
                self.measured.add(item)
                return fp.read().strip()
        except:
            return None

    def getint(self,item,scale=1,default=-1):
        try:
            return int(self.get(item)) / scale
        except:
            return default

    def estimate_charge_full(self):
        if self.capacity == 100 or self.status == 'Full':
          if (self.voltage_min_design > 0 and
              self.voltage_now > self.voltage_min_design and
              self.voltage_now <= self.voltage_max_design):
            if self.voltage_max != self.voltage_now:
              self.voltage_max = self.voltage_now
              self.saveProps()
        elif self.voltage_now > self.voltage_max:
          self.voltage_max = self.voltage_now
          self.saveProps()
        if self.energy_full > 0:
          self.charge_full = self.energy_full * 1000 / self.voltage_max
        elif (self.voltage_min_design > 0 and
            self.voltage_max > self.voltage_min_design and
            self.voltage_max <= self.voltage_max_design):
          rd = self.voltage_max_design - self.voltage_min_design
          rn = self.voltage_max - self.voltage_min_design
          self.charge_full = self.charge_full_design * rn / rd
        else:
          self.charge_full = self.charge_full_design
        #self.voltage()

    # update current data
    def update(self):
        self.now = time.time()
        self.capacity = self.getint('capacity')
        self.status = self.get('status')
        self.voltage_now = self.getint('voltage_now',1000000.0)
        if self.charge_full_design < 0:
          self.charge_full_design = self.getint('charge_full_design',1000.0)
        self.charge_full = self.getint('charge_full',1000.0)
        self.energy_full = self.getint('energy_full',1000000.0)
        if self.charge_full < 0:
          self.estimate_charge_full()
        if self.energy_full < 0:
          self.energy_full = self.charge_full * self.voltage_max / 1000
        self.current_now = self.getint('current_now',1000.0)
        self.power_now = self.getint('power_now',1000.0)
        if self.current_now < 0 and self.power_now > 0:
          self.current_now = self.power_now / self.voltage_now
        self.charge_now = self.getint('charge_now',1000.0)
        if (self.charge_now < 0):
          self.charge_now = self.capacity * self.charge_full / 100
        if self.status == 'Charging':
          self.remaining = (self.charge_full - self.charge_now) / self.current_now
        else:
          fcur = self.current_now * self.voltage_now / self.voltage_min_design
          avgcur = (fcur + self.current_now) / 2
          self.remaining = self.charge_now / avgcur

    def data(self):
        return self.capacity,self.status,self.current_now,self.voltage_now,self.now

    # write log record from current data
    def log(self):
        with open(self.LOGFILE,'a',newline='') as fp:
            w = csv.writer(fp)
            w.writerow(self.data())

    def iscalculated(self,item):
        if item in self.measured:
          return ' '
        return '*'

    def report(self,verbose=False):
        if verbose:
          self.voltage()
        m = int(self.remaining * 60)
        print("Capacity: %2.0f%%"%self.capacity,"%dh %dm"%(m//60,m%60))
        c = self.iscalculated('current_now')
        print("Current: %3.0fmA%c"%(self.current_now,c),self.status)
        m = int(self.charge_full / self.charge_full_design * 100)
        c = self.iscalculated('charge_full')
        cd = self.iscalculated('charge_full_design')
        print("Charge full: %3.0fmAhr%c %d%%%c"%(self.charge_full,c,m,cd))
        p = self.voltage_now * self.current_now
        c = self.iscalculated('voltage_now')
        print("Voltage: %4.1fV%c"%(self.voltage_now,c),"%4.1fW"%(p/1000))
        c = self.iscalculated('energy_full')
        print("Energy full: %4.1fWhr%c"%(self.energy_full,c))
        c = self.iscalculated('energy_full_design')
        print("Energy full design: %4.1fWhr%c"%(self.energy_full_design,c))

    def voltage(self):
        c = self.iscalculated('voltage_min_design')
        print("Voltage min design: %4.1fV%c"%(self.voltage_min_design,c))
        c = self.iscalculated('voltage_max')
        print("Voltage max: %4.1f%c"%(self.voltage_max,c))
        c = self.iscalculated('voltage_max_design')
        print("Voltage max design: %4.1fV%c"%(self.voltage_max_design,c))

    def short1(self):
        m = int(self.remaining * 60)
        p = int(self.capacity)
        if p == 100 or self.status == 'Full':
          print("%d%% Full"%p)
        else:
          print("%d%% %dh %dm"%(p,m//60,m%60))
    def short2(self):
        print("%dma %3.3s"%(int(self.current_now),self.status))

def main(argv):
    from getopt import getopt
    opts,args = getopt(argv[1:],'c1v2',['capacity','short','verbose'])
    b = battery()
    b.update()
    b.log()
    verbose = False
    for o,v in opts:
      if o in ('-1','--short'):
        b.short1()
        return 0
      if o == '-2':
        b.short2()
        return 0
      if o in ('-v','--verbose'):
        verbose = True
    b.report(verbose)

if __name__ == '__main__':
    import sys
    rc = main(sys.argv)
    sys.exit(rc)
