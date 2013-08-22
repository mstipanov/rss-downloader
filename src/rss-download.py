#!/usr/bin/env python
"""
    print node.toxml()
"""
import time
import traceback
from rssdownload import start, parseArguments, Setting, configureLogging, log
import sys

debug = False

setting = Setting(debug)
try:
    parseArguments(setting, sys.argv[1:]) # ignore program name
    configureLogging(setting)
    while 1:
        start(setting)
        if setting.waitPeriod < 1:
            break
        log("Waiting ...")
        time.sleep(setting.waitPeriod)
except Exception, e:
    exc_type, exc_value, exc_traceback = sys.exc_info()
    traceback.print_tb(exc_traceback, limit=100, file=sys.stderr)
    print e
    if(debug):
        log(e)
    log("Usage rss-download.py <options>\n\nOptions:\n-r\t--rules-file\tFile with rules spacification\n-f\t--feeds-file\tFile with RSS feeds URLs\n-o\t--output-dir\tThe output directory (Default is the current dir)\n-c\t--cache-dir\tThe cache directory (Default is the current dir)\n-p\t--wait-period\tWait period in seconds, after each check (Default is 600)\n-p\t--wait-period\tWait period in seconds, after each check (Default is 600)\n-l\t--logs-dir\tLogs direcotry")
