# batt
### Linux command line battery status display

The various laptops and small devices with an on board battery controller
provide useful information on current, capacity, total energy, etc.

Unfortunately, each device supports a slightly different set of
information. 

Fortunately, it is easy to see what information is available as it is
read from the /sys filesystem.

This script gets all available data, gets additional data from a config
file that is sometimes not available from the driver (like original
manufactured full capacity), and computes other data (like watts from current
and voltage).  Some fields, like voltage_max, are tracked in a log
and updated in the config when not available from the battery hardware
driver.

The result is a mini report with computed fields starred.

This is useful from the command line, or from panel applets that simply
display the output of a command.  It is also useful for testing 
battery status data gathering algorithms in a form easily changed
and easily run on a variety of devices - before commiting to C code
in less dynamic (but more efficient) panel applets.
