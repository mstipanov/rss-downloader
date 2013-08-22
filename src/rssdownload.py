#!/usr/bin/env python
"""
    print node.toxml() 
"""
import os
import sys
import re
import urllib
import time
import xml.sax.handler
import xml.sax
from urllib import urlopen
import logging

logger = logging.getLogger('rssdownload')

class Feed:
    def __init__(self, url=None, baseUrl=None, pattern=None):
        self.name = None
        self.url = url
        self.baseUrl = baseUrl
        self.pattern = pattern

    def toString(self):
        return "Feed{name: '%s', url: '%s', baseUrl: '%s', pattern: '%s'}" % (
        self.name, self.url, self.baseUrl, self.pattern)

class FeedHandler(xml.sax.handler.ContentHandler):
    def __init__(self):
        self.inName = False
        self.inUrl = False
        self.inBaseUrl = False
        self.inPattern = False
        self.feeds = []

    def startElement(self, name, attributes):
        if name == "feed":
            self.inName = False
            self.inUrl = False
            self.inBaseUrl = False
            self.inPattern = False
            self.feed = Feed()
            self.feeds.append(self.feed)
        elif name == "name":
            self.inName = True
        elif name == "url":
            self.inUrl = True
        elif name == "baseUrl":
            self.inBaseUrl = True
        elif name == "pattern":
            self.inPattern = True

    def characters(self, data):
        if self.inName:
            if(self.feed.name is None):
                self.feed.name = data
            else:
                self.feed.name += data
        elif self.inUrl:
            if(self.feed.url is None):
                self.feed.url = data
            else:
                self.feed.url += data
        elif self.inBaseUrl:
            if(self.feed.baseUrl is None):
                self.feed.baseUrl = data
            else:
                self.feed.baseUrl += data
        elif self.inPattern:
            if(self.feed.pattern is None):
                self.feed.pattern = data
            else:
                self.feed.pattern += data

    def endElement(self, name):
        if name == "name":
            self.inName = False
        elif name == "url":
            self.inUrl = False
        elif name == "baseUrl":
            self.inBaseUrl = False
        elif name == "pattern":
            self.inPattern = False

class RuleDataSource:
    def __init__(self, setting):
        self.setting = setting

    def findRules(self):
        return readNonEmptyLines(self.setting.rulesFile)

class ItemDataSource:
    def __init__(self, setting):
        self.setting = setting

    def obeysAnyRule(self, item, rules):
        for rule in rules:
            if self.obeysRule(item, rule):
                return True
        return False

    def obeysRule(self, item, rule):
        pattern = re.compile(rule, re.IGNORECASE)
        m = pattern.match(item.title)
        if m:
            return True
        return False

    def findItems(self, ruleDataSource, feedDataSource):
        rules = ruleDataSource.findRules()
        feeds = feedDataSource.findFeeds()
        itemList = []

        for feed in feeds:
            content = download(feed.url)
            pattern = re.compile(feed.pattern, re.IGNORECASE)
            for m in pattern.finditer(content):
                link = m.group("link")
                if(not feed.baseUrl is None):
                    link = feed.baseUrl + link
                item = Item(self.setting, m.group("title"), link)
                if self.obeysAnyRule(item, rules):
                    itemList.append(item)
        return itemList

class Item:
    def __init__(self, setting, title=None, link=None):
        self.link = link
        if(title is None):
            self.title = link
        else:
            self.title = title
        self.openRetries = 0
        self.setting = setting

    def toString(self):
        return "Item (title = '" + self.title + "', self.link = '" + self.link + "')"

    def openURL(self):
        log("Opening URL: %s" % (self.openRetries)) #debug
        try:
            return urlopen(self.link, None, None) #todo: proxy see: http://snippets.dzone.com/posts/show/2887
        except IOError:
            if self.openRetries >= 10:
                raise
            else:
                self.openRetries = self.openRetries + 1
                return self.openURL()

    def createDownload(self):
        self.openRetries = 1
        return self.retryDownload(0)

    def retryDownload(self, createRetries):
        createRetries = createRetries + 1

        if createRetries >= 10:
            return None

        instream = self.openURL()

        if instream is None:
            time.sleep(10)
            log("Retrying...")
            return instream, self.retryDownload(createRetries)

        filename = instream.info().getheader("Content-Disposition")

        if filename is None:
            filename = self.link[lastIndexOf(self.link, "/") + 1: len(self.link)]
        else:
            filename = filename[filename.index("=") + 1: len(filename)].replace("\"", "").replace("'", "").replace(";", "")

        return instream, filename

    def download(self):
        log("Getting file name for: %s" % (self.title))
        instream, filename = self.createDownload()
        if filename is None:
            log("Can't access server: %s" % (self.title))
            return

        tempFilename = "%s%s%s" % (self.setting.getDownloadDir(), os.sep, filename)
        if os.path.exists(tempFilename):
            log("Skipping file: %s" % (filename))
        else:
            log("Downloading file: %s" % (filename))
            file = open(tempFilename, "w")
            file.write(instream.read())
            file.close()
            if(self.setting.getDownloadDir() != self.setting.outputDir):
                targetFilename = "%s%s%s" % (self.setting.outputDir, os.sep, filename)
                copyFile(tempFilename, targetFilename)
        instream.close()

    def addAttribute(self, name, value):
        s = "self.%s=%s" % (name, value)
        exec(s)

