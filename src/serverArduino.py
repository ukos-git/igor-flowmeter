#!/usr/bin/env python
import time

from MKArduino import MKArduino

arduino = MKArduino()

threads = []
threads.append(arduino)

for t in threads:
    print "starting ..."
    t.start()
    t.debug()

try:
    while True:
        time.sleep(10)
except KeyboardInterrupt:
    for t in threads:
        print "stoping ..."
        t.stop()

