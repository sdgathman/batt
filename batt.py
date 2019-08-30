#!/usr/bin/python3

import time
import csv
import os.path

class battery(object):
    def __init__(self):
        self.capacity = -1
        self.current_now = -1
        self.voltage_min_design = -1
        self.voltage_max_design = -1
        self.voltage_now = -1
        self.status = None
        self.charge_full = -1
        self.charge_full_design = -1
        self.charge_now = -1
        self.remaining = 0.0
        self.now = 0.0
        self.batdir = '/sys/class/power_supply/axp20x-battery/'
        if not os.path.isdir(self.batdir):
          self.batdir = '/sys/class/power_supply/BAT0/'

    def get(self,item):
        try:
            with open(self.batdir+item) as fp:
                return fp.read().strip()
        except:
            return None

    def getint(self,item,scale=1):
        try:
            return int(self.get(item)) / scale
        except:
            return -1

    def estimate_charge_full(self):
        if self.charge_full_design < 0:
          self.charge_full_design = self.getint('charge_full_design',1000.0)
        if self.charge_full_design < 0:
          self.charge_full_design = 10000.0
        r = 1.0
        if self.capacity == 100 or self.status == 'Full':
          self.voltage_min_design = self.getint('voltage_min_design',1000000.0)
          self.voltage_max_design = self.getint('voltage_max_design',1000000.0)
          if (self.voltage_min_design > 0 and
              self.voltage_now > self.voltage_min_design and
              self.voltage_now <= self.voltage_max_design):
            rd = self.voltage_max_design - self.voltage_min_design
            rn = self.voltage_now - self.voltage_min_design
            r = rn / rd
        self.charge_full = self.charge_full_design * r

    # update current data
    def update(self):
        self.now = time.time()
        self.capacity = self.getint('capacity')
        self.status = self.get('status')
        self.voltage_now = self.getint('voltage_now',1000000.0)
        self.charge_full = self.getint('charge_full',1000.0)
        if self.charge_full < 0:
          self.estimate_charge_full()
        self.current_now = self.getint('current_now',1000.0)
        self.charge_now = self.getint('charge_now',1000.0)
        if (self.charge_now < 0):
          self.charge_now = self.capacity * self.charge_full / 100
        if self.status == 'Charging':
          self.remaining = (self.charge_full - self.charge_now) / self.current_now
        else:
          self.remaining = self.charge_now / self.current_now

    def data(self):
        return self.capacity,self.status,self.current_now,self.voltage_now,self.now

    # write log record from current data
    def log(self):
        with open('/home/stuart/.batt','a',newline='') as fp:
            w = csv.writer(fp)
            w.writerow(self.data())

    def report(self):
        print("Capacity:",self.capacity,"Remaining: %5.2f"%self.remaining,"hrs")
        print("Current:",self.current_now,self.status)
        print("Charge full: %5.2f"%self.charge_full)

b = battery()
b.update()
b.report()
while True:
    b.log()
    time.sleep(60)
    b.update()
#print(b.data(),b.remaining)