class FeedDataSource:
    def __init__(self, setting):
        self.setting = setting

    def findFeeds(self):
        try:
            log("Reading feeds as XML...")
            parser = xml.sax.make_parser()
            handler = FeedHandler()
            parser.setContentHandler(handler)
            parser.parse(self.setting.feedsFile)
            return handler.feeds
        except:
            log("Error reading feeds as XML from file ", self.setting.feedsFile, " - ", sys.exc_info())
            log("Reading feeds as plain text ...")
            feeds = []
            for url in readNonEmptyLines(self.setting.feedsFile):
                feeds.append(
                        Feed(url, r"(?s)<item>.*?<title>(?P<title>.*?)</title>.*?<link>(?P<link>.*?)</link>.*?</item>"))
            return feeds

def copyFile(sourceFile, targetFile):
    tempFile = "%s%s" % (targetFile, ".part")
    infile = open(sourceFile, "r")
    outfile = open(tempFile, "w")
    outfile.write(infile.read())
    infile.close()
    outfile.close()
    os.rename(tempFile, targetFile)

class Setting:
    def __init__(self, debug):
        self.rulesFile = None
        self.feedsFile = None
        self.outputDir = os.curdir
        self.cacheDir = None
        self.logsDir = None
        self.waitPeriod = float(600)
        self.debug = debug

    def getDownloadDir(self):
        if(self.cacheDir is None):
            return self.outputDir

        dir = os.path.expanduser(self.cacheDir)
        if not os.path.exists(dir):
            os.makedirs(dir)
        return dir


def readTextFile(f):
    file = open(f, "r")
    content = file.read()
    file.close()
    return content

def readNonEmptyLines(f):
    content = readTextFile(f)
    rules = []
    for rule in content.split("\n"):
        if '' != rule:
            rules.append(rule)
    return rules

def download(url):
    log("Downloading: %s" % url)
    f = urllib.urlopen(url)
    return f.read()

def lastIndexOf(str, sub):
    index = -1
    i = 0
    while True:
        i = str.find(sub, i + 1)
        if(i < 0):
            break
        index = i

    return index

def start(setting):
    try:
        log("Started!")
        ruleDataSource = RuleDataSource(setting)
        feedDataSource = FeedDataSource(setting)
        itemDataSource = ItemDataSource(setting)
        for item in itemDataSource.findItems(ruleDataSource, feedDataSource):
            try:
                item.download()
            except:
                log("Unexpected error:", sys.exc_info())
                log("Continuing to next item...")
        log("Finished!")
    except:
        log("Unexpected error:", sys.exc_info())

def parseArguments(setting, args):
    for i in range(0, len(args) - 1):
        arg = args[i]
        if arg == "-r" or arg == "--rules-file":
            setting.rulesFile = args[i + 1].strip()
        elif arg == "-f" or arg == "--feeds-file":
            setting.feedsFile = args[i + 1].strip()
        elif arg == "-o" or arg == "--output-dir":
            setting.outputDir = args[i + 1].strip()
        elif arg == "-c" or arg == "--cache-dir":
            setting.cacheDir = args[i + 1].strip()
        elif arg == "-p" or arg == "--wait-period":
            setting.waitPeriod = float(args[i + 1].strip())
        elif arg == "-l" or arg == "--logs-dir":
            setting.logsDir = args[i + 1].strip()

def configureLogging(setting):
    logger.setLevel(logging.DEBUG)

    if(setting.logsDir):
        fh = logging.FileHandler(setting.logsDir + '/rssdownload.log')
        if(setting.debug):
            fh.setLevel(logging.DEBUG)
        else:
            fh.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        fh.setFormatter(formatter)
        logger.addHandler(fh)

    # create console handler with a higher log level
    ch = logging.StreamHandler()
    if(setting.debug):
        ch.setLevel(logging.DEBUG)
    else:
        ch.setLevel(logging.INFO)
    logger.addHandler(ch)

def log(args):
    logger.info(args)
