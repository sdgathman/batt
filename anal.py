#!/usr/bin/python3

import csv
import fileinput

fp = fileinput.input()
r = csv.reader(fp)
mamin = 0.0 # milliampere minutes
beg = 0.0 # begin time
end = 0.0 # end time
minpct = 100
maxpct = 0
n = 0
for pct,status,curr,v,t in r:
    pct = float(pct)
    curr = float(curr)
    v = float(v)
    t = float(t)
    print(pct,status,curr,v,t)
    mamin += curr
    n += 1
    if beg == 0.0: beg = t
    end = t
    if pct < minpct: minpct = pct
    if pct > maxpct: maxpct = pct
hrs = (end-beg+60)/3600
used = maxpct - minpct + 1
mahr = mamin / n * hrs
print(hrs,'hrs',used,'%',mahr,'maHr')
print(mahr/used*100)
