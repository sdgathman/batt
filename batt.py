#!/usr/bin/python3

import time
import csv
import os.path

class battery(object):
    def __init__(self):
        self.capacity = -1
        self.current_now = -1
        self.voltage_now = -1
        self.status = None
        self.charge_full = 10000.0
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

    # update current data
    def update(self):
        self.now = time.time()
        self.capacity = self.getint('capacity')
        self.status = self.get('status')
        self.current_now = self.getint('current_now',1000.0)
        self.voltage_now = self.getint('voltage_now',1000000.0)
        self.charge_now = (self.capacity * self.charge_full + 50) / 100
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


b = battery()
while True:
    b.update()
    b.log()
    time.sleep(60)
#print(b.data(),b.remaining)
